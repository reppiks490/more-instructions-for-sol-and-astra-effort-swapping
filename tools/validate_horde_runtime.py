#!/usr/bin/env python3
"""Check horde wiring and in-editor acceptance coverage, not Verse execution."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    errors = []
    required = {
        "verse/core/runtime_tick_device.verse": ["AEONFALLHordeRuntime.TickAll(Interval)"],
        "verse/core/actor_registry.verse": ["AEONFALLHordeRuntime.RemoveBrood(RuntimeKey)"],
        "verse/npcs/horde_runtime.verse": [
            "Corpse.RegionId = Old.RegionId", "Corpse.RemainingSeconds > 0.0",
            "Corpses.Length < Policy.MaxCorpses", "Brood.Length < Policy.MaxBrood",
            "RegionalBiomass.Length < Policy.MaxBrood", "HasRegion(RegionId)?",
            "Id := NextCorpseId + 1", "not HasApex(Old.RegionId)?",
            "RegionTotal >= Policy.RegionalApexBiomass", "Open?",
            "Secondary = aeonfall_horde_trait.None", "ClearRegion", "RemoveBrood",
            "set ApexEventOpen = KeptEvents", "set RegionalBiomass = KeptBiomass",
            "DeltaSeconds <= 0.0", "horde.corpse_expired",
        ],
        "verse/npcs/horde_ecology_adapter_device.verse": [
            "Spawner.SpawnedEvent.Subscribe", "Character.EliminatedEvent().Subscribe",
            "Range <= BestDistance", "Character.IsActive[]", "player[Agent]",
            "Handled:logic = false", "set Handled = true", "Subscription.Cancel()",
            "StopEvent.Signal()", "StopEvent.Await()", "race:",
            "AEONFALLHordeRuntime.ClearRegion(RegionId)", "FindNearest",
            "GorgedEffects.Trigger(Agent)", "RemadeEffects.Trigger(Agent)",
            "ApostateEffects.Trigger(Agent)", "CrownedEffects.Trigger(Agent)",
        ],
    }
    for path, tokens in required.items():
        source = (ROOT / path).read_text()
        for token in tokens:
            if token not in source:
                errors.append(f"{path}: missing integration guard {token}")
    harness = (ROOT / "verse/testing/horde_runtime_test_device.verse").read_text()
    labels = set(re.findall(r'Check\("([^"]+)"', harness))
    coverage = {
        "duplicate registration", "consumption replay rejected", "first consumer wins",
        "zero corpse rejected", "negative corpse rejected", "oversized corpse rejected",
        "unknown region rejected", "primary trait retained", "two trait cap",
        "open apex event", "close apex event", "reopen apex event", "denial does not feed biomass", "second brood", "cross region feed", "cross region denial",
        "corpse use wins", "denied corpse cannot feed", "duplicate use rejected",
        "negative tick ignored", "corpse live before expiry", "expiry", "ID never reused",
        "region brood cleanup", "region corpse cleanup", "region biomass cleanup",
        "unrelated region preserved", "brood cap", "corpse cap", "expired slot reusable",
        "invalid policy rejected",
    }
    for label in sorted(coverage - labels):
        errors.append(f"missing in-editor assertion: {label}")
    for tier in range(1, 6):
        if f'CheckTier(Runtime, "a", {tier})' not in harness:
            errors.append(f"in-editor harness does not exercise tier {tier}")
    if "Enabled:logic = false" not in harness:
        errors.append("dev harness must default disabled")
    workflow = (ROOT / ".github/workflows/catalog-validation.yml").read_text()
    if "python tools/validate_horde_runtime.py" not in workflow:
        errors.append("horde integration guard is not wired into CI")
    if errors:
        print("Horde integration validation FAILED")
        print("\n".join(errors))
        return 1
    print(f"Horde integration validation PASSED: {len(coverage)} acceptance categories, 5 tiers")
    print("Static integration only. Execute horde_runtime_test_device in UEFN for runtime evidence.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
