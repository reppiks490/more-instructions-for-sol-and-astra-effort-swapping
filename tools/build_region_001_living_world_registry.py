#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "content" / "world" / "region_001_living_world.json"
OUTPUT = ROOT / "verse" / "generated" / "region_001_living_world_bootstrap.verse"

def q(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

def arr(values: list[str]) -> str:
    return "array{" + ", ".join(q(v) for v in values) + "}"

def nested(values: list[list[str]]) -> str:
    return "array{" + ", ".join(arr(v) for v in values) + "}"

def main() -> int:
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    region_id = doc["region_id"]

    lines = [
        "using { /Fortnite.com/Devices }",
        "using { /Verse.org/Simulation }",
        "",
        "# GENERATED FILE — do not hand edit.",
        "# Source: content/world/region_001_living_world.json",
        "",
        "Region001InvasionDefinitions:[]aeonfall_invasion_definition = array{",
    ]

    for inv in doc.get("invasions", []):
        lines.extend([
            "    aeonfall_invasion_definition{",
            f"        InvasionId := {q(inv['id'])},",
            f"        RegionId := {q(region_id)},",
            f"        AggressorId := {q(inv['aggressor_id'])},",
            f"        MinHostilityTier := {inv['min_hostility_tier']},",
            f"        WaveSpawnGroupIds := {nested(inv['waves'])},",
            f"        ObjectiveIds := {arr(inv.get('objective_ids', []))},",
            f"        HazardIds := {arr(inv.get('hazard_ids', []))},",
            f"        DurationSeconds := {float(inv['duration_seconds']):.1f},",
            f"        MaxConcurrentAi := {inv['max_concurrent_ai']},",
            f"        TimeoutIsFailure := {'true' if inv.get('timeout_is_failure', True) else 'false'}",
            "    },",
        ])

    lines.extend([
        "}",
        "",
        "aeonfall_region_001_living_world_bootstrap_device := class(creative_device):",
        "",
        "    OnBegin<override>()<suspends>:void=",
        "        var Ready:logic = false",
        "",
        "        for (Attempt := 1..20):",
        f"            if (AEONFALLRegionRegistry.IsRegistered[{q(region_id)}]):",
        "                set Ready = true",
        "                break",
        "            Sleep(0.25)",
        "",
        "        if (not Ready?):",
        "            AEONFALLRuntimeBus.Emit(",
        "                aeonfall_runtime_event{",
        '                    EventType := "bootstrap.region_001_world_not_ready",',
        f"                    SourceId := {q(region_id)}",
        "                }",
        "            )",
        "            return",
        "",
    ])

    for seed in doc.get("initial_faction_influence", []):
        lines.extend([
            "        Seeded := AEONFALLRegionRuntime.SetFactionInfluence(",
            f"            {q(region_id)},",
            f"            {q(seed['faction_id'])},",
            f"            {seed['influence']}",
            "        )",
            "        if (Seeded?):",
            "            Seeded = true",
        ])

    lines.extend([
        "",
        "        for (Definition : Region001InvasionDefinitions):",
        "            Registered := AEONFALLInvasionRegistry.Register(Definition)",
        "            if (not Registered?):",
        "                AEONFALLRuntimeBus.Emit(",
        "                    aeonfall_runtime_event{",
        '                        EventType := "bootstrap.invasion_registration_failed",',
        "                        SourceId := Definition.InvasionId,",
        "                        TargetId := Definition.RegionId",
        "                    }",
        "                )",
        "",
        f"        AEONFALLRegionalEscalation.ReconcileRegion({q(region_id)})",
        "",
    ])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"generated {OUTPUT.relative_to(ROOT)} with {len(doc.get('invasions', []))} invasions")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
