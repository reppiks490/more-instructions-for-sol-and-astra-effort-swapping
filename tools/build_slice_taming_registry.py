#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"content"/"vertical_slice"/"slice_001_taming.json"
OUT=ROOT/"verse"/"generated"/"slice_001_taming_bootstrap.verse"

def q(value:str)->str:
    return '"' + value.replace("\\","\\\\").replace('"','\\"') + '"'

def flt(value)->str:
    value=float(value)
    text=f"{value:.6f}".rstrip("0").rstrip(".")
    return text if "." in text else text+".0"

def steps(values:list[str])->str:
    return "array{" + ", ".join(f"aeonfall_taming_step_kind.{v}" for v in values) + "}"

def main()->int:
    doc=json.loads(DATA.read_text(encoding="utf-8"))
    lines=[
        "using { /Fortnite.com/Devices }",
        "using { /Verse.org/Simulation }",
        "",
        "# GENERATED FILE — do not hand edit.",
        "# Source: content/vertical_slice/slice_001_taming.json",
        "",
        "Slice001TamingDefinitions:[]aeonfall_taming_definition = array{"
    ]
    for item in doc["species"]:
        lines.extend([
            "    aeonfall_taming_definition{",
            f"        SpeciesId := {q(item['species_id'])},",
            f"        DisplayName := {q(item['name'])},",
            f"        RequiredClassId := {q(doc['required_class_id'])},",
            f"        AbilityId := {q(doc['ability_id'])},",
            f"        Steps := {steps(item['steps'])},",
            f"        MaxChallengeSeconds := {flt(item['max_challenge_seconds'])},",
            f"        FailureEventId := {q(item['failure_event_id'])},",
            f"        SuccessEventId := {q(item['success_event_id'])}",
            "    },"
        ])
    lines.extend([
        "}",
        "",
        "aeonfall_slice_001_taming_bootstrap_device := class(creative_device):",
        "",
        "    OnBegin<override>()<suspends>:void=",
        "        for (Definition : Slice001TamingDefinitions):",
        "            Registered := GetAEONFALLTamingRegistry().Register(Definition)",
        "            if (not Registered?):",
        "                AEONFALLRuntimeBus.Emit(",
        "                    aeonfall_runtime_event{",
        '                        EventType := "bootstrap.taming_registration_failed",',
        "                        SourceId := Definition.SpeciesId",
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
