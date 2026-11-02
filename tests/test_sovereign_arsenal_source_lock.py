"""Mutation guards for FUS-001 native source lock; not a Verse compiler."""
import copy
import json
from pathlib import Path
import unittest

from tools.validate_sovereign_arsenal_source_lock import (
    DEVICE, CONTRACT, validate_source_lock,
)


class NativeArsenalSourceLockTests(unittest.TestCase):
    def setUp(self):
        self.source = DEVICE.read_text(encoding="utf-8")
        self.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_source_lock_is_present(self):
        self.assertEqual(validate_source_lock(self.source, self.contract), [])

    def test_editable_flag_alone_cannot_enable_combat(self):
        changed = self.source.replace(
            "    Enabled:logic = false", "    Enabled:logic = true", 1
        )
        self.assertTrue(validate_source_lock(changed, self.contract))

    def test_hard_lock_cannot_be_flipped_true(self):
        changed = self.source.replace(
            "    NativeSourceGate:logic = false",
            "    NativeSourceGate:logic = true", 1,
        )
        self.assertTrue(validate_source_lock(changed, self.contract))

    def test_hard_lock_cannot_be_made_editor_editable(self):
        changed = self.source.replace(
            "    NativeSourceGate:logic = false",
            "    @editable\n    NativeSourceGate:logic = false", 1,
        )
        self.assertTrue(validate_source_lock(changed, self.contract))

    def test_hard_lock_cannot_be_skipped(self):
        changed = self.source.replace(
            "        if (not NativeSourceGate?):\n            return\n",
            "        if (not NativeSourceGate?):\n            Print(\"unlocked\")\n", 1,
        )
        self.assertTrue(validate_source_lock(changed, self.contract))

    def test_hard_lock_must_precede_side_effects(self):
        changed = self.source.replace(
            "        if (not NativeSourceGate?):",
            "        Service := GetAEONFALLSovereignArsenalRuntime()\n"
            "        if (not NativeSourceGate?):", 1,
        )
        self.assertTrue(validate_source_lock(changed, self.contract))

    def test_lock_must_be_first_executable_guard(self):
        changed = self.source.replace(
            "        if (not NativeSourceGate?):",
            "        if (not Enabled?):\n            return\n"
            "        if (not NativeSourceGate?):", 1,
        )
        self.assertTrue(validate_source_lock(changed, self.contract))

    def test_native_ability_enablement_is_rejected(self):
        changed = copy.deepcopy(self.contract)
        changed["abilities"][11]["native_enabled"] = True
        self.assertTrue(validate_source_lock(self.source, changed))

    def test_universe_first_gate_cannot_be_opened(self):
        changed = copy.deepcopy(self.contract)
        changed["universe_first_gate"]["prototype_allowed"] = True
        self.assertTrue(validate_source_lock(self.source, changed))

    def test_existing_adapter_entrypoints_are_preserved(self):
        changed = self.source.replace("    OnRend(", "    RemovedRend(", 1)
        self.assertTrue(validate_source_lock(changed, self.contract))


if __name__ == "__main__":
    unittest.main()
