"""Arsenal universe-first source contract and mutation regressions; NO UEFN proof."""
import copy
import json
from pathlib import Path
import unittest

from tools.validate_sovereign_arsenal_universe import DryRunArsenal, load_contract, validate

ROOT = Path(__file__).resolve().parents[1]
EXISTING = json.loads((ROOT / "content/sovereign/sovereign_arsenal.json").read_text())


class UniverseArsenalContractTests(unittest.TestCase):
    def setUp(self):
        self.c = load_contract()

    def check_mutation(self, fn):
        fn(self.c)
        self.assertTrue(validate(self.c, EXISTING))

    def test_unmodified_contract(self):
        self.assertEqual(validate(self.c, EXISTING), [])

    def test_no_prototype_before_universe(self):
        self.check_mutation(lambda c: c["universe_first_gate"].update(prototype_allowed=True))

    def test_no_native_enablement(self):
        self.check_mutation(lambda c: c["abilities"][3].update(native_enabled=True))

    def test_no_creator_spoof(self):
        self.check_mutation(lambda c: c["identity"].update(display_name_authorization=True))

    def test_no_permission_grant(self):
        self.check_mutation(lambda c: c["abilities"][5].update(permission_changes=True))

    def test_no_player_damage(self):
        self.check_mutation(lambda c: c["abilities"][11].update(target_players=True))

    def test_no_boss_bypass(self):
        self.check_mutation(lambda c: c["abilities"][4].update(target_bosses=True))

    def test_no_cover_bypass(self):
        self.check_mutation(lambda c: c["abilities"][6].update(requires_line_of_sight=False))

    def test_no_unbounded_pulses(self):
        self.check_mutation(lambda c: c["abilities"][4].update(max_pulses=999))

    def test_no_resource_escalation(self):
        self.check_mutation(lambda c: c["abilities"][11].update(energy_cost=0))

    def test_no_unbounded_damage(self):
        self.check_mutation(lambda c: c["abilities"][11].update(damage_each=999))

    def test_no_shield_generation_bypass(self):
        self.check_mutation(lambda c: c["abilities"][7].update(shield_generation_pool=None))

    def test_no_duplicated_mechanics(self):
        self.check_mutation(lambda c: c["abilities"][10].update(mechanic_id=c["abilities"][9]["mechanic_id"]))

    def test_no_progression_rewrite(self):
        self.check_mutation(lambda c: c["progression_invariants"].update(axiom_heart_unchanged=False))

    def test_no_false_editor_proof(self):
        self.check_mutation(lambda c: c["acceptance"].update(native_verse_compile="passed"))

    def test_no_source_kit_drift(self):
        self.check_mutation(lambda c: c["abilities"][0].update(upstream_energy_cost=0))

    def test_distinct_telegraph_required(self):
        self.check_mutation(lambda c: c["abilities"][11]["asset_plan"].pop("accessibility"))


class UniverseArsenalDryRunTests(unittest.TestCase):
    def setUp(self):
        self.a = DryRunArsenal(load_contract())

    def test_every_ability_has_bounded_dry_run(self):
        for aid in self.a.abilities:
            a = DryRunArsenal(load_contract())
            r = a.cast(aid, 1.0)
            self.assertTrue(r.allowed, aid)
            self.assertGreaterEqual(r.energy_after, 0)
            self.assertLessEqual(r.damage_upper_bound, 54)
            self.assertLessEqual(r.shield_restored, 20)

    def test_creator_only_and_stale_generation(self):
        self.assertFalse(self.a.cast("SFA-001", 1, owner=False).allowed)
        self.assertFalse(self.a.cast("SFA-001", 1, token=2).allowed)
        self.assertEqual(self.a.energy, 100)

    def test_atomic_rejection_preserves_energy(self):
        self.assertFalse(self.a.cast("SFA-001", 1, los=False).allowed)
        self.assertFalse(self.a.cast("SFA-001", 1, target_id="BOS-001").allowed)
        self.assertFalse(self.a.cast("SFA-001", 1, target_id="PLAYER").allowed)
        self.assertEqual(self.a.energy, 100)

    def test_reaver_payment_and_cooldown(self):
        self.assertEqual(self.a.cast("SFA-001", 1).energy_after, 85)
        self.assertFalse(self.a.cast("SFA-001", 2).allowed)
        self.assertTrue(self.a.cast("SFA-001", 3).allowed)

    def test_mark_bonus_only_for_equipped_class(self):
        self.a.cast("SFA-001", 1, target_id="MON-002")
        self.assertEqual(self.a.cast("SFA-002", 2, target_id="MON-002", target_count=3, class_id="CLS-006").damage_upper_bound, 34)
        b = DryRunArsenal(load_contract())
        b.cast("SFA-001", 1, target_id="MON-002")
        self.assertEqual(b.cast("SFA-002", 2, target_id="MON-002", target_count=3, class_id="CLS-007").damage_upper_bound, 30)

    def test_mark_expiration(self):
        self.a.cast("SFA-001", 1)
        self.assertEqual(self.a.cast("SFA-002", 5, target_count=3, class_id="CLS-006").damage_upper_bound, 30)

    def test_shared_shield_allowance(self):
        self.assertEqual(self.a.cast("SFA-003", 1).shield_restored, 20)
        self.assertEqual(self.a.cast("SFA-008", 2).shield_restored, 12)
        self.assertEqual(self.a.cast("SFA-003", 19).shield_restored, 8)
        self.assertFalse(self.a.cast("SFA-008", 27).allowed)

    def test_generation_change_preserves_cooldown(self):
        self.a.cast("SFA-012", 1)
        self.a.change_generation(2)
        self.assertFalse(self.a.cast("SFA-012", 2, token=2).allowed)
        self.assertTrue(self.a.cast("SFA-012", 61, token=2).allowed)

    def test_no_teleport_through_wall(self):
        self.assertFalse(self.a.cast("SFA-010", 1, los=False).allowed)
        self.assertFalse(self.a.cast("SFA-010", 1, destination_authored=False).allowed)

    def test_finisher_requires_threshold(self):
        self.assertFalse(self.a.cast("SFA-011", 1, health_fraction=0.26).allowed)
        self.assertTrue(self.a.cast("SFA-011", 1, health_fraction=0.25).allowed)

    def test_max_targets(self):
        self.assertFalse(self.a.cast("SFA-005", 1, target_count=4).allowed)
        self.assertEqual(self.a.energy, 100)


if __name__ == "__main__":
    unittest.main()
