#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"content"/"vertical_slice"/"slice_001_classes.json"
OUT=ROOT/"verse"/"generated"/"slice_001_class_bootstrap.verse"

def q(value:str)->str:
    return '"' + value.replace("\\","\\\\").replace('"','\\"') + '"'

def arr(values:list[str])->str:
    return "array{" + ", ".join(q(v) for v in values) + "}"

def main()->int:
    doc=json.loads(DATA.read_text(encoding="utf-8"))
    lines=[
        "using { /Fortnite.com/Devices }",
        "using { /Verse.org/Simulation }",
        "",
        "# GENERATED FILE — do not hand edit.",
        "# Source: content/vertical_slice/slice_001_classes.json",
        "",
        "Slice001ClassDefinitions:[]aeonfall_class_definition = array{"
    ]

    for item in doc["classes"]:
        lines.extend([
            "    aeonfall_class_definition{",
            f"        ClassId := {q(item['class_id'])},",
            f"        DisplayName := {q(item['name'])},",
            f"        AbilityIds := {arr(item['ability_ids'])},",
            f"        PassiveStatusIds := {arr(item['passive_status_ids'])},",
            f"        ResourceId := {q(item['resource_id'])},",
            f"        MaxResource := {item['max_resource']},",
            f"        BaseMaxCompanions := {item['base_max_companions']},",
            f"        RequiredUnlockIds := {arr(item['required_unlock_ids'])}",
            "    },"
        ])

    lines.extend([
        "}",
        "",
        "aeonfall_slice_001_class_bootstrap_device := class(creative_device):",
        "",
        "    OnBegin<override>()<suspends>:void=",
        "        for (Definition : Slice001ClassDefinitions):",
        "            Registered := GetAEONFALLClassRegistry().Register(Definition)",
        "            if (not Registered?):",
        "                AEONFALLRuntimeBus.Emit(",
        "                    aeonfall_runtime_event{",
        '                        EventType := "bootstrap.class_registration_failed",',
        "                        SourceId := Definition.ClassId",
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
