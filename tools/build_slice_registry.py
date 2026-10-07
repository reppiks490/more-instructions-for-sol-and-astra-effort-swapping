#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLICE = ROOT / "content" / "vertical_slice" / "slice_001_ossuary_march.json"
OUTPUT = ROOT / "generated" / "slice_001_registry.verse"

ARRAY_FIELDS = [
    ("monsters", "Slice001MonsterIds"),
    ("tameable_wildlife", "Slice001TameableIds"),
    ("hireables", "Slice001HireableIds"),
    ("weapons", "Slice001WeaponIds"),
    ("armor_sets", "Slice001ArmorIds"),
    ("vehicles", "Slice001VehicleIds"),
    ("classes", "Slice001ClassIds"),
    ("skills", "Slice001SkillIds"),
    ("minibosses", "Slice001MinibossIds"),
    ("crafting_materials", "Slice001CraftingMaterialIds"),
]

def verse_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

def verse_array(values: list[str]) -> str:
    if not values:
        return "array{}"
    inner = ", ".join(verse_string(v) for v in values)
    return f"array{{{inner}}}"

def main() -> int:
    doc = json.loads(SLICE.read_text(encoding="utf-8"))

    lines = [
        "# GENERATED FILE — do not hand edit.",
        "# Source: content/vertical_slice/slice_001_ossuary_march.json",
        "",
        f"Slice001Id:string = {verse_string(doc['slice_id'])}",
        f"Slice001Name:string = {verse_string(doc['name'])}",
        "",
    ]

    for field, symbol in ARRAY_FIELDS:
        values = doc.get(field, [])
        lines.append(f"{symbol}:[]string = {verse_array(values)}")

    lines.extend([
        "",
        f"Slice001MajorBossId:string = {verse_string(doc['major_boss'])}",
        f"Slice001WorldEventId:string = {verse_string(doc['world_event'])}",
        "",
        "# These are canonical IDs only. Actual prefabs, Character Definitions,",
        "# weapon templates, devices, VFX, audio, and inventory bindings resolve",
        "# through content/vertical_slice/slice_001_uefn_bindings.json.",
        "",
    ])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"generated {OUTPUT.relative_to(ROOT)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
