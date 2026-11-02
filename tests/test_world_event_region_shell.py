"""Regional world event shell cannot overclaim streamed gameplay regions.

These are source-level admission tests. Real UEFN streaming/AI is not proven.
"""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WorldEventShellOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = (ROOT / "verse/events/world_event_runtime.verse").read_text(encoding="utf-8")
        cls.invasion = (ROOT / "verse/world/invasion_runtime.verse").read_text(encoding="utf-8")
        cls.faction = (ROOT / "verse/factions/conflict_runtime.verse").read_text(encoding="utf-8")
        cls.topology = json.loads((ROOT / "content/world/world_topology.json").read_text(encoding="utf-8"))

    def test_streamed_footprint_is_smaller_than_world_and_abstract_allowed(self):
        self.assertGreater(len(self.topology["regions"]), 4)
        self.assertIn("AEONFALLWorldEventMaxActiveRegions:int = 4", self.world)
        valid = self.world.split("    CanClaimRegions(", 1)[1].split("    StartEvent(", 1)[0]
        self.assertIn("RegionIds.Length > AEONFALLWorldEventMaxActiveRegions", valid)
        self.assertNotIn("if (RegionIds.Length = 0)", valid)
        self.assertIn("true\n", valid)

    def test_start_and_stage_guard_before_state_commit(self):
        start = self.world.split("    StartEvent(", 1)[1].split("    GetState(", 1)[0]
        advance = self.world.split("    AdvanceStage(", 1)[1].split("    CompleteEvent(", 1)[0]
        self.assertLess(start.index("CanClaimRegions(EventId, InitialRegionIds)?"),
                        start.index("set States[EventId] = Initial"))
        self.assertLess(advance.index("CanClaimRegions(EventId, ActiveRegionIds)?"),
                        advance.index("set States[EventId] = Updated"))
        self.assertIn("NextStageIndex = Old.CurrentStageIndex + 1", advance)

    def test_claims_use_initialized_canonical_regions_and_exclude_duplicates(self):
        claim = self.world.split("    CanClaimRegions(", 1)[1].split("    StartEvent(", 1)[0]
        for token in ("RegionId = \"\"",
                      "GetAEONFALLRegionRegistry().IsRegistered[RegionId]",
                      "GetAEONFALLRegionRuntime().GetState[RegionId]",
                      "Seen.Find[RegionId]", "OtherEventId <> EventId",
                      "State.Active?", "State.ActiveRegionIds.Find[RegionId]"):
            self.assertIn(token, claim)

    def test_event_slot_cannot_overlap_three_encounter_families(self):
        claim = self.world.split("    CanClaimRegions(", 1)[1].split("    StartEvent(", 1)[0]
        self.assertIn("GetAEONFALLInvasionRuntime().HasActiveInRegion(RegionId)?", claim)
        self.assertIn("GetAEONFALLFactionConflictRuntime().HasActiveInRegion(RegionId)?", claim)
        invasion_start = self.invasion.split("    Start(InvasionId:", 1)[1].split(
            "    GetState(InvasionId:", 1
        )[0]
        war_start = self.faction.split("    StartConflict(", 1)[1].split(
            "    StartRegistered(", 1
        )[0]
        self.assertIn("WorldEventRuntime := GetAEONFALLWorldEventRuntime()", invasion_start)
        self.assertIn("not WorldEventRuntime.HasActiveInRegion(Definition.RegionId)?", invasion_start)
        self.assertIn("WorldEventRuntime := GetAEONFALLWorldEventRuntime()", war_start)
        self.assertIn("not WorldEventRuntime.HasActiveInRegion(RegionId)?", war_start)

    def test_terminal_outcomes_drop_region_footprints(self):
        for start, end in (("    CompleteEvent(", "    FailEvent("), ("    FailEvent(", None)):
            part = self.world.split(start, 1)[1]
            if end:
                part = part.split(end, 1)[0]
            self.assertIn("ActiveRegionIds := array{}", part)
            self.assertIn("Active := false", part)
        self.assertIn("AEONFALLWorldEventRuntimeSessions:weak_map(session,", self.world)

    def test_no_new_physical_spawners_or_persistent_profiles(self):
        self.assertNotIn("npc_spawner_device", self.world)
        self.assertNotIn("Spawner.Enable()", self.world)
        self.assertNotIn("SetFactionInfluence(", self.world)
        self.assertNotIn("SetCorruption(", self.world)


if __name__ == "__main__":
    unittest.main()
