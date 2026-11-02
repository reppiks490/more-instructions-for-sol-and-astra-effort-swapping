"""Adversarial server-admission *reference* tests; NOT native UEFN verification."""
from dataclasses import replace
import math
import unittest

from tools.sovereign_arsenal_admission import (
    AdmissionReceipt, ArsenalAdmissionOracle, AuthoritativeSnapshot, RegisteredTarget,
)


def evidence(*targets, at=0, sequence=1, generation=1, owner=True, lease=True,
             cls="", shield=0, max_shield=100, destination=False):
    return AuthoritativeSnapshot(
        owner_authorized=owner, controller_lease_valid=lease,
        generation=generation, server_time_ms=at, server_event_sequence=sequence,
        equipped_class_id=cls, targets=tuple(targets), shield=shield,
        max_shield=max_shield, destination_authored=destination,
        destination_clear=destination, destination_line_of_sight=destination,
        destination_distance_cm=150.0 if destination else 0.0,
    )


T = RegisteredTarget("MON-001")


class ServerAdmissionReferenceTests(unittest.TestCase):
    def setUp(self):
        self.a = ArsenalAdmissionOracle()

    def test_all_twelve_mechanics_have_bounded_preflight(self):
        for aid, ability in self.a.abilities.items():
            oracle = ArsenalAdmissionOracle()
            proof = evidence(T if ability["damage_each"] else None,
                             destination=aid == "SFA-010")
            if not ability["damage_each"]:
                proof = replace(proof, targets=())
            result = oracle.admit(aid, proof)
            self.assertTrue(result.admitted, (aid, result.reason))
            self.assertGreaterEqual(result.energy_after, 0)
            self.assertLessEqual(result.damage_upper_bound, 54)
            self.assertLessEqual(result.shield_restored, 20)

    def test_creator_identity_not_cosmetic(self):
        self.assertFalse(self.a.admit("SFA-001", evidence(T, owner=False)).admitted)
        self.assertFalse(self.a.admit("SFA-001", evidence(T, lease=False)).admitted)
        self.assertFalse(self.a.admit("SFA-001", evidence(T, generation=2)).admitted)
        self.assertEqual(self.a.energy, 100)

    def test_replayed_event_is_never_paid_twice(self):
        first = self.a.admit("SFA-001", evidence(T, at=1, sequence=7))
        replay = self.a.admit("SFA-001", evidence(T, at=8000, sequence=7))
        self.assertTrue(first.admitted)
        self.assertEqual(replay.reason, "duplicate/stale server event")
        self.assertEqual(self.a.energy, 85)

    def test_rejected_preflight_consumes_event_but_not_energy(self):
        bad = self.a.admit("SFA-001", evidence(replace(T, line_of_sight=False), sequence=6))
        retry = self.a.admit("SFA-001", evidence(T, sequence=6, at=100))
        self.assertFalse(bad.admitted)
        self.assertEqual(retry.reason, "duplicate/stale server event")
        self.assertEqual(self.a.energy, 100)
        self.assertTrue(self.a.admit("SFA-001", evidence(T, sequence=7, at=200)).admitted)

    def test_negative_nan_bool_and_regressing_clock(self):
        for bad in (-1, float("nan"), float("inf"), True, 2**63):
            self.assertFalse(self.a.admit("SFA-001", evidence(T, at=bad)).admitted)
        self.assertTrue(self.a.admit("SFA-001", evidence(T, at=200, sequence=1)).admitted)
        self.assertEqual(self.a.admit("SFA-002", evidence(T, at=199, sequence=2)).reason, "clock regression")

    def test_bool_negative_and_oversized_sequences(self):
        for bad in (True, 0, -1, 2**63, 1.5):
            self.assertFalse(self.a.admit("SFA-001", evidence(T, sequence=bad)).admitted)
        self.assertEqual(self.a.energy, 100)

    def test_source_family_and_registration_must_both_hold(self):
        for target in (replace(T, target_id="PLAYER-001"),
                       replace(T, target_id="MON-"),
                       replace(T, registered_monster=False)):
            oracle = ArsenalAdmissionOracle()
            self.assertFalse(oracle.admit("SFA-001", evidence(target)).admitted)

    def test_native_protections_fail_closed(self):
        exclusions = ("alive", "vulnerable", "friendly", "player", "boss",
                      "companion", "sovereign_army", "invulnerable",
                      "line_of_sight", "within_cone")
        for field in exclusions:
            oracle = ArsenalAdmissionOracle()
            value = False if field in ("alive", "vulnerable", "line_of_sight", "within_cone") else True
            result = oracle.admit("SFA-001", evidence(replace(T, **{field: value})))
            self.assertFalse(result.admitted, field)

    def test_single_covered_target_denies_whole_multi_target_cast(self):
        targets = (T, replace(T, target_id="MON-002"),
                   replace(T, target_id="MON-003", line_of_sight=False))
        result = self.a.admit("SFA-002", evidence(*targets))
        self.assertFalse(result.admitted)
        self.assertEqual(self.a.energy, 100)

    def test_duplicate_target_cannot_multiply_damage(self):
        self.assertFalse(self.a.admit("SFA-002", evidence(T, T)).admitted)

    def test_invalid_target_counts(self):
        self.assertFalse(self.a.admit("SFA-002", evidence()).admitted)
        self.assertFalse(self.a.admit("SFA-002", evidence(*(replace(T, target_id=f"MON-{i:03d}") for i in range(4)))).admitted)

    def test_self_abilities_cannot_accept_enemy_targets(self):
        self.assertFalse(self.a.admit("SFA-003", evidence(T)).admitted)

    def test_distance_health_and_non_finite_rejection(self):
        for field, value in (("distance_cm", -1), ("distance_cm", 351),
                             ("distance_cm", float("nan")), ("distance_cm", float("inf")),
                             ("health_fraction", -0.1), ("health_fraction", 1.1),
                             ("health_fraction", float("nan"))):
            oracle = ArsenalAdmissionOracle()
            self.assertFalse(oracle.admit("SFA-001", evidence(replace(T, **{field: value}))).admitted)

    def test_bounded_25_percent_finisher(self):
        denied = self.a.admit("SFA-011", evidence(replace(T, health_fraction=0.251)))
        self.assertFalse(denied.admitted)
        allowed = self.a.admit("SFA-011", evidence(replace(T, health_fraction=0.25), sequence=2))
        self.assertTrue(allowed.admitted)
        self.assertEqual(allowed.damage_upper_bound, 20)

    def test_status_immune_target_cannot_be_slowed(self):
        self.assertFalse(self.a.admit("SFA-007", evidence(replace(T, status_immune=True))).admitted)

    def test_anchor_is_not_wall_phasing(self):
        for change in ({"destination_authored": False},
                       {"destination_clear": False},
                       {"destination_line_of_sight": False}):
            oracle = ArsenalAdmissionOracle()
            self.assertFalse(oracle.admit("SFA-010", replace(evidence(destination=True), **change)).admitted)
        self.assertTrue(self.a.admit("SFA-010", evidence(destination=True)).admitted)

    def test_echo_step_anchor_has_strict_range_and_finite_distance(self):
        for distance in (0, -1, 401, float("inf"), float("nan"), True):
            oracle = ArsenalAdmissionOracle()
            result = oracle.admit("SFA-010", replace(
                evidence(destination=True), destination_distance_cm=distance))
            self.assertFalse(result.admitted, distance)
            self.assertEqual(oracle.energy, 100)
        self.assertTrue(self.a.admit("SFA-010", replace(
            evidence(destination=True), destination_distance_cm=400)).admitted)

    def test_cooldown_and_energy_debit_atomic(self):
        self.assertEqual(self.a.admit("SFA-001", evidence(T, at=0, sequence=1)).energy_after, 85)
        denied = self.a.admit("SFA-001", evidence(T, at=1999, sequence=2))
        self.assertEqual(denied.reason, "cooldown")
        self.assertEqual(self.a.energy, 85)
        self.assertEqual(self.a.admit("SFA-001", evidence(T, at=2000, sequence=3)).energy_after, 70)

    def test_energy_exhaustion_is_not_negative(self):
        for i in range(6):
            self.assertTrue(self.a.admit("SFA-001", evidence(T, at=i * 2000, sequence=i + 1)).admitted)
        denied = self.a.admit("SFA-001", evidence(T, at=12000, sequence=7))
        self.assertEqual(denied.reason, "energy")
        self.assertEqual(self.a.energy, 10)

    def test_generation_invalidates_mark_and_sequence_but_not_cooldown(self):
        self.assertTrue(self.a.admit("SFA-001", evidence(T, at=1)).admitted)
        self.a.change_generation(2)
        self.assertFalse(self.a.admit("SFA-001", evidence(T, at=1000, generation=1)).admitted)
        self.assertEqual(self.a.admit("SFA-001", evidence(T, at=1000, generation=2)).reason, "cooldown")
        result = self.a.admit("SFA-002", evidence(T, at=1000, generation=2, sequence=2, cls="CLS-006"))
        self.assertTrue(result.admitted)
        self.assertEqual(result.damage_upper_bound, 10)

    def test_reaver_mark_is_class_bound_and_target_specific(self):
        self.a.admit("SFA-001", evidence(T, at=100, sequence=1))
        other = replace(T, target_id="MON-002")
        bonus = self.a.admit("SFA-002", evidence(T, other, at=500, sequence=2, cls="CLS-006"))
        self.assertEqual(bonus.damage_upper_bound, 24)
        b = ArsenalAdmissionOracle()
        b.admit("SFA-001", evidence(T, at=100, sequence=1))
        self.assertEqual(b.admit("SFA-002", evidence(other, at=500, sequence=2, cls="CLS-006")).damage_upper_bound, 10)
        c = ArsenalAdmissionOracle()
        c.admit("SFA-001", evidence(T, at=100, sequence=1))
        self.assertEqual(c.admit("SFA-002", evidence(T, at=500, sequence=2, cls="CLS-001")).damage_upper_bound, 10)

    def test_mark_expires_exactly_at_four_seconds(self):
        self.a.admit("SFA-001", evidence(T, at=1))
        self.assertEqual(self.a.admit("SFA-002", evidence(T, at=4001, sequence=2, cls="CLS-006")).damage_upper_bound, 10)

    def test_shared_shield_allowance_survives_adapter_requests(self):
        self.assertEqual(self.a.admit("SFA-003", evidence(at=0, sequence=1)).shield_restored, 20)
        self.assertEqual(self.a.admit("SFA-008", evidence(at=1000, sequence=2)).shield_restored, 12)
        self.assertEqual(self.a.admit("SFA-003", evidence(at=18000, sequence=3)).shield_restored, 8)
        denied = self.a.admit("SFA-008", evidence(at=26000, sequence=4))
        self.assertEqual(denied.reason, "shared shield allowance exhausted")
        self.assertEqual(self.a.energy, 50)

    def test_invalid_shield_snapshots_denied(self):
        for pair in ((-1, 100), (101, 100), (0, 501), (False, 100), (10, True)):
            oracle = ArsenalAdmissionOracle()
            self.assertFalse(oracle.admit("SFA-003", evidence(shield=pair[0], max_shield=pair[1])).admitted)

    def test_new_generation_cannot_roll_back_server_clock(self):
        self.a.admit("SFA-001", evidence(T, at=9999))
        self.a.change_generation(2)
        self.assertEqual(self.a.admit("SFA-001", evidence(T, at=9998, generation=2)).reason, "clock regression")


if __name__ == "__main__":
    unittest.main()
