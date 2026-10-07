#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "content" / "catalog"

MINIMUMS = {
    "weapon": 180,
    "armor": 120,
    "monster": 170,
    "wildlife": 60,
    "npc": 60,
    "boss": 80,
    "relic": 45,
    "vehicle": 25,
    "class_skill": 30,
    "event": 30,
}

def load_counts() -> Counter:
    counts = Counter()
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
            if not isinstance(entity, dict):
                continue
            family = entity.get("family")
            if family == "class" or family == "skill":
                counts["class_skill"] += 1
            else:
                counts[family] += 1
    return counts

def main() -> int:
    counts = load_counts()
    failures = []
    for family, minimum in MINIMUMS.items():
        current = counts[family]
        if current < minimum:
            failures.append(f"{family}: {current} < required {minimum}")

    total_target_counted = sum(counts[k] for k in MINIMUMS)
    print("AEONFALL quota guard")
    for family, minimum in MINIMUMS.items():
        print(f"- {family}: {counts[family]} / {minimum}")
    print(f"- target-counted total: {total_target_counted}")

    if failures:
        print("QUOTA GUARD FAILED", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("QUOTA GUARD PASSED: every original family minimum is satisfied")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
