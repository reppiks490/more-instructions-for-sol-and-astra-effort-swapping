#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "content" / "vertical_slice" / "slice_001_rewards.json"
OUTPUT = ROOT / "verse" / "generated" / "slice_001_reward_bootstrap.verse"

def q(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

def arr(values: list[str]) -> str:
    return "array{" + ", ".join(q(v) for v in values) + "}"

def main() -> int:
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    lines = [
        "using { /Fortnite.com/Devices }",
        "using { /Verse.org/Simulation }",
        "",
        "# GENERATED FILE — do not hand edit.",
        "# Source: content/vertical_slice/slice_001_rewards.json",
        "",
        "Slice001EncounterRewardDefinitions:[]aeonfall_encounter_reward_definition = array{",
    ]

    for reward in doc.get("rewards", []):
        kind = "Boss" if reward["kind"] == "boss" else "WorldEvent"
        lines.extend([
            "    aeonfall_encounter_reward_definition{",
            f"        EncounterId := {q(reward['encounter_id'])},",
            f"        Kind := aeonfall_encounter_reward_kind.{kind},",
            f"        XP := {reward['xp']},",
            f"        MasteryPoints := {reward['mastery_points']},",
            f"        UnlockEntityIds := {arr(reward.get('unlock_entity_ids', []))},",
            "        MaterialRewards := array{",
        ])
        for material in reward.get("material_rewards", []):
            lines.extend([
                "            aeonfall_material_cost{",
                f"                MaterialId := {q(material['material_id'])},",
                f"                Amount := {material['amount']}",
                "            },",
            ])
        lines.extend([
            "        },",
            f"        FirstClearOnly := {'true' if reward.get('first_clear_only') else 'false'}",
            "    },",
        ])

    lines.extend([
        "}",
        "",
        "aeonfall_slice_001_reward_bootstrap_device := class(creative_device):",
        "",
        "    OnBegin<override>()<suspends>:void=",
        "        for (Definition : Slice001EncounterRewardDefinitions):",
        "            Registered := GetAEONFALLEncounterRewardRegistry().Register(Definition)",
        "            if (not Registered?):",
        "                AEONFALLRuntimeBus.Emit(",
        "                    aeonfall_runtime_event{",
        '                        EventType := "bootstrap.encounter_reward_registration_failed",',
        "                        SourceId := Definition.EncounterId",
        "                    }",
        "                )",
        "",
    ])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"generated {OUTPUT.relative_to(ROOT)} with {len(doc.get('rewards', []))} rewards")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
