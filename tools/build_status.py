#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "content" / "catalog"
STATUS = ROOT / "STATUS.md"

TARGETS = [
    ("weapon", "Weapons", 180),
    ("armor", "Armor / major pieces", 120),
    ("monster", "Monsters", 170),
    ("wildlife", "Wildlife / tameables", 60),
    ("npc", "Hireable / major NPCs", 60),
    ("boss", "Bosses", 80),
    ("relic", "Relics / artifacts", 45),
    ("vehicle", "Vehicles / advanced variants", 25),
    ("class_skill", "Classes / major skills", 30),
    ("event", "World events / special effects", 30),
]

def load_entities() -> list[dict]:
    entities: list[dict] = []
    for path in sorted(CATALOG.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and "entities" in payload:
            values = payload["entities"]
        elif isinstance(payload, list):
            values = payload
        elif isinstance(payload, dict):
            values = [payload]
        else:
            raise ValueError(f"Unsupported catalog payload in {path}")
        entities.extend(v for v in values if isinstance(v, dict))
    return entities

def render(entities: list[dict]) -> str:
    by_family = Counter(e.get("family") for e in entities)
    by_status = Counter(e.get("status") for e in entities)

    target_counts = {
        "weapon": by_family["weapon"],
        "armor": by_family["armor"],
        "monster": by_family["monster"],
        "wildlife": by_family["wildlife"],
        "npc": by_family["npc"],
        "boss": by_family["boss"],
        "relic": by_family["relic"],
        "vehicle": by_family["vehicle"],
        "class_skill": by_family["class"] + by_family["skill"],
        "event": by_family["event"],
    }

    target_total = sum(target for _, _, target in TARGETS)
    specified_total = sum(target_counts[key] for key, _, _ in TARGETS)
    extra_factions = by_family["faction"]

    lines = [
        "# AEONFALL — Live Status",
        "",
        "This file is generated from the canonical catalog by `tools/build_status.py`.",
        "",
        "## Major Entity Catalog",
        f"**Target-counted authored entities: {specified_total} / {target_total} ({specified_total / target_total * 100:.1f}%)**",
        f"**Additional major faction definitions: {extra_factions}**",
        f"**All catalog entities: {len(entities)}**",
        "",
        "| Family | Specified | Target | Progress |",
        "|---|---:|---:|---:|",
    ]

    for key, label, target in TARGETS:
        count = target_counts[key]
        pct = count / target * 100 if target else 0
        marker = " **(minimum met)**" if count >= target else ""
        lines.append(f"| {label} | {count} | {target} | {pct:.1f}%{marker} |")

    lines.extend([
        f"| **Target-counted total** | **{specified_total}** | **{target_total}** | **{specified_total / target_total * 100:.1f}%** |",
        "",
        "## Pipeline Status",
    ])

    ordered_status = [
        "concept","specified","prototype","implemented",
        "vfx_ready","animation_ready","tested","production",
    ]
    for status in ordered_status:
        lines.append(f"- {status}: {by_status[status]}")

    paid = [e for e in entities if isinstance(e.get("acquisition"), dict) and e["acquisition"].get("paid") is True]
    lines.extend([
        "",
        "## Premium-Designated Concepts",
        f"- {len(paid)} catalog entities currently carry `acquisition.paid=true`.",
        "- Premium designation is a design flag only; implementation must use Epic-supported entitlement/transaction systems and publication rules.",
        "",
        "## Integrity Gates",
        "- canonical ID uniqueness: enforced by CI",
        "- canonical dependency existence: enforced by CI",
        "- declared per-wave entity counts: enforced by CI",
        "- tier depth / presentation requirements: enforced by CI",
        "- status dashboard freshness: enforced by CI",
        "",
        "## Production Boundary",
        "Catalog specification is not equivalent to UEFN implementation.",
        "The next implementation gates require the UEFN project, asset binding, Verse compilation, Launch Session testing, memory profiling, VFX/animation production, and balance passes.",
        "",
    ])
    return "\n".join(lines)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rendered = render(load_entities())
    if args.check:
        current = STATUS.read_text(encoding="utf-8") if STATUS.exists() else ""
        if current != rendered:
            print("STATUS.md is stale. Run: python tools/build_status.py")
            return 1
        print("STATUS.md is current")
        return 0

    STATUS.write_text(rendered, encoding="utf-8")
    print("Updated STATUS.md")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
