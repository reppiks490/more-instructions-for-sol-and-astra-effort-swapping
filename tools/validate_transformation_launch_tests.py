#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "content" / "transcendent" / "transformation_launch_tests.json"

REQUIRED_CASES = {
    "TZT-001","TZT-002","TZT-003","TZT-004",
    "TZT-005","TZT-006","TZT-007","TZT-008",
    "TZT-009","TZT-010","TZT-011","TZT-012",
    "TZT-013","TZT-014","TZT-015","TZT-016",
}

REQUIRED_PHRASES = {
    "exact transformation",
    "pending",
    "teardown",
    "history",
    "session",
    "boss",
}

def main() -> int:
    doc = json.loads(PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    cases = doc.get("cases", [])
    ids = [c.get("id") for c in cases]

    if set(ids) != REQUIRED_CASES:
        errors.append(
            f"test case set mismatch: missing={sorted(REQUIRED_CASES-set(ids))} "
            f"extra={sorted(set(ids)-REQUIRED_CASES)}"
        )
    if len(ids) != len(set(ids)):
        errors.append("duplicate transformation test IDs")

    text = json.dumps(doc).lower()
    for phrase in REQUIRED_PHRASES:
        if phrase not in text:
            errors.append(f"test plan missing required concept {phrase!r}")

    for case in cases:
        cid = case.get("id")
        if not case.get("preconditions"):
            errors.append(f"{cid}: preconditions missing")
        if not str(case.get("action", "")).strip():
            errors.append(f"{cid}: action missing")
        if not case.get("expect"):
            errors.append(f"{cid}: expectations missing")

    if len(doc.get("required_observability", [])) < 5:
        errors.append("insufficient observability requirements")
    if not str(doc.get("pass_rule", "")).strip():
        errors.append("pass_rule missing")

    if errors:
        print("AEONFALL transformation Launch Session plan validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AEONFALL transformation Launch Session plan validation PASSED")
    print(f"- cases: {len(cases)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
