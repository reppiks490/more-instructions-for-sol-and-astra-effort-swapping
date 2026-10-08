#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"content"/"vertical_slice"/"slice_001_combat_runtime.json"
OUT=ROOT/"verse"/"generated"/"slice_001_combat_bootstrap.verse"

def q(value:str)->str:
    return '"' + value.replace("\\","\\\\").replace('"','\\"') + '"'

def logic(value:bool)->str:
    return "true" if value else "false"

def flt(value)->str:
    value=float(value)
    text=f"{value:.6f}".rstrip("0").rstrip(".")
    if "." not in text:
        text += ".0"
    return text

def arr(values:list[str])->str:
    return "array{" + ", ".join(q(v) for v in values) + "}"

def main()->int:
    doc=json.loads(DATA.read_text(encoding="utf-8"))
    lines=[
        "using { /Fortnite.com/Devices }",
        "using { /Verse.org/Simulation }",
        "",
        "# GENERATED FILE — do not hand edit.",
        "# Source: content/vertical_slice/slice_001_combat_runtime.json",
        "",
        "Slice001StatusDefinitions:[]aeonfall_status_definition = array{"
    ]

    for s in doc["statuses"]:
        lines.extend([
            "    aeonfall_status_definition{",
            f"        StatusId := {q(s['id'])},",
            f"        DisplayName := {q(s['name'])},",
            f"        Category := aeonfall_status_category.{s['category']},",
            f"        StackRule := aeonfall_status_stack_rule.{s['stack_rule']},",
            f"        MaxStacks := {s['max_stacks']},",
            f"        BaseDurationSeconds := {flt(s['duration_seconds'])},",
            f"        Dispellable := {logic(s['dispellable'])},",
            f"        BossEligible := {logic(s['boss_eligible'])},",
            f"        PresentationId := {q(s['presentation_id'])},",
            f"        AudioId := {q(s['audio_id'])}",
            "    },"
        ])
    lines.extend(["}", "", "Slice001AbilityDefinitions:[]aeonfall_ability_definition = array{"])

    for a in doc["abilities"]:
        lines.extend([
            "    aeonfall_ability_definition{",
            f"        AbilityId := {q(a['id'])},",
            f"        DisplayName := {q(a['name'])},",
            f"        OwnerEntityId := {q(a['owner_entity_id'])},",
            f"        ResourcePolicy := aeonfall_resource_policy.{a['resource_policy']},",
            f"        TargetPolicy := aeonfall_target_policy.{a['target_policy']},",
            f"        CooldownSeconds := {flt(a['cooldown_seconds'])},",
            f"        MaxCharges := {a['max_charges']},",
            f"        RechargeSeconds := {flt(a['recharge_seconds'])},",
            f"        MaxMeter := {a['max_meter']},",
            f"        ActivationCost := {a['activation_cost']},",
            f"        RequiresEncounterContext := {logic(a['requires_encounter_context'])},",
            f"        RequiresTransformationContext := {logic(a['requires_transformation_context'])},",
            f"        AllowWhileActive := {logic(a['allow_while_active'])},",
            f"        RequiredClassId := {q(a.get('required_class_id', ''))},",
            f"        ClassResourceCost := {a.get('class_resource_cost', 0)},",
            f"        ClassResourceMode := aeonfall_class_resource_mode.{a.get('class_resource_mode', 'None')},",
            f"        StatusIds := {arr(a['status_ids'])},",
            f"        SpawnIds := {arr(a['spawn_ids'])},",
            f"        EventIds := {arr(a['event_ids'])},",
            '        PresentationId := "",',
            '        AudioId := "",',
            f"        AdapterId := {q(a['adapter_id'])},",
            f"        ActivationLifetime := aeonfall_activation_lifetime.{a.get('activation_lifetime', 'Managed' if a.get('class_resource_mode') == 'ReserveWhileActive' else 'Instant')},",
            f"        BossSafe := {logic(a['boss_safe'])}",
            "    },"
        ])

    lines.extend([
        "}",
        "",
        "aeonfall_slice_001_combat_bootstrap_device := class(creative_device):",
        "",
        "    OnBegin<override>()<suspends>:void=",
        "        for (Definition : Slice001StatusDefinitions):",
        "            Registered := AEONFALLStatusRegistry.Register(Definition)",
        "            if (not Registered?):",
        "                AEONFALLRuntimeBus.Emit(",
        "                    aeonfall_runtime_event{",
        '                        EventType := "bootstrap.status_registration_failed",',
        "                        SourceId := Definition.StatusId",
        "                    }",
        "                )",
        "",
        "        for (Definition : Slice001AbilityDefinitions):",
        "            Registered := AEONFALLAbilityRegistry.Register(Definition)",
        "            if (not Registered?):",
        "                AEONFALLRuntimeBus.Emit(",
        "                    aeonfall_runtime_event{",
        '                        EventType := "bootstrap.ability_registration_failed",',
        "                        SourceId := Definition.AbilityId",
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
