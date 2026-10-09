"""Source mutation tests. They do not emulate native NPC/device/Verse behavior."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sovereign_guard", ROOT / "tools/validate_sovereign_unmaking.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)

class SovereignSourceGuards(unittest.TestCase):
    def setUp(self):
        self.sources = {name: (ROOT / path).read_text(encoding="utf-8") for name, path in guard.SOURCES.items()}
        self.policy = json.loads((ROOT / guard.POLICY_PATH).read_text(encoding="utf-8"))

    def mutation(self, name, old, new, method_name=None):
        original = guard.method(self.sources[name], method_name) if method_name else self.sources[name]
        self.assertIn(old, original)
        changed = original.replace(old, new, 1)
        self.sources[name] = self.sources[name].replace(original, changed, 1)
        self.assertTrue(guard.check_sources(self.sources, self.policy))

    def test_authored_source_passes(self):
        self.assertEqual(guard.check_sources(self.sources, self.policy), [])

    def test_open_by_default_rejected(self):
        self.mutation("authority", "Enabled:logic = false", "Enabled:logic = true")

    def test_reference_identity_must_match(self):
        self.mutation("authority", "Bound = Player", "Bound.IsActive[]", "CanWield")

    def test_stale_reference_is_not_a_grant(self):
        self.mutation("authority", "OwnerReference.IsReferenced[Player]", "Player.IsActive[]", "CanWield")

    def test_replacement_reference_cannot_inherit_grant(self):
        self.mutation("authority", "set Revoked = true", "set Revoked = false", "ObserveReference")

    def test_public_registration_is_rejected(self):
        self.sources["authority"] += "\n    Grant(Player:player):void=\n        OwnerReference.Register(Player)\n"
        self.assertTrue(guard.check_sources(self.sources, self.policy))

    def test_duplicate_manifestation_guard_required(self):
        self.mutation("runtime", "not Active?", "Generation >= 0", "Begin")

    def test_second_owner_cannot_take_control(self):
        self.mutation("runtime", "Existing = Player", "Player.IsActive[]", "Begin")

    def test_owner_cannot_tribute_to_self(self):
        self.mutation("runtime", "Sovereign <> Payer", "Sovereign.IsActive[]", "PayTribute")

    def test_two_saves_share_failure_scope(self):
        self.mutation("runtime", "<decides><transacts>:void=", "<transacts>:void=", "PayTribute")

    def test_failed_owner_save_cannot_keep_payer_debit(self):
        self.mutation("runtime", "OwnerSaved?", "PayerSaved?", "PayTribute")

    def test_failed_payer_save_cannot_award_tribute(self):
        self.mutation("runtime", "PayerSaved?", "Amount > 0", "PayTribute")

    def test_partial_commit_reordering_rejected(self):
        self.mutation("runtime", "OwnerSaved?\n        set Participants[Payer]", "set Participants[Payer]", "PayTribute")

    def test_quest_generation_check_required(self):
        self.mutation("runtime", "Generation = Token", "Generation >= 0", "Resolve")

    def test_late_join_grace_required(self):
        self.mutation("runtime", "Now - State.JoinedAt < MinimumExposureSeconds", "Now < 0.0", "Resolve")

    def test_owner_exemption_required(self):
        self.mutation("runtime", "Player <> OwnerPlayer", "OwnerPlayer.IsActive[]", "Enroll")

    def test_unbounded_army_rejected(self):
        self.mutation("runtime", "Army.Length < MaxArmy", "Army.Length >= 0", "ClaimArmy")

    def test_unlimited_veil_still_requires_identity(self):
        self.mutation("controller", "AuthorizedOwner[Agent]", "player[Agent]", "ToggleVeil")

    def test_stale_invisible_character_must_clear(self):
        self.mutation("controller", "not Hidden.IsActive[]", "not Running?", "MaintenanceLoop")

    def test_periodic_owner_revocation_required(self):
        self.mutation("controller", "Authority.CanWield(Sovereign)", "Service.IsOwner(Sovereign)", "MaintenanceLoop")

    def test_paid_late_join_snapshot_required(self):
        self.mutation("controller", "aeonfall_sovereign_quest_state.Tributed", "aeonfall_sovereign_quest_state.Demanded", "ShowParticipantSnapshot")

    def test_npc_spawners_must_have_unique_roles(self):
        self.mutation("controller", "SeenSpawners.Find[Region.Monstrosities]", "SeenRegions.Find[Region.RegionId]", "ValidSettings")

    def test_actual_countdown_required(self):
        self.mutation("controller", "Countdown.Start()", "Countdown.Reset()", "Draw")

    def test_failed_team_restores_must_remain_owned(self):
        self.mutation("controller", "set OriginalTeams = Pending", "set OriginalTeams = map{}", "RestoreTeams")

    def test_unmaking_is_opt_in_for_elimination(self):
        self.mutation("controller", "State.MayBeEliminated?", "State.Generation > 0", "Finish")

    def test_optional_elimination_disabled_by_default(self):
        self.mutation("controller", "EnableUnmakingElimination:logic = false", "EnableUnmakingElimination:logic = true")

    def test_native_navigation_must_be_interruptible(self):
        self.mutation("behavior", "Sleep(0.5)", "Sleep(600.0)", "OnBegin")

    def test_native_subscription_cannot_enter_option_failure_scope(self):
        self.mutation("controller", "option{DeathSubscription}",
                      "option{Character.EliminatedEvent().Subscribe(Listener.OnEliminated)}", "Draw")

    def test_policy_cannot_fake_compile_result(self):
        self.policy["engine_verification"]["compile"] = "passed"
        self.assertTrue(guard.check_sources(self.sources, self.policy))

    def test_policy_cannot_make_unique_power_ordinary_loot(self):
        self.policy["ordinary_unlockable"] = True
        self.assertTrue(guard.check_sources(self.sources, self.policy))

if __name__ == "__main__":
    unittest.main()
