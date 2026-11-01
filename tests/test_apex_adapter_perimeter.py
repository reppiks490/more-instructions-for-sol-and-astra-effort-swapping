"""Source-level regression tests: transformed effects cannot use generic adapters.

These tests check source guards, not native Verse compilation or physical UEFN
effects. Dedicated apex adapters remain required before enabling God/Absolute/Zero.
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = {
    "contract": "verse/combat/ability_contract.verse",
    "trigger": "verse/combat/trigger_ability_adapter_device.verse",
    "status": "verse/combat/status_ability_adapter_device.verse",
    "composite": "verse/combat/composite_ability_adapter_device.verse",
    "prop": "verse/core/prop_spawn_adapter_device.verse",
    "scent": "verse/npcs/royal_scent_adapter_device.verse",
}
GUARD = "AEONFALLRequiresSpecializedTransformationPreflight(Definition)?"
REJECTION = 'ResultCode := "apex_requires_specialized_preflight"'


def check_perimeter(sources: dict[str, str]) -> list[str]:
    errors: list[str] = []
    contract = sources["contract"]
    for flag in (
        'Definition.RequiredTransformationId <> ""',
        "Definition.RequiresTransformationContext?",
        "Definition.ResourcePolicy = aeonfall_resource_policy.TransformationOnly",
    ):
        if flag not in contract:
            errors.append(f"shared preflight omits {flag}")

    trigger = sources["trigger"]
    if (
        GUARD not in trigger
        or '"apex_requires_specialized_preflight"' not in trigger
        or trigger.find(GUARD) >= trigger.find("TriggerOutput.Trigger(")
        or '"ability_definition_missing"' not in trigger
    ):
        errors.append("trigger can dispatch without fail-closed transformed preflight")

    for name in ("status", "composite"):
        src = sources[name]
        first_effect = src.find("GetAEONFALLStatusRuntime().ApplyBatch")
        if (
            GUARD not in src
            or REJECTION not in src
            or first_effect < 0
            or src.find(GUARD) >= first_effect
            or src.find(REJECTION) >= first_effect
        ):
            errors.append(f"{name} can mutate statuses without transformed preflight")
        if name == "composite":
            trigger_pos = src.find("TriggerOutput.Trigger(")
            if trigger_pos < 0 or src.find(GUARD) >= trigger_pos:
                errors.append("composite can trigger a physical graph before preflight")

    prop = sources["prop"]
    prepare = prop.partition("    PrepareSpawn(")[2]
    if (
        "if (Prepared := PrepareSpawn[Request]):" not in prop
        or prop.find("if (Prepared := PrepareSpawn[Request]):") >= prop.find("SpawnProp(")
        or "not " + GUARD not in prepare
        or prepare.find("not " + GUARD) >= prepare.find("GetAEONFALLSpawnRuntime().Reserve(")
    ):
        errors.append("prop spawn lacks pre-reservation transformed preflight")

    scent = sources["scent"]
    marked = scent.partition("    StartMarkedChallenge(")[2]
    if (
        "not AEONFALLRequiresSpecializedTransformationPreflight(AbilityDefinition)?" not in marked
        or marked.find("not AEONFALLRequiresSpecializedTransformationPreflight(AbilityDefinition)?")
        >= marked.find("GetAEONFALLStatusRuntime().ApplyStatus(")
        or "StartMarkedChallenge[Request, SpeciesId]" not in scent
    ):
        errors.append("Royal Scent challenge lacks pre-mark transformed preflight")
    return errors


class ApexAdapterPerimeterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = {
            name: (ROOT / path).read_text(encoding="utf-8")
            for name, path in PATHS.items()
        }

    def mutate(self, name: str, old: str, new: str = "") -> list[str]:
        sources = dict(self.sources)
        self.assertIn(old, sources[name], f"mutation anchor missing in {name}")
        sources[name] = sources[name].replace(old, new, 1)
        return check_perimeter(sources)

    def test_baseline_perimeter(self):
        self.assertEqual(check_perimeter(self.sources), [])

    def test_missing_exact_transformation_id_guard(self):
        self.assertTrue(self.mutate("contract", 'Definition.RequiredTransformationId <> ""'))

    def test_missing_legacy_context_guard(self):
        self.assertTrue(self.mutate("contract", "Definition.RequiresTransformationContext?"))

    def test_missing_transformation_resource_guard(self):
        self.assertTrue(self.mutate("contract", "Definition.ResourcePolicy = aeonfall_resource_policy.TransformationOnly"))

    def test_trigger_guard_removed(self):
        self.assertTrue(self.mutate("trigger", GUARD))

    def test_status_guard_removed(self):
        self.assertTrue(self.mutate("status", GUARD))

    def test_composite_guard_removed(self):
        self.assertTrue(self.mutate("composite", GUARD))

    def test_prop_spawn_guard_removed(self):
        self.assertTrue(self.mutate("prop", "not " + GUARD))

    def test_royal_scent_guard_removed(self):
        self.assertTrue(self.mutate("scent", "not AEONFALLRequiresSpecializedTransformationPreflight(AbilityDefinition)?"))


if __name__ == "__main__":
    unittest.main()
