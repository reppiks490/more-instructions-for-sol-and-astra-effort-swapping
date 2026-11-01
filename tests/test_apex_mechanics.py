"""Mutation tests for the apex mechanics policy and fail-closed generic adapter."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.validate_apex_mechanics import ROOT, validate

class ApexMechanicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        paths = (
            ROOT / "content/transcendent/ascended_ability_mechanics.json",
            ROOT / "content/transcendent/ascended_forms.json",
            ROOT / "content/transcendent/ascended_form_adapter_bindings.json",
            ROOT / "content/vertical_slice/slice_001_classes.json",
        )
        cls.docs = [json.loads(p.read_text(encoding="utf-8")) for p in paths]

    def errors_after(self, mutate):
        docs = copy.deepcopy(self.docs)
        mutate(docs[0]["mechanics"])
        return validate(*docs)

    def test_baseline(self):
        self.assertEqual(validate(*self.docs), [])

    def test_missing_ability_rejected(self):
        self.assertTrue(self.errors_after(lambda entries: entries.pop()))

    def test_duplicate_ability_rejected(self):
        self.assertTrue(self.errors_after(lambda entries: entries.append(copy.deepcopy(entries[0]))))

    def test_unsafe_budget_rejected(self):
        self.assertTrue(self.errors_after(lambda entries: entries[0]["limits"].update(radius_m=1000)))

    def test_boss_immunity_bypass_rejected(self):
        self.assertTrue(self.errors_after(lambda entries: entries[5]["preflight"].update(boss_policy="ignore")))

    def test_missing_counterplay_rejected(self):
        self.assertTrue(self.errors_after(lambda entries: entries[0]["counterplay"].update(response="hit")))

    def test_missing_preflight_rejected(self):
        self.assertTrue(self.errors_after(lambda entries: entries[0]["preflight"].update(mode="generic_trigger")))

    def test_missing_class_synergy_rejected(self):
        self.assertTrue(self.errors_after(lambda entries: entries[0]["class_synergy"].update(class_ids=["CLS-NONEXISTENT"])))

    def test_generic_trigger_rejects_transformed_abilities_before_effect(self):
        source = (ROOT / "verse/combat/trigger_ability_adapter_device.verse").read_text(encoding="utf-8")
        self.assertIn('Definition.RequiredTransformationId <> ""', source)
        self.assertIn('"apex_requires_specialized_preflight"', source)
        self.assertLess(source.index('"apex_requires_specialized_preflight"'), source.index("TriggerOutput.Trigger("))

if __name__ == "__main__":
    unittest.main()
