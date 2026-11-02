"""Real full-universe terrain source tests; no UEFN native tests are inferred."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import build_all_region_terrain as builder
import validate_all_region_terrain as checker


class AllThirteenLandscapeSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.output=Path(cls.temp.name)/"world"
        cls.manifest=builder.generate(cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_full_thirteen_region_data_passes(self):
        self.assertEqual(checker.validate(self.output),[])

    def test_not_one_region_is_silently_missing(self):
        self.assertEqual(len(self.manifest["regions"]),13)
        self.assertEqual({r["region_id"] for r in self.manifest["regions"]},
                         set(builder.REGION_SLUGS))
        for item in self.manifest["regions"]:
            self.assertTrue((self.output/item["r16"]).is_file())
            self.assertTrue((self.output/item["png"]).is_file())

    def test_all_13_png16_r16_pairs_have_actual_pixel_equality(self):
        for entry in self.manifest["regions"]:
            numeric=struct.unpack("<"+str(builder.N**2)+"H",
                                  (self.output/entry["r16"]).read_bytes())
            decoded=checker.decode_png16((self.output/entry["png"]).read_bytes())
            self.assertEqual(list(numeric),decoded,entry["region_id"])

    def test_original_ossuary_terrain_is_preserved_exactly(self):
        original=(builder.OSSUARY/"ossuary_march_253.r16").read_bytes()
        current=(self.output/"REG-001"/"ossuary_march_253.r16").read_bytes()
        self.assertEqual(original,current)

    def test_every_other_terrain_profile_is_unique(self):
        shas={r["r16_sha256"] for r in self.manifest["regions"]}
        self.assertEqual(len(shas),13)
        for r in self.manifest["regions"]:
            self.assertGreater(r["max_height_m"]-r["min_height_m"],3.0)

    def test_consistent_unreal_landscape_source_resolution(self):
        f=self.manifest["format"]
        self.assertEqual(f["resolution"],[253,253])
        self.assertEqual(f["landscape_component_grid"],[4,4])
        self.assertEqual(f["quads_per_section"],63)
        self.assertEqual(f["xy_spacing_cm"],200)

    def test_no_native_uefn_completion_claim(self):
        self.assertTrue(self.manifest["source_terrain_only"])
        self.assertFalse(self.manifest["region_completion_claim"])
        for key in ("uefn_landscape_import","world_partition_assembled",
                    "navigation_compiled","fortnite_mobile_playtest",
                    "publishing_memory_calculated"):
            self.assertEqual(self.manifest[key],"not_run")

    def test_canonical_world_neighbor_topology_is_preserved(self):
        canonical={r["id"]:r["neighbors"] for r in
                   json.loads(builder.WORLD.read_text())["regions"]}
        self.assertEqual(
            {r["region_id"]:r["neighbor_ids"] for r in self.manifest["regions"]},
            canonical
        )

    def test_generation_is_deterministic_including_every_region(self):
        with tempfile.TemporaryDirectory() as tmp:
            second=builder.generate(Path(tmp)/"second")
            self.assertEqual(second,self.manifest)
            for region in self.manifest["regions"]:
                for kind in ("png","r16"):
                    path=region[kind]
                    self.assertEqual((self.output/path).read_bytes(),
                                     (Path(tmp)/"second"/path).read_bytes())

    def mutate(self,func):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"world"
            shutil.copytree(self.output,dest)
            func(dest)
            self.assertTrue(checker.validate(dest))

    def change_manifest(self,func):
        def action(dst):
            path=dst/"manifest.json"
            value=json.loads(path.read_text(encoding="utf-8"))
            func(value)
            path.write_text(json.dumps(value),encoding="utf-8")
        self.mutate(action)

    def test_falsely_finished_region_status_is_rejected(self):
        self.change_manifest(lambda m:m.__setitem__("region_completion_claim",True))

    def test_falsely_imported_uefn_is_rejected(self):
        self.change_manifest(lambda m:m.__setitem__("uefn_landscape_import","passed"))

    def test_misreported_fortnite_mobile_playtest_is_rejected(self):
        self.change_manifest(lambda m:m.__setitem__("fortnite_mobile_playtest","passed"))

    def test_deleted_landscape_is_rejected(self):
        self.mutate(lambda d:(d/"REG-013"/"threshold_of_zero_253.r16").unlink())

    def test_original_ossuary_replacement_is_rejected(self):
        def action(dst):
            p=dst/"REG-001"/"ossuary_march_253.r16"
            b=bytearray(p.read_bytes())
            b[0]^=1
            p.write_bytes(b)
        self.mutate(action)

    def test_corrupted_png_crc_is_rejected(self):
        def action(dst):
            p=dst/"REG-012"/"axiom_scar_253.png"
            raw=bytearray(p.read_bytes())
            raw[47]^=1
            p.write_bytes(raw)
        self.mutate(action)

    def test_wrong_region_neighbor_is_rejected(self):
        self.change_manifest(
            lambda m:m["regions"][1].__setitem__("neighbor_ids",["REG-999"]))

    def test_duplicate_terrain_hash_is_rejected(self):
        def action(dst):
            a=dst/"REG-003"/"crownless_tempest_253.r16"
            b=dst/"REG-002"/"black_sun_meridian_253.r16"
            a.write_bytes(b.read_bytes())
        self.mutate(action)

    def test_terrain_byte_count_and_hash_are_verified(self):
        self.change_manifest(
            lambda m:m["regions"][5].__setitem__("r16_sha256","0"*64))

    def test_invented_fourteenth_region_is_rejected(self):
        def action(m):
            m["regions"].append(dict(m["regions"][0],region_id="REG-014"))
            m["terrain_region_count"]=14
        self.change_manifest(action)


if __name__=="__main__":
    unittest.main()
