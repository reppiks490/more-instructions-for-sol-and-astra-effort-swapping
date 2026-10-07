#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "content" / "catalog"

PREFIX_TO_FAMILY = {
    "WPN":"weapon","ARM":"armor","REL":"relic","MON":"monster","WLD":"wildlife",
    "NPC":"npc","FAC":"faction","BOS":"boss","VEH":"vehicle","SKL":"skill",
    "CLS":"class","MAT":"material","EVT":"event","POI":"poi"
}
TIERS = ["Common","Uncommon","Rare","Epic","Legendary","Mythic","Exotic","God","Absolute","Transcendent Zero"]
STATUS = ["concept","specified","prototype","implemented","vfx_ready","animation_ready","tested","production"]
HIGH_TIERS = {"Legendary","Mythic","Exotic","God","Absolute","Transcendent Zero"}
REQUIRED = {
    "id","family","name","tier","role","concept","signature_mechanic",
    "visual_identity","animation_profile","vfx_profile","acquisition","performance","status"
}
ID_RE = re.compile(r"^(WPN|ARM|REL|MON|WLD|NPC|FAC|BOS|VEH|SKL|CLS|MAT|EVT|POI)-\d{3}$")

def fail(errors, source, entity_id, message):
    errors.append(f"{source}: {entity_id}: {message}")

def validate_entity(e, source, seen, errors):
    entity_id = e.get("id","<missing-id>")
    missing = REQUIRED - set(e)
    if missing:
        fail(errors, source, entity_id, f"missing required fields: {sorted(missing)}")
        return

    m = ID_RE.match(entity_id)
    if not m:
        fail(errors, source, entity_id, "invalid canonical ID")
    else:
        expected = PREFIX_TO_FAMILY[m.group(1)]
        if e["family"] != expected:
            fail(errors, source, entity_id, f"family must be {expected!r}")

    if entity_id in seen:
        fail(errors, source, entity_id, f"duplicate ID also found in {seen[entity_id]}")
    else:
        seen[entity_id] = source

    if e["tier"] not in TIERS:
        fail(errors, source, entity_id, f"unknown tier {e['tier']!r}")
    if e["status"] not in STATUS:
        fail(errors, source, entity_id, f"unknown status {e['status']!r}")

    perf = e.get("performance")
    if not isinstance(perf, dict):
        fail(errors, source, entity_id, "performance must be an object")
    else:
        for key in ("concurrency","vfx_band","replication_band"):
            if key not in perf:
                fail(errors, source, entity_id, f"performance missing {key}")
        if isinstance(perf.get("concurrency"), int) and perf["concurrency"] < 1:
            fail(errors, source, entity_id, "concurrency must be >= 1")

    caps = e.get("capabilities", [])
    if not isinstance(caps, list) or not caps:
        fail(errors, source, entity_id, "capabilities must contain at least one item")

    if e["tier"] in HIGH_TIERS:
        if len(e.get("counterplay", [])) < 1:
            fail(errors, source, entity_id, "high-tier entity requires explicit counterplay")
        if len(e.get("signature_mechanic","")) < 24:
            fail(errors, source, entity_id, "high-tier signature mechanic is under-specified")
        if len(e.get("animation_profile","")) < 24:
            fail(errors, source, entity_id, "high-tier animation profile is under-specified")
        if len(e.get("vfx_profile","")) < 24:
            fail(errors, source, entity_id, "high-tier VFX profile is under-specified")

def main():
    files = sorted(CATALOG.glob("*.json"))
    if not files:
        print("No catalog files found", file=sys.stderr)
        return 2

    errors = []
    seen = {}
    count = 0
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{path}: invalid JSON: {exc}")
            continue
        entities = payload.get("entities") if isinstance(payload, dict) else None
        if not isinstance(entities, list):
            errors.append(f"{path}: top-level object must contain entities[]")
            continue
        for entity in entities:
            count += 1
            if not isinstance(entity, dict):
                errors.append(f"{path}: entity #{count} is not an object")
                continue
            validate_entity(entity, path.relative_to(ROOT), seen, errors)

    if errors:
        print("\n".join(errors), file=sys.stderr)
        print(f"FAILED: {len(errors)} validation error(s)", file=sys.stderr)
        return 1

    print(f"OK: validated {count} major entities across {len(files)} catalog file(s)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
