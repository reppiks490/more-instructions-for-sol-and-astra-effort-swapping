#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLICE_PATH = ROOT / "content" / "vertical_slice" / "slice_001_ossuary_march.json"
BINDINGS_PATH = ROOT / "content" / "vertical_slice" / "slice_001_uefn_bindings.json"

ALLOWED_WEAPON_TEMPLATES = {
    "assault_rifle_template",
    "sub_machine_gun_template",
    "pistol_template",
    "shotgun_template",
    "held_item_template",
}

def ids(records):
    return [record.get("id") for record in records]

def unique_nonempty(values, label, errors):
    seen = set()
    for value in values:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{label}: empty or invalid binding name")
            continue
        if value in seen:
            errors.append(f"{label}: duplicate binding name {value}")
        seen.add(value)

def main() -> int:
    errors = []
    slice_doc = json.loads(SLICE_PATH.read_text(encoding="utf-8"))
    bind = json.loads(BINDINGS_PATH.read_text(encoding="utf-8"))

    expected = {
        "weapons": set(slice_doc["weapons"]),
        "hireables": set(slice_doc["hireables"]),
        "tameables": set(slice_doc["tameable_wildlife"]),
        "monsters": set(slice_doc["monsters"]),
        "armor": set(slice_doc["armor_sets"]),
        "vehicles": set(slice_doc["vehicles"]),
    }

    actual = {
        "weapons": set(ids(bind.get("weapons", []))),
        "hireables": set(ids(bind.get("hireables", []))),
        "tameables": set(ids(bind.get("tameables", []))),
        "monsters": set(ids(bind.get("monsters", []))),
        "armor": set(ids(bind.get("armor", []))),
        "vehicles": set(ids(bind.get("vehicles", []))),
    }

    for key in expected:
        if actual[key] != expected[key]:
            missing = sorted(expected[key] - actual[key])
            extra = sorted(actual[key] - expected[key])
            errors.append(f"{key}: binding mismatch; missing={missing}, extra={extra}")

    encounter_ids = set(ids(bind.get("encounters", [])))
    expected_encounters = set(slice_doc["minibosses"]) | {slice_doc["major_boss"]}
    if encounter_ids != expected_encounters:
        errors.append(
            f"encounters: binding mismatch; missing={sorted(expected_encounters - encounter_ids)}, "
            f"extra={sorted(encounter_ids - expected_encounters)}"
        )

    event_id = bind.get("world_event", {}).get("id")
    if event_id != slice_doc["world_event"]:
        errors.append(f"world_event: binding {event_id} != slice {slice_doc['world_event']}")

    for weapon in bind.get("weapons", []):
        template = weapon.get("template")
        if template not in ALLOWED_WEAPON_TEMPLATES:
            errors.append(f"{weapon.get('id')}: unsupported template {template}")
        if not weapon.get("prefab"):
            errors.append(f"{weapon.get('id')}: missing prefab")
        if not weapon.get("adapter"):
            errors.append(f"{weapon.get('id')}: missing mechanic adapter")

    for npc in bind.get("hireables", []):
        if npc.get("character_type") != "Guard":
            errors.append(f"{npc.get('id')}: first-slice hireable must preserve Guard base behavior")
        if not npc.get("definition") or not npc.get("behavior"):
            errors.append(f"{npc.get('id')}: missing Character Definition or behavior binding")

    for creature in bind.get("tameables", []) + bind.get("monsters", []):
        if not creature.get("definition") or not creature.get("behavior"):
            errors.append(f"{creature.get('id')}: missing Character Definition or behavior binding")

    for boss in bind.get("encounters", []):
        if not boss.get("definition") or not boss.get("behavior") or not boss.get("controller"):
            errors.append(f"{boss.get('id')}: missing definition, behavior, or encounter controller")

    unique_nonempty([w.get("prefab") for w in bind.get("weapons", [])], "weapon prefabs", errors)
    unique_nonempty([n.get("definition") for n in bind.get("hireables", [])], "hireable definitions", errors)
    unique_nonempty([n.get("definition") for n in bind.get("tameables", [])], "tameable definitions", errors)
    unique_nonempty([n.get("definition") for n in bind.get("monsters", [])], "monster definitions", errors)
    unique_nonempty([b.get("controller") for b in bind.get("encounters", [])], "boss controllers", errors)

    if errors:
        print("AEONFALL UEFN binding validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AEONFALL UEFN binding validation PASSED")
    print(f"- weapons bound: {len(bind['weapons'])}")
    print(f"- hireables bound: {len(bind['hireables'])}")
    print(f"- tameables bound: {len(bind['tameables'])}")
    print(f"- monsters bound: {len(bind['monsters'])}")
    print(f"- encounters bound: {len(bind['encounters'])}")
    print(f"- armor families bound: {len(bind['armor'])}")
    print(f"- vehicles bound: {len(bind['vehicles'])}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
