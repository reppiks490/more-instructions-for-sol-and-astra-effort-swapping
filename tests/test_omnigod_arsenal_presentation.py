"""Fail-closed source-only visual/audio/caption regression tests."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import build_omnigod_arsenal_presentation as art


class ArsenalPresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.manifest = art.build(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_full_unique_source_scope(self):
        self.assertEqual(self.manifest["ability_count"], 12)
        self.assertEqual(self.manifest["unique_shape_count"], 12)
        self.assertEqual(self.manifest["audio_event_count"], 14)
        self.assertEqual(len(self.manifest["files"]), 38)
        self.assertEqual(len({x["sha256"] for x in self.manifest["files"] if x["path"].endswith(".png")}), 12)
        self.assertEqual(len({x["sha256"] for x in self.manifest["files"] if x["path"].endswith(".wav")}), 14)
        self.assertEqual(art.validate(self.root), [])

    def test_png_and_pcm_headers(self):
        for item in self.manifest["files"]:
            p = self.root / item["path"]
            data = p.read_bytes()
            self.assertEqual(len(data), item["bytes"])
            self.assertEqual(art.digest(data), item["sha256"])
            if p.suffix == ".png":
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(struct.unpack_from(">II", data, 16), (256, 256))
            if p.suffix == ".wav":
                with wave.open(str(p), "rb") as w:
                    self.assertEqual((w.getnchannels(), w.getsampwidth(), w.getframerate()), (1, 2, 16000))
                    self.assertGreater(w.getnframes(), 0)

    def test_accessibility_and_native_gates(self):
        self.assertFalse(self.manifest["enabled_for_native_activation"])
        self.assertTrue(self.manifest["event_not_damage_or_hit_receipt"])
        self.assertEqual(self.manifest["native_uefn_import"], "not_run")
        self.assertEqual(self.manifest["accessibility"]["reduced_flash_screen_flashes"], 0)
        self.assertEqual(len(self.manifest["region_ids"]), 13)
        self.assertIn("region_unloaded", self.manifest["cleanup_triggers"])

    def test_two_pulses_and_optional_class_bonus(self):
        events = self.manifest["events"]
        self.assertEqual([(e["role"], e["start_ms"]) for e in events if e["ability_id"] == "SFA-005"],
                         [("base_warning", 0), ("pulse_two", 420)])
        self.assertEqual([(e["role"], e["start_ms"]) for e in events if e["ability_id"] == "SFA-002"],
                         [("base_warning", 0), ("cls006_mark_bonus", 300)])
        self.assertEqual(self.manifest["abilities"][10]["id"], "SFA-011")
        self.assertEqual(self.manifest["abilities"][7]["presentation_hold_ms"], 3000)

    def test_determinism(self):
        other, files = art.expected()
        self.assertEqual(other, self.manifest)
        self.assertEqual({x["path"] for x in other["files"]}, set(files))

    def test_mutated_png_rejected(self):
        path = self.root / "textures/SFA-011_noncolor_telegraph.png"
        old = path.read_bytes()
        try:
            path.write_bytes(old[:-1] + b"x")
            self.assertTrue(art.validate(self.root))
        finally:
            path.write_bytes(old)

    def test_mutated_audio_rejected(self):
        path = self.root / "audio/SFA-005_pulse_two.wav"
        old = path.read_bytes()
        try:
            path.write_bytes(old[:50] + b"\0" + old[51:])
            self.assertTrue(art.validate(self.root))
        finally:
            path.write_bytes(old)

    def test_forged_manifest_rejected(self):
        path = self.root / "arsenal_presentation_manifest.json"
        old = path.read_bytes()
        try:
            changed = copy.deepcopy(self.manifest)
            changed["native_uefn_import"] = "verified"
            path.write_text(json.dumps(changed))
            self.assertTrue(art.validate(self.root))
        finally:
            path.write_bytes(old)

    def test_caption_mutation_rejected(self):
        path = self.root / "captions/SFA-002.vtt"
        old = path.read_bytes()
        try:
            path.write_text("WEBVTT\n\nFake hit confirmed\n")
            self.assertTrue(art.validate(self.root))
        finally:
            path.write_bytes(old)

    def test_contract_fail_closed(self):
        contract = self.root / "external_contract.json"
        data = {"form_id": "FUS-001", "universe_first_gate": {"native_enablement_allowed": False},
                "abilities": [{"id": x[0], "name": x[1], "native_enabled": False} for x in art.ABILITIES]}
        try:
            contract.write_text(json.dumps(data))
            art.validate_contract(contract)
            data["abilities"][5]["name"] = "wrong"
            contract.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                art.validate_contract(contract)
            data["abilities"][5]["name"] = art.ABILITIES[5][1]
            data["universe_first_gate"]["native_enablement_allowed"] = True
            contract.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                art.validate_contract(contract)
        finally:
            contract.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
