#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"content"/"vertical_slice"/"slice_001_combat_runtime.json"
OUT=ROOT/"generated"/"slice_001_combat_registry.verse"

def q(v:str)->str:
    return '"' + v.replace("\\","\\\\").replace('"','\\"') + '"'

def arr(values:list[str])->str:
    return "array{" + ", ".join(q(v) for v in values) + "}"

def main()->int:
    doc=json.loads(DATA.read_text(encoding="utf-8"))
    lines=[
      "# GENERATED FILE — do not hand edit.",
      "# Source: content/vertical_slice/slice_001_combat_runtime.json",
      "",
      f"Slice001StatusIds:[]string = {arr([s['id'] for s in doc['statuses']])}",
      f"Slice001AbilityIds:[]string = {arr([a['id'] for a in doc['abilities']])}",
      f"Slice001AbilityOwnerIds:[]string = {arr([a['owner_entity_id'] for a in doc['abilities']])}",
      f"Slice001AbilityAdapterIds:[]string = {arr([a['adapter_id'] for a in doc['abilities']])}",
      ""
    ]
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text("\n".join(lines),encoding="utf-8")
    print(f"generated {OUT.relative_to(ROOT)}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
