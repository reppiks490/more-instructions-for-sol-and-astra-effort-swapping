#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "content" / "transcendent" / "authorities.json"
OUTPUT = ROOT / "verse" / "generated" / "transcendent_authority_bootstrap.verse"

def q(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

def arr(values: list[str]) -> str:
    if not values:
        return "array{}"
    return "array{" + ", ".join(q(v) for v in values) + "}"

def main() -> int:
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    authorities = doc["authorities"]

    lines = [
        "using { /Fortnite.com/Devices }",
        "using { /Verse.org/Simulation }",
        "",
        "# GENERATED FILE — do not hand edit.",
        "# Source: content/transcendent/authorities.json",
        "",
        "AEONFALLTranscendentAuthorityDefinitions:[]aeonfall_transcendent_authority_definition = array{",
    ]

    for authority in authorities:
        ability_ids = [a["id"] for a in authority["abilities"]]
        lines.extend([
            "    aeonfall_transcendent_authority_definition{",
            f"        AuthorityId := {q(authority['id'])},",
            f"        DisplayName := {q(authority['name'])},",
            f"        Fantasy := {q(authority['fantasy'])},",
            f"        ActiveSeconds := {float(authority['active_seconds']):.1f},",
            f"        ExhaustionSeconds := {float(authority['cooldown_seconds']):.1f},",
            f"        MinHistoryActivations := {authority['min_history_activations']},",
            f"        AbilityIds := {arr(ability_ids)},",
            f"        PresentationId := {q(authority['presentation_id'])},",
            f"        AudioId := {q(authority['audio_id'])}",
            "    },",
        ])

    lines.extend([
        "}",
        "",
        "AEONFALLTranscendentAbilityDefinitions:[]aeonfall_ability_definition = array{",
    ])

    for authority in authorities:
        for ability in authority["abilities"]:
            lines.extend([
                "    aeonfall_ability_definition{",
                f"        AbilityId := {q(ability['id'])},",
                f"        DisplayName := {q(ability['name'])},",
                f"        OwnerEntityId := {q(authority['id'])},",
                "        ResourcePolicy := aeonfall_resource_policy.TransformationOnly,",
                f"        TargetPolicy := aeonfall_target_policy.{ability['target']},",
                "        CooldownSeconds := 0.0,",
                "        MaxCharges := 0,",
                "        RechargeSeconds := 0.0,",
                "        MaxMeter := 0,",
                "        ActivationCost := 0,",
                "        RequiresEncounterContext := false,",
                "        RequiresTransformationContext := true,",
                "        ActivationLifetime := aeonfall_activation_lifetime.Managed,",
                f"        RequiredTransformationId := {q('TRANSCENDENT_ZERO::' + authority['id'])},",
                "        AllowWhileActive := false,",
                '        RequiredClassId := "",',
                "        ClassResourceCost := 0,",
                "        ClassResourceMode := aeonfall_class_resource_mode.None,",
                "        StatusIds := array{},",
                "        SpawnIds := array{},",
                f"        EventIds := array{{{q(ability['event'])}}},",
                f"        PresentationId := {q(authority['presentation_id'])},",
                f"        AudioId := {q(authority['audio_id'])},",
                f"        AdapterId := {q(ability['adapter'])},",
                f"        BossSafe := {'true' if ability['boss_safe'] else 'false'}",
                "    },",
            ])

    lines.extend([
        "}",
        "",
        "aeonfall_transcendent_authority_bootstrap_device := class(creative_device):",
        "",
        "    OnBegin<override>()<suspends>:void=",
        "        for (Definition : AEONFALLTranscendentAuthorityDefinitions):",
        "            Registered := AEONFALLTranscendentAuthorityRegistry.Register(Definition)",
        "            if (not Registered?):",
        "                AEONFALLRuntimeBus.Emit(",
        "                    aeonfall_runtime_event{",
        '                        EventType := "bootstrap.transcendent_authority_registration_failed",',
        "                        SourceId := Definition.AuthorityId",
        "                    }",
        "                )",
        "",
        "        for (Definition : AEONFALLTranscendentAbilityDefinitions):",
        "            Registered := AEONFALLAbilityRegistry.Register(Definition)",
        "            if (not Registered?):",
        "                AEONFALLRuntimeBus.Emit(",
        "                    aeonfall_runtime_event{",
        '                        EventType := "bootstrap.transcendent_ability_registration_failed",',
        "                        SourceId := Definition.AbilityId",
        "                    }",
        "                )",
        "",
    ])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"generated {OUTPUT.relative_to(ROOT)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
