"""Source-mutation guards for the shared world-event state machine.

These tests inspect Verse text; they are not UEFN compilation or execution.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "runtime_invariants", ROOT / "tools/validate_runtime_invariants.py"
)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class WorldEventTransitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "verse/events/world_event_runtime.verse").read_text(
            encoding="utf-8"
        )

    def errors(self, source: str) -> list[str]:
        return VALIDATOR.check_world_event_state_machine(source)

    def test_current_source_has_no_state_machine_errors(self):
        self.assertEqual(self.errors(self.source), [])

    def test_blank_event_id_cannot_start(self):
        changed = self.source.replace('if (EventId = ""):', 'if (false?):', 1)
        self.assertTrue(self.errors(changed))

    def test_blank_objective_id_cannot_count(self):
        changed = self.source.replace(
            'if (EventId = "" or ObjectiveId = ""):', 'if (false?):', 1
        )
        self.assertTrue(self.errors(changed))

    def test_stage_jump_is_rejected(self):
        changed = self.source.replace(
            "NextStageIndex = Old.CurrentStageIndex + 1",
            "NextStageIndex > Old.CurrentStageIndex", 1
        )
        self.assertTrue(self.errors(changed))

    def test_advance_cannot_skip_active_state(self):
        changed = self.source.replace(
            "    AdvanceStage(", "    AdvanceStage(", 1
        )
        prefix, suffix = changed.split("    AdvanceStage(", 1)
        stage, remainder = suffix.split("    CompleteEvent(", 1)
        stage = stage.replace("Old.Active?", "true?", 1)
        self.assertTrue(self.errors(prefix + "    AdvanceStage(" + stage +
                                    "    CompleteEvent(" + remainder))

    def test_terminal_completion_clears_loaded_regions(self):
        prefix, suffix = self.source.split("    CompleteEvent(", 1)
        complete, tail = suffix.split("    FailEvent(", 1)
        complete = complete.replace("ActiveRegionIds := array{}", 
                                    "ActiveRegionIds := Old.ActiveRegionIds", 1)
        self.assertTrue(self.errors(prefix + "    CompleteEvent(" + complete +
                                    "    FailEvent(" + tail))

    def test_failure_does_not_leak_participation(self):
        changed = self.source.replace(
            "GetAEONFALLEncounterParticipation().ClearEncounter(",
            "Print(", 1
        )
        self.assertTrue(self.errors(changed))

    def test_completion_reward_gate_must_exist(self):
        changed = self.source.replace(
            "AEONFALLEncounterRewardService.AwardRegistered(",
            "AEONFALLUnverifiedReward(", 1
        )
        self.assertTrue(self.errors(changed))

    def test_region_shell_budget_guard_cannot_be_removed(self):
        changed = self.source.replace(
            "RegionIds.Length > AEONFALLWorldEventMaxActiveRegions",
            "RegionIds.Length > 1000", 1
        )
        self.assertTrue(self.errors(changed))

    def test_world_event_does_not_claim_foreign_or_duplicate_regions(self):
        for needle in (
            "GetAEONFALLRegionRegistry().IsRegistered[RegionId]",
            "GetAEONFALLRegionRuntime().GetState[RegionId]",
            "Seen.Find[RegionId]",
            "OtherEventId <> EventId",
            "State.ActiveRegionIds.Find[RegionId]",
        ):
            with self.subTest(guard=needle):
                changed = self.source.replace(needle, "GUARD_REMOVED", 1)
                self.assertTrue(self.errors(changed))

    def test_world_event_rechecks_stage_footprint_before_transition(self):
        changed = self.source.replace(
            "CanClaimRegions(EventId, ActiveRegionIds)?",
            "true?", 1
        )
        self.assertTrue(self.errors(changed))

    def test_world_event_start_cannot_bypass_claim_admission(self):
        changed = self.source.replace(
            "if (not CanClaimRegions(EventId, InitialRegionIds)?):",
            "if (false?):", 1
        )
        self.assertTrue(self.errors(changed))

    def test_region_claims_cannot_ignore_active_invasion_or_faction_war(self):
        for needle in (
            "GetAEONFALLInvasionRuntime().HasActiveInRegion(RegionId)?",
            "GetAEONFALLFactionConflictRuntime().HasActiveInRegion(RegionId)?",
        ):
            with self.subTest(guard=needle):
                self.assertTrue(self.errors(self.source.replace(needle, "false?", 1)))


if __name__ == "__main__":
    unittest.main()
