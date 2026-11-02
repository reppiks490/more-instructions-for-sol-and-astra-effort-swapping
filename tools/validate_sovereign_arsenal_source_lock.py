#!/usr/bin/env python3
"""Source-only, fail-closed gate for the disabled FUS-001 native Arsenal device.

Does not compile Verse or attest native collision, damage, mobile or memory.
The non-editable lock must be removed only in a reviewed future native change.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEVICE = ROOT / "verse/sovereign/sovereign_arsenal_device.verse"
CONTRACT = ROOT / "content/sovereign/sovereign_arsenal_universe_contract.json"


def validate_source_lock(source: str, contract: dict) -> list[str]:
    errors: list[str] = []
    gate = contract.get("universe_first_gate", {})
    if not isinstance(gate, dict) or any(
        gate.get(k) is not False
        for k in ("world_content_complete", "prototype_allowed",
                  "native_enablement_allowed")
    ):
        errors.append("universe-first stop gate must remain closed")
    abilities = contract.get("abilities", [])
    if not isinstance(abilities, list) or len(abilities) != 12 or any(
        not isinstance(a, dict) or a.get("native_enabled") is not False
        for a in abilities
    ):
        errors.append("all twelve native abilities must remain disabled")
    if source.count("    NativeSourceGate:logic = false") != 1:
        errors.append("non-editable native source lock missing or changed")
    if source.count("NativeSourceGate") != 2:
        errors.append("source lock has unexpected references or mutations")
    if "    Enabled:logic = false" not in source:
        errors.append("editor-visible Enabled must default to false")

    declaration = source.find("    NativeSourceGate:logic = false")
    if declaration >= 0:
        prior = [
            line.strip() for line in source[:declaration].splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        if prior and prior[-1] == "@editable":
            errors.append("native source lock must never be editor-editable")

    marker = "    OnBegin<override>()<suspends>:void="
    if source.count(marker) != 1:
        errors.append("expected one Arsenal OnBegin entrypoint")
        return errors
    begin = source.split(marker, 1)[1].split(
        "    # Every ability rechecks live native owner", 1
    )[0]
    executable = [
        line.strip() for line in begin.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if executable[:2] != ["if (not NativeSourceGate?):", "return"]:
        errors.append("native lock must be first executable OnBegin guard")
    if "if (not Enabled? or not ValidSettings()?):" not in begin:
        errors.append("existing editor and binding preflight missing")
    for forbidden_before_lock in (
        "GetAEONFALLSovereignArsenalRuntime", "AcquireController",
        ".Subscribe(", "set Running = true",
    ):
        prefix = begin.split("if (not NativeSourceGate?):", 1)[0]
        if forbidden_before_lock in prefix:
            errors.append("side effect occurs before hard source lock")
    for method in ("OnRend", "OnCollapse", "OnBulwark"):
        if f"    {method}(" not in source:
            errors.append(f"existing {method} source was removed")
    return errors


def main() -> int:
    errors = validate_source_lock(
        DEVICE.read_text(encoding="utf-8"),
        json.loads(CONTRACT.read_text(encoding="utf-8")),
    )
    for error in errors:
        print("FAIL:", error)
    if errors:
        return 1
    print("PASS: native Arsenal hard-locked; source-only, no UEFN proof.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
