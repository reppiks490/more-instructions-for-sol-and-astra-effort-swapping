"""Deterministic source-asset tests; no UEFN native execution is simulated."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import build_omnigod_manifestation_assets as builder
import validate_omnigod_manifestation_assets as validation
import build_ossuary_starter_assets as geom


class OmnigodSourceGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.output=Path(cls.temp.name)/"pack"
        cls.manifest=builder.generate(cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_pack_passes_source_validation(self):
        self.assertEqual(validation.check_pack(self.output),[])

    def test_source_assets_are_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            second=builder.generate(Path(tmp)/"again")
            self.assertEqual(self.manifest,second)
            a=(self.output/"manifest.json").read_bytes()
            b=(Path(tmp)/"again"/"manifest.json").read_bytes()
            self.assertEqual(hashlib.sha256(a).hexdigest(),hashlib.sha256(b).hexdigest())

    def test_palette_override_is_local(self):
        original=geom.MATERIALS
        with tempfile.TemporaryDirectory() as tmp:
            builder.generate(Path(tmp)/"source")
        self.assertIs(geom.MATERIALS,original)

    def test_lod_and_triangle_budget_are_finite(self):
        budget=self.manifest["budget"]
        self.assertLessEqual(budget["unique_triangles"],builder.MAX_TRIANGLES_PER_PACK)
        self.assertEqual(budget["physical_spawns"],0)
        self.assertGreater(budget["unique_triangles"],200)

    def test_independent_modules_and_stable_anchor_keys(self):
        self.assertEqual(len(self.manifest["parts"]),len(builder.ANCHORS))
        self.assertEqual(len(set(p["mesh"] for p in self.manifest["placements"])),len(builder.ANCHORS))
        self.assertTrue(all(p["planned_socket"] for p in self.manifest["placements"]))

    def test_eclipse_is_an_open_hole_not_solid_blocker(self):
        halo=next(p for p in builder.create_parts() if p.name.endswith("_Eclipse"))
        self.assertGreaterEqual(len(halo.solids),16)
        self.assertTrue(all(s["label"].startswith(("eclipse_plate","crimson_corona")) for s in halo.solids))
        self.assertEqual(next(p for p in self.manifest["placements"] if p["mesh"].endswith("_Eclipse"))["collision"],
                         "disabled_for_cosmetic_proxy")

    def test_not_a_skeletal_or_playable_claim(self):
        self.assertFalse(self.manifest["skeletal_mesh_implemented"])
        self.assertFalse(self.manifest["npc_possession_implemented"])
        self.assertFalse(self.manifest["owner_entitlement_granted"])
        self.assertEqual(self.manifest["launch_session"],"not_run")

    def test_materials_include_crimson_and_violet(self):
        self.assertIn("BloodCrimson",[m["name"] for m in self.manifest["materials"]])
        self.assertIn("AxiomViolet",[m["name"] for m in self.manifest["materials"]])
        self.assertTrue(any(m["emission"] is not None for m in self.manifest["materials"]))

    def test_per_part_obj_contains_actual_faces(self):
        for p in self.manifest["parts"]:
            data=(self.output/"meshes"/(p["id"]+".obj")).read_text(encoding="utf-8")
            self.assertIn("\nf ",data)
            self.assertIn("\nv ",data)

    def test_corrupted_assembly_hash_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst=Path(tmp)/"pack"
            import shutil
            shutil.copytree(self.output,dst)
            file=dst/"omnigod_dormant_assembly.glb"
            data=file.read_bytes()
            file.write_bytes(data[:-4])
            self.assertTrue(validation.check_pack(dst))

    def test_unsupported_native_status_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst=Path(tmp)/"pack"
            import shutil
            shutil.copytree(self.output,dst)
            path=dst/"manifest.json"
            obj=json.loads(path.read_text(encoding="utf-8"))
            obj["native_uefn_import"]="passed"
            path.write_text(json.dumps(obj),encoding="utf-8")
            self.assertTrue(validation.check_pack(dst))

    def test_unauthorized_form_claim_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst=Path(tmp)/"pack"
            import shutil
            shutil.copytree(self.output,dst)
            path=dst/"manifest.json"
            obj=json.loads(path.read_text(encoding="utf-8"))
            obj["canonical_fusion_mode"]="FUS-002"
            path.write_text(json.dumps(obj),encoding="utf-8")
            self.assertTrue(validation.check_pack(dst))

    def test_public_owner_grant_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst=Path(tmp)/"pack"
            import shutil
            shutil.copytree(self.output,dst)
            path=dst/"manifest.json"
            obj=json.loads(path.read_text(encoding="utf-8"))
            obj["owner_entitlement_granted"]=True
            path.write_text(json.dumps(obj),encoding="utf-8")
            self.assertTrue(validation.check_pack(dst))

    def test_wrong_socket_binding_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst=Path(tmp)/"pack"
            import shutil
            shutil.copytree(self.output,dst)
            path=dst/"manifest.json"
            obj=json.loads(path.read_text(encoding="utf-8"))
            obj["placements"][1]["planned_socket"]="public_player_outfit"
            path.write_text(json.dumps(obj),encoding="utf-8")
            self.assertTrue(validation.check_pack(dst))

    def test_crossplayer_cosmetic_collision_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst=Path(tmp)/"pack"
            import shutil
            shutil.copytree(self.output,dst)
            path=dst/"manifest.json"
            obj=json.loads(path.read_text(encoding="utf-8"))
            obj["placements"][0]["collision"]="physical_solid"
            path.write_text(json.dumps(obj),encoding="utf-8")
            self.assertTrue(validation.check_pack(dst))

    def test_deleted_part_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst=Path(tmp)/"pack"
            import shutil
            shutil.copytree(self.output,dst)
            (dst/"meshes"/(self.manifest["parts"][0]["id"]+".obj")).unlink()
            self.assertTrue(validation.check_pack(dst))

    def test_changed_authority_identity_not_in_pack(self):
        data=json.dumps(self.manifest)
        self.assertNotIn("OwnerReference.Register",data)
        self.assertNotIn("EpicAccountId",data)
        self.assertNotIn("account_identity_verified",data)


if __name__=="__main__":
    unittest.main()
