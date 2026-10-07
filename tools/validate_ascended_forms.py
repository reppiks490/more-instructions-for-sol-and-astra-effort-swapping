#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "content" / "transcendent" / "ascended_forms.json"

EXPECTED = [
    ("FORM-GOD", "God Form", "ASCENDED_GOD", 1),
    ("FORM-ABSOLUTE", "Absolute Form", "ASCENDED_ABSOLUTE", 2),
]

VALID_TARGETS = {
    "Self", "Ally", "Enemy", "Position",
    "Direction", "Area", "AuthoredObjective",
}

def main() -> int:
    doc = json.loads(PATH.read_text(encoding="utf-8"))
    forms = doc.get("forms", [])
    errors: list[str] = []

    observed = [
        (
            f.get("id"),
            f.get("name"),
            f.get("transformation_id"),
            f.get("required_ascension_rank"),
        )
        for f in forms
    ]
    if observed != EXPECTED:
        errors.append(f"canonical form definition mismatch: {observed!r}")

    ability_ids: set[str] = set()
    adapters: set[str] = set()

    for form in forms:
        fid = form.get("id")
        active = form.get("active_seconds")
        cooldown = form.get("cooldown_seconds")

        if not isinstance(active, (int, float)) or not 15 <= active <= 60:
            errors.append(f"{fid}: active_seconds must be in [15, 60]")
        if not isinstance(cooldown, (int, float)) or not 60 <= cooldown <= 600:
            errors.append(f"{fid}: cooldown_seconds must be in [60, 600]")

        abilities = form.get("abilities", [])
        if len(abilities) != 5:
            errors.append(f"{fid}: exactly five abilities required")

        expected_prefix = "GOD-ABL-" if fid == "FORM-GOD" else "ABS-ABL-"
        expected_event = "god." if fid == "FORM-GOD" else "absolute."

        for ability in abilities:
            aid = ability.get("id")
            adapter = ability.get("adapter")
            target = ability.get("target")
            event = ability.get("event")

            if not isinstance(aid, str) or not aid.startswith(expected_prefix):
                errors.append(f"{fid}: invalid ability id {aid!r}")
            elif aid in ability_ids:
                errors.append(f"duplicate ability id {aid}")
            else:
                ability_ids.add(aid)

            if not isinstance(adapter, str) or not adapter:
                errors.append(f"{aid}: adapter missing")
            elif adapter in adapters:
                errors.append(f"duplicate adapter id {adapter}")
            else:
                adapters.add(adapter)

            if target not in VALID_TARGETS:
                errors.append(f"{aid}: invalid target policy {target!r}")
            if not isinstance(event, str) or not event.startswith(expected_event):
                errors.append(f"{aid}: invalid event {event!r}")
            if not isinstance(ability.get("guardrail"), str) or len(ability["guardrail"]) < 40:
                errors.append(f"{aid}: guardrail must be descriptive")
            if not isinstance(ability.get("boss_safe"), bool):
                errors.append(f"{aid}: boss_safe must be boolean")

    if len(ability_ids) != 10:
        errors.append(f"expected 10 unique abilities, found {len(ability_ids)}")

    if len(forms) == 2:
        god, absolute = forms
        if absolute["active_seconds"] >= god["active_seconds"]:
            errors.append("Absolute should remain shorter-lived than God form")
        if absolute["cooldown_seconds"] <= god["cooldown_seconds"]:
            errors.append("Absolute should retain a longer exhaustion than God form")

    if errors:
        print("AEONFALL ascended form validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AEONFALL ascended form validation PASSED")
    print(f"- forms: {len(forms)}")
    print(f"- abilities: {len(ability_ids)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
