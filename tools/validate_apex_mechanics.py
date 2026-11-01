#!/usr/bin/env python3
"""Cross-check bounded God/Absolute mechanics against canonical IDs and UEFN bindings."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "content/transcendent/ascended_ability_mechanics.json"
FORMS = ROOT / "content/transcendent/ascended_forms.json"
BINDINGS = ROOT / "content/transcendent/ascended_form_adapter_bindings.json"
CLASSES = ROOT / "content/vertical_slice/slice_001_classes.json"

def validate(mechanics_doc: dict, forms_doc: dict, bindings_doc: dict, classes_doc: dict) -> list[str]:
    errors: list[str] = []
    canonical = {
        ability["id"]: (form, ability)
        for form in forms_doc["forms"]
        for ability in form["abilities"]
    }
    bindings = {binding["ability_id"]: binding for binding in bindings_doc["bindings"]}
    class_ids = {cls["class_id"] for cls in classes_doc["classes"]}
    entries = mechanics_doc.get("mechanics", [])
    seen: set[str] = set()
    effects: set[str] = set()
    cues: set[str] = set()
    covered_classes: set[str] = set()
    if mechanics_doc.get("ability_count") != len(entries):
        errors.append("ability_count mismatch")
    if mechanics_doc.get("version") != 1:
        errors.append("unexpected mechanics version")

    for entry in entries:
        aid = entry.get("ability_id")
        if aid in seen:
            errors.append(f"{aid}: duplicate mechanics")
        seen.add(aid)
        if aid not in canonical or aid not in bindings:
            errors.append(f"{aid}: unknown canonical ability or adapter binding")
            continue
        form, ability = canonical[aid]
        binding = bindings[aid]
        for key, expected in (
            ("form_id", form["id"]),
            ("adapter_id", ability["adapter"]),
            ("target_policy", ability["target"]),
            ("boss_safe", ability["boss_safe"]),
        ):
            if entry.get(key) != expected:
                errors.append(f"{aid}: {key} drift")
        if entry.get("implementation_state") != "specified_unbound":
            errors.append(f"{aid}: cannot claim a physically implemented adapter")
        effect = entry.get("effect_kind")
        if not isinstance(effect, str) or not effect:
            errors.append(f"{aid}: missing effect kind")
        elif effect in effects:
            errors.append(f"{aid}: duplicate mechanical identity {effect}")
        effects.add(effect)

        limits = entry.get("limits", {})
        if limits.get("uses_per_form") != 1:
            errors.append(f"{aid}: one-use-per-form requirement drift")
        for field, minimum, maximum in (
            ("max_targets", 1, 8),
            ("max_instances", 1, 2),
            ("radius_m", 0, 15),
            ("max_range_m", 0, 30),
            ("lifetime_seconds", 1, 10),
        ):
            value = limits.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not minimum <= value <= maximum:
                errors.append(f"{aid}: invalid {field} budget")
        if ability["target"] in {"Position", "Area"} and limits.get("max_range_m", 0) <= 0:
            errors.append(f"{aid}: position/area needs finite positive range")
        if ability["target"] == "Area" and limits.get("radius_m", 0) <= 0:
            errors.append(f"{aid}: area needs finite positive radius")

        preflight = entry.get("preflight", {})
        if preflight.get("mode") != "specialized_preflight_required":
            errors.append(f"{aid}: missing specialized preflight")
        if preflight.get("registered_target_required") is not binding["require_registered_target"]:
            errors.append(f"{aid}: registered-target preflight drift")
        if preflight.get("destination_validation_required") is not (ability["target"] in {"Position", "Area"}):
            errors.append(f"{aid}: destination preflight drift")
        if preflight.get("encounter_owned_rules_only") is not True:
            errors.append(f"{aid}: encounter rule ownership bypass")
        expected_boss = "respect_immune" if ability["boss_safe"] else "reject_immune"
        if preflight.get("boss_policy") != expected_boss:
            errors.append(f"{aid}: boss immunity preflight drift")

        counterplay = entry.get("counterplay", {})
        for key, minimum, maximum in (("telegraph_seconds", 0.5, 3.0), ("recovery_seconds", 0.25, 2.0)):
            value = counterplay.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not minimum <= value <= maximum:
                errors.append(f"{aid}: invalid {key}")
        if len(str(counterplay.get("response", ""))) < 50:
            errors.append(f"{aid}: missing actionable counterplay")
        synergy = entry.get("class_synergy", {})
        linked = synergy.get("class_ids", [])
        if not isinstance(linked, list) or not linked or any(cid not in class_ids for cid in linked):
            errors.append(f"{aid}: invalid class synergy reference")
        else:
            covered_classes.update(linked)
        if len(str(synergy.get("interaction", ""))) < 40:
            errors.append(f"{aid}: missing bounded class synergy")
        presentation = entry.get("presentation", {})
        for key in ("tell_vfx", "impact_vfx", "exit_vfx", "tell_audio", "impact_audio"):
            cue = presentation.get(key)
            if not isinstance(cue, str) or not cue.startswith("CUE_APEX_") or cue in cues:
                errors.append(f"{aid}: missing/duplicate planned cue {key}")
            else:
                cues.add(cue)
        if len(str(presentation.get("direction", ""))) < 40:
            errors.append(f"{aid}: insufficient presentation direction")

    if seen != set(canonical):
        errors.append(f"canonical coverage mismatch missing={sorted(set(canonical)-seen)} extra={sorted(seen-set(canonical))}")
    if not class_ids.issubset(covered_classes):
        errors.append(f"missing slice class synergy coverage: {sorted(class_ids-covered_classes)}")
    return errors

def main() -> int:
    docs = [json.loads(path.read_text(encoding="utf-8")) for path in (SOURCE, FORMS, BINDINGS, CLASSES)]
    errors = validate(*docs)
    if errors:
        print("AEONFALL apex mechanics validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("AEONFALL apex mechanics validation PASSED (10 canonical abilities, bounded cues/counterplay)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
