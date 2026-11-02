"""Deterministic source-only Omnigod motion and audio regression tests."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_omnigod_manifestation_assets as geometry
import build_omnigod_cinematic as cinematic
import validate_omnigod_cinematic as validator


class CinematicSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.source_dir = cls.root / "source"
        geometry.generate(cls.source_dir)
        cls.source = cls.source_dir / "omnigod_dormant_assembly.glb"

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_real_animation_channels_and_unmodified_geometry(self):
        out = self.root / "motion"
        manifest = cinematic.build(self.source, out)
        original, _ = cinematic.read_glb(self.source)
        animated, _ = cinematic.read_glb(out / "omnigod_mechanical_motion.glb")
        self.assertEqual(len(animated["animations"]), 3)
        self.assertEqual(len(animated["meshes"]), 13)
        self.assertEqual(animated["meshes"], original["meshes"])
        self.assertEqual([x["name"] for x in animated["animations"]], list(cinematic.CLIPS))
        for animation in animated["animations"]:
            self.assertEqual(len(animation["channels"]), 14)
            self.assertEqual(len(animation["samplers"]), 14)
            self.assertEqual({c["target"]["node"] for c in animation["channels"]}, set(range(13)))
            self.assertEqual(sum(c["target"]["path"] == "rotation" for c in animation["channels"]), 1)
            self.assertTrue(all(s["interpolation"] == "LINEAR" for s in animation["samplers"]))
        self.assertFalse(manifest["enabled_for_native_activation"])
        self.assertFalse(manifest["npc_skeletal_rig"])
        self.assertEqual(manifest["native_uefn_import"], "not_run")
        self.assertEqual(manifest["binding_rules"]["npc_replaceable_binding_visibility"],
                         "Everyone_separate_sequence")

    def test_audio_is_actual_bounded_pcm_and_hashes_match(self):
        out = self.root / "sound"
        manifest = cinematic.build(self.source, out)
        self.assertEqual(len(manifest["files"]), 4)
        for item in manifest["files"]:
            path = out / item["path"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"])
            self.assertEqual(path.stat().st_size, item["bytes"])
        for name in cinematic.SOUNDS:
            with wave.open(str(out / "audio" / (name + ".wav")), "rb") as wav:
                self.assertEqual(wav.getnchannels(), 1)
                self.assertEqual(wav.getframerate(), cinematic.SAMPLE_RATE)
                self.assertEqual(wav.getsampwidth(), 2)
                samples = wav.readframes(wav.getnframes())
                peak = max(abs(x[0]) for x in struct.iter_unpack("<h", samples))
                self.assertGreater(peak, 100)
                self.assertLess(peak, 9000)

    def test_determinism_and_budget(self):
        first = cinematic.build(self.source, self.root / "a")
        second = cinematic.build(self.source, self.root / "b")
        self.assertEqual(first, second)
        self.assertEqual(len(first["lod_policy"]), 3)
        self.assertEqual([tier["max_particles"] for tier in first["lod_policy"]], [80, 24, 0])
        self.assertTrue(first["accessibility"]["reduced_flash"])
        self.assertEqual(first["accessibility"]["screen_flash_count"], 0)
        self.assertTrue(first["binding_rules"]["abort_cancels_all_cues"])

    def test_independent_validator_and_mutated_cues(self):
        out = self.root / "validated"
        cinematic.build(self.source, out)
        self.assertEqual(validator.validate(out), [])
        cue_path = out / "cue_sheet.json"
        original = json.loads(cue_path.read_text())
        tampered = json.loads(json.dumps(original))
        tampered["binding_rules"]["abort_cancels_all_cues"] = False
        cue_path.write_text(json.dumps(tampered))
        self.assertTrue(any("cleanup" in e for e in validator.validate(out)))
        tampered = json.loads(json.dumps(original))
        tampered["files"][0]["sha256"] = "0" * 64
        cue_path.write_text(json.dumps(tampered))
        self.assertTrue(any("hash mismatch" in e for e in validator.validate(out)))
        cue_path.write_text(json.dumps(original))
        self.assertEqual(validator.validate(out), [])

    def test_wrong_source_and_corruption_fail_closed(self):
        broken = self.root / "broken.glb"
        broken.write_bytes(b"not a glb")
        with self.assertRaises(ValueError):
            cinematic.build(broken, self.root / "bad")
        source_doc, binary = cinematic.read_glb(self.source)
        source_doc["nodes"][0]["name"] = "Untrusted_Replacement"
        with self.assertRaises(ValueError):
            cinematic.animate(source_doc, binary)


if __name__ == "__main__":
    unittest.main()
