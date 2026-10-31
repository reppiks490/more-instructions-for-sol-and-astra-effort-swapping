#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "content" / "catalog"
EVIDENCE = ROOT / "content" / "implementation" / "implementation_evidence.json"

STATUS_ORDER = {
    "concept": 0,
    "specified": 1,
    "prototype": 2,
    "implemented": 3,
    "vfx_ready": 4,
    "animation_ready": 5,
    "tested": 6,
    "production": 7,
}

def load_catalog() -> dict[str, dict]:
    result = {}
    for path in sorted(CATALOG.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        values = payload.get("entities", []) if isinstance(payload, dict) else payload
        if isinstance(values, dict):
            values = [values]
        for entity in values:
            if isinstance(entity, dict) and entity.get("id"):
                result[entity["id"]] = entity
    return result

def main() -> int:
    catalog = load_catalog()
    doc = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    errors: list[str] = []

    records = doc.get("entity_records", [])
    by_id = {}
    for record in records:
        cid = record.get("canonical_id")
        if cid in by_id:
            errors.append(f"duplicate evidence record for {cid}")
        by_id[cid] = record

        if cid not in catalog:
            errors.append(f"evidence references missing catalog entity {cid}")
            continue

        # Evidence implications must remain monotonic.
        if record.get("launch_session_verified") and not record.get("verse_compiled"):
            errors.append(f"{cid}: Launch Session cannot be verified before Verse compile")
        if record.get("multiplayer_verified") and not record.get("launch_session_verified"):
            errors.append(f"{cid}: multiplayer verification requires Launch Session verification")
        if record.get("performance_profiled") and not record.get("launch_session_verified"):
            errors.append(f"{cid}: performance profiling requires Launch Session verification")
        if record.get("verse_compiled") and not record.get("uefn_asset_bound"):
            errors.append(f"{cid}: entity compile claim requires UEFN asset binding")

        status = catalog[cid].get("status", "concept")
        level = STATUS_ORDER.get(status, -1)
        if level < 0:
            errors.append(f"{cid}: unknown catalog status {status!r}")
            continue

        if level >= STATUS_ORDER["prototype"]:
            if not record.get("binding_declared"):
                errors.append(f"{cid}: prototype status requires declared binding evidence")
        if level >= STATUS_ORDER["implemented"]:
            if not record.get("uefn_asset_bound") or not record.get("verse_compiled"):
                errors.append(f"{cid}: implemented status requires UEFN binding + Verse compile")
        if level >= STATUS_ORDER["vfx_ready"] and not record.get("vfx_ready"):
            errors.append(f"{cid}: vfx_ready status lacks VFX evidence")
        if level >= STATUS_ORDER["animation_ready"] and not record.get("animation_ready"):
            errors.append(f"{cid}: animation_ready status lacks animation evidence")
        if level >= STATUS_ORDER["tested"]:
            required = (
                record.get("launch_session_verified"),
                record.get("cleanup_verified"),
            )
            if not all(required):
                errors.append(f"{cid}: tested status lacks Launch Session/cleanup evidence")
        if level >= STATUS_ORDER["production"]:
            if not record.get("performance_profiled"):
                errors.append(f"{cid}: production status lacks performance evidence")
            if not record.get("audio_ready"):
                errors.append(f"{cid}: production status lacks audio evidence")

    for cid, entity in catalog.items():
        status = entity.get("status", "concept")
        if STATUS_ORDER.get(status, -1) >= STATUS_ORDER["prototype"] and cid not in by_id:
            errors.append(f"{cid}: promoted catalog entity has no implementation evidence record")

    system_ids = set()
    for record in doc.get("system_records", []):
        sid = record.get("system_id")
        if not sid or sid in system_ids:
            errors.append(f"duplicate/empty system evidence id {sid!r}")
        system_ids.add(sid)
        if record.get("launch_session_verified") and not record.get("verse_compiled"):
            errors.append(f"{sid}: Launch Session claim requires Verse compile")

    if not doc.get("promotion_rules"):
        errors.append("promotion_rules missing")

    if errors:
        print("AEONFALL implementation evidence validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AEONFALL implementation evidence validation PASSED")
    print(f"- entity evidence records: {len(records)}")
    print(f"- system evidence records: {len(system_ids)}")
    print("- unverified UEFN claims remain explicitly false")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
