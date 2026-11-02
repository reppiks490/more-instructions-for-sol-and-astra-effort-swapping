"""Source-only deterministic presentation handoff and corruption regressions."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import build_omnigod_presentation_handoff as handoff


def sha(data):
    return hashlib.sha256(data).hexdigest()


class PresentationHandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "audio").mkdir()
        (self.root / "omnigod_mechanical_motion.glb").write_bytes(b"fixture-not-a-GLB")
        for name, duration in (("eclipse_subpulse", 1300),
                               ("iron_plate_lock", 480), ("void_separation", 1100)):
            with wave.open(str(self.root / "audio" / (name + ".wav")), "wb") as sound:
                sound.setnchannels(1)
                sound.setsampwidth(2)
                sound.setframerate(16000)
                sound.writeframes(b"\x00\x00" * (16 * duration))
        self.cue = {
            "schema_version": 1, "mode": "FUS-001",
            "enabled_for_native_activation": False, "native_uefn_import": "not_run",
            "npc_skeletal_rig": False,
            "animations": ["AEON_FUS001_Fusion_Preview", "AEON_FUS001_Separation_Preview",
                           "AEON_OMNI_DormantBreath_Preview"],
            "accessibility": {"reduced_flash": True, "non_color_cues": True,
                              "screen_flash_count": 0},
            "binding_rules": {"requires_authoritative_generation": True,
                              "abort_cancels_all_cues": True,
                              "cleanup_before_canonical_abort": True,
                              "owner_sequence_visibility": "Instigator_Only_no_replaceable_npc_binding",
                              "npc_replaceable_binding_visibility": "Everyone_separate_sequence"},
            "lod_policy": [{"tier": "near", "max_particles": 80},
                           {"tier": "mid", "max_particles": 24},
                           {"tier": "far", "max_particles": 0}],
            "cue_events": [{"phase": phase, "name": name, "time_seconds": start / 1000,
                            "shape": shape, "audio": wav, "visibility": "instigator_only"}
                           for phase, name, start, shape, wav, _ in handoff.EXPECTED_CUES],
            "files": []}
        self.refresh_inventory()

    def refresh_inventory(self):
        self.cue["files"] = [{"path": rel,
                              "sha256": sha((self.root / rel).read_bytes()),
                              "bytes": (self.root / rel).stat().st_size}
                             for rel in sorted(handoff.SOURCE_FILES)]
        (self.root / "cue_sheet.json").write_text(json.dumps(self.cue), encoding="utf-8")

    def test_real_webvtt_and_machine_readable_binding_plan(self):
        handoff.build(self.root)
        self.assertEqual(handoff.validate(self.root), [])
        plan = json.loads((self.root / "presentation_handoff.json").read_text())
        self.assertFalse(plan["native_devices_bound"])
        self.assertEqual(plan["native_uefn_import"], "not_run")
        self.assertEqual(len(plan["bindings"]), 3)
        self.assertEqual([b["end_ms"] for b in plan["bindings"]], [1300, 3580, 1100])
        self.assertEqual(plan["lod_design_caps_unmeasured"][2]["max_particles"], 0)
        text = (self.root / "captions" / "fusion_owner.vtt").read_text()
        self.assertTrue(text.startswith("WEBVTT\n\n"))
        self.assertIn("00:00:03.100 --> 00:00:03.580", text)
        self.assertIn("Armor plates lock", text)
        self.assertIn("cleanup", plan["authority_requirements"])

    def test_byte_identical_regeneration(self):
        handoff.build(self.root)
        files = {p: (self.root / p).read_bytes()
                 for p in (*handoff.GENERATED_FILES, "presentation_handoff_manifest.json")}
        handoff.build(self.root)
        self.assertEqual(files, {p: (self.root / p).read_bytes() for p in files})

    def test_tampered_caption_is_rejected(self):
        handoff.build(self.root)
        caption = self.root / "captions" / "fusion_owner.vtt"
        caption.write_text(caption.read_text().replace("Armor plates lock", "Silent"))
        self.assertTrue(any("caption timeline" in error for error in handoff.validate(self.root)))

    def test_tampered_binding_and_manifest_are_rejected(self):
        handoff.build(self.root)
        plan_path = self.root / "presentation_handoff.json"
        plan = json.loads(plan_path.read_text())
        plan["native_devices_bound"] = True
        plan_path.write_text(json.dumps(plan))
        self.assertTrue(any("unsafe native claim" in error for error in handoff.validate(self.root)))
        handoff.build(self.root)
        package = self.root / "presentation_handoff_manifest.json"
        package.write_text(package.read_text().replace("not_run", "success"))
        self.assertTrue(any("inventory/status" in error for error in handoff.validate(self.root)))

    def test_phase_and_owner_visibility_must_match(self):
        self.cue["cue_events"][0]["visibility"] = "everyone"
        self.refresh_inventory()
        with self.assertRaisesRegex(ValueError, "visibility"):
            handoff.build(self.root)
        self.cue["cue_events"][0]["visibility"] = "instigator_only"
        self.cue["cue_events"][1]["time_seconds"] = 3.2
        self.refresh_inventory()
        with self.assertRaisesRegex(ValueError, "out-of-order"):
            handoff.build(self.root)

    def test_audio_duration_mismatch_even_with_fresh_hash(self):
        with wave.open(str(self.root / "audio" / "iron_plate_lock.wav"), "wb") as sound:
            sound.setnchannels(1)
            sound.setsampwidth(2)
            sound.setframerate(16000)
            sound.writeframes(b"\x00\x00" * 12000)
        self.refresh_inventory()
        with self.assertRaisesRegex(ValueError, "audio duration mismatch"):
            handoff.build(self.root)

    def test_mutated_asset_hash_or_privilege_is_rejected(self):
        self.cue["files"][0]["sha256"] = "0" * 64
        (self.root / "cue_sheet.json").write_text(json.dumps(self.cue))
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            handoff.build(self.root)
        self.refresh_inventory()
        self.cue["enabled_for_native_activation"] = True
        self.refresh_inventory()
        with self.assertRaisesRegex(ValueError, "native success"):
            handoff.build(self.root)

    def test_reduced_flash_contract_is_required(self):
        self.cue["accessibility"]["screen_flash_count"] = 1
        self.refresh_inventory()
        with self.assertRaisesRegex(ValueError, "inaccessible"):
            handoff.build(self.root)


if __name__ == "__main__":
    unittest.main()
