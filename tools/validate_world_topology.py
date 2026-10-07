#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOPOLOGY = ROOT / "content" / "world" / "world_topology.json"

def main() -> int:
    doc = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    regions = doc.get("regions", [])
    errors = []

    ids = [r.get("id") for r in regions]
    names = [str(r.get("name", "")).casefold() for r in regions]

    if len(ids) != len(set(ids)):
        errors.append("duplicate region IDs")
    if len(names) != len(set(names)):
        errors.append("duplicate normalized region names")
    if sum(1 for r in regions if r.get("vertical_slice") is True) != 1:
        errors.append("exactly one region must be marked vertical_slice=true")

    by_id = {r["id"]: r for r in regions if r.get("id")}
    for region in regions:
        rid = region.get("id")
        neighbors = region.get("neighbors", [])
        if not neighbors:
            errors.append(f"{rid}: region has no neighbors")
        for neighbor in neighbors:
            if neighbor not in by_id:
                errors.append(f"{rid}: missing neighbor {neighbor}")
            elif rid not in by_id[neighbor].get("neighbors", []):
                errors.append(f"{rid}: adjacency to {neighbor} is not reciprocal")

    if regions:
        start = regions[0]["id"]
        seen = {start}
        q = deque([start])
        while q:
            current = q.popleft()
            for nxt in by_id[current].get("neighbors", []):
                if nxt not in seen:
                    seen.add(nxt)
                    q.append(nxt)
        missing = set(by_id) - seen
        if missing:
            errors.append(f"region graph is disconnected; unreachable={sorted(missing)}")

    shell_ids = [s.get("id") for s in doc.get("event_shells", [])]
    if len(shell_ids) != len(set(shell_ids)):
        errors.append("duplicate event shell IDs")

    if not doc.get("profiling_gates"):
        errors.append("profiling_gates must not be empty")

    if errors:
        print("AEONFALL world topology validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AEONFALL world topology validation PASSED")
    print(f"- regions: {len(regions)}")
    print(f"- event shells: {len(shell_ids)}")
    print(f"- connected region graph: yes")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
