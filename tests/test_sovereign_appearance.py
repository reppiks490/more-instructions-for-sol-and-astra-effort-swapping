"""Mutation tests for appearance safety guards; these do not execute native Verse."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("appearance_guard", ROOT / "tools/validate_sovereign_appearance.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class SovereignAppearanceGuards(unittest.TestCase):
    def setUp(self):
        source_path = ROOT / guard.SOURCE_PATH
        policy_path = ROOT / guard.POLICY_PATH
        self.source = source_path.read_text(encoding="utf-8") if source_path.exists() else ""
        self.policy = json.loads(policy_path.read_text(encoding="utf-8")) if policy_path.exists() else {}

    def mutate(self, old, new, method_name=None):
        original = guard.method(self.source, method_name) if method_name else self.source
        self.assertIn(old, original)
        self.source = self.source.replace(original, original.replace(old, new, 1), 1)
        self.assertTrue(guard.check_source(self.source, self.policy))

    def test_authored_source_has_required_owner_and_lifecycle_guards(self):
        self.assertEqual(guard.check_source(self.source, self.policy), [])

    def test_default_open_is_rejected(self):
        self.mutate("Enabled:logic = false", "Enabled:logic = true")

    def test_unknown_automatic_spawn_cannot_be_accepted(self):
        self.mutate("Automatic := Disguise.ShouldApplyDisguiseOnPlayerSpawn?", "Automatic := false", "SpawnConfigurationSafe")

    def test_true_automatic_spawn_is_rejected(self):
        self.mutate("not Automatic?", "Automatic?", "SpawnConfigurationSafe")

    def test_already_enabled_native_rig_is_rejected(self):
        self.mutate("not Disguise.IsEnabled[]", "Disguise.IsEnabled[]", "OnBegin")

    def test_duplicate_controller_cannot_claim_lease(self):
        self.mutate("Existing = Self", "Running?", "AcquireLease")

    def test_native_enable_cannot_precede_lease(self):
        self.mutate("Safe := SpawnConfigurationSafe()", "Disguise.Enable()\n        Safe := SpawnConfigurationSafe()", "OnBegin")

    def test_native_application_requires_unique_authority(self):
        self.mutate("Authorized := Authority.CanWield(Player)", "Authorized := true", "FindAuthorizedTarget")

    def test_inactive_player_cannot_receive_disguise(self):
        self.mutate("Player.IsActive[]", "Running?", "FindAuthorizedTarget")

    def test_inactive_native_character_cannot_receive_disguise(self):
        self.mutate("Character.IsActive[]", "Running?", "FindAuthorizedTarget")

    def test_respawn_identity_must_reset_attempt_budget(self):
        self.mutate("Previous <> Target.Character", "Attempts < 0", "Reconcile")

    def test_retry_budget_cannot_be_unbounded(self):
        self.mutate("Attempts >= 16", "Attempts < 0", "Reconcile")

    def test_retry_budget_numeric_prefix_cannot_hide_extra_attempts(self):
        self.mutate("Attempts >= 16", "Attempts >= 160", "Reconcile")

    def test_retry_sleep_cannot_spin(self):
        self.mutate("Sleep(1.0)", "Sleep(0.0)", "MaintenanceLoop")

    def test_void_application_cannot_be_reported_as_confirmed_success(self):
        self.mutate("Disguise.ApplyDisguise(Target.Player)\n        if (Disguise.IsDisguiseApplied[Target.Player]):\n            set Confirmed = true",
                    "Disguise.ApplyDisguise(Target.Player)\n        set Confirmed = true", "Reconcile")

    def test_disabling_alone_cannot_replace_owned_disguise_removal(self):
        self.mutate("Disguise.RemoveDisguise(Player)", "Disguise.Disable()", "ClearOwnedDisguise")

    def test_removing_unrelated_disguises_is_rejected(self):
        self.mutate("Disguise.RemoveDisguise(Player)", "Disguise.RemoveAnyDisguise(Player)", "ClearOwnedDisguise")

    def test_appearance_must_not_reveal_native_invisibility(self):
        self.source += "\n    Reveal():void=\n        Character.Show()\n"
        self.assertTrue(guard.check_source(self.source, self.policy))

    def test_native_effect_cannot_enter_failure_condition(self):
        self.mutate("Disguise.ApplyDisguise(Target.Player)", "if (Disguise.ApplyDisguise(Target.Player)) {}", "Reconcile")

    def test_native_effect_cannot_use_transactional_method(self):
        self.mutate("Reconcile<private>(Target:aeonfall_sovereign_appearance_target):void=", "Reconcile<private>(Target:aeonfall_sovereign_appearance_target)<transacts>:void=", "Reconcile")

    def test_arbitrary_uploaded_skin_claim_is_rejected(self):
        self.policy["native"]["arbitrary_uploaded_player_skin"] = True
        self.assertTrue(guard.check_source(self.source, self.policy))

    def test_fake_native_session_success_is_rejected(self):
        self.policy["engine_verification"]["session"] = "passed"
        self.assertTrue(guard.check_source(self.source, self.policy))


if __name__ == "__main__":
    unittest.main()
