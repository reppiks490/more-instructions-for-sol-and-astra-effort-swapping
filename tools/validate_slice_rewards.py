#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "content" / "vertical_slice" / "slice_001_rewards.json"
SLICE = ROOT / "content" / "vertical_slice" / "slice_001_ossuary_march.json"
CATALOG = ROOT / "content" / "catalog"
MATERIALS = ROOT / "content" / "crafting" / "material_registry.json"

def load_catalog() -> dict[str, dict]:
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
    doc = json.loads(DATA.read_text(encoding="utf-8"))
    slice_doc = json.loads(SLICE.read_text(encoding="utf-8"))
    catalog = load_catalog()
    material_ids = {
        item["id"]
        for item in json.loads(MATERIALS.read_text(encoding="utf-8")).get("materials", [])
    }

    expected = set(slice_doc["minibosses"]) | {slice_doc["major_boss"], slice_doc["world_event"]}
    seen = set()

    for reward in doc.get("rewards", []):
        encounter_id = reward.get("encounter_id")
        if encounter_id in seen:
            errors.append(f"duplicate reward definition {encounter_id}")
        seen.add(encounter_id)

        if encounter_id not in expected:
            errors.append(f"reward encounter not in Slice 001: {encounter_id}")

        kind = reward.get("kind")
        expected_family = "boss" if kind == "boss" else "event" if kind == "world_event" else None
        if expected_family is None:
            errors.append(f"{encounter_id}: invalid kind {kind}")
        elif catalog.get(encounter_id, {}).get("family") != expected_family:
            errors.append(f"{encounter_id}: catalog family mismatch")

        if not isinstance(reward.get("xp"), int) or reward["xp"] <= 0:
            errors.append(f"{encounter_id}: xp must be positive integer")
        if not isinstance(reward.get("mastery_points"), int) or reward["mastery_points"] < 0:
            errors.append(f"{encounter_id}: invalid mastery_points")
        if reward.get("first_clear_only") is not True:
            errors.append(f"{encounter_id}: durable Slice 001 reward must be first_clear_only")

        for unlock_id in reward.get("unlock_entity_ids", []):
            if unlock_id not in catalog:
                errors.append(f"{encounter_id}: missing unlock {unlock_id}")

        for material in reward.get("material_rewards", []):
            mid = material.get("material_id")
            amount = material.get("amount")
            if mid not in material_ids:
                errors.append(f"{encounter_id}: unknown material {mid}")
            if not isinstance(amount, int) or amount <= 0:
                errors.append(f"{encounter_id}: invalid material amount for {mid}")

    if seen != expected:
        errors.append(f"reward coverage mismatch; missing={sorted(expected-seen)} extra={sorted(seen-expected)}")

    if errors:
        print("AEONFALL Slice 001 reward validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AEONFALL Slice 001 reward validation PASSED")
    print(f"- reward definitions: {len(seen)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
