#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOP = ROOT / "content" / "vertical_slice" / "slice_001_shop.json"
RECIPES = ROOT / "content" / "vertical_slice" / "slice_001_recipes.json"
COVERAGE = ROOT / "content" / "vertical_slice" / "slice_001_delivery_coverage.json"

ALLOWED = {
    "item_granter": "aeonfall_unlock_item_granter_adapter_device",
    "trigger_device_graph": "aeonfall_unlock_delivery_adapter_device",
}

def main() -> int:
    errors: list[str] = []
    shop = json.loads(SHOP.read_text(encoding="utf-8"))
    recipes = json.loads(RECIPES.read_text(encoding="utf-8"))
    coverage = json.loads(COVERAGE.read_text(encoding="utf-8"))

    required = {
        offer["output_entity_id"]
        for offer in shop.get("offers", [])
    } | {
        recipe["output_entity_id"]
        for recipe in recipes.get("recipes", [])
    }

    rows = coverage.get("delivery_bindings", [])
    ids = [row.get("entity_id") for row in rows]

    if len(ids) != len(set(ids)):
        errors.append("duplicate delivery coverage entities")

    actual = set(ids)
    if actual != required:
        errors.append(
            "delivery coverage mismatch: "
            f"missing={sorted(required - actual)}, "
            f"extra={sorted(actual - required)}"
        )

    binding_ids: set[str] = set()
    for row in rows:
        entity_id = row.get("entity_id")
        strategy = row.get("strategy")
        runtime_device = row.get("runtime_device")
        binding_id = str(row.get("binding_id", "")).strip()

        if strategy not in ALLOWED:
            errors.append(f"{entity_id}: unsupported strategy {strategy}")
        elif runtime_device != ALLOWED[strategy]:
            errors.append(
                f"{entity_id}: {strategy} requires {ALLOWED[strategy]}, "
                f"found {runtime_device}"
            )

        if not binding_id:
            errors.append(f"{entity_id}: binding_id is empty")
        elif binding_id in binding_ids:
            errors.append(f"{entity_id}: duplicate binding_id {binding_id}")
        binding_ids.add(binding_id)

        if str(entity_id).startswith("WPN-") and strategy != "item_granter":
            errors.append(f"{entity_id}: first-slice weapon unlock must use item_granter strategy")

    if errors:
        print("AEONFALL delivery coverage validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AEONFALL delivery coverage validation PASSED")
    print(f"- durable unlock outputs: {len(required)}")
    print(f"- explicit delivery bindings: {len(rows)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
