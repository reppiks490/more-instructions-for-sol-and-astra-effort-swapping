#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMBAT = ROOT / "content" / "vertical_slice" / "slice_001_combat_runtime.json"
COVERAGE = ROOT / "content" / "vertical_slice" / "slice_001_adapter_coverage.json"

ALLOWED_RUNTIME_DEVICES = {
    "aeonfall_trigger_ability_adapter_device",
    "aeonfall_status_ability_adapter_device",
    "aeonfall_composite_ability_adapter_device",
}

def main() -> int:
    errors: list[str] = []
    combat = json.loads(COMBAT.read_text(encoding="utf-8"))
    coverage = json.loads(COVERAGE.read_text(encoding="utf-8"))

    abilities = {a["id"]: a for a in combat.get("abilities", [])}
    adapters = coverage.get("adapters", [])
    covered_ids = [a.get("ability_id") for a in adapters]

    if len(covered_ids) != len(set(covered_ids)):
        errors.append("duplicate ability adapter coverage rows detected")

    if set(covered_ids) != set(abilities):
        errors.append(
            "ability coverage mismatch: "
            f"missing={sorted(set(abilities) - set(covered_ids))}, "
            f"extra={sorted(set(covered_ids) - set(abilities))}"
        )

    status_bridge_ids = {
        row.get("status_id")
        for row in coverage.get("status_bridges", [])
        if row.get("status_id")
    }

    for row in adapters:
        aid = row.get("ability_id")
        source = abilities.get(aid)
        if source is None:
            continue

        if row.get("adapter_id") != source.get("adapter_id"):
            errors.append(
                f"{aid}: adapter id mismatch "
                f"{row.get('adapter_id')} != {source.get('adapter_id')}"
            )

        if row.get("runtime_device") not in ALLOWED_RUNTIME_DEVICES:
            errors.append(
                f"{aid}: unsupported runtime device {row.get('runtime_device')}"
            )

        strategy = row.get("strategy")
        statuses = source.get("status_ids", [])

        if strategy == "canonical_status":
            if not statuses:
                errors.append(f"{aid}: canonical_status strategy has no statuses")
            if row.get("runtime_device") != "aeonfall_status_ability_adapter_device":
                errors.append(f"{aid}: canonical_status must use status adapter")

        if strategy == "composite_status_and_trigger":
            if not statuses:
                errors.append(f"{aid}: composite strategy has no statuses")
            if row.get("runtime_device") != "aeonfall_composite_ability_adapter_device":
                errors.append(f"{aid}: composite strategy must use composite adapter")

        if strategy == "trigger_device_graph":
            if row.get("runtime_device") != "aeonfall_trigger_ability_adapter_device":
                errors.append(f"{aid}: trigger strategy must use trigger adapter")

        for status_id in statuses:
            if status_id not in status_bridge_ids:
                errors.append(
                    f"{aid}: referenced status {status_id} lacks a project status bridge"
                )

        if not str(row.get("target_mode", "")).strip():
            errors.append(f"{aid}: target_mode is empty")
        if not str(row.get("notes", "")).strip():
            errors.append(f"{aid}: notes are empty")

    combat_status_ids = {s["id"] for s in combat.get("statuses", [])}
    for row in coverage.get("status_bridges", []):
        sid = row.get("status_id")
        if sid not in combat_status_ids:
            errors.append(f"status bridge references unknown status {sid}")
        if not row.get("gameplay_binding"):
            errors.append(f"{sid}: gameplay binding missing")
        if not row.get("vfx_binding"):
            errors.append(f"{sid}: VFX binding missing")

    if errors:
        print("AEONFALL adapter coverage validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AEONFALL adapter coverage validation PASSED")
    print(f"- abilities covered: {len(abilities)}")
    print(f"- status bridges: {len(status_bridge_ids)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
