"""Source-level regression checks for canonical corpse-to-region consequences.

These checks inspect Verse source; they do not execute or compile Verse.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
ESCALATION = ROOT / "verse/world/regional_escalation_runtime.verse"
HORDE = ROOT / "verse/npcs/horde_runtime.verse"
REGION = ROOT / "verse/world/region_runtime.verse"


class CorpseRegionalPressureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.escalation = ESCALATION.read_text(encoding="utf-8")
        cls.horde = HORDE.read_text(encoding="utf-8")
        cls.region = REGION.read_text(encoding="utf-8")

    def test_counterplay_is_bounded_and_asymmetric(self):
        method = self.escalation.split("    ApplyCorpseUse(", 1)[1].split(
            "    ComputeHostility(", 1
        )[0]
        values = dict(re.findall(
            r"if \(Use = aeonfall_corpse_use\.(\w+)\):\s+set Delta = (-?\d+)",
            method,
        ))
        self.assertEqual(values, {
            "Burn": "-2", "Sanctify": "-4", "Necromancy": "5",
        })
        self.assertIn("if (Use = aeonfall_corpse_use.Harvest):\n            return true", method)
        self.assertIn("State.Corruption + Delta", method)
        self.assertIn("ClampPercent(Value:int)", self.region)
        self.assertIn("else if (Value > 100)", self.region)
        self.assertIn("else if (Value > 5)", self.region)

    def test_canonical_region_commit_precedes_exclusive_corpse_removal(self):
        method = self.horde.split("    UseCorpse(", 1)[1].split(
            "    RemoveCorpse(", 1
        )[0]
        self.assertIn("Corpse := Corpses[CorpseId]", method)
        self.assertIn("Corpse.RegionId = RegionId", method)
        self.assertIn("Corpse.RemainingSeconds > 0.0", method)
        self.assertIn("IsRegistered[RegionId]", method)
        self.assertIn("Use <> aeonfall_corpse_use.Harvest", method)
        self.assertIn("Applied := AEONFALLRegionalEscalation.ApplyCorpseUse", method)
        self.assertIn("if (not Applied?):\n                    return false", method)
        self.assertLess(method.index("ApplyCorpseUse"), method.index("RemoveCorpse(CorpseId)"))
        self.assertIn("RemoveCorpse(CorpseId)", method)
        self.assertIn("EventType := Kind", self.horde)

    def test_region_reconciliation_is_transactional_and_fail_closed(self):
        method = self.escalation.split("    ApplyCorpseUse(", 1)[1].split(
            "    ComputeHostility(", 1
        )[0]
        self.assertIn("<transacts>:logic=", method)
        self.assertLess(
            method.index("GetState[RegionId]"),
            method.index("SetCorruption("),
        )
        self.assertLess(
            method.index("SetCorruption("),
            method.index("ReconcileRegion(RegionId)"),
        )
        self.assertIn("Updated?", method)
        self.assertIn("Reconciled?", method)
        self.assertIn("return false", method)
        self.assertIn("ReconcileMutation(", self.escalation)
        self.assertNotIn("npc_spawner_device", method)
        self.assertNotIn("Spawn(", method)

    def test_no_duplicate_use_or_new_population_records(self):
        method = self.horde.split("    UseCorpse(", 1)[1].split(
            "    RemoveCorpse(", 1
        )[0]
        self.assertEqual(method.count("RemoveCorpse(CorpseId)"), 1)
        self.assertNotIn("RegisterBrood(", method)
        self.assertNotIn("AddCorpse(", method)
        self.assertNotIn("RequestWave(", method)


if __name__ == "__main__":
    unittest.main()
