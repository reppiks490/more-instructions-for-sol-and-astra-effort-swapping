"""Independent source-level original Omnigod rigid-skin regression tests.

These exercise real generated geometry/three motion clips, not UEFN gameplay.
"""
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
import build_omnigod_manifestation_assets as model
import build_omnigod_cinematic as cinema
import build_omnigod_rigid_skin as rig
import validate_omnigod_rigid_skin as validation


class MechanicalSkeletalHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        root=Path(cls.tmp.name)
        cls.source_model=root/"model"
        cls.source_cinema=root/"cinema"
        cls.output=root/"rig"
        model.generate(cls.source_model)
        cinema.build(cls.source_model/"omnigod_dormant_assembly.glb",cls.source_cinema)
        cls.cinematic=cls.source_cinema/"omnigod_mechanical_motion.glb"
        cls.manifest=rig.build(cls.cinematic,cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_generated_real_skin_passes_numerical_validation(self):
        self.assertEqual(validation.inspect(self.cinematic,self.output),[])

    def test_all_13_source_modules_are_rigid_skinned(self):
        self.assertEqual(len(self.manifest["joint_names"]),13)
        self.assertEqual(sum(self.manifest["part_vertex_counts"].values()),
                         self.manifest["skinned_vertices"])
        self.assertTrue(all(n.startswith("J_OMNI_") for n in self.manifest["joint_names"]))

    def test_three_animation_clips_retarget_to_bones(self):
        doc,_=cinema.read_glb(self.output/rig.FILENAME)
        self.assertEqual(len(doc["animations"]),3)
        self.assertTrue(all(len(a["channels"])==14 for a in doc["animations"]))
        self.assertTrue(all(c["target"]["node"]>=14 for a in doc["animations"]
                            for c in a["channels"]))
        self.assertEqual(doc["skins"][0]["joints"],list(range(14,27)))

    def test_actual_weights_and_inverse_bind_matrices_present(self):
        doc,_=cinema.read_glb(self.output/rig.FILENAME)
        for mesh in doc["meshes"]:
            for p in mesh["primitives"]:
                self.assertIn("JOINTS_0",p["attributes"])
                self.assertIn("WEIGHTS_0",p["attributes"])
        self.assertEqual(doc["accessors"][doc["skins"][0]["inverseBindMatrices"]]["type"],"MAT4")

    def test_rebuild_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            regenerated=rig.build(self.cinematic,folder)
            self.assertEqual(self.manifest,regenerated)
            self.assertEqual((folder/rig.FILENAME).read_bytes(),
                             (self.output/rig.FILENAME).read_bytes())
            self.assertEqual((folder/rig.MANIFEST).read_bytes(),
                             (self.output/rig.MANIFEST).read_bytes())

    def test_original_cinematic_geometry_bytes_remain_unchanged(self):
        before=hashlib.sha256(self.cinematic.read_bytes()).hexdigest()
        rig.build(self.cinematic,self.output)
        self.assertEqual(before,hashlib.sha256(self.cinematic.read_bytes()).hexdigest())

    def test_native_uefn_proof_remains_explicitly_unverified(self):
        for key in ("native_uefn_import","native_uefn_compile","fortnite_launch_session",
                    "blender_fbx_export"):
            self.assertEqual(self.manifest[key],"not_run")
        self.assertFalse(self.manifest["humanoid_locomotion_rig"])
        self.assertFalse(self.manifest["native_npc_possession"])
        self.assertFalse(self.manifest["owner_entitlement_modified"])

    def _tamper_manifest(self,mutator):
        with tempfile.TemporaryDirectory() as tmp:
            location=Path(tmp)/"rig"
            shutil.copytree(self.output,location)
            file=location/rig.MANIFEST
            data=json.loads(file.read_text(encoding="utf-8"))
            mutator(data)
            file.write_text(json.dumps(data),encoding="utf-8")
            self.assertTrue(validation.inspect(self.cinematic,location))

    def _tamper_glb(self,mutator):
        with tempfile.TemporaryDirectory() as tmp:
            location=Path(tmp)/"rig"
            shutil.copytree(self.output,location)
            file=location/rig.FILENAME
            doc,blob=cinema.read_glb(file)
            mutator(doc,blob)
            file.write_bytes(cinema.pack_glb(doc,blob))
            manifest=location/rig.MANIFEST
            data=json.loads(manifest.read_text(encoding="utf-8"))
            data["skinned_glb_sha256"]=hashlib.sha256(file.read_bytes()).hexdigest()
            data["skinned_bytes"]=len(file.read_bytes())
            manifest.write_text(json.dumps(data),encoding="utf-8")
            self.assertTrue(validation.inspect(self.cinematic,location))

    def test_false_fbx_success_is_rejected(self):
        self._tamper_manifest(lambda x:x.__setitem__("blender_fbx_export","success"))

    def test_false_humanoid_rig_claim_is_rejected(self):
        self._tamper_manifest(lambda x:x.__setitem__("humanoid_locomotion_rig",True))

    def test_creator_entitlement_mint_is_rejected(self):
        self._tamper_manifest(lambda x:x.__setitem__("owner_entitlement_modified",True))

    def test_titan_mode_is_not_publicly_activatable(self):
        self._tamper_manifest(lambda x:x.__setitem__("canonical_fusion_id","FUS-002"))

    def test_wrong_joint_hierarchy_rejected(self):
        self._tamper_glb(lambda d,b:d["nodes"][13].__setitem__("children",[14,15]))

    def test_wrong_inverse_bind_matrix_rejected(self):
        def mutate(doc,blob):
            accessor=doc["accessors"][doc["skins"][0]["inverseBindMatrices"]]
            view=doc["bufferViews"][accessor["bufferView"]]
            struct.pack_into("<f",blob,view["byteOffset"]+12*4,999.0)
        self._tamper_glb(mutate)

    def test_invalid_weight_allocation_rejected(self):
        def mutate(doc,blob):
            accessor=doc["accessors"][doc["meshes"][0]["primitives"][0]["attributes"]["WEIGHTS_0"]]
            view=doc["bufferViews"][accessor["bufferView"]]
            struct.pack_into("<f",blob,view["byteOffset"],0.9)
        self._tamper_glb(mutate)

    def test_illegal_joint_index_rejected(self):
        def mutate(doc,blob):
            accessor=doc["accessors"][doc["meshes"][0]["primitives"][0]["attributes"]["JOINTS_0"]]
            view=doc["bufferViews"][accessor["bufferView"]]
            struct.pack_into("<H",blob,view["byteOffset"],12)
        self._tamper_glb(mutate)

    def test_missing_skin_binding_rejected(self):
        self._tamper_glb(lambda d,b:d["nodes"][0].pop("skin"))

    def test_mesh_translation_double_transform_rejected(self):
        self._tamper_glb(lambda d,b:d["nodes"][0].__setitem__("translation",[1,1,1]))

    def test_clip_target_unrigged_node_rejected(self):
        self._tamper_glb(lambda d,b:d["animations"][0]["channels"][0]["target"].__setitem__("node",0))

    def test_original_rest_appearance_restoration_rejected_if_baked_wrong(self):
        def mutate(doc,blob):
            pos=doc["meshes"][0]["primitives"][0]["attributes"]["POSITION"]
            a=doc["accessors"][pos]
            view=doc["bufferViews"][a["bufferView"]]
            old=struct.unpack_from("<f",blob,view["byteOffset"])[0]
            struct.pack_into("<f",blob,view["byteOffset"],old+0.5)
        self._tamper_glb(mutate)

    def test_skeletal_glb_checksum_integrity(self):
        self._tamper_manifest(lambda x:x.__setitem__("skinned_glb_sha256","0"*64))


if __name__=="__main__":
    unittest.main()
