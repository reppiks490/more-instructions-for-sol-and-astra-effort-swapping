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

    def test_second_pulse_rechecks_cover_after_first_hit(self):
        p = plan("SFA-005")
        self.assertTrue(self.stage(p))
        first = self.gate.resolve(observe(pulse=0, at=101))
        second = self.gate.resolve(observe(pulse=1, at=201, line_of_sight=False))
        self.assertEqual((first.damage, second.damage), (6, 0))
        self.assertEqual(second.damage_committed, 6)
        self.assertFalse(self.gate.resolve(observe(pulse=1, at=202)).accepted)

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

    def test_noncanonical_monster_aliases_never_stage(self):
        for target in ("MON-ABC", "MON-001 ", "MON-١٢٣", "MON-001\n",
                       "MON-01", "MON-00001", "MON-001-2", "MON-１２３"):
            p = plan(targets=(target,))
            b = (BoundActor(target, "actor-instance-0", "REG-001"),)
            self.assertFalse(self.stage(p, b), target)
        self.assertTrue(self.stage(plan(targets=("MON-1234",)),
                                   (BoundActor("MON-1234", "actor-instance-0", "REG-001"),)))

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
        duplicate = contract()
        duplicate["abilities"].append(dict(duplicate["abilities"][0]))
        with self.assertRaises(ValueError):
            SourceHitObservationGate(duplicate)
        extended = contract()
        extended["abilities"][0]["range_cm"] = 651
        with self.assertRaises(ValueError):
            SourceHitObservationGate(extended)


    def test_revocation_precedes_stale_target_actor_and_event_routing(self):
        # Trusted revocation is generation-wide, not scoped to whichever
        # target/pulse happens to be delivered with the revoked callback.
        cases = (
            ("missing target", replace(observe(target="MON-002"),
                                       owner_authorized=False)),
            ("recycled actor", replace(observe(actor="recycled-actor"),
                                       controller_lease_valid=False)),
            ("region transfer", replace(observe(region="REG-002"),
                                        owner_authorized=False)),
            ("unknown event", replace(observe(sequence=999),
                                      controller_lease_valid=False)),
            ("invalid paid pulse", replace(observe(pulse=3),
                                           owner_authorized=False)),
            ("clock regression", replace(observe(at=99),
                                         controller_lease_valid=False)),
        )
        for label, evidence in cases:
            with self.subTest(label=label):
                gate = SourceHitObservationGate(contract())
                self.assertTrue(gate.stage(plan(), bindings(), opened_ms=100,
                                           deadline_ms=500))
                self.assertTrue(gate.stage(plan(sequence=2), bindings(),
                                           opened_ms=100, deadline_ms=500))
                result = gate.resolve(evidence)
                self.assertFalse(result.accepted)
                self.assertIn("revoked", result.reason)
                self.assertEqual(gate.active_count, 0)
                self.assertFalse(gate.resolve(observe(sequence=2)).accepted)
                self.assertFalse(gate.stage(plan(sequence=3), bindings(),
                                            opened_ms=100, deadline_ms=500))
                gate.change_generation(2)
                self.assertTrue(gate.stage(plan(generation=2), bindings(),
                                           opened_ms=100, deadline_ms=500))
                self.assertEqual(gate.resolve(observe(generation=2)).damage, 18)

    def test_stale_generation_cannot_revoke_current_owner(self):
        gate = SourceHitObservationGate(contract())
        gate.change_generation(2)
        self.assertTrue(gate.stage(plan(generation=2), bindings(),
                                   opened_ms=100, deadline_ms=500))
        stale = replace(observe(generation=1), owner_authorized=False)
        self.assertFalse(gate.resolve(stale).accepted)
        self.assertEqual(gate.active_count, 1)
        self.assertEqual(gate.resolve(observe(generation=2)).damage, 18)

    def test_all_thirteen_region_unloads_revoke_local_plans_only(self):
        for n in range(1, 14):
            with self.subTest(region=n):
                region = f"REG-{n:03d}"
                other = f"REG-{(n % 13) + 1:03d}"
                gate = SourceHitObservationGate(contract())
                self.assertTrue(gate.stage(plan(sequence=1),
                                           bindings(region=region),
                                           opened_ms=100, deadline_ms=500))
                self.assertTrue(gate.stage(plan(sequence=2),
                                           bindings(region=other),
                                           opened_ms=100, deadline_ms=500))
                self.assertEqual(gate.retire_region(region), 1)
                self.assertEqual(gate.retire_region(region), 0)
                self.assertEqual(gate.active_count, 1)
                self.assertFalse(gate.resolve(observe(region=region)).accepted)
                self.assertFalse(gate.stage(plan(sequence=3),
                                            bindings(region=region),
                                            opened_ms=100, deadline_ms=500))
                self.assertEqual(gate.resolve(observe(sequence=2, region=other)).damage, 18)
                self.assertTrue(gate.resume_region(region, 2))
                self.assertTrue(gate.stage(
                    plan(sequence=3),
                    (BoundActor("MON-001", "fresh-actor", region, 2),),
                    opened_ms=100, deadline_ms=500))
                self.assertEqual(gate.resolve(
                    replace(observe(sequence=3, region=region, actor="fresh-actor"),
                            region_epoch=2)).damage, 18)

    def test_actor_despawn_revokes_whole_paid_plan_not_neighbor(self):
        p = plan("SFA-002", targets=("MON-001", "MON-002"))
        self.assertTrue(self.stage(p))
        self.assertTrue(self.stage(plan(sequence=2),
                                   bindings(region="REG-002")))
        self.assertEqual(self.gate.retire_actor("actor-instance-1", "REG-002", 1), 0)
        self.assertEqual(self.gate.retire_actor("actor-instance-1", "REG-001", 2), 0)
        self.assertEqual(self.gate.retire_actor("actor-instance-1", "REG-001", 1), 1)
        self.assertEqual(self.gate.active_count, 1)
        self.assertFalse(self.gate.resolve(observe()).accepted)
        self.assertEqual(self.gate.resolve(
            observe(sequence=2, region="REG-002")).damage, 18)

    def test_region_epoch_malformed_evidence_does_not_consume(self):
        for epoch in (0, True, "1", 2**63):
            with self.subTest(epoch=epoch):
                gate = SourceHitObservationGate(contract())
                self.assertFalse(gate.stage(plan(),
                                            (BoundActor("MON-001", "actor", "REG-001", epoch),),
                                            opened_ms=100, deadline_ms=500))
                self.assertTrue(gate.stage(plan(), bindings(),
                                           opened_ms=100, deadline_ms=500))
                bad = replace(observe(), region_epoch=epoch)
                self.assertFalse(gate.resolve(bad).accepted)
                self.assertEqual(gate.active_count, 1)
                self.assertEqual(gate.resolve(observe()).damage, 18)

    def test_valid_but_wrong_epoch_closes_paid_event(self):
        self.assertTrue(self.stage())
        denied = self.gate.resolve(replace(observe(), region_epoch=2))
        self.assertFalse(denied.accepted)
        self.assertEqual(self.gate.active_count, 0)
        self.assertFalse(self.gate.resolve(observe()).accepted)

    def test_region_retirement_persists_across_owner_generation(self):
        self.assertTrue(self.stage())
        self.assertEqual(self.gate.retire_region("REG-001"), 1)
        self.gate.change_generation(2)
        self.assertFalse(self.gate.stage(plan(generation=2),
                                         bindings(), opened_ms=100, deadline_ms=500))
        self.assertTrue(self.gate.resume_region("REG-001", 2))
        self.assertFalse(self.gate.stage(plan(generation=2),
                                         bindings(), opened_ms=100, deadline_ms=500))
        self.assertTrue(self.gate.stage(
            plan(generation=2),
            (BoundActor("MON-001", "fresh", "REG-001", 2),),
            opened_ms=100, deadline_ms=500))
        self.assertEqual(self.gate.resolve(replace(
            observe(generation=2, actor="fresh"), region_epoch=2)).damage, 18)

    def test_region_epoch_monotonic_resume_and_bad_teardown_arguments(self):
        self.assertFalse(self.gate.resume_region("REG-001", 2))
        self.assertEqual(self.gate.retire_region([]), 0)
        self.assertEqual(self.gate.retire_region("REG-999"), 0)
        self.assertEqual(self.gate.retire_region("REG-001"), 0)
        for epoch in (0, 1, True, "2", 2**63):
            self.assertFalse(self.gate.resume_region("REG-001", epoch))
        self.assertTrue(self.gate.resume_region("REG-001", 2))
        self.assertEqual(self.gate.retire_region("REG-001"), 0)
        self.assertFalse(self.gate.resume_region("REG-001", 2))
        self.assertTrue(self.gate.resume_region("REG-001", 3))
        for args in ((None, "REG-001", 3), ("", "REG-001", 3),
                     ("actor-instance-0", [], 3),
                     ("actor-instance-0", "REG-001", True)):
            self.assertEqual(self.gate.retire_actor(*args), 0)

    def test_owner_loss_from_retired_region_revokes_other_region_too(self):
        # World-stream teardown cannot hide a trusted global owner revocation.
        self.assertTrue(self.stage(plan(sequence=1)))
        self.assertTrue(self.stage(plan(sequence=2),
                                   bindings(region="REG-002")))
        self.assertEqual(self.gate.retire_region("REG-001"), 1)
        loss = replace(observe(sequence=1), owner_authorized=False)
        denied = self.gate.resolve(loss)
        self.assertFalse(denied.accepted)
        self.assertIn("revoked", denied.reason)
        self.assertEqual(self.gate.active_count, 0)
        self.assertFalse(self.gate.resolve(
            observe(sequence=2, region="REG-002")).accepted)
        self.assertFalse(self.gate.stage(
            plan(sequence=3), bindings(region="REG-002"),
            opened_ms=100, deadline_ms=500))

    def test_unload_after_first_pulse_cancels_second_pulse(self):
        self.assertTrue(self.stage(plan("SFA-005")))
        first = self.gate.resolve(observe(pulse=0))
        self.assertEqual(first.damage, 6)
        self.assertEqual(self.gate.retire_region("REG-001"), 1)
        self.assertFalse(self.gate.resolve(observe(pulse=1, at=201)).accepted)
        self.assertEqual(self.gate.active_count, 0)


if __name__ == "__main__":
    unittest.main()
