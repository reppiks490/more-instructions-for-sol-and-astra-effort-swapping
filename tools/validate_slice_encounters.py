#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "content" / "catalog"
DATA = ROOT / "content" / "vertical_slice" / "slice_001_encounters.json"
SLICE = ROOT / "content" / "vertical_slice" / "slice_001_ossuary_march.json"
MATERIALS = ROOT / "content" / "crafting" / "material_registry.json"

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
    doc = json.loads(DATA.read_text(encoding="utf-8"))
    slice_doc = json.loads(SLICE.read_text(encoding="utf-8"))
    material_ids = {m["id"] for m in json.loads(MATERIALS.read_text(encoding="utf-8")).get("materials", [])}

    expected_bosses = set(slice_doc["minibosses"]) | {slice_doc["major_boss"]}
    actual_bosses = {b.get("boss_id") for b in doc.get("boss_encounters", [])}
    if actual_bosses != expected_bosses:
        errors.append(f"boss encounter set mismatch: expected={sorted(expected_bosses)} actual={sorted(actual_bosses)}")

    global_ids = set()
    for boss in doc.get("boss_encounters", []):
        bid = boss.get("boss_id")
        if catalog.get(bid, {}).get("family") != "boss":
            errors.append(f"{bid}: missing or not a boss")
        phases = boss.get("phases", [])
        if len(phases) < 3:
            errors.append(f"{bid}: requires at least three authored phases")
        if not any(p.get("allows_direct_boss_damage") for p in phases):
            errors.append(f"{bid}: no direct-damage phase exists")
        for expected_index, phase in enumerate(phases):
            if phase.get("index") != expected_index:
                errors.append(f"{bid}: non-contiguous phase index at {phase.get('id')}")
            pid = phase.get("id")
            if not pid or pid in global_ids:
                errors.append(f"{bid}: duplicate/empty phase id {pid}")
            global_ids.add(pid)
            if not phase.get("transition"):
                errors.append(f"{pid}: transition is empty")
            if not phase.get("cleanup"):
                errors.append(f"{pid}: cleanup rules are empty")
        for reward in boss.get("rewards", {}).get("unlock_ids", []):
            if reward not in catalog:
                errors.append(f"{bid}: missing reward unlock {reward}")
        for reward in boss.get("rewards", {}).get("material_rewards", []):
            if reward.get("id") not in material_ids:
                errors.append(f"{bid}: missing reward material {reward.get('id')}")

    event = doc.get("world_event", {})
    eid = event.get("event_id")
    if eid != slice_doc["world_event"]:
        errors.append(f"world event mismatch: {eid} != {slice_doc['world_event']}")
    if catalog.get(eid, {}).get("family") != "event":
        errors.append(f"{eid}: missing or not an event")
    stages = event.get("stages", [])
    if len(stages) < 4:
        errors.append("world event requires at least four stages")
    for expected_index, stage in enumerate(stages):
        if stage.get("index") != expected_index:
            errors.append(f"{eid}: non-contiguous stage index at {stage.get('id')}")
        sid = stage.get("id")
        if not sid or sid in global_ids:
            errors.append(f"{eid}: duplicate/empty stage id {sid}")
        global_ids.add(sid)
        if not stage.get("objectives") or not stage.get("transition"):
            errors.append(f"{sid}: objectives/transition incomplete")
    if not event.get("cleanup"):
        errors.append("world event cleanup rules are empty")

    if errors:
        print("AEONFALL encounter validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AEONFALL encounter validation PASSED")
    print(f"- bosses: {len(actual_bosses)}")
    print(f"- boss phases: {sum(len(b['phases']) for b in doc['boss_encounters'])}")
    print(f"- event stages: {len(stages)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
