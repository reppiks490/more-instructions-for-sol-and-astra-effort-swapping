"""Guard actual Verse harness coverage for the horde-substrate admission query.

Python validates harness source only. UEFN Launch Session must execute it.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "verse/testing/horde_runtime_test_device.verse"
VALIDATOR = ROOT / "tools/validate_horde_runtime.py"


class HordeSubstrateHarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HARNESS.read_text(encoding="utf-8")
        cls.validator = VALIDATOR.read_text(encoding="utf-8")

    def test_harness_disabled_by_default(self):
        self.assertIn("@editable\n    Enabled:logic = false", self.source)
        self.assertIn('HORDE RESULT: {Checks} checks, {Failures} failures', self.source)

    def test_actual_horde_query_used_at_tiers_one_four_and_five(self):
        for tier, label in ((1, "tier-I query"), (4, "tier-IV query"), (5, "tier-V query")):
            self.assertIn(f'Check("{label}", Runtime.HasBroodAtLeastTier("test", {tier}))', self.source)
            self.assertIn(f'"{label}"', self.validator)

    def test_relevant_substrate_boundary_is_exercised_in_order(self):
        for amount in (599, 600):
            self.assertIn(
                f'Check("substrate {amount}", logic{{Runtime.GetRegionalBiomass("test") = {amount}}})',
                self.source,
            )
            self.assertIn(f'"substrate {amount}"', self.validator)
        self.assertLess(self.source.index('Check("substrate 599"'),
                        self.source.index('Check("substrate 600"'))

    def test_region_isolation_and_clearing(self):
        for name in ("foreign tier isolation", "invalid minimum tier",
                     "tier above maximum rejected", "cleared region tier absent",
                     "foreign region tier preserved"):
            self.assertIn(f'Check("{name}"', self.source)
            self.assertIn(f'"{name}"', self.validator)
        self.assertLess(self.source.index('Runtime.ClearRegion("test")'),
                        self.source.index('Check("cleared region tier absent"'))

    def test_runtime_test_does_not_spawn_physical_npcs(self):
        self.assertNotIn("npc_spawner_device", self.source)
        self.assertIn('Runtime := aeonfall_horde_runtime{}', self.source)
        self.assertNotIn("Start(InvasionId:", self.source)


if __name__ == "__main__":
    unittest.main()
