"""Source contract tests for the canonical Axiom Heart final forge.

These guards cannot substitute for native Verse compilation or Launch Session.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "content/crafting/axiom_heart_recipe.json"
GENERATED = ROOT / "verse/generated/axiom_heart_final_costs.verse"
SERVICE = ROOT / "verse/transcendent/axiom_heart_forge_service.verse"
DEVICE = ROOT / "verse/transcendent/axiom_heart_forge_device.verse"
PROFILE = ROOT / "verse/persistence/profile_service.verse"

spec = importlib.util.spec_from_file_location(
    "build_axiom_heart_final_costs", ROOT / "tools/build_axiom_heart_final_costs.py"
)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class AxiomHeartForgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = json.loads(GRAPH.read_text(encoding="utf-8"))
        cls.generated = GENERATED.read_text(encoding="utf-8")
        cls.service = SERVICE.read_text(encoding="utf-8")
        cls.device = DEVICE.read_text(encoding="utf-8")
        cls.profile = PROFILE.read_text(encoding="utf-8")

    def test_generated_vector_matches_authoritative_recipe(self):
        self.assertEqual(self.generated, builder.render(self.graph))
        recipe = next(r for r in self.graph["recipes"] if r["id"] == "RCP-013")
        self.assertEqual(recipe["output"], {"material_id": "MAT-030", "quantity": 1})
        self.assertEqual(recipe["station"], "Throne of Zero")
        self.assertEqual(len(recipe["inputs"]), 12)

    def test_generator_rejects_duplicate_and_nonpositive_costs(self):
        import copy
        changed = copy.deepcopy(self.graph)
        final = next(r for r in changed["recipes"] if r["id"] == "RCP-013")
        final["inputs"].append(dict(final["inputs"][0]))
        with self.assertRaises(ValueError):
            builder.render(changed)
        final["inputs"].pop()
        final["inputs"][0]["quantity"] = 0
        with self.assertRaises(ValueError):
            builder.render(changed)

    def test_eligibility_precedes_any_material_debit(self):
        source = self.service
        self.assertLess(source.index("CandidateManager.CanForgeAxiomHeart[Agent]"),
                        source.index("var UpdatedLedger"))
        self.assertIn("Profile.AxiomHeartCrafted?", source)
        self.assertIn("Profile.TranscendentState <> 0", source)
        self.assertIn("ExistingHeart <> 0", source)

    def test_costs_are_checked_and_deducted_without_partial_commit(self):
        source = self.service
        for guard in ("Cost.Amount > 0", "Balance >= Cost.Amount",
                      "set UpdatedLedger[Cost.MaterialId] = Balance - Cost.Amount",
                      "if (not CostsValid?):", "return false"):
            self.assertIn(guard, source)
        self.assertLess(source.index("if (not CostsValid?):"),
                        source.index("ProfileService.TrySaveProfile(Player, Candidate)"))

    def test_output_flag_and_debit_commit_together(self):
        source = self.service
        self.assertIn("MakeAEONFALLPlayerProfile<constructor>(Profile)", source)
        self.assertIn("MaterialLedger := UpdatedLedger", source)
        self.assertIn("AxiomHeartCrafted := true", source)
        self.assertIn("set UpdatedLedger[AxiomHeartFinalOutputMaterialId] = 1", source)
        self.assertEqual(source.count("ProfileService.TrySaveProfile(Player, Candidate)"), 1)
        self.assertLess(source.index("Saved := ProfileService.TrySaveProfile"),
                        source.index('EventType := "transcendent.axiom_heart_forged"'))
        self.assertIn("if (Saved?):", source)

    def test_legacy_flag_setter_cannot_grant_apex_progress(self):
        setter = self.profile.split("    SetAxiomHeartCrafted(", 1)[1].split(
            "    SetZeroCandidate(", 1
        )[0]
        self.assertNotIn("AxiomHeartCrafted := IsCrafted", setter)
        self.assertNotIn("SaveProfile(", setter)
        self.assertNotIn("TrySaveProfile(", setter)
        self.assertIn("return", setter)

    def test_editor_button_owns_and_releases_subscription(self):
        self.assertIn("ForgeButton.InteractedWithEvent.Subscribe(OnInteracted)", self.device)
        self.assertIn("ButtonSubscription = option{Subscription}", self.device)
        self.assertIn("OnEnd<override>()", self.device)
        self.assertIn("Subscription.Cancel()", self.device)
        self.assertIn("ForgeService.TryForge(Agent)", self.device)
        self.assertIn("if (Forged?):", self.device)


if __name__ == "__main__":
    unittest.main()
