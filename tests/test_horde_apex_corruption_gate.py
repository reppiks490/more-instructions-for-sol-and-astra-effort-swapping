"""Source/data regression checks for canonical Tier V ecology admission.

These checks do not compile or execute Verse; native Launch Session evidence
is required for gameplay behavior, streaming and multiplayer races.
"""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
HORDE = ROOT / "verse/npcs/horde_runtime.verse"
REGION_DATA = ROOT / "content/world/region_001_living_world.json"
ESCALATION = ROOT / "verse/world/regional_escalation_runtime.verse"


class HordeApexCorruptionGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HORDE.read_text(encoding="utf-8")
        cls.escalation = ESCALATION.read_text(encoding="utf-8")
        cls.data = json.loads(REGION_DATA.read_text(encoding="utf-8"))
        cls.method = cls.source.split("    NextTier(", 1)[1].split("    Feed(", 1)[0]

    def test_canonical_apex_requires_initialized_corrupted_region(self):
        method = self.method
        guard = "GetAEONFALLRegionRegistry().IsRegistered[Old.RegionId]"
        state = "GetAEONFALLRegionRuntime().GetState[Old.RegionId]"
        threshold = "RegionState.Corruption < 80"
        promotion = "return 5"
        for token in (guard, state, threshold, promotion,
                      "return Old.Tier", "RegionalApexBiomass",
                      "not HasApex(Old.RegionId)?", "Open?"):
            self.assertIn(token, method)
        self.assertLess(method.index(guard), method.index(state))
        self.assertLess(method.index(state), method.index(threshold))
        self.assertLess(method.index(threshold), method.index(promotion))
        self.assertIn(
            "else:\n                    # A registered but uninitialized region cannot promote.\n"
            "                    return Old.Tier", method
        )

    def test_apex_gate_matches_authored_devouring_front_band(self):
        bands = self.data["corruption_thresholds"]
        front = next(row for row in bands if row["label"] == "devouring_front")
        self.assertEqual((front["min"], front["max"]), (80, 94))
        self.assertIn("if (Value >= 80):", self.escalation)
        self.assertIn("RegionState.Corruption < 80", self.method)

    def test_gate_preserves_existing_one_apex_and_population_budget(self):
        self.assertIn("not HasApex(Old.RegionId)?", self.method)
        self.assertIn("Open := ApexEventOpen[Old.RegionId]", self.method)
        self.assertIn("if (GetAEONFALLRegionRegistry().IsRegistered[Old.RegionId]):",
                      self.method)
        for forbidden in ("RegisterBrood(", "AddCorpse(", "Spawner.Enable(",
                          "RequestWave(", "npc_spawner_device"):
            self.assertNotIn(forbidden, self.method)

    def test_cleansing_counterplay_remains_effective(self):
        # Sanctifying one corpse can move a region from 80 to 76,
        # preventing a *new* apex without despawning an existing one.
        self.assertIn("set Delta = -4", self.escalation)
        self.assertIn("set Delta = -2", self.escalation)
        self.assertIn("set Delta = 5", self.escalation)
        self.assertIn("Reconciled := ReconcileRegion(RegionId)", self.escalation)


if __name__ == "__main__":
    unittest.main()
