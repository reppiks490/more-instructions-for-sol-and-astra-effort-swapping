#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "content" / "world" / "region_001_faction_conflicts.json"
OUTPUT = ROOT / "verse" / "generated" / "region_001_faction_conflict_bootstrap.verse"

def q(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

def arr(values: list[str]) -> str:
    return "array{" + ", ".join(q(v) for v in values) + "}"

def main() -> int:
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    region_id = doc["region_id"]

    lines = [
        "using { /Fortnite.com/Devices }",
        "using { /Verse.org/Simulation }",
        "",
        "# GENERATED FILE — do not hand edit.",
        "# Source: content/world/region_001_faction_conflicts.json",
        "",
        "Region001FactionConflictDefinitions:[]aeonfall_faction_conflict_definition = array{",
    ]

    for conflict in doc.get("conflicts", []):
        lines.extend([
            "    aeonfall_faction_conflict_definition{",
            f"        ConflictId := {q(conflict['id'])},",
            f"        RegionId := {q(region_id)},",
            f"        FactionAId := {q(conflict['faction_a_id'])},",
            f"        FactionBId := {q(conflict['faction_b_id'])},",
            f"        VictoryScore := {conflict['victory_score']},",
            f"        MinHostilityTier := {conflict['min_hostility_tier']},",
            f"        ObjectiveIds := {arr(conflict.get('objective_ids', []))},",
            f"        HazardIds := {arr(conflict.get('hazard_ids', []))}",
            "    },",
        ])

    lines.extend([
        "}",
        "",
        "aeonfall_region_001_faction_conflict_bootstrap_device := class(creative_device):",
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
        '                    EventType := "bootstrap.region_001_conflict_world_not_ready",',
        f"                    SourceId := {q(region_id)}",
        "                }",
        "            )",
        "            return",
        "",
        "        for (Definition : Region001FactionConflictDefinitions):",
        "            Registered := AEONFALLFactionConflictRegistry.Register(Definition)",
        "            if (not Registered?):",
        "                AEONFALLRuntimeBus.Emit(",
        "                    aeonfall_runtime_event{",
        '                        EventType := "bootstrap.faction_conflict_registration_failed",',
        "                        SourceId := Definition.ConflictId,",
        "                        TargetId := Definition.RegionId",
        "                    }",
        "                )",
        "",
    ])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"generated {OUTPUT.relative_to(ROOT)} with {len(doc.get('conflicts', []))} conflicts")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
