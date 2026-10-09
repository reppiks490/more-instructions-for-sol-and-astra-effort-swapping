#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"content"/"vertical_slice"/"slice_001_hireables.json"
OUT=ROOT/"verse"/"generated"/"slice_001_hireable_bootstrap.verse"

def q(value:str)->str:
    return '"' + value.replace("\\","\\\\").replace('"','\\"') + '"'

def arr(values:list[str])->str:
    return "array{" + ", ".join(q(v) for v in values) + "}"

def logic(v:bool)->str:
    return "true" if v else "false"

def main()->int:
    doc=json.loads(DATA.read_text(encoding="utf-8"))
    lines=[
        "using { /Fortnite.com/Devices }",
        "using { /Verse.org/Simulation }",
        "",
        "# GENERATED FILE — do not hand edit.",
        "# Source: content/vertical_slice/slice_001_hireables.json",
        "",
        "Slice001HireableDefinitions:[]aeonfall_companion_contract = array{"
    ]

    for item in doc["hireables"]:
        lines.extend([
            "    aeonfall_companion_contract{",
            f"        EntityId := {q(item['npc_id'])},",
            f"        FactionId := {q(item['faction_id'])},",
            "        Kind := aeonfall_companion_kind.Hireable,",
            f"        RequiredReputation := {item['required_reputation']},",
            f"        RequiredUnlockIds := {arr(item['required_unlock_ids'])},",
            f"        RequiredBossIds := {arr(item['required_boss_ids'])},",
            f"        RequiredWorldEventIds := {arr(item['required_world_event_ids'])},",
            "        AbilityIds := array{},",
            f"        AllowedOrderIds := {arr(item['allowed_orders'])},",
            f"        MaxSimultaneousPerPlayer := {item['max_simultaneous_per_player']},",
            f"        CanEnterBossArenas := {logic(item['can_enter_boss_arenas'])},",
            f"        CanBeRevived := {logic(item['can_be_revived'])}",
            "    },"
        ])

    lines.extend([
        "}",
        "",
        "aeonfall_slice_001_hireable_bootstrap_device := class(creative_device):",
        "",
        "    OnBegin<override>()<suspends>:void=",
        "        for (Definition : Slice001HireableDefinitions):",
        "            Registered := GetAEONFALLHireableRegistry().Register(Definition)",
        "            if (not Registered?):",
        "                AEONFALLRuntimeBus.Emit(",
        "                    aeonfall_runtime_event{",
        '                        EventType := "bootstrap.hireable_registration_failed",',
        "                        SourceId := Definition.EntityId",
        "                    }",
        "                )",
        ""
    ])

    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text("\n".join(lines),encoding="utf-8")
    print(f"generated {OUT.relative_to(ROOT)}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
