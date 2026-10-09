#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "content" / "vertical_slice" / "slice_001_recipes.json"
OUTPUT = ROOT / "verse" / "generated" / "slice_001_recipe_bootstrap.verse"

def q(value: str) -> str:
    return json.dumps(str(value))

def string_array(values: list[str]) -> str:
    if not values:
        return "array{}"
    return "array{" + ", ".join(q(v) for v in values) + "}"

def cost_array(costs: list[dict]) -> str:
    if not costs:
        return "array{}"
    return "array{" + ", ".join(
        f'aeonfall_material_cost{{MaterialId := {q(c["material_id"])}, Amount := {int(c["amount"])}}}'
        for c in costs
    ) + "}"

def station_id(name: str) -> str:
    return "STATION::" + name.strip().upper().replace(" ", "-")

def main() -> int:
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))

    lines = [
        "using { /Fortnite.com/Devices }",
        "using { /Verse.org/Simulation }",
        "",
        "# GENERATED FILE — do not hand edit.",
        "# Source: content/vertical_slice/slice_001_recipes.json",
        "",
        "Slice001RecipeDefinitions:[]aeonfall_recipe_definition = array{",
    ]

    for recipe in doc["recipes"]:
        lines.extend([
            "    aeonfall_recipe_definition{",
            f"        RecipeId := {q(recipe['id'])},",
            f"        StationId := {q(station_id(recipe['station']))},",
            f"        OutputEntityId := {q(recipe['output_entity_id'])},",
            f"        Costs := {cost_array(recipe['costs'])},",
            f"        RequiredUnlockIds := {string_array(recipe.get('required_unlock_ids', []))}",
            "    },",
        ])

    lines.extend([
        "}",
        "",
        "aeonfall_slice_001_recipe_bootstrap_device := class(creative_device):",
        "",
        "    OnBegin<override>()<suspends>:void=",
        "        for (Recipe : Slice001RecipeDefinitions):",
        "            Registered := GetAEONFALLRecipeRegistry().Register(Recipe)",
        "            if (not Registered?):",
        "                AEONFALLRuntimeBus.Emit(",
        "                    aeonfall_runtime_event{",
        '                        EventType := "bootstrap.recipe_registration_failed",',
        "                        SourceId := Recipe.RecipeId,",
        "                        TargetId := Recipe.OutputEntityId",
        "                    }",
        "                )",
        "",
    ])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"generated {OUTPUT.relative_to(ROOT)} with {len(doc['recipes'])} recipes")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
