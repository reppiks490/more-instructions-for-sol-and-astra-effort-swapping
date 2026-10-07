#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "content" / "crafting" / "material_registry.json"
GRAPH_PATH = ROOT / "content" / "crafting" / "axiom_heart_recipe.json"

MAT_RE = re.compile(r"^MAT-\d{3}$")
RCP_RE = re.compile(r"^RCP-\d{3}$")

def die(errors: list[str], message: str) -> None:
    errors.append(message)

def main() -> int:
    errors: list[str] = []

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))

    materials = registry.get("materials", [])
    recipes = graph.get("recipes", [])

    material_by_id: dict[str, dict] = {}
    for material in materials:
        material_id = material.get("id")
        if not isinstance(material_id, str) or not MAT_RE.match(material_id):
            die(errors, f"invalid material id: {material_id!r}")
            continue
        if material_id in material_by_id:
            die(errors, f"duplicate material id: {material_id}")
        material_by_id[material_id] = material
        if not str(material.get("name", "")).strip():
            die(errors, f"{material_id} has empty name")
        if material.get("kind") not in {"raw", "refined", "apex"}:
            die(errors, f"{material_id} has invalid kind {material.get('kind')!r}")
        if not str(material.get("source", "")).strip():
            die(errors, f"{material_id} has no acquisition/source description")

    recipe_ids: set[str] = set()
    output_to_recipe: dict[str, dict] = {}

    for recipe in recipes:
        recipe_id = recipe.get("id")
        if not isinstance(recipe_id, str) or not RCP_RE.match(recipe_id):
            die(errors, f"invalid recipe id: {recipe_id!r}")
            continue
        if recipe_id in recipe_ids:
            die(errors, f"duplicate recipe id: {recipe_id}")
        recipe_ids.add(recipe_id)

        output = recipe.get("output", {})
        output_id = output.get("material_id")
        output_qty = output.get("quantity")
        if output_id not in material_by_id:
            die(errors, f"{recipe_id} outputs missing material {output_id}")
        if not isinstance(output_qty, int) or output_qty <= 0:
            die(errors, f"{recipe_id} has invalid output quantity {output_qty!r}")
        if output_id in output_to_recipe:
            die(errors, f"multiple recipes produce {output_id}")
        output_to_recipe[output_id] = recipe

        inputs = recipe.get("inputs", [])
        if not inputs:
            die(errors, f"{recipe_id} has no inputs")
        for item in inputs:
            input_id = item.get("material_id")
            qty = item.get("quantity")
            if input_id not in material_by_id:
                die(errors, f"{recipe_id} references missing material {input_id}")
            if not isinstance(qty, int) or qty <= 0:
                die(errors, f"{recipe_id} input {input_id} has invalid quantity {qty!r}")

        if not str(recipe.get("station", "")).strip():
            die(errors, f"{recipe_id} has no crafting station")

    for material_id, material in material_by_id.items():
        if material.get("kind") in {"refined", "apex"} and material_id not in output_to_recipe:
            die(errors, f"{material_id} is {material.get('kind')} but has no recipe")

    visiting: set[str] = set()
    memo: dict[str, Counter[str]] = {}

    def expand(material_id: str, quantity: int = 1) -> Counter[str]:
        if material_id in visiting:
            raise ValueError(f"recipe cycle detected at {material_id}")

        material = material_by_id[material_id]
        if material.get("kind") == "raw":
            return Counter({material_id: quantity})

        recipe = output_to_recipe.get(material_id)
        if recipe is None:
            raise ValueError(f"no recipe for non-raw material {material_id}")

        output_qty = recipe["output"]["quantity"]
        if quantity % output_qty != 0:
            raise ValueError(
                f"{material_id} requested quantity {quantity} is not divisible by recipe output {output_qty}"
            )
        crafts = quantity // output_qty

        if material_id in memo:
            return Counter({k: v * crafts for k, v in memo[material_id].items()})

        visiting.add(material_id)
        one_craft = Counter()
        for item in recipe["inputs"]:
            one_craft.update(expand(item["material_id"], item["quantity"]))
        visiting.remove(material_id)
        memo[material_id] = one_craft

        return Counter({k: v * crafts for k, v in one_craft.items()})

    root_id = graph.get("root_material_id")
    if root_id not in material_by_id:
        die(errors, f"root material does not exist: {root_id}")
        raw = Counter()
    else:
        try:
            raw = expand(root_id, 1)
        except Exception as exc:
            die(errors, str(exc))
            raw = Counter()

    raw_total = sum(raw.values())
    declared_total = graph.get("declared_raw_acquisition_total")
    minimum_total = graph.get("minimum_raw_acquisitions", 0)

    if raw_total != declared_total:
        die(errors, f"raw acquisition total mismatch: computed {raw_total}, declared {declared_total}")
    if raw_total < minimum_total:
        die(errors, f"Axiom Heart grind weakened below minimum: {raw_total} < {minimum_total}")

    if errors:
        print("AEONFALL crafting validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AEONFALL crafting validation PASSED")
    print(f"Axiom Heart raw acquisitions: {raw_total}")
    for material_id, qty in sorted(raw.items()):
        name = material_by_id[material_id]["name"]
        print(f"- {material_id} {name}: {qty}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
