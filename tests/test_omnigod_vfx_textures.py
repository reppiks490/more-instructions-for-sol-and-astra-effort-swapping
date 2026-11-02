"""Deterministic source output and negative-mutation guards (not UEFN tests)."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import build_omnigod_vfx_textures as build
import validate_omnigod_vfx_textures as verify


class VFXSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "a"
        build.build(self.root)

    def test_source_pack_validates(self):
        self.assertEqual(verify.validate(self.root), [])

    def test_deterministic_bytes(self):
        second = Path(self.temp.name) / "b"
        build.build(second)
        for item in self.root.rglob("*"):
            if item.is_file():
                self.assertEqual(item.read_bytes(), (second / item.relative_to(self.root)).read_bytes())

    def test_png_crc_corruption_rejected(self):
        path = self.root / "textures/telegraph_reaver_chevrons.png"
        payload = bytearray(path.read_bytes())
        payload[-17] ^= 0x40
        path.write_bytes(payload)
        self.assertTrue(verify.validate(self.root))

    def test_wav_truncation_rejected(self):
        path = self.root / "audio/aegis_guard_warning.wav"
        path.write_bytes(path.read_bytes()[:-100])
        self.assertTrue(verify.validate(self.root))

    def test_native_claim_rejected(self):
        self._mutate(lambda m: m.update(native_uefn_import="verified"))

    def test_owner_grant_rejected(self):
        self._mutate(lambda m: m.update(owner_entitlement_modified=True))

    def test_flash_rejected(self):
        self._mutate(lambda m: m["accessibility"].update(screen_flashes=1))

    def test_budget_expansion_rejected(self):
        self._mutate(lambda m: m["lod_design_caps_unmeasured"][0].update(max_particles=10000))

    def test_cue_alias_rejected(self):
        self._mutate(lambda m: m["attack_telegraphs"][1].update(shape="three_forward_chevrons"))

    def test_visibility_leak_rejected(self):
        self._mutate(lambda m: m["binding"].update(owner_only_sequence="Everyone"))

    def test_inventory_omission_rejected(self):
        self._mutate(lambda m: m["files"].pop())

    def _mutate(self, edit):
        path = self.root / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        edit(manifest)
        path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertTrue(verify.validate(self.root))


if __name__ == "__main__":
    unittest.main()
