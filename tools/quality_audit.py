#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "content" / "catalog"

def entities():
    for path in sorted(CATALOG.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        values = payload.get("entities", []) if isinstance(payload, dict) else payload
        if not isinstance(values, list):
            continue
        for entity in values:
            if isinstance(entity, dict):
                yield path, entity

def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", text.lower()).strip()

def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    names: dict[str, tuple[Path, str]] = {}
    signature_lines: defaultdict[str, list[str]] = defaultdict(list)
    family_tier = Counter()

    for path, entity in entities():
        eid = entity.get("id", "<missing>")
        name = str(entity.get("name", "")).strip()
        norm_name = normalize(name)
        if norm_name:
            if norm_name in names:
                old_path, old_id = names[norm_name]
                errors.append(
                    f"duplicate normalized name: {eid} and {old_id} "
                    f"({path.relative_to(ROOT)} / {old_path.relative_to(ROOT)})"
                )
            else:
                names[norm_name] = (path, eid)

        family_tier[(entity.get("family"), entity.get("tier"))] += 1

        mechanics = entity.get("mechanics", {})
        for line in mechanics.get("signature", []) if isinstance(mechanics, dict) else []:
            norm = normalize(str(line))
            if len(norm) >= 40:
                signature_lines[norm].append(eid)

    for line, ids in signature_lines.items():
        if len(ids) >= 3:
            warnings.append(f"signature line repeated across {len(ids)} entities: {', '.join(ids[:8])}")

    print("AEONFALL diversity audit")
    print(f"- unique normalized names: {len(names)}")
    print(f"- family/tier buckets: {len(family_tier)}")
    print(f"- repeated long signature warnings: {len(warnings)}")

    for warning in warnings[:50]:
        print(f"WARNING: {warning}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
