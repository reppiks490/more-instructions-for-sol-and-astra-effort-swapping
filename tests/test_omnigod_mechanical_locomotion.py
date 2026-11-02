"""Source-level tests: five bone-animated Omnigod NPC locomotion roles."""
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
import build_omnigod_rigid_skin as skin
import build_omnigod_mechanical_locomotion as gait
import validate_omnigod_mechanical_locomotion as audit


class MechanicalFiveWaySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        parent=Path(cls.temp.name)
        cls.source_mesh=parent/"model"
        cls.source_clip=parent/"cinema"
        cls.source_skin=parent/"skin"
        cls.output=parent/"gait"
        model.generate(cls.source_mesh)
        cinema.build(cls.source_mesh/"omnigod_dormant_assembly.glb",cls.source_clip)
        skin.build(cls.source_clip/"omnigod_mechanical_motion.glb",cls.source_skin)
        cls.skin=cls.source_skin/skin.FILENAME
        cls.manifest=gait.generate(cls.skin,cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_actual_gltf_bone_locomotion_validates(self):
        self.assertEqual(audit.validate(self.skin,self.output),[])

    def test_five_roles_are_distinct_and_named(self):
        self.assertEqual(list(self.manifest["basic_locomotion_clips"]),["idle","forward","backward","left","right"])
        self.assertEqual(self.manifest["all_clips_count"],8)
        doc,_=cinema.read_glb(self.output/gait.FILENAME)
        self.assertEqual(len(doc["animations"]),8)

    def test_original_three_fusion_cinematic_clips_preserved(self):
        source_doc,_=cinema.read_glb(self.skin)
        output_doc,_=cinema.read_glb(self.output/gait.FILENAME)
        self.assertEqual(output_doc["animations"][:3],source_doc["animations"])

    def test_no_root_motion_and_existing_skin_preserved(self):
        source_doc,_=cinema.read_glb(self.skin)
        output_doc,_=cinema.read_glb(self.output/gait.FILENAME)
        self.assertEqual(source_doc["nodes"],output_doc["nodes"])
        self.assertEqual(source_doc["skins"],output_doc["skins"])
        self.assertTrue(all(ch["target"]["node"]>=14 for a in output_doc["animations"][3:]
                            for ch in a["channels"]))

    def test_determinism_and_source_unmodified(self):
        original=hashlib.sha256(self.skin.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)/"new"
            self.assertEqual(gait.generate(self.skin,d),self.manifest)
            self.assertEqual((d/gait.FILENAME).read_bytes(),
                             (self.output/gait.FILENAME).read_bytes())
        self.assertEqual(hashlib.sha256(self.skin.read_bytes()).hexdigest(),original)

    def test_finite_default_budget_and_in_place(self):
        self.assertTrue(self.manifest["in_place"])
        self.assertEqual(self.manifest["frame_count"],17)
        self.assertEqual(self.manifest["max_displacement_m"],0.28)
        self.assertFalse(self.manifest["real_humanoid_locomotion_rig"])

    def test_native_uefn_claims_are_not_fabricated(self):
        for key in ("uefn_npc_character_definition","uefn_animation_preset",
                    "blender_fbx_export","fortnite_launch_session"):
            self.assertEqual(self.manifest[key],"not_run")
        self.assertFalse(self.manifest["native_owner_fusion_enabled"])

    def mutate_manifest(self,fn):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/"gait"
            shutil.copytree(self.output,target)
            file=target/gait.MANIFEST
            obj=json.loads(file.read_text(encoding="utf-8"))
            fn(obj)
            file.write_text(json.dumps(obj),encoding="utf-8")
            self.assertTrue(audit.validate(self.skin,target))

    def mutate_binary(self,fn):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/"gait"
            shutil.copytree(self.output,target)
            file=target/gait.FILENAME
            doc,blob=cinema.read_glb(file)
            fn(doc,blob)
            file.write_bytes(cinema.pack_glb(doc,blob))
            meta=target/gait.MANIFEST
            obj=json.loads(meta.read_text(encoding="utf-8"))
            raw=file.read_bytes()
            obj["output_glb_sha256"]=hashlib.sha256(raw).hexdigest()
            obj["bytes"]=len(raw)
            meta.write_text(json.dumps(obj),encoding="utf-8")
            self.assertTrue(audit.validate(self.skin,target))

    def test_false_uefn_animation_preset_is_rejected(self):
        self.mutate_manifest(lambda x:x.__setitem__("uefn_animation_preset","verified"))

    def test_public_owner_fusion_is_rejected(self):
        self.mutate_manifest(lambda x:x.__setitem__("native_owner_fusion_enabled",True))

    def test_absent_locomotion_role_rejected(self):
        self.mutate_manifest(lambda x:x["basic_locomotion_clips"].pop("left"))

    def test_wrong_canonical_titan_rejected(self):
        self.mutate_manifest(lambda x:x.__setitem__("canonical_fusion_id","FUS-002"))

    def test_falsified_rig_claim_rejected(self):
        self.mutate_manifest(lambda x:x.__setitem__("real_humanoid_locomotion_rig",True))

    def test_unauthorized_root_motion_rejected(self):
        self.mutate_binary(lambda d,b:d["animations"][3]["channels"][0]["target"].__setitem__("node",13))

    def test_missing_animation_channel_rejected(self):
        self.mutate_binary(lambda d,b:d["animations"][3]["channels"].pop())

    def test_duplicate_bone_animation_rejected(self):
        self.mutate_binary(lambda d,b:d["animations"][3]["channels"].__setitem__(0,dict(d["animations"][3]["channels"][1])))

    def test_excessive_bone_offset_rejected(self):
        def fn(doc,blob):
            anim=doc["animations"][3]
            s=anim["samplers"][0]
            a=doc["accessors"][s["output"]]
            v=doc["bufferViews"][a["bufferView"]]
            off=v["byteOffset"]+3*3*4
            original=struct.unpack_from("<f",blob,off)[0]
            struct.pack_into("<f",blob,off,original+9.0)
        self.mutate_binary(fn)

    def test_nonunit_eclipse_quaternion_rejected(self):
        def fn(doc,blob):
            anim=doc["animations"][4]
            ch=next(c for c in anim["channels"] if c["target"]["path"]=="rotation")
            a=doc["accessors"][anim["samplers"][ch["sampler"]]["output"]]
            v=doc["bufferViews"][a["bufferView"]]
            struct.pack_into("<f",blob,v["byteOffset"]+4*4,2.0)
        self.mutate_binary(fn)

    def test_directional_footwork_uses_real_separate_vectors(self):
        doc,blob=cinema.read_glb(self.output/gait.FILENAME)
        values={}
        for anim in doc["animations"][3:]:
            for ch in anim["channels"]:
                if ch["target"]=={"node":14+gait.SLOTS.index("Greave_L"),"path":"translation"}:
                    a=anim["samplers"][ch["sampler"]]["output"]
                    from validate_ossuary_starter_assets import accessor
                    values[anim["name"]]=accessor(doc,blob,a)[4]
        self.assertNotEqual(values[gait.CLIP_NAMES["forward"]],values[gait.CLIP_NAMES["backward"]])
        self.assertNotEqual(values[gait.CLIP_NAMES["left"]],values[gait.CLIP_NAMES["right"]])


if __name__=="__main__":
    unittest.main()
