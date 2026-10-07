#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMS = ROOT / "content" / "transcendent" / "ascended_forms.json"
BINDINGS = ROOT / "content" / "transcendent" / "ascended_form_adapter_bindings.json"

EXPECTED_INPUT = {
    "Self": "self",
    "Position": "position",
    "Area": "position",
    "Enemy": "targeted",
    "Ally": "targeted",
    "AuthoredObjective": "targeted",
}

def main() -> int:
    form_doc = json.loads(FORMS.read_text(encoding="utf-8"))
    binding_doc = json.loads(BINDINGS.read_text(encoding="utf-8"))
    errors: list[str] = []

    abilities = {}
    for form in form_doc["forms"]:
        for ability in form["abilities"]:
            abilities[ability["id"]] = (form, ability)

    bindings = binding_doc.get("bindings", [])
    by_id = {}
    adapter_ids = set()

    for binding in bindings:
        aid = binding.get("ability_id")
        if aid in by_id:
            errors.append(f"duplicate binding for {aid}")
        by_id[aid] = binding

        if aid not in abilities:
            errors.append(f"unknown ability binding {aid}")
            continue

        form, ability = abilities[aid]
        checks = {
            "form_id": form["id"],
            "transformation_id": form["transformation_id"],
            "adapter_id": ability["adapter"],
            "target_policy": ability["target"],
            "boss_safe": ability["boss_safe"],
        }
        for field, expected in checks.items():
            if binding.get(field) != expected:
                errors.append(f"{aid}: {field} mismatch")

        expected_input = EXPECTED_INPUT[ability["target"]]
        if binding.get("input_bridge") != expected_input:
            errors.append(f"{aid}: input bridge mismatch")

        should_require = ability["target"] in {"Enemy", "Ally", "AuthoredObjective"}
        if binding.get("require_registered_target") is not should_require:
            errors.append(f"{aid}: registered-target policy mismatch")

        should_target_agent = ability["target"] in {"Enemy", "Ally"}
        if binding.get("use_target_agent") is not should_target_agent:
            errors.append(f"{aid}: target-agent policy mismatch")

        adapter = binding.get("adapter_id")
        if adapter in adapter_ids:
            errors.append(f"duplicate adapter id {adapter}")
        adapter_ids.add(adapter)

        if binding.get("adapter_device") != "aeonfall_trigger_ability_adapter_device":
            errors.append(f"{aid}: unexpected adapter device")
        if binding.get("requires_project_effect_graph") is not True:
            errors.append(f"{aid}: project effect graph must be required")
        if binding.get("implementation_state") != "binding_required":
            errors.append(f"{aid}: unverified binding may not claim implementation")
        if binding.get("guardrail") != ability.get("guardrail"):
            errors.append(f"{aid}: guardrail drift")

    missing = sorted(set(abilities) - set(by_id))
    extra = sorted(set(by_id) - set(abilities))
    if missing:
        errors.append(f"missing bindings: {missing}")
    if extra:
        errors.append(f"extra bindings: {extra}")

    if binding_doc.get("binding_count") != len(bindings):
        errors.append("binding_count mismatch")
    if len(bindings) != 10:
        errors.append(f"expected 10 bindings, found {len(bindings)}")

    if errors:
        print("AEONFALL ascended-form adapter validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AEONFALL ascended-form adapter validation PASSED")
    print(f"- abilities: {len(abilities)}")
    print(f"- bindings: {len(bindings)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
