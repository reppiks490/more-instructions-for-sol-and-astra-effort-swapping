#!/usr/bin/env python3
"""Generate the authoritative final Axiom Heart cost vector from RCP-013."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "content/crafting/axiom_heart_recipe.json"
OUTPUT = ROOT / "verse/generated/axiom_heart_final_costs.verse"


def render(graph: dict) -> str:
    recipes = [recipe for recipe in graph["recipes"] if recipe["id"] == "RCP-013"]
    if len(recipes) != 1 or graph["root_material_id"] != "MAT-030":
        raise ValueError("canonical RCP-013/MAT-030 root missing or duplicated")
    recipe = recipes[0]
    if (recipe["station"] != "Throne of Zero"
            or recipe["output"] != {"material_id": "MAT-030", "quantity": 1}):
        raise ValueError("canonical final station/output contract changed")
    inputs = recipe["inputs"]
    ids = [cost["material_id"] for cost in inputs]
    if not inputs or len(set(ids)) != len(ids):
        raise ValueError("final forge costs must be nonempty and unique")
    if any(not isinstance(cost["quantity"], int) or isinstance(cost["quantity"], bool)
           or cost["quantity"] <= 0 or cost["material_id"] == "MAT-030"
           for cost in inputs):
        raise ValueError("invalid final forge input")
    lines = [
        "# GENERATED FILE — do not hand edit.",
        "# Source: content/crafting/axiom_heart_recipe.json, RCP-013",
        'AxiomHeartFinalRecipeId:string = "RCP-013"',
        'AxiomHeartFinalOutputMaterialId:string = "MAT-030"',
        'AxiomHeartFinalStationId:string = "Throne of Zero"',
        "AxiomHeartFinalCosts:[]aeonfall_material_cost = array{",
    ]
    for cost in inputs:
        lines.append(
            f'    aeonfall_material_cost{{MaterialId := "{cost["material_id"]}", Amount := {cost["quantity"]}}},'
        )
    lines.extend(["}", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render(json.loads(SOURCE.read_text(encoding="utf-8")))
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != expected:
            raise SystemExit("stale Axiom Heart forge costs; regenerate with this tool")
        print("Axiom Heart RCP-013 generated costs match canonical graph")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(expected, encoding="utf-8")
        print(f"generated {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
