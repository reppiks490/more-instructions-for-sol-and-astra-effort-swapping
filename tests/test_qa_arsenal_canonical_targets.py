"""Independent QA: canonical monster identities across paid admission and hit settlement.

Source-only Python reference tests. These do not establish native registry
membership, UEFN compilation, damage authority or multiplayer correctness.
"""
import unittest

from tools.sovereign_arsenal_admission import (
    ArsenalAdmissionOracle, AuthoritativeSnapshot, RegisteredTarget,
)
from tools.sovereign_arsenal_hit_journal import (
    HitPlan, SourceHitJournal, plan_from_admission,
)


def snapshot(target_id, sequence=7):
    return AuthoritativeSnapshot(
        owner_authorized=True, controller_lease_valid=True,
        generation=1, server_time_ms=100, server_event_sequence=sequence,
        targets=(RegisteredTarget(target_id),),
    )


def plan(target_id, sequence=7):
    return HitPlan(1, sequence, "SFA-001", (target_id,), 18, 1, 18)


# ASCII-only canonical IDs, not arbitrary MON-prefix strings or Unicode digits.
INVALID_IDS = (
    "MON-1", "MON-01", "MON-00001", "MON-ABC",
    "MON-001 ", " MON-001", "MON-001\n", "MON-001/PLAYER",
    "MON-001-MON-002", "MON-001\x00", "MON-\u0660\u0660\u0661",
    "MON-\uff10\uff10\uff11", "MON-001\t",
)


class CanonicalMonsterIdentityQATests(unittest.TestCase):
    def test_noncanonical_target_cannot_spend_energy_or_create_mark(self):
        for bad_id in INVALID_IDS:
            with self.subTest(target=repr(bad_id)):
                oracle = ArsenalAdmissionOracle()
                denied = oracle.admit("SFA-001", snapshot(bad_id))
                self.assertFalse(denied.admitted)
                self.assertEqual(denied.reason, "unregistered/protected/covered target")
                self.assertEqual(oracle.energy, 100)
                self.assertIsNone(oracle.mark)
                self.assertEqual(oracle.last_event_sequence, 7)
                self.assertEqual(oracle.last_server_time_ms, 100)
                replay = oracle.admit("SFA-001", snapshot("MON-001"))
                self.assertEqual(replay.reason, "duplicate/stale server event")

    def test_noncanonical_hit_plan_cannot_stage_or_consume_event_sequence(self):
        for bad_id in INVALID_IDS:
            with self.subTest(target=repr(bad_id)):
                journal = SourceHitJournal()
                self.assertFalse(journal.stage(plan(bad_id)))
                self.assertTrue(journal.stage(plan("MON-001")))
                hit = journal.resolve(
                    1, 7, "MON-001", 0, native_hit_confirmed=True,
                )
                self.assertTrue(hit.accepted)
                self.assertEqual(hit.damage, 18)

    def test_translation_cannot_reintroduce_malformed_target(self):
        ability = {"id": "SFA-001", "damage_each": 18, "max_pulses": 1}
        for bad_id in INVALID_IDS:
            with self.subTest(target=repr(bad_id)):
                translated = plan_from_admission(
                    ability=ability, generation=1, event_sequence=7,
                    target_ids=(bad_id,), admitted=True, damage_upper_bound=18,
                )
                self.assertIsNone(translated)

    def test_valid_three_and_four_digit_ascii_monster_ids_still_work(self):
        for valid_id in ("MON-001", "MON-999", "MON-1000", "MON-9999"):
            with self.subTest(target=valid_id):
                oracle = ArsenalAdmissionOracle()
                receipt = oracle.admit("SFA-001", snapshot(valid_id))
                self.assertTrue(receipt.admitted)
                self.assertEqual(receipt.energy_after, 85)
                journal = SourceHitJournal()
                self.assertTrue(journal.stage(plan(valid_id)))
                self.assertEqual(
                    journal.resolve(
                        1, 7, valid_id, 0, native_hit_confirmed=True,
                    ).damage, 18,
                )


if __name__ == "__main__":
    unittest.main()
