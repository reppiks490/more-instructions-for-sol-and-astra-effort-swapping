"""Source-level glTF animation regression tests, NOT native Verse/UEFN tests."""
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
import build_omnigod_manifestation_assets as geometry
import build_omnigod_fusion_animation as builder
import validate_omnigod_fusion_animation as checker
import validate_ossuary_starter_assets as glb


class MechanicalFusionAnimationSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.output=Path(cls.temp.name)/"source"
        geometry.generate(cls.output)
        cls.cue=builder.generate(cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def corrupt(self,mutator):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"source"
            shutil.copytree(self.output,target)
            mutator(target)
            self.assertTrue(checker.check_animation(target))

    def test_authored_clip_passes(self):
        self.assertEqual(checker.check_animation(self.output),[])

    def test_rebuild_is_byte_deterministic(self):
        original=(self.output/builder.FILENAME).read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"source"
            geometry.generate(target)
            cue=builder.generate(target)
            self.assertEqual(cue,self.cue)
            self.assertEqual((target/builder.FILENAME).read_bytes(),original)

    def test_source_geometry_is_not_mutated_by_clip(self):
        current=hashlib.sha256((self.output/"omnigod_dormant_assembly.glb").read_bytes()).hexdigest()
        builder.generate(self.output)
        self.assertEqual(hashlib.sha256((self.output/"omnigod_dormant_assembly.glb").read_bytes()).hexdigest(),current)

    def test_real_glb_contains_animated_scene(self):
        doc,blob=glb.read_glb(self.output/builder.FILENAME)
        self.assertEqual(len(doc["animations"]),1)
        self.assertEqual(doc["animations"][0]["name"],builder.NAME)
        self.assertEqual(len(doc["animations"][0]["channels"]),len(builder.OFFSETS)+3)
        self.assertEqual(len(doc["nodes"]),13)

    def test_animation_has_actual_module_motion(self):
        doc,blob=glb.read_glb(self.output/builder.FILENAME)
        clip=doc["animations"][0]
        samples={}
        for channel in clip["channels"]:
            target=channel["target"]
            name=doc["nodes"][target["node"]]["name"]
            output=clip["samplers"][channel["sampler"]]["output"]
            samples[(name,target["path"])]=glb.accessor(doc,blob,output)
        x=samples[("Prototype_Pauldron_L","translation")]
        self.assertLess(x[2][0],x[0][0]-.5)
        y=samples[("Prototype_Pauldron_R","translation")]
        self.assertGreater(y[2][0],y[0][0]+.5)
        core=samples[("Prototype_AxiomCore","scale")]
        self.assertGreater(core[3][0],core[0][0]+.5)
        halo=samples[("Prototype_Eclipse","rotation")]
        self.assertNotEqual(halo[0],halo[3])

    def test_timeline_provides_accessible_noncolor_cues(self):
        self.assertEqual(len(self.cue["beats"]),len(builder.TIMES))
        self.assertTrue(all(beat["telegraph"] and beat["audio"] for beat in self.cue["beats"]))

    def test_clip_has_no_false_native_status(self):
        self.assertEqual(self.cue["fortnite_launch_session"],"not_run")
        self.assertEqual(self.cue["native_uefn_compile"],"not_run")
        self.assertFalse(self.cue["skeletal_rig"])
        self.assertFalse(self.cue["real_audio_generated"])
        self.assertFalse(self.cue["owner_entitlement_modified"])

    def test_sha_tampering_rejected(self):
        def mutate(d):
            p=d/builder.TIMELINE
            obj=json.loads(p.read_text(encoding="utf-8"))
            obj["glb_sha256"]="0"*64
            p.write_text(json.dumps(obj),encoding="utf-8")
        self.corrupt(mutate)

    def test_malformed_glb_rejected(self):
        def mutate(d):
            f=d/builder.FILENAME
            f.write_bytes(f.read_bytes()[:-17])
        self.corrupt(mutate)

    def test_no_fabricated_uefn_import(self):
        def mutate(d):
            p=d/builder.TIMELINE
            obj=json.loads(p.read_text(encoding="utf-8"))
            obj["native_uefn_sequencer"]="passed"
            p.write_text(json.dumps(obj),encoding="utf-8")
        self.corrupt(mutate)

    def test_no_owner_entitlement_mutation(self):
        def mutate(d):
            p=d/builder.TIMELINE
            obj=json.loads(p.read_text(encoding="utf-8"))
            obj["owner_entitlement_modified"]=True
            p.write_text(json.dumps(obj),encoding="utf-8")
        self.corrupt(mutate)

    def test_no_fake_skeletal_claim(self):
        def mutate(d):
            p=d/builder.TIMELINE
            obj=json.loads(p.read_text(encoding="utf-8"))
            obj["skeletal_rig"]=True
            p.write_text(json.dumps(obj),encoding="utf-8")
        self.corrupt(mutate)

    def test_no_playable_titan_unlock(self):
        def mutate(d):
            p=d/builder.TIMELINE
            obj=json.loads(p.read_text(encoding="utf-8"))
            obj["canonical_mode"]="FUS-002"
            p.write_text(json.dumps(obj),encoding="utf-8")
        self.corrupt(mutate)

    def test_visibility_cue_cannot_falsely_unify_npc_and_owner(self):
        def mutate(d):
            p=d/builder.TIMELINE
            obj=json.loads(p.read_text(encoding="utf-8"))
            obj["visibility_warning"]="owner-only bound NPC"
            p.write_text(json.dumps(obj),encoding="utf-8")
        self.corrupt(mutate)

    def test_animation_target_duplicates_rejected(self):
        def mutate(d):
            file=d/builder.FILENAME
            doc,blob=builder.unpack_glb(file.read_bytes())
            channel=dict(doc["animations"][0]["channels"][0])
            doc["animations"][0]["channels"].append(channel)
            file.write_bytes(builder.pack_glb(doc,blob))
            cue=d/builder.TIMELINE
            meta=json.loads(cue.read_text(encoding="utf-8"))
            meta["glb_sha256"]=hashlib.sha256(file.read_bytes()).hexdigest()
            cue.write_text(json.dumps(meta),encoding="utf-8")
        self.corrupt(mutate)

    def test_scale_explosion_rejected(self):
        def mutate(d):
            path=d/builder.FILENAME
            doc,blob=builder.unpack_glb(path.read_bytes())
            clip=doc["animations"][0]
            for chan in clip["channels"]:
                if chan["target"]["path"]=="scale":
                    accessor=doc["accessors"][clip["samplers"][chan["sampler"]]["output"]]
                    view=doc["bufferViews"][accessor["bufferView"]]
                    import struct
                    offset=view["byteOffset"]+accessor.get("byteOffset",0)
                    struct.pack_into("<f",blob,offset+3*3*4,100.0)
                    break
            path.write_bytes(builder.pack_glb(doc,blob))
            meta=d/builder.TIMELINE
            obj=json.loads(meta.read_text(encoding="utf-8"))
            obj["glb_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
            meta.write_text(json.dumps(obj),encoding="utf-8")
        self.corrupt(mutate)


if __name__=="__main__":
    unittest.main()
