"""GLB-backed Omnigod 13-plate edit-track regression and mutation tests."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import wave
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import build_omnigod_cinematic as motion
import build_omnigod_presentation_handoff as handoff
import build_omnigod_sequence_tracks as tracks

class SequencerTracksTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "audio").mkdir()
        doc = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": 0}],
               "bufferViews": [], "accessors": [],
               "nodes": [{"name": "Prototype_" + p, "translation": [0, 0, 0]}
                         for p in motion.PARTS],
               "meshes": [{} for _ in motion.PARTS]}
        binary = bytearray()
        motion.animate(doc, binary)
        (self.root / "omnigod_mechanical_motion.glb").write_bytes(
            motion.pack_glb(doc, binary))
        for name, duration in (("eclipse_subpulse", 1300),
                               ("iron_plate_lock", 480), ("void_separation", 1100)):
            with wave.open(str(self.root / "audio" / (name + ".wav")), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(16000)
                wav.writeframes(b"\x00\x00" * (16 * duration))
        self.cue = {
            "schema_version": 1, "mode": "FUS-001",
            "enabled_for_native_activation": False, "native_uefn_import": "not_run",
            "npc_skeletal_rig": False, "animations": list(motion.CLIPS),
            "accessibility": {"reduced_flash": True, "non_color_cues": True,
                              "screen_flash_count": 0},
            "binding_rules": {
                "requires_authoritative_generation": True,
                "abort_cancels_all_cues": True,
                "cleanup_before_canonical_abort": True,
                "owner_sequence_visibility": "Instigator_Only_no_replaceable_npc_binding",
                "npc_replaceable_binding_visibility": "Everyone_separate_sequence"},
            "lod_policy": [{"tier": "near", "max_particles": 80},
                           {"tier": "mid", "max_particles": 24},
                           {"tier": "far", "max_particles": 0}],
            "cue_events": [
                {"phase": phase, "name": name, "time_seconds": start / 1000,
                 "shape": shape, "audio": audio, "visibility": "instigator_only"}
                for phase, name, start, shape, audio, _ in handoff.EXPECTED_CUES],
            "files": []}
        self.refresh()
        handoff.build(self.root)

    def refresh(self):
        self.cue["files"] = [
            {"path": p, "bytes": (self.root / p).stat().st_size,
             "sha256": hashlib.sha256((self.root / p).read_bytes()).hexdigest()}
            for p in sorted(handoff.SOURCE_FILES)]
        (self.root / "cue_sheet.json").write_text(json.dumps(self.cue), encoding="utf-8")

    def test_real_binary_animation_channels_and_event_counts(self):
        tracks.build(self.root)
        self.assertEqual(tracks.validate(self.root), [])
        plan = json.loads((self.root / tracks.JSON_NAME).read_text())
        self.assertEqual(len(plan["plate_tracks"]), 26)
        self.assertEqual(plan["row_count"], 146)
        self.assertEqual(sum(r["role"] == "npc_plate_translation" for r in plan["rows"]), 130)
        self.assertEqual(sum(r["role"] == "owner_camera_dolly" for r in plan["rows"]), 10)
        self.assertEqual(sum(r["role"] == "owner_caption" for r in plan["rows"]), 3)
        self.assertEqual(sum(r["role"] == "owner_audio_cue" for r in plan["rows"]), 3)
        self.assertFalse(plan["enabled_for_native_activation"])

    def test_visibility_accessibility_and_non_native_status(self):
        plan, _ = tracks.compile_tracks(self.root)
        self.assertEqual(plan["native_uefn_import"], "not_run")
        self.assertEqual(plan["reduced_motion"]["screen_flashes"], 0)
        self.assertTrue(plan["reduced_motion"]["non_color_cues"])
        self.assertTrue(all(r["visibility"] == "instigator_only"
                            for r in plan["rows"] if r["role"].startswith("owner_")))
        self.assertTrue(all(r["visibility"] == "everyone_npc_sequence"
                            for r in plan["rows"] if r["role"] == "npc_plate_translation"))

    def test_deterministic_regeneration(self):
        tracks.build(self.root)
        names = (tracks.JSON_NAME, tracks.CSV_NAME, tracks.MANIFEST_NAME)
        initial = {name: (self.root / name).read_bytes() for name in names}
        tracks.build(self.root)
        self.assertEqual(initial, {name: (self.root / name).read_bytes() for name in names})

    def test_csv_tampering_rejected(self):
        tracks.build(self.root)
        path = self.root / tracks.CSV_NAME
        path.write_bytes(path.read_bytes().replace(b"instigator_only", b"everyone"))
        self.assertTrue(any("content drift" in e for e in tracks.validate(self.root)))

    def test_native_status_forgery_rejected(self):
        tracks.build(self.root)
        path = self.root / tracks.JSON_NAME
        plan = json.loads(path.read_text())
        plan["native_sequencer_binding"] = "verified"
        path.write_text(json.dumps(plan))
        self.assertTrue(any("content drift" in e for e in tracks.validate(self.root)))

    def test_manifest_hash_forgery_rejected(self):
        tracks.build(self.root)
        path = self.root / tracks.MANIFEST_NAME
        manifest = json.loads(path.read_text())
        manifest["files_sha256"][tracks.CSV_NAME] = "0" * 64
        path.write_text(json.dumps(manifest))
        self.assertTrue(any("provenance/status" in e for e in tracks.validate(self.root)))

    def test_glb_clip_mutation_even_when_rehashed(self):
        doc, binary = motion.read_glb(self.root / "omnigod_mechanical_motion.glb")
        doc["animations"][0]["name"] = "FORGED"
        (self.root / "omnigod_mechanical_motion.glb").write_bytes(
            motion.pack_glb(doc, binary))
        self.refresh()
        handoff.build(self.root)
        with self.assertRaisesRegex(ValueError, "GLB animation clip"):
            tracks.build(self.root)

    def test_missing_glb_rotation_channel_rejected(self):
        doc, binary = motion.read_glb(self.root / "omnigod_mechanical_motion.glb")
        doc["animations"][0]["channels"].pop()
        (self.root / "omnigod_mechanical_motion.glb").write_bytes(
            motion.pack_glb(doc, binary))
        self.refresh()
        handoff.build(self.root)
        with self.assertRaisesRegex(ValueError, "GLB channel count"):
            tracks.build(self.root)

    def test_upstream_owner_binding_forgery_rejected(self):
        path = self.root / "presentation_handoff.json"
        plan = json.loads(path.read_text())
        plan["native_devices_bound"] = True
        path.write_text(json.dumps(plan))
        self.assertTrue(any("upstream presentation" in e for e in tracks.validate(self.root)))

    def test_audio_owner_visibility_rejected(self):
        self.cue["cue_events"][0]["visibility"] = "everyone"
        self.refresh()
        with self.assertRaisesRegex(ValueError, "visibility"):
            handoff.build(self.root)


    def test_glb_plate_translation_values_rejected_even_when_rehashed(self):
        import struct
        doc, binary = motion.read_glb(self.root / "omnigod_mechanical_motion.glb")
        sampler = doc["animations"][0]["samplers"][0]
        output = doc["accessors"][sampler["output"]]
        view = doc["bufferViews"][output["bufferView"]]
        offset = view.get("byteOffset", 0) + output.get("byteOffset", 0)
        struct.pack_into("<f", binary, offset, 1000.0)
        (self.root / "omnigod_mechanical_motion.glb").write_bytes(
            motion.pack_glb(doc, binary))
        self.refresh()
        handoff.build(self.root)
        with self.assertRaisesRegex(ValueError, "actual plate/rotation keyframe"):
            tracks.build(self.root)

    def test_per_plate_sampler_time_forgery_rejected(self):
        doc, binary = motion.read_glb(self.root / "omnigod_mechanical_motion.glb")
        doc["animations"][0]["samplers"][1]["input"] = doc["animations"][1]["samplers"][0]["input"]
        (self.root / "omnigod_mechanical_motion.glb").write_bytes(
            motion.pack_glb(doc, binary))
        self.refresh()
        handoff.build(self.root)
        with self.assertRaisesRegex(ValueError, "per-plate time sampler"):
            tracks.build(self.root)

if __name__ == "__main__":
    unittest.main()
