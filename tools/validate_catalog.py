#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "content" / "catalog"

ID_RE = re.compile(r"^(WPN|ARM|REL|MON|WLD|NPC|FAC|BOS|VEH|SKL|CLS|MAT|EVT|POI)-\d{3}$")
TIERS = {
    "common","uncommon","rare","epic","legendary","mythic","exotic",
    "god","absolute","transcendent_zero"
}
STATUSES = {
    "concept","specified","prototype","implemented",
    "vfx_ready","animation_ready","tested","production"
}
FAMILIES = {
    "weapon","armor","relic","monster","wildlife","npc","faction","boss",
    "vehicle","skill","class","material","event","poi"
}
CONCURRENCY = {"tiny","low","medium","high","event_only"}
VFX = {"low","medium","high","cinematic"}
REPLICATION = {"low","medium","high","critical"}
LOCALITY = {"local","regional","global_event"}

PREFIX_FAMILY = {
    "WPN":"weapon","ARM":"armor","REL":"relic","MON":"monster","WLD":"wildlife",
    "NPC":"npc","FAC":"faction","BOS":"boss","VEH":"vehicle","SKL":"skill",
    "CLS":"class","MAT":"material","EVT":"event","POI":"poi",
}

REQUIRED = {
    "id","name","family","tier","status","role","identity",
    "mechanics","presentation","acquisition","performance","dependencies"
}

def fail(errors, path, message):
    errors.append(f"{path.relative_to(ROOT)}: {message}")

def nonempty_string_list(value):
    return isinstance(value, list) and len(value) > 0 and all(isinstance(v, str) and v.strip() for v in value)

def validate_entity(path: Path, data: dict, seen_ids: dict[str, Path], seen_names: dict[str, Path], errors: list[str]):
    missing = REQUIRED - data.keys()
    if missing:
        fail(errors, path, f"missing required fields: {sorted(missing)}")

    entity_id = data.get("id")
    if not isinstance(entity_id, str) or not ID_RE.match(entity_id):
        fail(errors, path, f"invalid id: {entity_id!r}")
    else:
        if entity_id in seen_ids:
            fail(errors, path, f"duplicate id {entity_id}; first seen in {seen_ids[entity_id].relative_to(ROOT)}")
        else:
            seen_ids[entity_id] = path
        prefix = entity_id.split("-", 1)[0]
        expected_family = PREFIX_FAMILY.get(prefix)
        if expected_family and data.get("family") != expected_family:
            fail(errors, path, f"id prefix {prefix} requires family={expected_family!r}")

    name = data.get("name")
    if not isinstance(name, str) or len(name.strip()) < 3:
        fail(errors, path, "name must be at least 3 characters")
    elif name.casefold() in seen_names:
        fail(errors, path, f"duplicate name {name!r}; first seen in {seen_names[name.casefold()].relative_to(ROOT)}")
    else:
        seen_names[name.casefold()] = path

    if data.get("family") not in FAMILIES:
        fail(errors, path, f"invalid family: {data.get('family')!r}")
    if data.get("tier") not in TIERS:
        fail(errors, path, f"invalid tier: {data.get('tier')!r}")
    if data.get("status") not in STATUSES:
        fail(errors, path, f"invalid status: {data.get('status')!r}")

    identity = data.get("identity")
    if not isinstance(identity, dict):
        fail(errors, path, "identity must be an object")
    else:
        for field in ("fantasy","silhouette","lore_hook"):
            value = identity.get(field)
            if not isinstance(value, str) or len(value.strip()) < 12:
                fail(errors, path, f"identity.{field} must be descriptive")

    mechanics = data.get("mechanics")
    if not isinstance(mechanics, dict):
        fail(errors, path, "mechanics must be an object")
        mechanics = {}
    else:
        for field in ("core","signature","counterplay"):
            if not nonempty_string_list(mechanics.get(field)):
                fail(errors, path, f"mechanics.{field} must be a non-empty string list")

    presentation = data.get("presentation")
    if not isinstance(presentation, dict):
        fail(errors, path, "presentation must be an object")
        presentation = {}
    else:
        for field in ("vfx","animation","audio"):
            if not isinstance(presentation.get(field), list):
                fail(errors, path, f"presentation.{field} must be a list")

    acquisition = data.get("acquisition")
    if not isinstance(acquisition, dict) or not nonempty_string_list(acquisition.get("method")):
        fail(errors, path, "acquisition.method must be a non-empty string list")

    perf = data.get("performance")
    if not isinstance(perf, dict):
        fail(errors, path, "performance must be an object")
    else:
        checks = (
            ("concurrency_class", CONCURRENCY),
            ("vfx_class", VFX),
            ("replication_class", REPLICATION),
            ("streaming_locality", LOCALITY),
        )
        for field, allowed in checks:
            if perf.get(field) not in allowed:
                fail(errors, path, f"performance.{field} invalid: {perf.get(field)!r}")

    deps = data.get("dependencies")
    if not isinstance(deps, list) or not all(isinstance(x, str) for x in deps):
        fail(errors, path, "dependencies must be a string list")

    tier = data.get("tier")
    signature_count = len(mechanics.get("signature", []))
    vfx_count = len(presentation.get("vfx", []))
    animation_count = len(presentation.get("animation", []))

    signature_minimums = {
        "epic": 2,
        "legendary": 3,
        "mythic": 3,
        "exotic": 3,
        "god": 4,
        "absolute": 4,
        "transcendent_zero": 5,
    }
    presentation_depth = {
        "epic": 80,
        "legendary": 100,
        "mythic": 120,
        "exotic": 130,
        "god": 160,
        "absolute": 180,
        "transcendent_zero": 220,
    }
    if tier in signature_minimums:
        min_sig = signature_minimums[tier]
        if signature_count < min_sig:
            fail(errors, path, f"{tier} tier requires at least {min_sig} signature mechanics")
        if vfx_count < 1:
            fail(errors, path, f"{tier} tier requires an authored VFX profile")
        if animation_count < 1:
            fail(errors, path, f"{tier} tier requires an authored animation profile")

        presentation_text = " ".join(
            [str(x) for x in presentation.get("vfx", [])]
            + [str(x) for x in presentation.get("animation", [])]
            + [str(x) for x in presentation.get("audio", [])]
        )
        if len(presentation_text) < presentation_depth[tier]:
            fail(
                errors,
                path,
                f"{tier} tier presentation depth is under-specified "
                f"({len(presentation_text)} < {presentation_depth[tier]} chars)",
            )

def iter_entities(payload):
    if isinstance(payload, dict) and "entities" in payload:
        entries = payload["entities"]
        if not isinstance(entries, list):
            raise ValueError("entities must be a list")
        return entries
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return [payload]
    raise ValueError("top-level JSON must be an entity object, list, or object containing entities[]")

def main() -> int:
    errors: list[str] = []
    seen_ids: dict[str, Path] = {}
    seen_names: dict[str, Path] = {}
    files = sorted(CATALOG.rglob("*.json"))
    all_entities: list[tuple[Path, dict]] = []

    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            entities = iter_entities(payload)
        except Exception as exc:
            fail(errors, path, f"invalid catalog JSON: {exc}")
            continue

        for index, entity in enumerate(entities):
            if not isinstance(entity, dict):
                fail(errors, path, f"entry {index} is not an object")
                continue
            validate_entity(path, entity, seen_ids, seen_names, errors)
            all_entities.append((path, entity))

        if isinstance(payload, dict) and "entity_count" in payload:
            declared = payload.get("entity_count")
            if declared != len(entities):
                fail(errors, path, f"entity_count metadata mismatch: declared {declared}, actual {len(entities)}")

    for path, entity in all_entities:
        entity_id = entity.get("id")
        for dependency in entity.get("dependencies", []):
            if dependency == entity_id:
                fail(errors, path, f"{entity_id} cannot depend on itself")
            if isinstance(dependency, str) and ID_RE.match(dependency) and dependency not in seen_ids:
                fail(errors, path, f"{entity_id} references missing dependency {dependency}")

    if errors:
        print("AEONFALL catalog validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"AEONFALL catalog validation PASSED: {len(seen_ids)} entities across {len(files)} file(s)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
