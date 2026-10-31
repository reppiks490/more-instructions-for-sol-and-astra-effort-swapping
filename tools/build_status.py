#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "content" / "catalog"
STATUS = ROOT / "STATUS.md"
TRANSCENDENT_ROOT = ROOT / "content" / "transcendent"

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

def load_optional_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

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

    trial_doc = load_optional_json(TRANSCENDENT_ROOT / "ascension_trials.json")
    authority_doc = load_optional_json(TRANSCENDENT_ROOT / "authorities.json")
    form_doc = load_optional_json(TRANSCENDENT_ROOT / "ascended_forms.json")
    authority_binding_doc = load_optional_json(TRANSCENDENT_ROOT / "adapter_bindings.json")
    form_binding_doc = load_optional_json(TRANSCENDENT_ROOT / "ascended_form_adapter_bindings.json")
    transform_test_doc = load_optional_json(TRANSCENDENT_ROOT / "transformation_launch_tests.json")

    trial_count = len(trial_doc.get("trials", []))
    authorities = authority_doc.get("authorities", [])
    authority_count = len(authorities)
    authority_ability_count = sum(len(a.get("abilities", [])) for a in authorities)
    forms = form_doc.get("forms", [])
    form_count = len(forms)
    form_ability_count = sum(len(f.get("abilities", [])) for f in forms)
    authority_binding_count = len(authority_binding_doc.get("bindings", []))
    form_binding_count = len(form_binding_doc.get("bindings", []))
    transformation_test_count = len(transform_test_doc.get("cases", []))

    runtime_files = [
        ROOT / "verse/transcendent/ascension_trial_runtime.verse",
        ROOT / "verse/transcendent/choosing_runtime.verse",
        ROOT / "verse/transcendent/ascended_form_runtime.verse",
        ROOT / "verse/transcendent/transcendent_runtime.verse",
        ROOT / "verse/transcendent/hall_of_ascendants_runtime.verse",
    ]
    runtime_file_count = sum(1 for path in runtime_files if path.exists())

    lines.extend([
        "",
        "## Premium-Designated Concepts",
        f"- {len(paid)} catalog entities currently carry `acquisition.paid=true`.",
        "- Premium designation is a design flag only; implementation must use Epic-supported entitlement/transaction systems and publication rules.",
        "",
        "## Integrity Gates",
        "- canonical ID uniqueness / dependencies / per-wave counts: enforced by CI",
        "- tier depth and presentation requirements: enforced by CI",
        "- original family minimums: enforced by quota guard",
        "- normalized-name / repeated-signature diversity checks: enforced by CI",
        "- Verse static safety and runtime lifecycle invariants: enforced by CI",
        "- generated registries are regenerated and drift-checked in CI",
        "- Axiom Heart recursive crafting graph: validated in CI",
        "- transformation data, adapter coverage, and Launch Session acceptance matrix: validated in CI",
        "",
        "## Endgame Runtime",
        f"- Ascension Trials authored: **{trial_count}**",
        f"- canonical God/Absolute forms: **{form_count}** with **{form_ability_count}** registered transformation abilities",
        f"- Transcendent Zero Authorities: **{authority_count}** with **{authority_ability_count}** registered Authority abilities",
        f"- declared project effect bindings: **{form_binding_count + authority_binding_count}** ({form_binding_count} God/Absolute + {authority_binding_count} Transcendent)",
        f"- transformation Launch Session acceptance cases: **{transformation_test_count}**",
        f"- endgame session runtime files present: **{runtime_file_count} / {len(runtime_files)}** (Trials, Choosing, God/Absolute, Transcendent, Hall)",
        "- transformation identity is explicit, so God/Absolute/Authority abilities cannot satisfy one another's context gates.",
        "- active transformation/exhaustion state is session-only; permanent eligibility/history stays in the persistent profile.",
        "- Hall of Ascendants is currently an honest session registry derived from connected players' persistent progress, not a claimed global leaderboard.",
        "",
        "## Production Boundary",
        "Repository runtime scaffolding and CI validation are not equivalent to a finished Fortnite island.",
        "Project-bound effect graphs, prefabs, Character Definitions, VFX/animation/audio assets, Verse compilation inside the actual UEFN project, multiplayer Launch Session tests, memory/spatial profiling, platform validation, balance, and Epic publication/compliance review still remain.",
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
