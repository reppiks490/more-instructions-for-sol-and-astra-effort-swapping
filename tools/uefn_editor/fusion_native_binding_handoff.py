#!/usr/bin/env python3
"""Source-bound UEFN physical role checklist for Sovereign Armor / Titan.

This is NOT an editor client and cannot prove native compilation, inventory,
Fortnite gameplay, engine asset existence, or a provisioned Epic account.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = "content/sovereign/fusion_native_binding_handoff.json"
EXPECTED_COMPONENTS = {
    "authority": ("verse/sovereign/sovereign_authority_device.verse", "aeonfall_sovereign_authority_device", "core"),
    "armor": ("verse/sovereign/sovereign_fusion_device.verse", "aeonfall_sovereign_fusion_device", "core"),
    "arsenal": ("verse/sovereign/sovereign_arsenal_device.verse", "aeonfall_sovereign_arsenal_device", "core"),
    "appearance": ("verse/sovereign/sovereign_appearance_device.verse", "aeonfall_sovereign_appearance_device", "optional"),
    "titan": ("verse/sovereign/titan_proxy_device.verse", "aeonfall_titan_proxy_device", "experimental"),
}
ALIASES = {
    "armor.Authority": "authority",
    "arsenal.Controller": "armor",
    "arsenal.RendRequest": "armor.AttackOutput",
    "appearance.Authority": "authority",
    "titan.AvatarController": "armor",
}
EVIDENCE_STATE = {
    "uefn_compile": "not_run",
    "uefn_editor": "not_run",
    "client_one": "not_run",
    "client_two": "not_run",
    "combat_los": "not_run",
    "player_possession": "unproven",
}
SHA = re.compile(r"^[0-9a-f]{64}$")
EDITABLE = re.compile(r"(?m)^[ \t]*@editable[ \t]*\n[ \t]+([A-Za-z]\w*)[ \t]*:[ \t]*([A-Za-z_]\w*|\[\][A-Za-z_]\w*)[ \t]*=")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_contract(root: Path = ROOT) -> dict:
    return json.loads((root / MANIFEST).read_text(encoding="utf-8"))


def component_sources(root: Path, doc: dict) -> dict:
    return {component["id"]: root / component["source"] for component in doc["components"]}


def source_device_editables(code: str) -> dict[str, str]:
    # A duplicate editable declaration is a source error, not permission to
    # silently overwrite the earlier physical role in a Python dictionary.
    fields = EDITABLE.findall(code)
    names = [name for name, _ in fields]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate @editable field names in Verse source")
    all_fields = dict(fields)
    return {
        name: kind for name, kind in all_fields.items()
        if kind.endswith("_device") or kind == "creative_prop" or kind == "[]creative_prop"
    }


def validate_contract(root: Path, doc: dict) -> list[str]:
    errors = []
    if doc.get("schema_version") != 1 or doc.get("feature") != "AEONFALL_FUS_001_002_native_binding_handoff":
        errors.append("Incorrect binding contract schema or feature")
    if doc.get("state") != "authored_unplaced" or doc.get("native_evidence") != EVIDENCE_STATE:
        errors.append("Native evidence cannot be asserted from an authored contract")
    required_guards = {
        "require_explicit_actor_paths": True,
        "allow_shared_physical_object_only_when_aliased": True,
        "require_disabled_by_default": True,
        "no_auto_owner_provision": True,
        "no_global_input_register": True,
        "titan_enabled": False,
        "attack_los_verified": False,
        "physical_native_compile_verified": False,
        "fortnite_launch_session_verified": False,
    }
    if doc.get("editor_guardrails") != required_guards:
        errors.append("Native editor and safety guardrails drifted")
    components = doc.get("components")
    if not isinstance(components, list):
        return errors + ["Components must be a list"]
    keys = [c.get("id") if isinstance(c, dict) else None for c in components]
    if len(keys) != len(EXPECTED_COMPONENTS) or set(keys) != set(EXPECTED_COMPONENTS):
        errors.append("Missing/duplicated/unknown fusion controller component")
        return errors
    catalog = {}
    for component in components:
        name = component["id"]
        source, class_name, tier = EXPECTED_COMPONENTS[name]
        if (component.get("source"), component.get("class_name"), component.get("tier")) != (source, class_name, tier):
            errors.append(f"{name}: source, native class, or release tier drift")
        file = root / source
        if not file.is_file():
            errors.append(f"{name}: actual Verse source not present")
            continue
        code = file.read_text(encoding="utf-8")
        if f"{class_name} := class(creative_device):" not in code:
            errors.append(f"{name}: missing editor-placeable creative device class")
        if not re.search(r"(?m)^[ \t]+Enabled:logic = false[ \t]*$", code):
            errors.append(f"{name}: controller is not disabled by default")
        try:
            actual = source_device_editables(code)
        except ValueError as error:
            errors.append(f"{name}: {error}")
            continue
        declared = component.get("bindings")
        if not isinstance(declared, dict):
            errors.append(f"{name}: bindings must be a keyed map")
            continue
        if set(actual) != set(declared):
            errors.append(f"{name}: editable physical fields do not match the Verse source: {set(actual) ^ set(declared)}")
        for field, definition in declared.items():
            if not isinstance(definition, dict) or definition.get("type") != actual.get(field):
                errors.append(f"{name}.{field}: physical native class mismatch")
                continue
            role = f"{name}.{field}"
            target = definition.get("alias")
            expected_keys = {"type"}
            if role in ALIASES:
                expected_keys.add("alias")
            if role in ("authority.OwnerReference", "titan.AttackCueOutput"):
                expected_keys.add("restriction")
            if role == "titan.Waypoints":
                expected_keys |= {"min_items", "max_items"}
            if set(definition) != expected_keys:
                errors.append(f"{role}: unexpected or missing physical role contract property")
            if target != ALIASES.get(role):
                errors.append(f"{role}: expected explicit shared-role alias {ALIASES.get(role)!r}")
            if "min_items" in definition or "max_items" in definition:
                if role != "titan.Waypoints" or definition.get("min_items") != 1 or definition.get("max_items") != 8:
                    errors.append(f"{role}: unsafe array bounds")
            if role == "authority.OwnerReference" and definition.get("restriction") != "trusted_operator_provisioned_reference_only":
                errors.append("The trusted player reference must be provisioned by an operator")
            if role == "titan.AttackCueOutput" and definition.get("restriction") != "non_damaging_owner_cue_only":
                errors.append("Titan attack cue cannot be authorized as damage")
            catalog[role] = definition["type"]
        catalog[name] = class_name
    for role, target in ALIASES.items():
        if role not in catalog or target not in catalog or catalog[role] != catalog[target]:
            errors.append(f"{role}: invalid native type or dangling shared-role alias to {target}")
    return errors


def inventory_template(root: Path, doc: dict) -> dict:
    issues = validate_contract(root, doc)
    if issues:
        raise ValueError("Cannot generate handoff from inconsistent source: " + "; ".join(issues))
    objects, links, source_hashes = [], {}, {}
    for component in doc["components"]:
        name = component["id"]
        src = component["source"]
        source_hashes[src] = sha(root / src)
        objects.append({"role_id": name, "expected_type": component["class_name"],
                        "object_path": None, "observed_type": None})
        for field, definition in component["bindings"].items():
            role = f"{name}.{field}"
            if "alias" in definition:
                links[role] = {"target_role": definition["alias"], "observed_object_path": None}
            elif definition["type"] == "[]creative_prop":
                objects.append({"role_id": role, "expected_type": definition["type"],
                                "object_paths": [], "observed_types": []})
            else:
                objects.append({"role_id": role, "expected_type": definition["type"],
                                "object_path": None, "observed_type": None})
    return {
        "schema_version": 1, "feature": doc["feature"],
        "authored_manifest_sha256": sha(root / MANIFEST),
        "verse_source_sha256": source_hashes,
        "editor_project": None, "editor_level": None, "editor_capture": None,
        "objects": objects, "shared_editor_links": links,
        "native_evidence": dict(EVIDENCE_STATE),
        "claim_boundary": "operator_binding_report_only_not_native_acceptance",
    }


def valid_editor_path(path: object) -> bool:
    if not isinstance(path, str) or len(path) < 8 or len(path) > 512:
        return False
    if not path.startswith("/") or "//" in path or any(ch.isspace() for ch in path):
        return False
    if any(part in ("..", ".") for part in path.split("/")):
        return False
    return not any(marker in path.lower() for marker in ("<", ">", "{", "}", "placeholder", "invented_path"))


def verify_capture(capture, evidence_root):
    if capture is None:
        return False, []
    if not isinstance(capture, dict) or set(capture) != {"path", "sha256"}:
        return False, ["Malformed editor evidence-capture record"]
    if not isinstance(capture["path"], str) or not isinstance(capture["sha256"], str) or not SHA.fullmatch(capture["sha256"]):
        return False, ["Invalid editor evidence capture path or digest"]
    if evidence_root is None:
        return False, ["A local editor capture requires --evidence-root"]
    root = Path(evidence_root).resolve()
    candidate = root / capture["path"]
    path = candidate.resolve()
    if not path.is_relative_to(root) or candidate.is_symlink() or not path.is_file() or path.stat().st_size == 0:
        return False, ["Editor evidence capture is missing, empty, symlinked or escapes evidence root"]
    if sha(path) != capture["sha256"]:
        return False, ["Editor evidence capture digest mismatch"]
    return True, []


def audit(root: Path, doc: dict, report: dict, *, evidence_root=None) -> dict:
    issues = validate_contract(root, doc)
    expected = inventory_template(root, doc) if not issues else None
    if expected is None:
        return {"binding_consistent": False, "errors": issues, "native_playability": "not_established"}
    if set(report) != set(expected):
        issues.append("Inventory contains missing or unrecognized top-level fields")
    for field in ("schema_version", "feature", "authored_manifest_sha256",
                  "verse_source_sha256", "claim_boundary", "native_evidence"):
        if report.get(field) != expected[field]:
            issues.append(f"{field}: report is stale, altered, or claims unverified engine evidence")

    roles = {item["role_id"]: item for item in expected["objects"]}
    data = report.get("objects")
    if not isinstance(data, list):
        data = []
        issues.append("Editor physical objects must be an array")
    observed, used_paths, pending, core_bound = {}, {}, [], 0
    tier = {c["id"]: c["tier"] for c in doc["components"]}
    for item in data:
        if not isinstance(item, dict):
            issues.append("Malformed editor object record")
            continue
        role = item.get("role_id")
        if not isinstance(role, str) or role not in roles or role in observed:
            issues.append(f"Unknown or duplicated physical role: {role!r}")
            continue
        observed[role] = item
        declared = roles[role]
        if set(item) != set(declared):
            issues.append(f"{role}: unexpected editor evidence fields")
        if item.get("expected_type") != declared["expected_type"]:
            issues.append(f"{role}: expected class field does not match source")
        values = item.get("object_paths") if role == "titan.Waypoints" else [item.get("object_path")]
        classes = item.get("observed_types") if role == "titan.Waypoints" else [item.get("observed_type")]
        if not isinstance(values, list) or not isinstance(classes, list) or len(values) != len(classes):
            issues.append(f"{role}: editor object paths and class evidence disagree")
            continue
        if role == "titan.Waypoints" and len(values) > 8:
            issues.append("Titan waypoint count exceeds eight")
        if not values or values == [None]:
            if any(observed_type is not None for observed_type in classes):
                issues.append(f"{role}: claimed native class without an editor object path")
            pending.append(role)
            continue
        for location, actual_type in zip(values, classes):
            if not valid_editor_path(location) or actual_type != declared["expected_type"].removeprefix("[]"):
                issues.append(f"{role}: missing/invalid editor path or observed native class")
                continue
            if location in used_paths:
                issues.append(f"{role}: physical object already assigned to {used_paths[location]}")
            else:
                used_paths[location] = role
                if tier[role.split(".", 1)[0]] == "core":
                    core_bound += 1
    for role in roles.keys() - observed.keys():
        issues.append(f"{role}: missing editor observation record")
    # Aliases are explicit pointers to one concrete instance, never a second
    # physical object. Require the same object path if an alias is reported.
    links = report.get("shared_editor_links")
    if not isinstance(links, dict):
        links = {}
        issues.append("Editor shared aliases must be a mapping")
    if set(links) != set(expected["shared_editor_links"]):
        issues.append("Shared native links do not match the source roles")
    for role, original in expected["shared_editor_links"].items():
        value = links.get(role)
        if not isinstance(value, dict) or set(value) != set(original) or value.get("target_role") != original["target_role"]:
            issues.append(f"{role}: shared native object alias is mismatched")
            continue
        target = observed.get(original["target_role"], {})
        target_path = target.get("object_path")
        link_path = value.get("observed_object_path")
        if link_path is not None and (not valid_editor_path(link_path) or not target_path or link_path != target_path):
            issues.append(f"{role}: observed editor alias does not point to its declared shared object")
        if link_path is None:
            pending.append(role)

    captured, capture_errors = verify_capture(report.get("editor_capture"), evidence_root)
    issues.extend(capture_errors)
    editor_project = report.get("editor_project")
    editor_level = report.get("editor_level")
    if editor_project is not None and (not isinstance(editor_project, str) or not editor_project.strip()):
        issues.append("Editor project identity is malformed")
    if editor_level is not None and not valid_editor_path(editor_level):
        issues.append("Editor level path is malformed")
    core_pending = [role for role in pending if tier.get(role.split(".", 1)[0]) == "core"]
    # A complete reported inventory MUST identify an actual editor project,
    # level, and hash-checked capture. Such reports still are NOT engine proof.
    if not core_pending:
        if not isinstance(editor_project, str) or not editor_project.strip():
            issues.append("Reported complete bindings require an editor project identity")
        if not valid_editor_path(editor_level):
            issues.append("Reported complete bindings require an editor level path")
        if not captured:
            issues.append("Reported complete bindings require an integrity-checked editor capture")
    return {
        "schema_version": 1, "feature": doc["feature"],
        "source_controller_count": len(doc["components"]),
        "physical_role_count": len(roles),
        "shared_alias_count": len(expected["shared_editor_links"]),
        "reported_unique_object_paths": len(used_paths),
        "reported_core_object_count": core_bound,
        "unbound_core_roles": sorted(set(core_pending)),
        "unbound_optional_roles": sorted(set(pending) - set(core_pending)),
        "editor_capture_integrity_checked": captured,
        "binding_consistent": not issues,
        "core_binding_report_complete": not core_pending and not issues,
        "native_verse_compile": "not_assessed",
        "native_multiplayer": "not_assessed",
        "native_playability": "not_established",
        "errors": sorted(issues),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("template", "audit"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--require-core-complete", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        doc = read_contract(root)
        if args.command == "template":
            result = inventory_template(root, doc)
            args.inventory.parent.mkdir(parents=True, exist_ok=True)
            args.inventory.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            print(f"Generated {len(result['objects'])} unbound physical roles and {len(result['shared_editor_links'])} aliases. UEFN not assessed.")
            return 0
        report = json.loads(args.inventory.read_text(encoding="utf-8"))
        result = audit(root, doc, report, evidence_root=args.evidence_root)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        return int(not result["binding_consistent"] or (args.require_core_complete and not result["core_binding_report_complete"]))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Fusion handoff failed: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
