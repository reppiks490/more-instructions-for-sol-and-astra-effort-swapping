#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORITIES = ROOT / "content" / "transcendent" / "authorities.json"
BINDINGS = ROOT / "content" / "transcendent" / "adapter_bindings.json"

EXPECTED_INPUT = {
    "Self": "self",
    "Position": "position",
    "Area": "position",
    "Enemy": "targeted",
    "Ally": "targeted",
    "AuthoredObjective": "targeted",
}

def main() -> int:
    authority_doc = json.loads(AUTHORITIES.read_text(encoding="utf-8"))
    binding_doc = json.loads(BINDINGS.read_text(encoding="utf-8"))
    errors: list[str] = []

    abilities = {}
    for authority in authority_doc["authorities"]:
        for ability in authority["abilities"]:
            abilities[ability["id"]] = (authority["id"], ability)

    bindings = binding_doc.get("bindings", [])
    by_ability = {}
    adapters = set()

    for binding in bindings:
        ability_id = binding.get("ability_id")
        if ability_id in by_ability:
            errors.append(f"duplicate binding for {ability_id}")
        by_ability[ability_id] = binding

        if ability_id not in abilities:
            errors.append(f"binding references unknown ability {ability_id}")
            continue

        authority_id, ability = abilities[ability_id]
        if binding.get("authority_id") != authority_id:
            errors.append(f"{ability_id}: authority mismatch")
        if binding.get("adapter_id") != ability.get("adapter"):
            errors.append(f"{ability_id}: adapter mismatch")
        if binding.get("target_policy") != ability.get("target"):
            errors.append(f"{ability_id}: target-policy mismatch")

        expected_input = EXPECTED_INPUT[ability["target"]]
        if binding.get("input_bridge") != expected_input:
            errors.append(
                f"{ability_id}: input bridge {binding.get('input_bridge')} != {expected_input}"
            )

        adapter_id = binding.get("adapter_id")
        if adapter_id in adapters:
            errors.append(f"duplicate adapter id {adapter_id}")
        adapters.add(adapter_id)

        should_require = ability["target"] in {"Enemy", "Ally", "AuthoredObjective"}
        if binding.get("require_registered_target") is not should_require:
            errors.append(f"{ability_id}: registered-target policy mismatch")

        should_use_target = ability["target"] in {"Enemy", "Ally"}
        if binding.get("use_target_agent") is not should_use_target:
            errors.append(f"{ability_id}: target-agent policy mismatch")

        if binding.get("adapter_device") != "aeonfall_trigger_ability_adapter_device":
            errors.append(f"{ability_id}: unexpected adapter device")
        if binding.get("requires_project_effect_graph") is not True:
            errors.append(f"{ability_id}: must require project effect graph")

    missing = sorted(set(abilities) - set(by_ability))
    extra = sorted(set(by_ability) - set(abilities))
    if missing:
        errors.append(f"missing adapter bindings: {missing}")
    if extra:
        errors.append(f"extra adapter bindings: {extra}")

    if binding_doc.get("binding_count") != len(bindings):
        errors.append("declared binding_count does not match bindings length")

    if len(bindings) != 24:
        errors.append(f"expected 24 bindings, found {len(bindings)}")

    if errors:
        print("AEONFALL Transcendent adapter binding validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AEONFALL Transcendent adapter binding validation PASSED")
    print(f"- abilities: {len(abilities)}")
    print(f"- bindings: {len(bindings)}")
    print(f"- unique adapters: {len(adapters)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
