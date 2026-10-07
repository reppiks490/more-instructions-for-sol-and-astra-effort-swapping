#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "content" / "catalog"

TARGETS = {
    "weapon": 180,
    "armor": 120,
    "monster": 170,
    "wildlife": 60,
    "npc": 60,
    "boss": 80,
    "relic": 45,
    "vehicle": 25,
    "class": 10,
    "skill": 20,
    "event": 30,
}

def iter_entities():
    for path in sorted(CATALOG.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and isinstance(payload.get("entities"), list):
            yield from payload["entities"]

def main():
    entities = list(iter_entities())
    families = Counter(e.get("family") for e in entities)
    tiers = Counter(e.get("tier") for e in entities)
    statuses = Counter(e.get("status") for e in entities)

    print(f"AEONFALL major entities: {len(entities)}")
    print("\nBy family")
    for family, target in TARGETS.items():
        count = families.get(family, 0)
        pct = 100.0 * count / target if target else 0.0
        print(f"- {family:10s} {count:3d}/{target:3d} ({pct:5.1f}%)")

    print("\nBy tier")
    for tier, count in sorted(tiers.items()):
        print(f"- {tier:20s} {count}")

    print("\nBy status")
    for status, count in sorted(statuses.items()):
        print(f"- {status:20s} {count}")

if __name__ == "__main__":
    main()
