#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "content" / "transcendent" / "authorities.json"

EXPECTED = [
    ("AUTH-001", "Axiom Break"),
    ("AUTH-002", "World Devourer"),
    ("AUTH-003", "Omnipresence"),
    ("AUTH-004", "Causality Rejection"),
    ("AUTH-005", "Genesis Engine"),
    ("AUTH-006", "Pantheon"),
    ("AUTH-007", "The Last Word"),
    ("AUTH-008", "Reality Engine"),
]

VALID_TARGETS = {
    "Self", "Ally", "Enemy", "Position",
    "Direction", "Area", "AuthoredObjective",
}

def main() -> int:
    doc = json.loads(PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    authorities = doc.get("authorities", [])

    observed = [(a.get("id"), a.get("name")) for a in authorities]
    if observed != EXPECTED:
        errors.append(
            f"canonical authority order/name mismatch: expected={EXPECTED!r} observed={observed!r}"
        )

    ability_ids: set[str] = set()
    adapter_ids: set[str] = set()
    previous_history = -1

    for authority in authorities:
        aid = authority.get("id")
        active = authority.get("active_seconds")
        cooldown = authority.get("cooldown_seconds")
        min_history = authority.get("min_history_activations")

        if not isinstance(active, (int, float)) or not 10 <= active <= 45:
            errors.append(f"{aid}: active_seconds must be in [10, 45]")
        if not isinstance(cooldown, (int, float)) or not 120 <= cooldown <= 900:
            errors.append(f"{aid}: cooldown_seconds must be in [120, 900]")
        if not isinstance(min_history, int) or min_history < 0:
            errors.append(f"{aid}: min_history_activations must be non-negative")
        elif min_history < previous_history:
            errors.append(f"{aid}: history requirement regresses from prior authority")
        else:
            previous_history = min_history

        abilities = authority.get("abilities", [])
        if len(abilities) != 3:
            errors.append(f"{aid}: exactly three abilities required")

        for ability in abilities:
            ability_id = ability.get("id")
            adapter_id = ability.get("adapter")
            target = ability.get("target")
            event = ability.get("event")

            if not isinstance(ability_id, str) or not ability_id.startswith("TZA-"):
                errors.append(f"{aid}: invalid Transcendent ability id {ability_id!r}")
            elif ability_id in ability_ids:
                errors.append(f"{aid}: duplicate ability id {ability_id}")
            else:
                ability_ids.add(ability_id)

            if not isinstance(adapter_id, str) or not adapter_id:
                errors.append(f"{ability_id}: adapter id missing")
            elif adapter_id in adapter_ids:
                errors.append(f"{ability_id}: adapter id must be unique: {adapter_id}")
            else:
                adapter_ids.add(adapter_id)

            if target not in VALID_TARGETS:
                errors.append(f"{ability_id}: invalid target policy {target!r}")
            if not isinstance(event, str) or not event.startswith("transcendent."):
                errors.append(f"{ability_id}: invalid event id {event!r}")
            if not isinstance(ability.get("boss_safe"), bool):
                errors.append(f"{ability_id}: boss_safe must be boolean")

    if len(ability_ids) != 24:
        errors.append(f"expected 24 unique Transcendent abilities, found {len(ability_ids)}")

    if authorities:
        reality = authorities[-1]
        if reality.get("id") != "AUTH-008" or reality.get("min_history_activations", 0) < 8:
            errors.append("Reality Engine must remain final and require at least 8 prior activations")

    if errors:
        print("AEONFALL Transcendent Authority validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AEONFALL Transcendent Authority validation PASSED")
    print(f"- authorities: {len(authorities)}")
    print(f"- abilities: {len(ability_ids)}")
    print(f"- final authority: {authorities[-1]['name']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
