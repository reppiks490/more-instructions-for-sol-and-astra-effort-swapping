"""Guard the public ascension guide against canonical trial and recipe drift."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class AscensionGuideTests(unittest.TestCase):
    def test_guide_matches_canonical_trial_order(self):
        doc = (ROOT / "docs/TRANSCENDENT_ZERO_ASCENSION.md").read_text(encoding="utf-8")
        trials = json.loads((ROOT / "content/transcendent/ascension_trials.json").read_text(encoding="utf-8"))["trials"]
        roman = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X")
        headings = re.findall(r"^### ([IVX]+) — (.+)$", doc, re.MULTILINE)
        self.assertEqual(headings, [(roman[i], trial["name"]) for i, trial in enumerate(trials)])
        self.assertIn("Level **1000**", doc)
        self.assertIn("Trials I–IX → Axiom Heart → Trial X", doc)
        self.assertIn("Zero Candidate; it is **not** a Transcendent grant", doc)

    def test_recipe_summary_points_to_authoritative_graph(self):
        summary = json.loads((ROOT / "content/progression/axiom_heart_recipe.json").read_text(encoding="utf-8"))
        doc = (ROOT / "docs/TRANSCENDENT_ZERO_ASCENSION.md").read_text(encoding="utf-8")
        canonical = (ROOT / "content/progression" / summary["authoritative_graph"]).resolve()
        self.assertTrue(canonical.is_file())
        self.assertIn("content/crafting/axiom_heart_recipe.json", doc)
        self.assertEqual(summary["declared_raw_acquisition_total"], 68420)

if __name__ == "__main__":
    unittest.main()
