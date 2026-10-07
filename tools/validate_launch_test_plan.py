#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "content" / "vertical_slice" / "slice_001_launch_tests.json"
HARNESS = ROOT / "verse" / "testing" / "slice_001_dev_harness_device.verse"

REQUIRED_CATEGORIES = {
    "bootstrap","persistence","shop","crafting","delivery",
    "ability_self","ability_targeted","ability_position","ability_timeout",
    "class_resource","taming","hireable","boss","world_event","teardown",
    "streaming","performance","accessibility",
}

def main() -> int:
    errors: list[str] = []
    doc = json.loads(PLAN.read_text(encoding="utf-8"))
    tests = doc.get("tests", [])

    ids = [t.get("id") for t in tests]
    if len(ids) != len(set(ids)):
        errors.append("duplicate launch test IDs")

    categories = {t.get("category") for t in tests}
    missing = REQUIRED_CATEGORIES - categories
    if missing:
        errors.append(f"missing required launch-test categories: {sorted(missing)}")

    for test in tests:
        tid = test.get("id")
        if not str(test.get("name", "")).strip():
            errors.append(f"{tid}: name is empty")
        if len(test.get("steps", [])) < 2:
            errors.append(f"{tid}: requires at least two steps")
        if len(test.get("pass", [])) < 2:
            errors.append(f"{tid}: requires at least two pass criteria")

    harness = HARNESS.read_text(encoding="utf-8")
    if "Enabled:logic = false" not in harness:
        errors.append("developer harness must default to Enabled=false")
    if "SeedEconomyButton.Disable()" not in harness:
        errors.append("disabled developer harness must disable economy seed button")

    if len(tests) < 20:
        errors.append(f"expected at least 20 launch tests, found {len(tests)}")

    if errors:
        print("AEONFALL Launch Session plan validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AEONFALL Launch Session plan validation PASSED")
    print(f"- tests: {len(tests)}")
    print(f"- categories: {len(categories)}")
    print("- developer harness defaults disabled: yes")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
