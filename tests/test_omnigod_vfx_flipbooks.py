"""Negative mutation tests for actual 16-frame RGBA flipbooks; source-only."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import build_omnigod_vfx_textures as original
import build_omnigod_vfx_flipbooks as motion
import validate_omnigod_vfx_flipbooks as check


class FlipbookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.source = Path(cls.temp.name) / "src"
        cls.gold = Path(cls.temp.name) / "gold"
        original.build(cls.source)
        motion.build(cls.source, cls.gold)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.out = Path(self.work.name) / "atlases"
        shutil.copytree(self.gold, self.out)

    def manifest(self):
        return json.loads((self.out / "flipbook_manifest.json").read_text())

    def set_manifest(self, data):
        (self.out / "flipbook_manifest.json").write_text(json.dumps(data), encoding="utf-8")

    def test_original_48_frames_validate(self):
        self.assertEqual(check.validate(self.source, self.out), [])
        data = self.manifest()
        self.assertEqual(len(data["atlases"]), 3)
        self.assertEqual(sum(e["frame_count"] for e in data["atlases"]), 48)
        self.assertEqual([x["duration_ms"] for x in data["atlases"]], [550, 900, 700])
        self.assertEqual(data["per_effect_lod_design_caps_unmeasured"][2]["max_particles"], 0)
        self.assertFalse(data["activation_enabled"])

    def test_deterministic_same_artifacts(self):
        other = Path(self.work.name) / "other"
        motion.build(self.source, other)
        for item in self.gold.rglob("*"):
            if item.is_file():
                self.assertEqual(item.read_bytes(), (other / item.relative_to(self.gold)).read_bytes())

    def test_png_crc_tampering_fails_closed(self):
        path = self.out / self.manifest()["files"][0]["path"]
        payload = bytearray(path.read_bytes())
        payload[-20] ^= 0x10
        path.write_bytes(payload)
        self.assertTrue(check.validate(self.source, self.out))

    def test_rogue_native_import_claim_fails(self):
        data = self.manifest()
        data["native_niagara_binding"] = "verified"
        self.set_manifest(data)
        self.assertTrue(any("native claim" in x for x in check.validate(self.source, self.out)))

    def test_hijacked_visibility_fails(self):
        data = self.manifest()
        data["atlases"][0]["requested_visibility"] = "everyone"
        self.set_manifest(data)
        self.assertTrue(any("visibility" in x for x in check.validate(self.source, self.out)))

    def test_ability_audio_mismatch_fails(self):
        data = self.manifest()
        data["atlases"][1]["source_audio"] = data["atlases"][0]["source_audio"]
        self.set_manifest(data)
        self.assertTrue(any("identity" in x for x in check.validate(self.source, self.out)))

    def test_budget_inflation_fails(self):
        data = self.manifest()
        data["per_effect_lod_design_caps_unmeasured"][0]["max_particles"] = 10000
        self.set_manifest(data)
        self.assertTrue(any("ceiling" in x for x in check.validate(self.source, self.out)))

    def test_flashing_retiming_fails(self):
        data = self.manifest()
        data["atlases"][0]["loop"] = True
        data["atlases"][0]["frame_times_ms"][7] = 1
        self.set_manifest(data)
        self.assertTrue(any("timeline" in x for x in check.validate(self.source, self.out)))

    def test_inventory_omission_fails(self):
        data = self.manifest()
        data["files"].pop()
        self.set_manifest(data)
        self.assertTrue(any("inventory" in x for x in check.validate(self.source, self.out)))

    def test_rehashed_opacity_regression_fails(self):
        """Even a self-consistent rehash must not hide a nonmonotonic flash."""
        data = self.manifest()
        clip = data["atlases"][0]
        path = self.out / clip["atlas_png"]
        rgba = bytearray(check.rgba_png(path.read_bytes()))
        # Frame 14 should have lit pixels. Erasing it produces a visible flash.
        for y in range(128):
            for x in range(128):
                off = (((14 // 4 * 128 + y) * 512 + (14 % 4) * 128 + x) * 4 + 3)
                rgba[off] = 0
        new_png = motion.png_rgba(512, bytes(rgba))
        path.write_bytes(new_png)
        sha = hashlib.sha256(new_png).hexdigest()
        clip["atlas_sha256"] = sha
        for item in data["files"]:
            if item["path"] == clip["atlas_png"]:
                item["sha256"] = sha
                item["bytes"] = len(new_png)
        self.set_manifest(data)
        self.assertTrue(any("nonmonotonic" in e for e in check.validate(self.source, self.out)))

    def test_wrong_generation_and_cleanup_fails(self):
        data = self.manifest()
        data["authoritative_generation_required"] = False
        data["cleanup_on_cancel_before_abort"] = False
        self.set_manifest(data)
        self.assertTrue(any("generation or cancellation" in x for x in check.validate(self.source, self.out)))


if __name__ == "__main__":
    unittest.main()
