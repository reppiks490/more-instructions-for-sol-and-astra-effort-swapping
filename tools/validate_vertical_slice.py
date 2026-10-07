#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "content" / "catalog"
MATERIALS = ROOT / "content" / "crafting" / "material_registry.json"
SLICE = ROOT / "content" / "vertical_slice" / "slice_001_ossuary_march.json"

MINIMUMS = {
    "monsters": 12,
    "tameable_wildlife": 6,
    "hireables": 8,
    "weapons": 12,
    "armor_sets": 2,
    "minibosses": 2,
    "vehicles": 1,
    "classes": 1,
    "skills": 1,
}

EXPECTED_FAMILY = {
    "monsters": "monster",
    "tameable_wildlife": "wildlife",
    "hireables": "npc",
    "weapons": "weapon",
    "armor_sets": "armor",
    "vehicles": "vehicle",
    "classes": "class",
    "skills": "skill",
    "minibosses": "boss",
}

def load_catalog() -> dict[str, dict]:
    result = {}
    for path in sorted(CATALOG.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and "entities" in payload:
            entities = payload["entities"]
        elif isinstance(payload, list):
            entities = payload
        elif isinstance(payload, dict):
            entities = [payload]
        else:
            raise ValueError(f"unsupported catalog payload: {path}")
        for entity in entities:
            if isinstance(entity, dict) and entity.get("id"):
                result[entity["id"]] = entity
    return result

def main() -> int:
    errors = []
    catalog = load_catalog()
    material_doc = json.loads(MATERIALS.read_text(encoding="utf-8"))
    material_ids = {m["id"] for m in material_doc.get("materials", [])}
    doc = json.loads(SLICE.read_text(encoding="utf-8"))

    for key, minimum in MINIMUMS.items():
        values = doc.get(key, [])
        if not isinstance(values, list) or len(values) < minimum:
            errors.append(f"{key}: requires at least {minimum}, found {len(values) if isinstance(values, list) else 'invalid'}")
            continue
        if len(values) != len(set(values)):
            errors.append(f"{key}: duplicate IDs detected")
        family = EXPECTED_FAMILY[key]
        for entity_id in values:
            entity = catalog.get(entity_id)
            if entity is None:
                errors.append(f"{key}: missing canonical ID {entity_id}")
            elif entity.get("family") != family:
                errors.append(f"{key}: {entity_id} has family {entity.get('family')}, expected {family}")

    for key, family in (("major_boss","boss"),("world_event","event")):
        entity_id = doc.get(key)
        entity = catalog.get(entity_id)
        if entity is None:
            errors.append(f"{key}: missing canonical ID {entity_id}")
        elif entity.get("family") != family:
            errors.append(f"{key}: {entity_id} has family {entity.get('family')}, expected {family}")

    materials = doc.get("crafting_materials", [])
    if not materials:
        errors.append("crafting_materials must not be empty")
    for material_id in materials:
        if material_id not in material_ids:
            errors.append(f"crafting_materials: missing material {material_id}")

    shop = doc.get("shop", {})
    for entity_id in shop.get("stock_ids", []):
        if entity_id not in catalog:
            errors.append(f"shop stock references missing canonical ID {entity_id}")

    dungeon = doc.get("dungeon", {})
    if len(dungeon.get("acts", [])) < 4:
        errors.append("dungeon must define at least four acts")

    if not doc.get("runtime_requirements"):
        errors.append("runtime_requirements must not be empty")
    if not doc.get("acceptance_gates"):
        errors.append("acceptance_gates must not be empty")

    if errors:
        print("AEONFALL vertical slice validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AEONFALL vertical slice validation PASSED")
    print(f"- slice: {doc['slice_id']} {doc['name']}")
    for key in MINIMUMS:
        print(f"- {key}: {len(doc[key])}")
    print(f"- major boss: {doc['major_boss']}")
    print(f"- world event: {doc['world_event']}")
    print(f"- crafting materials: {len(materials)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
