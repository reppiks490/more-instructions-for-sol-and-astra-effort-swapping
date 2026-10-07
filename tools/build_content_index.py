#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "content" / "catalog"
OUTPUT = ROOT / "generated" / "content_index.json"

def iter_entities():
    for path in sorted(CATALOG.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and "entities" in payload:
            entities = payload["entities"]
        elif isinstance(payload, list):
            entities = payload
        elif isinstance(payload, dict):
            entities = [payload]
        else:
            raise ValueError(f"Unsupported catalog payload: {path}")
        for entity in entities:
            if isinstance(entity, dict) and entity.get("id"):
                yield path, entity

def main() -> int:
    index = {}
    for path, entity in iter_entities():
        entity_id = entity["id"]
        if entity_id in index:
            raise SystemExit(f"duplicate canonical id: {entity_id}")
        index[entity_id] = {
            "name": entity.get("name"),
            "family": entity.get("family"),
            "tier": entity.get("tier"),
            "status": entity.get("status"),
            "role": entity.get("role"),
            "source": str(path.relative_to(ROOT)),
            "dependencies": entity.get("dependencies", []),
        }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "version": 1,
        "entity_count": len(index),
        "entities": dict(sorted(index.items())),
    }
    OUTPUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"generated {OUTPUT.relative_to(ROOT)} with {len(index)} entities")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
