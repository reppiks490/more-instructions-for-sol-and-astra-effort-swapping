"""Mutation tests for fusion authority and state-machine source contract.

These tests never compile Verse or run Fortnite.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_fusion_architecture", ROOT / "tools/validate_fusion_architecture.py"
)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class FusionArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads(validator.CONTRACT.read_text(encoding="utf-8"))
        cls.source = validator.SOURCE.read_text(encoding="utf-8")

    def errors(self, policy=None, source=None):
        return validator.check_contract(
            self.policy if policy is None else policy,
            self.source if source is None else source,
        )

    def test_authored_contract(self):
        self.assertEqual(self.errors(), [])

    def test_cannot_enable_unverified_titan(self):
        data = copy.deepcopy(self.policy)
        data["forms"][1]["enabled_for_native_activation"] = True
        self.assertTrue(self.errors(policy=data))

    def test_cannot_rename_existing_uni_001(self):
        data = copy.deepcopy(self.policy)
        data["preservation"]["canonical_sovereign_ability_id"] = "UNI-002"
        self.assertTrue(self.errors(policy=data))

    def test_cannot_forge_native_evidence(self):
        data = copy.deepcopy(self.policy)
        data["evidence"]["native_verse_compile"] = "passed"
        self.assertTrue(self.errors(policy=data))

    def test_cannot_expand_owner_limit(self):
        data = copy.deepcopy(self.policy)
        data["identity"]["owner_limit"] = 2
        self.assertTrue(self.errors(policy=data))

    def test_cannot_erase_controller_lease(self):
        self.assertTrue(self.errors(source=self.source.replace(
            "if (Controller?):", "if (false?):"
        )))

    def test_cannot_remove_native_authorization(self):
        self.assertTrue(self.errors(source=self.source.replace(
            "Authorized := Gate.CanWield(Player)", "Authorized := true"
        )))

    def test_cannot_remove_owner_identity_check(self):
        self.assertTrue(self.errors(source=self.source.replace(
            "Existing <> Player", "Existing = Player"
        )))

    def test_cannot_accept_stale_generation(self):
        self.assertTrue(self.errors(source=self.source.replace(
            "Generation = Token", "Generation > Token"
        )))

    def test_cannot_skip_activation_ack(self):
        self.assertTrue(self.errors(source=self.source.replace(
            "set Phase = aeonfall_fusion_phase.Activating",
            "set Phase = aeonfall_fusion_phase.Active"
        )))

    def test_cleanup_does_not_require_live_authority(self):
        mutated = self.source.replace(
            "    Abort(Device:creative_device, Token:int)<transacts>:logic=\n",
            "    Abort(Device:creative_device, Token:int)<transacts>:logic=\n"
            "        Authorized := Gate.CanWield(Player)\n"
        )
        self.assertTrue(self.errors(source=mutated))

    def test_cannot_release_active_fusion_before_cleanup(self):
        mutated = self.source.replace(
            'if (Phase <> aeonfall_fusion_phase.Dormant or FormId <> ""):',
            'if (false?):'
        )
        self.assertTrue(self.errors(source=mutated))

    def test_cannot_move_release_guard_after_lease_reset(self):
        original = (
            '        if (Phase <> aeonfall_fusion_phase.Dormant or FormId <> ""):\\n'
            '            return false\\n'
        )
        source = self.source
        # Moving the gate behind the actual lease reset is unsafe.
        start = source.index("    ReleaseController(")
        section = source[start:]
        self.assertIn(original.replace("\\n", "\n"), section)
        segment = original.replace("\\n", "\n")
        section = section.replace(segment, "", 1)
        section = section.replace("            set Controller = false",
                                  "            set Controller = false\\n" + segment.rstrip(), 1)
        self.assertTrue(self.errors(source=source[:start] + section.replace("\\n", "\n")))

    def test_controller_release_contract_cannot_be_downgraded(self):
        data = copy.deepcopy(self.policy)
        data["runtime"]["controller_release"] = "unconditional"
        self.assertTrue(self.errors(policy=data))

    def test_cannot_clear_owner_on_release(self):
        mutated = self.source.replace(
            "set Controller = false", "set Owner = false\n            set Controller = false"
        )
        self.assertTrue(self.errors(source=mutated))

    def test_cannot_add_public_registration(self):
        self.assertTrue(self.errors(source=self.source + "\nOwnerReference.Register(Player)\n"))

    def test_cannot_allow_titan_before_native_validation(self):
        self.assertTrue(self.errors(source=self.source.replace(
            'RequestedFormId <> "FUS-001"',
            'RequestedFormId <> "FUS-002"'
        )))


if __name__ == "__main__":
    unittest.main()
