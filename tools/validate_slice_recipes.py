#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "content" / "catalog"
MATERIALS = ROOT / "content" / "crafting" / "material_registry.json"
SLICE = ROOT / "content" / "vertical_slice" / "slice_001_ossuary_march.json"
RECIPES = ROOT / "content" / "vertical_slice" / "slice_001_recipes.json"

def catalog_ids():
    result = {}
    for path in sorted(CATALOG.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        values = payload.get("entities", []) if isinstance(payload, dict) else payload
        for entity in values:
            if isinstance(entity, dict) and entity.get("id"):
                result[entity["id"]] = entity
    return result

def main() -> int:
    errors = []
    catalog = catalog_ids()
    material_ids = {
        item["id"]
        for item in json.loads(MATERIALS.read_text(encoding="utf-8")).get("materials", [])
    }
    slice_doc = json.loads(SLICE.read_text(encoding="utf-8"))
    doc = json.loads(RECIPES.read_text(encoding="utf-8"))

    recipe_ids = set()
    outputs = set()
    allowed_outputs = (
        set(slice_doc["weapons"])
        | set(slice_doc["armor_sets"])
        | set(slice_doc["vehicles"])
    )

    for recipe in doc.get("recipes", []):
        rid = recipe.get("id")
        output = recipe.get("output_entity_id")

        if not rid or rid in recipe_ids:
            errors.append(f"duplicate or empty recipe id: {rid}")
        recipe_ids.add(rid)

        if output not in catalog:
            errors.append(f"{rid}: missing output entity {output}")
        if output not in allowed_outputs:
            errors.append(f"{rid}: output {output} is not part of slice equipment/vehicle scope")
        if output in outputs:
            errors.append(f"{rid}: duplicate output recipe for {output}")
        outputs.add(output)

        costs = recipe.get("costs", [])
        if not costs:
            errors.append(f"{rid}: recipe has no costs")
        for cost in costs:
            mid = cost.get("material_id")
            amount = cost.get("amount")
            if mid not in material_ids:
                errors.append(f"{rid}: unknown material {mid}")
            if mid not in set(slice_doc["crafting_materials"]):
                errors.append(f"{rid}: material {mid} not declared in vertical slice")
            if not isinstance(amount, int) or amount <= 0:
                errors.append(f"{rid}: invalid amount for {mid}: {amount}")

        for dependency in recipe.get("required_unlock_ids", []):
            if dependency not in catalog:
                errors.append(f"{rid}: missing unlock prerequisite {dependency}")
            if dependency == output:
                errors.append(f"{rid}: output cannot require itself")

        if not str(recipe.get("station", "")).strip():
            errors.append(f"{rid}: station is empty")

    if len(doc.get("recipes", [])) < 6:
        errors.append("first slice must define at least six test recipes")

    if errors:
        print("AEONFALL slice recipe validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AEONFALL slice recipe validation PASSED")
    print(f"- recipes: {len(doc['recipes'])}")
    print(f"- unique outputs: {len(outputs)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
