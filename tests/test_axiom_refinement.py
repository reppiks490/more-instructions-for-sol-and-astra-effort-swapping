"""Source-level and canonical-graph regression checks for intermediate Axiom refinement."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "build_axiom_refinement_registry", ROOT / "tools/build_axiom_refinement_registry.py"
)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class AxiomRefinementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = json.loads((ROOT / "content/crafting/axiom_heart_recipe.json").read_text())
        cls.bindings = json.loads((ROOT / "content/crafting/refinement_gate_bindings.json").read_text())
        cls.generated = (ROOT / "verse/generated/axiom_refinement_recipes.verse").read_text()
        cls.service = (ROOT / "verse/crafting/axiom_refinement_service.verse").read_text()
        cls.device = (ROOT / "verse/crafting/axiom_refinement_button_device.verse").read_text()

    def test_generated_registry_matches_canonical_source(self):
        self.assertEqual(self.generated, builder.render(self.graph, self.bindings))
        self.assertEqual(self.generated.count("aeonfall_refinement_recipe_definition{"), 13)
        self.assertNotIn('RecipeId := "RCP-013"', self.generated)
        self.assertNotIn('OutputMaterialId := "MAT-030"', self.generated)

    def test_only_provable_gate_is_enabled(self):
        bound = [x for x in self.bindings["recipes"] if x["state"] == "bound"]
        self.assertEqual([x["recipe_id"] for x in bound], ["RCP-012"])
        self.assertEqual(bound[0]["minimum_ascension_rank"], 2)
        self.assertEqual(bound[0]["required_trial_ids"], ["ASC-TRIAL-008"])
        self.assertEqual(self.generated.count("GateBound := true"), 1)

    def test_missing_or_fabricated_gate_bindings_rejected(self):
        altered = copy.deepcopy(self.bindings)
        altered["recipes"] = altered["recipes"][:-1]
        with self.assertRaises(ValueError):
            builder.render(self.graph, altered)
        altered = copy.deepcopy(self.bindings)
        altered["recipes"][0]["state"] = "bound"
        with self.assertRaises(ValueError):
            builder.render(self.graph, altered)
        altered = copy.deepcopy(self.bindings)
        item = next(x for x in altered["recipes"] if x["recipe_id"] == "RCP-012")
        item["required_trial_ids"] = []
        with self.assertRaises(ValueError):
            builder.render(self.graph, altered)

    def test_duplicate_costs_and_apex_output_rejected(self):
        graph = copy.deepcopy(self.graph)
        recipe = next(r for r in graph["recipes"] if r["id"] == "RCP-012")
        recipe["inputs"].append(dict(recipe["inputs"][0]))
        with self.assertRaises(ValueError):
            builder.render(graph, self.bindings)
        graph = copy.deepcopy(self.graph)
        recipe = next(r for r in graph["recipes"] if r["id"] == "RCP-012")
        recipe["output"]["material_id"] = "MAT-030"
        with self.assertRaises(ValueError):
            builder.render(graph, self.bindings)

    def test_transaction_is_atomic_and_cannot_reach_final_forge(self):
        source = self.service
        for fragment in (
            "if (not Recipe.GateBound?):", 'Recipe.RecipeId <> "RCP-013"',
            'Recipe.OutputMaterialId <> "MAT-030"', "Recipe.StationId = StationId",
            "Profile.CompletedTrialIds.Find[TrialId]",
            "Profile.AscensionRank >= Recipe.MinimumAscensionRank",
            "Balance >= Cost.Amount", "MaterialLedger := UpdatedLedger",
            "ProfileService.TrySaveProfile(Player, Candidate)",
        ):
            self.assertIn(fragment, source)
        self.assertEqual(source.count("ProfileService.TrySaveProfile(Player, Candidate)"), 1)
        self.assertLess(source.index("if (not Valid?):"),
                        source.index("ProfileService.TrySaveProfile(Player, Candidate)"))
        self.assertLess(source.index("Saved := ProfileService.TrySaveProfile"),
                        source.index('EventType := "crafting.refinement_committed"'))
        self.assertNotIn("SetMaterialCount(", source)
        self.assertNotIn("AxiomHeartCrafted := true", source)

    def test_editor_device_owns_subscription_and_checks_station(self):
        self.assertIn("RefinementButton.InteractedWithEvent.Subscribe(OnInteracted)", self.device)
        self.assertIn("Subscription.Cancel()", self.device)
        self.assertIn("OnEnd<override>()", self.device)
        self.assertIn("TryRefine(Agent, RecipeId, StationId)", self.device)


if __name__ == "__main__":
    unittest.main()
