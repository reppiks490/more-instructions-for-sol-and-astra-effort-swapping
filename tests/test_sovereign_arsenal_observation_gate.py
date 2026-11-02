"""Adversarial offline tests; no native Fortnite/UEFN claims."""
from dataclasses import replace
import unittest

from tools.sovereign_arsenal_admission import RegisteredTarget
from tools.sovereign_arsenal_hit_journal import ATTACK_SPECS, HitPlan, MAX_ACTIVE_PLANS
from tools.sovereign_arsenal_observation_gate import (
    BoundActor, HitObservation, SourceHitObservationGate,
)

RANGES = {"SFA-001": 350, "SFA-002": 650, "SFA-004": 500,
          "SFA-005": 600, "SFA-007": 450, "SFA-009": 450,
          "SFA-011": 350, "SFA-012": 650}


def contract():
    return {"universe_first_gate": {
        "world_content_complete": False, "prototype_allowed": False,
        "native_enablement_allowed": False,
    }, "abilities": [dict(id=k, damage_each=d, max_pulses=p,
                          max_targets=t, range_cm=RANGES[k], native_enabled=False)
                    for k, (d, p, t) in ATTACK_SPECS.items()]}


def plan(ability="SFA-001", sequence=1, generation=1, targets=("MON-001",),
         marked="", bonus=0):
    damage, pulses, _ = ATTACK_SPECS[ability]
    return HitPlan(generation, sequence, ability, targets, damage, pulses,
                   len(targets) * damage * pulses + bonus, marked, bonus)


def bindings(targets=("MON-001",), region="REG-001"):
    return tuple(BoundActor(t, f"actor-instance-{i}", region)
                 for i, t in enumerate(targets))


def observe(target="MON-001", actor="actor-instance-0", region="REG-001",
            sequence=1, generation=1, pulse=0, at=101,
            **target_changes):
    return HitObservation(generation, sequence, pulse, at, actor, region,
                          True, True, True,
                          replace(RegisteredTarget(target), **target_changes))


class SourceObservationGateTests(unittest.TestCase):
    def setUp(self):
        self.gate = SourceHitObservationGate(contract())

    def stage(self, p=None, b=None, opened=100, deadline=500):
        p = p if p is not None else plan()
        b = b if b is not None else bindings(p.target_ids)
        return self.gate.stage(p, b, opened_ms=opened, deadline_ms=deadline)

    def test_all_eight_offensive_contracts_and_bounded_damage(self):
        for ability, (damage, pulses, count) in ATTACK_SPECS.items():
            with self.subTest(ability=ability):
                gate = SourceHitObservationGate(contract())
                targets = tuple(f"MON-{i:03d}" for i in range(1, count + 1))
                p = plan(ability, targets=targets)
                self.assertTrue(gate.stage(p, bindings(targets), opened_ms=100,
                                           deadline_ms=600))
                total = 0
                for pulse in range(pulses):
                    for i, target in enumerate(targets):
                        result = gate.resolve(observe(target=target,
                                                      actor=f"actor-instance-{i}",
                                                      pulse=pulse, at=101 + pulse * 100))
                        self.assertTrue(result.accepted, result.reason)
                        total += result.damage
                self.assertEqual(total, len(targets) * damage * pulses)
                self.assertLessEqual(total, 54)
                self.assertEqual(gate.active_count, 0)
                self.assertFalse(gate.resolve(observe()).accepted)

    def test_class_mark_bonus_once_only_on_confirmed_marked_target(self):
        p = plan("SFA-002", targets=("MON-001", "MON-002", "MON-003"),
                 marked="MON-002", bonus=4)
        self.assertTrue(self.stage(p))
        a = self.gate.resolve(observe(target="MON-001", actor="actor-instance-0"))
        b = self.gate.resolve(observe(target="MON-002", actor="actor-instance-1"))
        c = self.gate.resolve(observe(target="MON-003", actor="actor-instance-2"))
        self.assertEqual([a.damage, b.damage, c.damage], [10, 14, 10])
        self.assertEqual(c.damage_committed, 34)
        self.assertEqual(self.gate.active_count, 0)

    def test_protected_targets_become_terminal_zero_damage_misses(self):
        for changes in (
            {"alive": False}, {"registered_monster": False},
            {"vulnerable": False}, {"friendly": True}, {"player": True},
            {"boss": True}, {"companion": True}, {"sovereign_army": True},
            {"invulnerable": True}, {"line_of_sight": False},
            {"within_cone": False}, {"distance_cm": 351},
            {"health_fraction": 1.1},
        ):
            with self.subTest(changes=changes):
                gate = SourceHitObservationGate(contract())
                self.assertTrue(gate.stage(plan(), bindings(), opened_ms=100,
                                           deadline_ms=500))
                denied = gate.resolve(observe(**changes))
                self.assertTrue(denied.accepted)
                self.assertEqual(denied.damage, 0)
                self.assertEqual(gate.active_count, 0)
                self.assertFalse(gate.resolve(observe()).accepted)

    def test_native_collision_miss_is_terminal(self):
        self.assertTrue(self.stage())
        miss = self.gate.resolve(replace(observe(), native_hit_confirmed=False))
        self.assertTrue(miss.accepted)
        self.assertEqual(miss.damage, 0)
        self.assertFalse(self.gate.resolve(observe()).accepted)

    def test_status_immunity_and_finisher_threshold(self):
        self.assertTrue(self.stage(plan("SFA-007")))
        self.assertEqual(self.gate.resolve(observe(status_immune=True)).damage, 0)
        self.assertTrue(self.stage(plan("SFA-011", sequence=2)))
        self.assertEqual(self.gate.resolve(observe(sequence=2, health_fraction=0.251)).damage, 0)
        self.assertTrue(self.stage(plan("SFA-011", sequence=3)))
        self.assertEqual(self.gate.resolve(observe(sequence=3, health_fraction=0.25)).damage, 20)

    def test_malformed_evidence_cannot_consume_or_throw(self):
        self.assertTrue(self.stage())
        bad = [None, {}, object(), replace(observe(), native_hit_confirmed="true"),
               replace(observe(), owner_authorized=1),
               replace(observe(), server_time_ms=True),
               replace(observe(), pulse_index=False),
               replace(observe(), target=replace(RegisteredTarget("MON-001"), boss="false")),
               replace(observe(), target=replace(RegisteredTarget("MON-001"), distance_cm=float("nan"))),
               replace(observe(), target=replace(RegisteredTarget("MON-001"), target_id=[])),
               replace(observe(), target={}),
               replace(observe(), actor_key=None)]
        for item in bad:
            with self.subTest(item=item):
                result = self.gate.resolve(item)
                self.assertFalse(result.accepted)
                self.assertEqual(self.gate.active_count, 1)
        self.assertEqual(self.gate.resolve(observe()).damage, 18)

    def test_actor_reuse_or_region_unload_closes_paid_event(self):
        for changed in ({"actor_key": "recycled-actor"},
                        {"region_id": "REG-002"}):
            gate = SourceHitObservationGate(contract())
            self.assertTrue(gate.stage(plan(), bindings(), opened_ms=100,
                                       deadline_ms=500))
            self.assertFalse(gate.resolve(replace(observe(), **changed)).accepted)
            self.assertEqual(gate.active_count, 0)
            self.assertFalse(gate.resolve(observe()).accepted)

    def test_lease_loss_revokes_all_outstanding_events_until_new_generation(self):
        self.assertTrue(self.stage())
        self.assertTrue(self.stage(plan(sequence=2)))
        denied = self.gate.resolve(replace(observe(), controller_lease_valid=False))
        self.assertFalse(denied.accepted)
        self.assertEqual(self.gate.active_count, 0)
        self.assertFalse(self.stage(plan(sequence=3)))
        self.gate.change_generation(2)
        self.assertFalse(self.gate.resolve(observe()).accepted)
        self.assertTrue(self.stage(plan(sequence=1, generation=2)))
        self.assertEqual(self.gate.resolve(observe(generation=2)).damage, 18)

    def test_expiry_clock_regression_and_replay(self):
        self.assertTrue(self.stage())
        self.assertFalse(self.gate.resolve(observe(at=99)).accepted)
        self.assertEqual(self.gate.active_count, 1)
        self.assertFalse(self.gate.resolve(observe(at=501)).accepted)
        self.assertEqual(self.gate.active_count, 0)
        self.assertFalse(self.stage())
        self.assertTrue(self.stage(plan(sequence=2)))
        self.assertEqual(self.gate.resolve(observe(sequence=2, at=500)).damage, 18)
        self.assertFalse(self.gate.resolve(observe(sequence=2, at=500)).accepted)

    def test_all_thirteen_regions_accept_same_region_bindings(self):
        for n in range(1, 14):
            region = f"REG-{n:03d}"
            gate = SourceHitObservationGate(contract())
            p = plan("SFA-002", targets=("MON-001", "MON-002"))
            self.assertTrue(gate.stage(p, bindings(p.target_ids, region),
                                       opened_ms=100, deadline_ms=500))
            self.assertEqual(gate.resolve(observe(region=region)).damage, 10)
        p = plan("SFA-002", targets=("MON-001", "MON-002"))
        mixed = (BoundActor("MON-001", "actor-instance-0", "REG-001"),
                 BoundActor("MON-002", "actor-instance-1", "REG-002"))
        self.assertFalse(self.stage(p, mixed))

    def test_stage_bounds_and_invalid_binding(self):
        p = plan()
        for b in ([], (), (BoundActor("MON-001", "", "REG-001"),),
                  (BoundActor("MON-001", "actor-instance-0", "REG-999"),),
                  (BoundActor("BOS-001", "actor-instance-0", "REG-001"),)):
            self.assertFalse(self.stage(p, b))
        for opened, deadline in ((0, 0), (100, 6101), (True, 500),
                                 (100, False), (-1, 500), (100, 2**63)):
            self.assertFalse(self.stage(p, opened=opened, deadline=deadline))
        self.assertTrue(self.stage(p))
        self.assertFalse(self.stage(p))

    def test_bound_capacity_and_monotonic_replay(self):
        for i in range(1, MAX_ACTIVE_PLANS + 1):
            self.assertTrue(self.stage(plan(sequence=i)))
        self.assertFalse(self.stage(plan(sequence=MAX_ACTIVE_PLANS + 1)))
        self.assertTrue(self.gate.close(1, 1))
        self.assertTrue(self.stage(plan(sequence=MAX_ACTIVE_PLANS + 1)))
        self.assertFalse(self.stage(plan(sequence=1)))

    def test_real_contract_loader_matches_eight_offensive_specs(self):
        self.assertEqual(set(SourceHitObservationGate()._abilities), set(ATTACK_SPECS))

    def test_mutated_contract_rejected(self):
        for change in ({"native_enabled": True}, {"damage_each": 999},
                       {"max_targets": 100}, {"range_cm": float("inf")}):
            data = contract()
            data["abilities"][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                SourceHitObservationGate(data)
        data = contract()
        data["universe_first_gate"]["native_enablement_allowed"] = True
        with self.assertRaises(ValueError):
            SourceHitObservationGate(data)


if __name__ == "__main__":
    unittest.main()
