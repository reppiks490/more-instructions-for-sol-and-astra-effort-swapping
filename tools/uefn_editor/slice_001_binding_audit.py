#!/usr/bin/env python3
"""Fail-closed physical binding inventory audit for SLICE-001.

A consistent inventory is not evidence of native Verse compilation, editor
execution, or a successful Fortnite Launch Session.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RIG = ROOT / "content/vertical_slice/first_playable_rig.json"
BINDINGS = ROOT / "content/vertical_slice/slice_001_uefn_bindings.json"
LAUNCH = ROOT / "content/vertical_slice/slice_001_launch_tests.json"
ROOT_KEYS = {"StartInput", "FailInput", "ParticipantVolume", "BossSpawners",
             "CompletedOutput", "FailedOutput"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reference_ids(bindings):
    refs = []

    def visit(node, key=""):
        if isinstance(node, dict):
            for field, value in node.items():
                visit(value, field)
        elif isinstance(node, list):
            for value in node:
                visit(value, key)
        elif key in ROOT_KEYS or key.endswith("_ref") or key.endswith("_refs"):
            if not isinstance(node, str) or not node:
                raise ValueError(f"Invalid physical reference in {key}")
            refs.append(node)

    visit(bindings)
    if len(refs) != len(set(refs)):
        raise ValueError("Physical reference is assigned to multiple roles")
    return refs


def contracts(rig_path=RIG, bindings_path=BINDINGS, launch_path=LAUNCH):
    paths = tuple(map(Path, (rig_path, bindings_path, launch_path)))
    rig, bindings, launch = (json.loads(p.read_text(encoding="utf-8")) for p in paths)
    if rig.get("state") != "authored_unplaced" or rig.get("encounter_id") != "BOS-005":
        raise ValueError("Expected unplaced BOS-005 rig")
    if bindings.get("slice_id") != "SLICE-001" or launch.get("slice_id") != "SLICE-001":
        raise ValueError("Slice contracts disagree")
    devices = rig["devices"]
    ids = [d["id"] for d in devices]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("Duplicate or empty rig device IDs")
    directors = [d for d in devices if d.get("type") == "aeonfall_encounter_director_device"]
    if len(directors) != 1:
        raise ValueError("Exactly one encounter director required")
    refs = reference_ids(directors[0]["bindings"])
    if not set(refs) <= set(ids):
        raise ValueError("Rig references unknown devices")
    tests = [t["id"] for t in launch["tests"]]
    if not tests or len(tests) != len(set(tests)):
        raise ValueError("Duplicate or missing launch test IDs")
    return {"paths": paths, "devices": devices, "refs": refs,
            "test_ids": tests, "sha256": [sha256(p) for p in paths]}


def template(spec):
    return {
        "schema_version": 1, "slice_id": "SLICE-001", "encounter_id": "BOS-005",
        "contract_sha256": dict(zip(("rig", "bindings", "launch_tests"), spec["sha256"])),
        "editor_project": None, "editor_level": None,
        "editor_capture": None,
        "observations": [{"device_id": d["id"], "observed_class": None,
                          "object_path": None} for d in spec["devices"]],
        "director_observed_links": {ref: None for ref in spec["refs"]},
        "launch_test_status": {tid: "not_run" for tid in spec["test_ids"]},
    }


def audit(spec, inventory, *, evidence_root=None):
    errors = []
    hashes = dict(zip(("rig", "bindings", "launch_tests"), spec["sha256"]))
    if (inventory.get("schema_version") != 1 or inventory.get("slice_id") != "SLICE-001"
            or inventory.get("encounter_id") != "BOS-005"):
        errors.append("Inventory schema/slice/encounter mismatch")
    if inventory.get("contract_sha256") != hashes:
        errors.append("Authored contracts changed after inventory was created")
    devices = {d["id"]: d for d in spec["devices"]}
    observations = inventory.get("observations")
    if not isinstance(observations, list):
        observations = []
        errors.append("Observations must be a list")
    seen, paths = {}, {}
    for item in observations:
        if not isinstance(item, dict):
            errors.append("Malformed observation record")
            continue
        key = item.get("device_id")
        if not isinstance(key, str) or key not in devices:
            errors.append(f"Unknown device observation: {key!r}")
            continue
        if key in seen:
            errors.append(f"Duplicate device observation: {key}")
            continue
        seen[key] = item
        if item.get("observed_class") != devices[key]["type"]:
            errors.append(f"{key}: observed device class mismatch or missing")
        path = item.get("object_path")
        if (not isinstance(path, str) or not path.startswith("/Game/")
                or any(c.isspace() for c in path) or len(path) <= 6):
            errors.append(f"{key}: missing/invalid editor object path")
        elif path in paths:
            errors.append(f"{key}: physical object aliased by {paths[path]}")
        else:
            paths[path] = key
    for key in devices.keys() - seen.keys():
        errors.append(f"{key}: no editor observation")
    links = inventory.get("director_observed_links")
    if not isinstance(links, dict):
        links = {}
        errors.append("Director observed links must be an object")
    expected_refs = set(spec["refs"])
    for key in links.keys() - expected_refs:
        errors.append(f"Unexpected director physical reference: {key}")
    for key in expected_refs:
        expected_path = seen.get(key, {}).get("object_path")
        if not expected_path or links.get(key) != expected_path:
            errors.append(f"{key}: missing/mismatched observed director link")
    statuses = inventory.get("launch_test_status")
    if not isinstance(statuses, dict) or set(statuses) != set(spec["test_ids"]):
        errors.append("Launch test inventory does not cover exact canonical IDs")
        statuses = {}
    for tid, status in statuses.items():
        if status not in ("not_run", "blocked", "failed", "passed"):
            errors.append(f"{tid}: invalid launch status")
    capture = inventory.get("editor_capture")
    capture_valid = False
    if capture is not None:
        if (not isinstance(capture, dict) or not isinstance(capture.get("path"), str)
                or not isinstance(capture.get("sha256"), str)
                or not SHA256.fullmatch(capture["sha256"])):
            errors.append("Malformed editor capture provenance")
        elif evidence_root is None:
            errors.append("Editor capture requires an explicit evidence root")
        else:
            root = Path(evidence_root).resolve()
            candidate = root / capture["path"]
            file = candidate.resolve()
            if (not file.is_relative_to(root) or not file.is_file()
                    or candidate.is_symlink() or file.stat().st_size == 0):
                errors.append("Editor capture missing, empty, symlinked, or outside evidence root")
            elif sha256(file) != capture["sha256"]:
                errors.append("Editor capture SHA-256 mismatch")
            else:
                capture_valid = True
    if not isinstance(inventory.get("editor_project"), str) or not inventory["editor_project"].strip():
        errors.append("Editor project identity missing")
    if not isinstance(inventory.get("editor_level"), str) or not inventory["editor_level"].startswith("/Game/"):
        errors.append("Editor level identity missing")
    return {
        "schema_version": 1, "slice_id": "SLICE-001",
        "source_device_count": len(devices),
        "observed_device_count": sum(isinstance(i.get("object_path"), str) and i["object_path"].startswith("/Game/") for i in seen.values()),
        "physical_role_count": len(spec["refs"]),
        "matching_role_count": sum(bool(seen.get(ref, {}).get("object_path")) and links.get(ref) == seen[ref]["object_path"] for ref in spec["refs"]),
        "launch_test_count": len(spec["test_ids"]),
        "launch_tests_claimed_passed": sum(s == "passed" for s in statuses.values()),
        "editor_capture_integrity_checked": capture_valid,
        "inventory_consistent": not errors,
        "native_verse_compile": "not_assessed",
        "fortnite_launch_session": "not_assessed",
        "playable_claim": "not_established",
        "errors": sorted(errors),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("template", "audit"))
    parser.add_argument("--rig", type=Path, default=RIG)
    parser.add_argument("--bindings", type=Path, default=BINDINGS)
    parser.add_argument("--launch-tests", type=Path, default=LAUNCH)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--evidence-root", type=Path)
    args = parser.parse_args(argv)
    try:
        spec = contracts(args.rig, args.bindings, args.launch_tests)
        if args.command == "template":
            if args.inventory.exists():
                raise ValueError("Refusing to overwrite an existing editor inventory")
            args.inventory.parent.mkdir(parents=True, exist_ok=True)
            args.inventory.write_text(json.dumps(template(spec), indent=2) + "\n", encoding="utf-8")
            print(f"Wrote unobserved editor checklist: {args.inventory}")
            return 0
        inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
        report = audit(spec, inventory, evidence_root=args.evidence_root)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 0 if report["inventory_consistent"] else 1
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"Binding audit failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
