"""Full 13-region ORIGINAL static landmark source-artifact regressions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import build_all_region_landmarks as source
import validate_all_region_landmarks as check
import build_ossuary_starter_assets as geometry


class AllRegionLandmarkSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.root=Path(cls.tmp.name)/"landmarks"
        cls.manifest=source.build(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_all_39_real_landmark_source_meshes_validate(self):
        self.assertEqual(check.audit(self.root),[])

    def test_full_world_no_sampling_of_region_coverage(self):
        self.assertEqual(self.manifest["region_count"],13)
        self.assertEqual(self.manifest["source_module_count"],39)
        self.assertEqual(len(self.manifest["files"]),130)
        self.assertEqual(len(self.manifest["regions"]),13)
        self.assertEqual(
            {r["id"] for r in self.manifest["regions"]},
            {f"REG-{i:03d}" for i in range(1,14)})
        self.assertTrue(all(len(r["source_modules"])==3
                            for r in self.manifest["regions"]))

    def test_per_region_palette_and_motif_are_genuinely_distinct(self):
        self.assertEqual(len({r["motif"] for r in self.manifest["regions"]}),13)
        signatures={
            hashlib.sha256((self.root/f"{r['id']}/meshes/{m['mesh']}.glb").read_bytes()).hexdigest()
            for r in self.manifest["regions"]
            for m in r["source_modules"]
        }
        self.assertEqual(len(signatures),39)

    def test_glb_placement_matches_canonical_raw_terrain(self):
        for region in self.manifest["regions"]:
            samples,sw=source.height_samples(region["id"])
            for part in region["source_modules"]:
                expected=source.best_anchor(samples,sw,part["kind"],region["id"])
                self.assertEqual(part["terrain_contact"],expected)
                x,y,z=expected["center_local_m"]
                self.assertEqual(part["placement"]["location_cm"],
                                 [round(x*100),round(y*100),round((z+.65)*100)])

    def test_budget_source_only_and_real_original_provenance(self):
        self.assertLessEqual(self.manifest["total_triangles"],source.MAX_TRIANGLES_TOTAL)
        self.assertTrue(self.manifest["source_artifact_only"])
        self.assertFalse(self.manifest["actual_region_completion"])
        self.assertEqual(self.manifest["native_uefn_import"],"not_run")
        self.assertFalse(self.manifest["npc_navmesh_quest_or_streaming_verified"])

    def test_global_ossuary_material_exporter_is_not_mutated(self):
        old=geometry.MATERIALS
        with tempfile.TemporaryDirectory() as td:
            source.build(Path(td)/"out")
        self.assertIs(geometry.MATERIALS,old)

    def test_generator_is_binary_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            other=Path(td)/"out"
            self.assertEqual(source.build(other),self.manifest)
            for record in self.manifest["files"]:
                path=record["path"]
                self.assertEqual((other/path).read_bytes(),(self.root/path).read_bytes())

    def test_normal_portal_shell_keeps_open_ground_gap(self):
        for number in range(1,14):
            mesh=source.module(number,"ThresholdGate")
            # The center must remain clear of physical source solids below
            # the horizontal lintel; x ±4.5m is an editor design envelope.
            for solid in mesh.solids:
                xs=[p[0] for p in solid["vertices_m"]]
                zs=[p[2] for p in solid["vertices_m"]]
                if min(zs)<6.0 and max(zs)>0.0:
                    self.assertTrue(max(xs)<=-4.5 or min(xs)>=4.5,
                                    f"REG-{number:03d}: low center crossing in {solid['label']}")

    def corrupt(self,mutation):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/"out"
            shutil.copytree(self.root,target)
            mutation(target)
            self.assertTrue(check.audit(target))

    def modify_manifest(self,mutation):
        def update(folder):
            path=folder/"manifest.json"
            data=json.loads(path.read_text(encoding="utf-8"))
            mutation(data)
            path.write_text(json.dumps(data),encoding="utf-8")
        self.corrupt(update)

    def test_false_native_uefn_import_rejected(self):
        self.modify_manifest(lambda m:m.__setitem__("native_uefn_import","passed"))

    def test_false_completed_region_rejected(self):
        self.modify_manifest(lambda m:m.__setitem__("actual_region_completion",True))

    def test_removed_region_rejected(self):
        self.modify_manifest(lambda m:m["regions"].pop())

    def test_missing_mesh_rejected(self):
        self.corrupt(lambda d:(d/"REG-009"/"meshes"/"SM_AEON_REG009_Sanctum.glb").unlink())

    def test_hijacked_terrain_anchor_rejected(self):
        self.modify_manifest(lambda m:m["regions"][10]["source_modules"][0]
                             ["placement"].__setitem__("location_cm",[0,0,0]))

    def test_tampered_png_or_glb_hash_rejected(self):
        self.modify_manifest(lambda m:m["files"][9].__setitem__("sha256","0"*64))

    def test_corrupted_glb_geometry_rejected(self):
        def damage(folder):
            f=folder/"REG-012"/"landmark_preview.glb"
            f.write_bytes(f.read_bytes()[:-32])
        self.corrupt(damage)

    def test_recycled_region_palette_rejected(self):
        self.modify_manifest(lambda m:m["regions"][4].__setitem__(
            "palette",m["regions"][3]["palette"]))

    def test_forged_canonical_neighbor_rejected(self):
        self.modify_manifest(lambda m:m["regions"][8].__setitem__(
            "neighbors",["REG-999"]))

    def test_unknown_fourteenth_region_rejected(self):
        def mutate(m):
            m["regions"].append(dict(m["regions"][0],id="REG-014"))
            m["region_count"]=14
        self.modify_manifest(mutate)


if __name__=="__main__":
    unittest.main()
