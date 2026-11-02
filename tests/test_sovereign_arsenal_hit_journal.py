"""Offline adversarial hit-journal tests; no Verse/UEFN claims."""
from dataclasses import replace
import unittest

from tools.sovereign_arsenal_hit_journal import (
    HitPlan, SourceHitJournal, MAX_ACTIVE_PLANS, plan_from_admission,
)


def plan(*, generation=1, sequence=1, targets=("MON-001",), damage=12,
         pulses=1, bonus=0, marked="", ability="SFA-009"):
    return HitPlan(generation, sequence, ability, targets, damage, pulses,
                   len(targets) * damage * pulses + bonus, marked, bonus)


class HitJournalTests(unittest.TestCase):
    def setUp(self):
        self.j = SourceHitJournal()

    def test_two_pulse_three_target_bounded_grid(self):
        p = plan(targets=("MON-001", "MON-002", "MON-003"), damage=6,
                 pulses=2, ability="SFA-005")
        self.assertTrue(self.j.stage(p))
        decisions = [self.j.resolve(1, 1, t, pulse, native_hit_confirmed=True)
                     for pulse in range(2) for t in p.target_ids]
        self.assertEqual([d.damage for d in decisions], [6] * 6)
        self.assertEqual(decisions[-1].damage_committed, 36)
        self.assertFalse(self.j.resolve(1, 1, "MON-003", 1,
                                        native_hit_confirmed=True).accepted)

    def test_miss_consumes_slot_and_cannot_turn_into_hit(self):
        self.assertTrue(self.j.stage(plan()))
        miss = self.j.resolve(1, 1, "MON-001", 0, native_hit_confirmed=False)
        self.assertTrue(miss.accepted)
        self.assertEqual(miss.damage, 0)
        self.assertFalse(self.j.resolve(1, 1, "MON-001", 0,
                                        native_hit_confirmed=True).accepted)

    def test_invalid_evidence_never_consumes_slot(self):
        self.assertTrue(self.j.stage(plan()))
        for invalid in ("true", 1, None):
            self.assertFalse(self.j.resolve(1, 1, "MON-001", 0,
                                            native_hit_confirmed=invalid).accepted)
        self.assertFalse(self.j.resolve(1, 1, "MON-001", True,
                                        native_hit_confirmed=True).accepted)
        self.assertFalse(self.j.resolve(1, 1, ["MON-001"], 0,
                                        native_hit_confirmed=True).accepted)
        self.assertTrue(self.j.resolve(1, 1, "MON-001", 0,
                                       native_hit_confirmed=True).accepted)

    def test_reject_unpaid_unregistered_and_out_of_plan(self):
        self.assertFalse(self.j.resolve(1, 1, "MON-001", 0,
                                        native_hit_confirmed=True).accepted)
        self.assertTrue(self.j.stage(plan()))
        self.assertFalse(self.j.resolve(1, 1, "BOS-001", 0,
                                        native_hit_confirmed=True).accepted)
        self.assertFalse(self.j.resolve(1, 1, "MON-002", 0,
                                        native_hit_confirmed=True).accepted)
        self.assertFalse(self.j.resolve(1, 1, "MON-001", 1,
                                        native_hit_confirmed=True).accepted)

    def test_bonus_once_only_for_marked_target(self):
        p = plan(targets=("MON-001", "MON-002", "MON-003"), damage=10,
                 bonus=4, marked="MON-002", ability="SFA-002")
        self.assertTrue(self.j.stage(p))
        first = self.j.resolve(1, 1, "MON-001", 0, native_hit_confirmed=True)
        second = self.j.resolve(1, 1, "MON-002", 0, native_hit_confirmed=True)
        third = self.j.resolve(1, 1, "MON-003", 0, native_hit_confirmed=True)
        self.assertEqual((first.damage, second.damage, third.damage), (10, 14, 10))
        self.assertEqual(third.damage_committed, 34)

    def test_bonus_not_granted_when_marked_hit_misses(self):
        p = plan(targets=("MON-001", "MON-002"), damage=10,
                 bonus=4, marked="MON-002", ability="SFA-002")
        self.assertTrue(self.j.stage(p))
        self.assertEqual(self.j.resolve(1, 1, "MON-002", 0,
                                        native_hit_confirmed=False).damage, 0)
        self.assertEqual(self.j.resolve(1, 1, "MON-001", 0,
                                        native_hit_confirmed=True).damage, 10)

    def test_stale_generation_revoked_even_with_matching_sequence(self):
        self.assertTrue(self.j.stage(plan()))
        self.j.change_generation(2)
        self.assertFalse(self.j.resolve(1, 1, "MON-001", 0,
                                        native_hit_confirmed=True).accepted)
        self.assertTrue(self.j.stage(plan(generation=2)))
        self.assertTrue(self.j.resolve(2, 1, "MON-001", 0,
                                       native_hit_confirmed=True).accepted)

    def test_closed_event_never_reopens_in_generation(self):
        p = plan()
        self.assertTrue(self.j.stage(p))
        self.assertTrue(self.j.close(1, 1))
        self.assertFalse(self.j.stage(p))
        self.assertFalse(self.j.resolve(1, 1, "MON-001", 0,
                                        native_hit_confirmed=True).accepted)

    def test_invalid_plan_shapes_are_denied_without_exception(self):
        p = plan()
        bad = [replace(p, target_ids=["MON-001"]),
               replace(p, target_ids=("MON-001", "MON-001")),
               replace(p, target_ids=("PLAYER",)),
               replace(p, target_ids=(None,)),
               replace(p, pulses=True),
               replace(p, damage_each=1.5),
               replace(p, damage_upper_bound=999),
               replace(p, damage_upper_bound=True),
               replace(p, generation=True),
               replace(p, event_sequence=0),
               replace(p, event_sequence=2**63),
               replace(p, bonus_damage_total=4),
               replace(p, ability_id="SFA-002", bonus_target_id="MON-001"),
               replace(p, damage_each=0),
               replace(p, ability_id="SFA-003"),
               replace(p, ability_id="SFA-999"),
               replace(p, damage_each=54, damage_upper_bound=54),
               replace(p, target_ids=("MON-001", "MON-002", "MON-003", "MON-004"))]
        for b in bad:
            with self.subTest(b=b):
                self.assertFalse(self.j.stage(b))
        self.assertTrue(self.j.stage(p))

    def test_monotonic_stage_prevents_replay_without_unbounded_seen_set(self):
        self.assertTrue(self.j.stage(plan(sequence=2)))
        self.assertTrue(self.j.close(1, 2))
        self.assertFalse(self.j.stage(plan(sequence=1)))
        self.assertFalse(self.j.stage(plan(sequence=2)))
        self.assertTrue(self.j.stage(plan(sequence=3)))
        self.assertFalse(hasattr(self.j, "_seen"))

    def test_active_event_limit_prevents_unbounded_ledger(self):
        for i in range(1, MAX_ACTIVE_PLANS + 1):
            self.assertTrue(self.j.stage(plan(sequence=i)))
        self.assertFalse(self.j.stage(plan(sequence=MAX_ACTIVE_PLANS + 1)))
        self.assertTrue(self.j.close(1, 1))
        self.assertTrue(self.j.stage(plan(sequence=MAX_ACTIVE_PLANS + 1)))

    def test_receipt_translation_rejects_forged_bonus_and_invalid_cost(self):
        ability = {"id": "SFA-002", "damage_each": 10, "max_pulses": 1}
        valid = plan_from_admission(ability=ability, generation=1, event_sequence=1,
                                    target_ids=("MON-001", "MON-002"), admitted=True,
                                    damage_upper_bound=24, marked_target_id="MON-002")
        self.assertIsNotNone(valid)
        self.assertTrue(self.j.stage(valid))
        for args in ({"admitted": False}, {"damage_upper_bound": 50},
                     {"marked_target_id": "MON-999"}, {"damage_upper_bound": 20.5}):
            kw = dict(ability=ability, generation=1, event_sequence=2,
                      target_ids=("MON-001", "MON-002"), admitted=True,
                      damage_upper_bound=24, marked_target_id="MON-002")
            kw.update(args)
            self.assertIsNone(plan_from_admission(**kw))

    def test_receipt_translation_rejects_invalid_ability_types(self):
        for bad in ("6", 1.5, True, None, [], {}):
            a = {"id": "SFA-005", "damage_each": bad, "max_pulses": 2}
            self.assertIsNone(plan_from_admission(
                ability=a, generation=1, event_sequence=1,
                target_ids=("MON-001",), admitted=True, damage_upper_bound=12))

    def test_real_admission_oracle_to_hit_journal_handoff(self):
        """Source-only integration; native collision/receipt proof is still absent."""
        from tools.sovereign_arsenal_admission import (
            ArsenalAdmissionOracle, AuthoritativeSnapshot, RegisteredTarget,
        )
        oracle = ArsenalAdmissionOracle()
        targets = tuple(RegisteredTarget(f"MON-{i:03d}") for i in range(1, 4))
        snapshot = AuthoritativeSnapshot(
            owner_authorized=True, controller_lease_valid=True,
            generation=1, server_time_ms=1000, server_event_sequence=1,
            targets=targets,
        )
        receipt = oracle.admit("SFA-005", snapshot)
        self.assertTrue(receipt.admitted)
        p = plan_from_admission(
            ability=oracle.abilities["SFA-005"], generation=snapshot.generation,
            event_sequence=receipt.event_sequence,
            target_ids=tuple(t.target_id for t in snapshot.targets),
            admitted=receipt.admitted, damage_upper_bound=receipt.damage_upper_bound,
        )
        self.assertIsNotNone(p)
        self.assertTrue(self.j.stage(p))
        for pulse in range(2):
            for target in targets:
                result = self.j.resolve(1, 1, target.target_id, pulse,
                                        native_hit_confirmed=True)
                self.assertTrue(result.accepted)
        self.assertEqual(result.damage_committed, receipt.damage_upper_bound)
        self.assertEqual(oracle.energy, receipt.energy_after)

    def test_generation_must_advance(self):
        for value in (1, 0, True, "2"):
            with self.assertRaises(ValueError):
                self.j.change_generation(value)


if __name__ == "__main__":
    unittest.main()
