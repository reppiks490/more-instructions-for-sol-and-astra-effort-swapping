#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "content" / "world" / "region_001_faction_conflicts.json"
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

    region_id = doc.get("region_id")
    region_ids = {r["id"] for r in topology.get("regions", [])}
    if region_id not in region_ids:
        errors.append(f"unknown region {region_id}")

    ids = set()
    pairs = set()

    for conflict in doc.get("conflicts", []):
        cid = conflict.get("id")
        a = conflict.get("faction_a_id")
        b = conflict.get("faction_b_id")

        if not cid or cid in ids:
            errors.append(f"duplicate/empty conflict id {cid}")
        ids.add(cid)

        for faction_id in (a, b):
            if catalog.get(faction_id, {}).get("family") != "faction":
                errors.append(f"{cid}: unknown/non-faction {faction_id}")

        if a == b:
            errors.append(f"{cid}: factions must differ")

        pair = tuple(sorted((a, b)))
        if pair in pairs:
            errors.append(f"{cid}: duplicate faction pair {pair}")
        pairs.add(pair)

        score = conflict.get("victory_score")
        if not isinstance(score, int) or score < 50:
            errors.append(f"{cid}: victory_score must be >= 50")

        tier = conflict.get("min_hostility_tier")
        if not isinstance(tier, int) or not 0 <= tier <= 5:
            errors.append(f"{cid}: invalid min_hostility_tier {tier}")

        if len(conflict.get("objective_ids", [])) < 2:
            errors.append(f"{cid}: requires at least two objectives")

    if len(ids) < 3:
        errors.append("REG-001 must define at least three faction conflicts")

    if errors:
        print("AEONFALL REG-001 faction conflict validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AEONFALL REG-001 faction conflict validation PASSED")
    print(f"- conflicts: {len(ids)}")
    print(f"- faction pairs: {len(pairs)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
