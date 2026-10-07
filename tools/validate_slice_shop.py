#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "content" / "catalog"
MATERIALS = ROOT / "content" / "crafting" / "material_registry.json"
SLICE = ROOT / "content" / "vertical_slice" / "slice_001_ossuary_march.json"
SHOP = ROOT / "content" / "vertical_slice" / "slice_001_shop.json"

def load_catalog():
    result = {}
    for path in CATALOG.rglob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        values = payload.get("entities", []) if isinstance(payload, dict) else payload
        for entity in values:
            if isinstance(entity, dict) and entity.get("id"):
                result[entity["id"]] = entity
    return result

def main() -> int:
    errors = []
    catalog = load_catalog()
    materials = {
        item["id"]
        for item in json.loads(MATERIALS.read_text(encoding="utf-8")).get("materials", [])
    }
    slice_doc = json.loads(SLICE.read_text(encoding="utf-8"))
    doc = json.loads(SHOP.read_text(encoding="utf-8"))

    if doc.get("real_money_enabled") is not False:
        errors.append("first-slice shop must keep real_money_enabled=false")

    allowed = set(slice_doc["weapons"]) | set(slice_doc["armor_sets"]) | set(slice_doc["vehicles"])
    seen_offers = set()
    seen_outputs = set()

    offers = doc.get("offers", [])
    if len(offers) < 5:
        errors.append("first-slice shop must define at least five offers")

    previous_rep = -1
    for offer in offers:
        oid = offer.get("id")
        output = offer.get("output_entity_id")
        rep = offer.get("required_reputation")

        if not oid or oid in seen_offers:
            errors.append(f"duplicate/empty offer id: {oid}")
        seen_offers.add(oid)

        if output not in catalog:
            errors.append(f"{oid}: missing output {output}")
        if output not in allowed:
            errors.append(f"{oid}: output {output} is not part of the vertical slice equipment/vehicle scope")
        if output in seen_outputs:
            errors.append(f"{oid}: duplicate output {output}")
        seen_outputs.add(output)

        if not isinstance(rep, int) or rep < 0:
            errors.append(f"{oid}: invalid reputation requirement {rep}")
        elif rep < previous_rep:
            errors.append(f"{oid}: reputation progression is not monotonic")
        else:
            previous_rep = rep

        costs = offer.get("costs", [])
        if not costs:
            errors.append(f"{oid}: offer has no costs")
        for cost in costs:
            mid = cost.get("material_id")
            amount = cost.get("amount")
            if mid not in materials:
                errors.append(f"{oid}: unknown material {mid}")
            if not isinstance(amount, int) or amount <= 0:
                errors.append(f"{oid}: invalid material amount for {mid}: {amount}")

        for unlock in offer.get("required_unlock_ids", []):
            if unlock not in catalog:
                errors.append(f"{oid}: missing unlock prerequisite {unlock}")
            if unlock == output:
                errors.append(f"{oid}: output cannot require itself")

    if errors:
        print("AEONFALL first-slice shop validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AEONFALL first-slice shop validation PASSED")
    print(f"- offers: {len(offers)}")
    print(f"- payment model: {doc['payment_model']}")
    print(f"- real money enabled: {doc['real_money_enabled']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
