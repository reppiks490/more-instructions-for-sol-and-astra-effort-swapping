"""Guard the durable Trial I-X completion boundary against source regressions.

Source checks do not replace native Verse compilation or multiplayer testing.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "verse/persistence/profile_service.verse"
TRIAL = ROOT / "verse/transcendent/ascension_trial_runtime.verse"
TRIALS = ROOT / "content/transcendent/ascension_trials.json"


class AscensionTrialCommitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = PROFILE.read_text(encoding="utf-8")
        cls.trial = TRIAL.read_text(encoding="utf-8")
        cls.canonical = json.loads(TRIALS.read_text(encoding="utf-8"))["trials"]

    def test_all_ten_canonical_trials_remain_in_order(self):
        self.assertEqual(
            [t["id"] for t in self.canonical],
            [f"ASC-TRIAL-{i:03d}" for i in range(1, 11)],
        )
        self.assertTrue(self.canonical[8]["unlocks_axiom_forge"])
        self.assertTrue(self.canonical[9]["requires_axiom_heart"])

    def test_profile_trial_completion_requires_durable_ack(self):
        method = self.profile.split("    CompleteTrial(", 1)[1].split("    DiscoverPoi(", 1)[0]
        self.assertIn(")<transacts>:logic=", method)
        self.assertIn('TrialId <> ""', method)
        self.assertIn("Player.IsActive[]", method)
        self.assertIn("Old.CompletedTrialIds.Find[TrialId]", method)
        self.assertIn("return false", method)
        self.assertIn("CompletedTrialIds := Old.CompletedTrialIds + array{TrialId}", method)
        self.assertIn("return TrySaveProfile(Player, Candidate)", method)
        self.assertNotIn("\n                SaveProfile(Player, Candidate)", method)

    def test_trial_runtime_waits_for_persistence_before_unlocks(self):
        complete = self.trial.split("    Complete(Agent:agent)", 1)[1].split("    FailOwner(", 1)[0]
        self.assertIn("Committed := ProfileService.CompleteTrial(", complete)
        self.assertIn("if (not Committed?):", complete)
        self.assertIn('EventType := "ascension_trial.persistence_rejected"', complete)
        self.assertLess(
            complete.index("if (not Committed?):"),
            complete.index("set StatesByOwner[OwnerKey] = Finished"),
        )
        self.assertLess(
            complete.index("set StatesByOwner[OwnerKey] = Finished"),
            complete.index("CandidateManager.EvaluateCandidate(Agent)"),
        )
        self.assertLess(
            complete.index("set StatesByOwner[OwnerKey] = Finished"),
            complete.index('"ascension_trial.axiom_forge_unlocked"'),
        )

    def test_final_objective_retries_save_without_duplicate_progress(self):
        mark = self.trial.split("    MarkObjectiveComplete(", 1)[1].split("    Complete(Agent:agent)", 1)[0]
        self.assertIn("Old.CompletedObjectiveIds.Find[ObjectiveId]", mark)
        self.assertIn("if (Old.CompletedObjectiveIds.Length >= Definition.ObjectiveIds.Length):", mark)
        self.assertIn("return Complete(Agent)", mark)
        self.assertIn("UpdatedObjectives:[]string =", mark)
        self.assertIn("Old.CompletedObjectiveIds + array{ObjectiveId}", mark)
        self.assertLess(
            mark.index("Old.CompletedObjectiveIds.Find[ObjectiveId]"),
            mark.index("UpdatedObjectives:[]string ="),
        )

    def test_expired_trial_cannot_finish_or_accept_objectives(self):
        mark = self.trial.split("    MarkObjectiveComplete(", 1)[1].split("    Complete(Agent:agent)", 1)[0]
        complete = self.trial.split("    Complete(Agent:agent)", 1)[1].split("    FailOwner(", 1)[0]
        self.assertIn("Old.RemainingSeconds > 0.0", mark)
        self.assertIn("Old.RemainingSeconds > 0.0", complete)

    def test_failed_save_does_not_emit_completion_or_candidate(self):
        complete = self.trial.split("    Complete(Agent:agent)", 1)[1].split("    FailOwner(", 1)[0]
        failure = complete.split("if (not Committed?):", 1)[1].split("Finished :=", 1)[0]
        self.assertIn("return false", failure)
        self.assertNotIn("CandidateManager.EvaluateCandidate", failure)
        self.assertNotIn('"ascension_trial.completed"', failure)


if __name__ == "__main__":
    unittest.main()
