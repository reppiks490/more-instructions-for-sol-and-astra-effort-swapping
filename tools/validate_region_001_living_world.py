#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "content" / "world" / "region_001_living_world.json"
TOPOLOGY = ROOT / "content" / "world" / "world_topology.json"
CATALOG = ROOT / "content" / "catalog"

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
    topology = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    catalog = load_catalog()

    region_ids = {r["id"] for r in topology.get("regions", [])}
    region_id = doc.get("region_id")
    if region_id not in region_ids:
        errors.append(f"unknown region {region_id}")

    influence_total = 0
    seen_factions = set()
    for item in doc.get("initial_faction_influence", []):
        fid = item.get("faction_id")
        value = item.get("influence")
        if catalog.get(fid, {}).get("family") != "faction":
            errors.append(f"unknown/non-faction influence id {fid}")
        if fid in seen_factions:
            errors.append(f"duplicate faction influence {fid}")
        seen_factions.add(fid)
        if not isinstance(value, int) or not 0 <= value <= 100:
            errors.append(f"invalid influence for {fid}: {value}")
        else:
            influence_total += value
    if influence_total > 100:
        errors.append(f"initial influence exceeds 100: {influence_total}")

    thresholds = doc.get("corruption_thresholds", [])
    expected_min = 0
    for row in thresholds:
        lo, hi = row.get("min"), row.get("max")
        if lo != expected_min:
            errors.append(f"corruption threshold gap/overlap at {lo}; expected {expected_min}")
        if not isinstance(hi, int) or hi < lo:
            errors.append(f"invalid corruption range {lo}-{hi}")
            break
        expected_min = hi + 1
    if expected_min != 101:
        errors.append("corruption thresholds must cover 0..100 exactly")

    groups = {}
    for group in doc.get("spawn_groups", []):
        gid = group.get("id")
        if not gid or gid in groups:
            errors.append(f"duplicate/empty spawn group {gid}")
            continue
        groups[gid] = group
        cap = group.get("max_active")
        if not isinstance(cap, int) or cap <= 0 or cap > 24:
            errors.append(f"{gid}: max_active must be 1..24")
        ids = group.get("entity_ids", [])
        if not ids:
            errors.append(f"{gid}: no entities")
        for eid in ids:
            if catalog.get(eid, {}).get("family") not in {"monster","npc","wildlife"}:
                errors.append(f"{gid}: invalid spawn entity {eid}")

    invasion_ids = set()
    for inv in doc.get("invasions", []):
        iid = inv.get("id")
        if not iid or iid in invasion_ids:
            errors.append(f"duplicate/empty invasion {iid}")
        invasion_ids.add(iid)
        tier = inv.get("min_hostility_tier")
        if not isinstance(tier, int) or not 0 <= tier <= 5:
            errors.append(f"{iid}: invalid hostility tier {tier}")
        duration = inv.get("duration_seconds")
        if not isinstance(duration, (int,float)) or duration <= 0:
            errors.append(f"{iid}: invalid duration")
        cap = inv.get("max_concurrent_ai")
        if not isinstance(cap, int) or cap <= 0 or cap > 24:
            errors.append(f"{iid}: max_concurrent_ai must be 1..24")
        waves = inv.get("waves", [])
        if len(waves) < 2:
            errors.append(f"{iid}: requires at least two waves")
        for wave in waves:
            if not wave:
                errors.append(f"{iid}: empty wave")
            for gid in wave:
                if gid not in groups:
                    errors.append(f"{iid}: missing spawn group {gid}")
        if not inv.get("objective_ids"):
            errors.append(f"{iid}: no objectives")

    if len(invasion_ids) < 5:
        errors.append("REG-001 must define at least five invasion profiles")

    if errors:
        print("AEONFALL REG-001 living-world validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AEONFALL REG-001 living-world validation PASSED")
    print(f"- factions seeded: {len(seen_factions)}")
    print(f"- spawn groups: {len(groups)}")
    print(f"- invasions: {len(invasion_ids)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
