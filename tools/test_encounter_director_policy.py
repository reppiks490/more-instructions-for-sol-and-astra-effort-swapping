#!/usr/bin/env python3
"""Mutation tests for policy validation; these do not execute Verse."""
import copy
import json
import unittest

from build_slice_encounter_directors import POLICY, SOURCE
from validate_encounter_directors import validate_policy


class EncounterDirectorPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads(POLICY.read_text())
        self.source = json.loads(SOURCE.read_text())

    def rejects(self, mutated):
        self.assertTrue(validate_policy(mutated, self.source))

    def test_authored_policy_passes(self):
        self.assertEqual(validate_policy(self.policy, self.source), [])

    def test_arbitrary_encounter_rejected(self):
        self.policy["encounters"][0]["id"] = "BOS-999"
        self.rejects(self.policy)

    def test_empty_transition_rejected(self):
        gate = self.policy["encounters"][0]["phases"][0]["transition_alternatives"][0]
        gate["objectives"] = []
        self.rejects(self.policy)

    def test_future_objective_rejected(self):
        self.policy["encounters"][0]["phases"][0]["transition_alternatives"][0]["objectives"] = ["OBJ-BOS005-PUNISH-WHISTLE"]
        self.rejects(self.policy)

    def test_boss_victory_without_body_death_rejected(self):
        phase = self.policy["encounters"][0]["phases"][-1]
        phase["transition_alternatives"][0] = {"objectives": ["OBJ-BOS005-PUNISH-WHISTLE"], "weak_points": [], "signals": []}
        self.rejects(self.policy)

    def test_early_body_death_signal_rejected(self):
        phase = self.policy["encounters"][0]["phases"][0]
        phase["signals"][0]["boss_defeat"] = True
        self.rejects(self.policy)

    def test_single_anchor_bypass_rejected(self):
        self.policy["encounters"][0]["phases"][1]["transition_alternatives"][0]["objectives"].pop()
        self.rejects(self.policy)

    def test_failed_bite_requirement_cannot_be_dropped(self):
        self.policy["encounters"][1]["phases"][0]["transition_alternatives"][0]["objectives"] = []
        self.rejects(self.policy)

    def test_decree_requirement_cannot_be_lowered(self):
        self.policy["encounters"][2]["phases"][2]["objective_counts"]["OBJ-BOS011-SOLVE-DECREES"] = 1
        self.rejects(self.policy)

    def test_lot_requirement_cannot_be_lowered(self):
        self.policy["encounters"][3]["phases"][0]["signals"][0]["count"] = 1
        self.rejects(self.policy)

    def test_world_event_cannot_impersonate_boss(self):
        self.policy["encounters"][3]["phases"][0]["signals"][0]["boss_health_percent"] = 70
        self.rejects(self.policy)

    def test_nonpositive_and_boolean_counts_rejected(self):
        for invalid in (0, -1, True):
            with self.subTest(invalid=invalid):
                mutated = copy.deepcopy(self.policy)
                mutated["encounters"][0]["phases"][0]["signals"][0]["count"] = invalid
                self.rejects(mutated)

    def test_phase_reorder_rejected(self):
        self.policy["encounters"][0]["phases"].reverse()
        self.rejects(self.policy)


if __name__ == "__main__":
    unittest.main()
