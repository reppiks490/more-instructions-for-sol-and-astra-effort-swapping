#!/usr/bin/env python3
"""Install AEONFALL into an editor-created UEFN project; never invent metadata."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAFE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def within(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes its declared root: {path}")
    return resolved

def writable_path(path: Path, root: Path) -> Path:
    # Even an in-project symlink could alias the .uefnproject/.uplugin. Reject
    # links along the entire write path and hard-linked destination files.
    absolute = path.absolute()
    cursor = root.resolve()
    for part in absolute.relative_to(cursor).parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"Symlink destination escapes owned namespace: {cursor}")
    result = within(absolute, root)
    if result.is_file() and result.stat().st_nlink > 1:
        raise ValueError(f"Hard-linked destination is not owned safely: {result}")
    return result

def discover_plugin(project_file: Path, plugin_name: str | None = None) -> Path:
    project_file = project_file.resolve()
    if project_file.suffix.lower() != ".uefnproject" or not project_file.is_file():
        raise ValueError("Select an existing .uefnproject created by the UEFN editor.")
    json.loads(project_file.read_text(encoding="utf-8-sig"))
    candidates = []
    for plugin in (project_file.parent / "Plugins").glob("*/*.uplugin"):
        plugin = within(plugin, project_file.parent)
        metadata = json.loads(plugin.read_text(encoding="utf-8-sig"))
        if metadata.get("CanContainContent") is True:
            if plugin_name is None or plugin.stem == plugin_name:
                candidates.append(plugin)
    if len(candidates) != 1:
        raise ValueError("Expected one content plugin; select it explicitly with --plugin-name.")
    if not SAFE_NAME.fullmatch(candidates[0].stem):
        raise ValueError("Content plugin name is not a safe Unreal package identifier.")
    return candidates[0]

def source_plan(source_root: Path) -> list[tuple[Path, str]]:
    source_root = source_root.resolve()
    files = sorted((source_root / "verse").rglob("*.verse"))
    if not files:
        raise ValueError("No Verse sources found.")
    seen = set()
    result = []
    for path in files:
        within(path, source_root)
        name = path.name.casefold()
        if name in seen:
            raise ValueError(f"Duplicate flattened Verse filename: {path.name}")
        seen.add(name)
        result.append((path, path.name))
    return result

# These contracts are copied alongside the geometry so the editor handoff is
# traceable to the exact source revision. They are NOT editor/Launch Session proof.
SLICE_CONTRACTS = (
    "first_playable_rig.json",
    "slice_001_uefn_bindings.json",
    "slice_001_launch_tests.json",
)

def inspect_slice_handoff(source_root: Path) -> dict | None:
    folder = source_root / "content" / "vertical_slice"
    if not folder.exists():
        return None  # Standalone Verse-only source trees remain installable.
    if not folder.is_dir():
        raise ValueError("Slice handoff path is not a directory.")
    contracts = {}
    for name in SLICE_CONTRACTS:
        path = within(folder / name, source_root)
        if not path.is_file():
            raise ValueError(f"Missing required slice handoff contract: {name}")
        contracts[name] = json.loads(path.read_text(encoding="utf-8"))
    rig, bindings, launch = (contracts[name] for name in SLICE_CONTRACTS)
    if bindings.get("slice_id") != "SLICE-001" or launch.get("slice_id") != "SLICE-001":
        raise ValueError("Slice handoff contracts disagree on SLICE-001.")
    devices = rig.get("devices")
    if not isinstance(devices, list) or not devices:
        raise ValueError("First playable rig has no devices.")
    by_id = {}
    for device in devices:
        device_id = device.get("id")
        if not isinstance(device_id, str) or not device_id or device_id in by_id:
            raise ValueError("First playable rig has duplicate/empty device IDs.")
        by_id[device_id] = device
    for device in devices:
        for dependency in device.get("depends_on", []):
            if dependency not in by_id or dependency == device["id"]:
                raise ValueError(f"Invalid rig dependency: {device['id']} -> {dependency}")
        source_path = device.get("source_path")
        if source_path:
            source = within(source_root / source_path, source_root)
            if not source.is_file():
                raise ValueError(f"Missing Verse source for rig device: {device['id']}")
    encounter_id = rig.get("encounter_id")
    if encounter_id not in {item.get("id") for item in bindings.get("encounters", [])}:
        raise ValueError("First playable encounter is absent from UEFN bindings.")
    directors = [device for device in devices
                 if device.get("type") == "aeonfall_encounter_director_device"]
    if len(directors) != 1:
        raise ValueError("First playable rig requires exactly one encounter director.")
    director = directors[0]
    if director.get("editable_values", {}).get("EncounterId") != encounter_id:
        raise ValueError("Rig director EncounterId disagrees with its contract.")
    refs = set()
    def require_ref(ref, expected, role):
        device = by_id.get(ref)
        if device is None or device.get("type") != expected:
            raise ValueError(f"Invalid {role} reference: {ref} (expected {expected})")
        if ref in refs:
            raise ValueError(f"Physical device reused by multiple encounter roles: {ref}")
        refs.add(ref)
    config = director.get("bindings", {})
    for field, expected in (
        ("StartInput", "trigger_device"), ("FailInput", "trigger_device"),
        ("ParticipantVolume", "volume_device"),
        ("CompletedOutput", "trigger_device"), ("FailedOutput", "trigger_device"),
    ):
        require_ref(config.get(field), expected, field)
    for ref in config.get("BossSpawners", []):
        require_ref(ref, "npc_spawner_device", "BossSpawners")
    phases = config.get("Phases", [])
    if not phases or len({p.get("phase_id") for p in phases}) != len(phases):
        raise ValueError("Rig encounter phases are missing or duplicated.")
    for phase in phases:
        label = phase["phase_id"]
        require_ref(phase.get("enter_ref"), "trigger_device", label + ".enter")
        require_ref(phase.get("cleanup_ref"), "trigger_device", label + ".cleanup")
        for item in phase.get("inputs", []):
            kind = item.get("source")
            if kind not in ("TriggerGraph", "PropDestroyed"):
                raise ValueError(f"Unknown encounter input source: {kind}")
            expected = "prop_manipulator_device" if kind == "PropDestroyed" else "trigger_device"
            require_ref(item.get("device_ref"), expected, label + ".input")
        for hazard in phase.get("hazards", []):
            require_ref(hazard.get("enable_ref"), "trigger_device", label + ".hazard_enable")
            require_ref(hazard.get("disable_ref"), "trigger_device", label + ".hazard_disable")
            for ref in hazard.get("damage_volume_refs", []):
                require_ref(ref, "damage_volume_device", label + ".hazard_volume")
        for group in phase.get("spawn_groups", []):
            for ref in group.get("spawner_refs", []):
                require_ref(ref, "npc_spawner_device", label + ".spawn_group")
    tests = launch.get("tests", [])
    if not isinstance(tests, list) or not tests:
        raise ValueError("Launch acceptance tests are missing.")
    test_ids = [item.get("id") for item in tests]
    if any(not isinstance(t, str) or not t for t in test_ids) or len(test_ids) != len(set(test_ids)):
        raise ValueError("Launch acceptance test IDs are missing or duplicated.")
    return {
        "state": "contracts_validated_editor_unbound",
        "rig_id": rig.get("rig_id"),
        "encounter_id": encounter_id,
        "rig_device_count": len(devices),
        "physical_encounter_roles": len(refs),
        "phase_count": len(phases),
        "launch_test_count": len(tests),
        "binding_counts": {key: len(bindings.get(key, [])) for key in
                           ("weapons", "monsters", "tameables", "hireables", "encounters", "vehicles")},
        "contracts": [f"content/vertical_slice/{name}" for name in SLICE_CONTRACTS],
        "uefn_compile": "not_run",
        "device_placement": "not_run",
        "launch_session": "not_run",
    }

def install(project_file: Path, source_root: Path = ROOT, plugin_name: str | None = None,
            dry_run: bool = False) -> dict:
    plugin = discover_plugin(project_file, plugin_name)
    project_root = project_file.resolve().parent
    sources = source_plan(source_root)
    handoff = inspect_slice_handoff(source_root)
    destination = writable_path(plugin.parent / "Content" / "AEONFALL", project_root)
    package = writable_path(project_root / "AEONFALLImportPackage", project_root)
    inventory_path = destination / "aeonfall-install.json"
    writable_path(inventory_path, project_root)
    previous = json.loads(inventory_path.read_text()) if inventory_path.exists() else {"files": {}}
    # Every plan is validated before any mutation; existing symlinks may not
    # redirect source installation outside the selected project.
    plan = []
    for source, name in sources:
        target = writable_path(destination / name, project_root)
        if target.exists() and not target.is_file():
            raise ValueError(f"Destination is not a regular file: {target}")
        plan.append((source, target, digest(source)))
    stale = []
    wanted = {name for _, name in sources}
    for name, old_hash in previous.get("files", {}).items():
        if Path(name).name != name or not name.endswith(".verse"):
            raise ValueError("Unsafe filename in previous install inventory.")
        if name not in wanted:
            path = writable_path(destination / name, project_root)
            if path.exists():
                if not path.is_file() or digest(path) != old_hash:
                    raise ValueError(f"Edited stale source requires manual resolution: {path}")
                stale.append((path, old_hash))
    imports = []
    for relative in ["assets/source/ossuary_starter", "tools/uefn_editor", "docs", "content/vertical_slice"]:
        candidate = source_root / relative
        if candidate.is_dir():
            for item in sorted(candidate.rglob("*")):
                if item.is_file() and "__pycache__" not in item.parts:
                    within(item, source_root)
                    target = writable_path(package / item.relative_to(source_root), project_root)
                    imports.append((item, target))
        elif candidate.is_file():
            within(candidate, source_root)
            imports.append((candidate, writable_path(package / relative, project_root)))
    for source, target in imports:
        if target.exists() and not target.is_file():
            raise ValueError(f"Import destination is not a regular file: {target}")
    writable_path(package / "editor_config.json", project_root)
    summary = {"project": str(project_file.resolve()), "plugin": plugin.stem,
               "verse_directory": str(destination), "source_count": len(plan),
               "changed_sources": sum(not p.exists() or digest(p) != h for _, p, h in plan),
               "import_files": len(imports), "dry_run": dry_run,
               "editor_script": str(package / "tools/uefn_editor/build_ossuary_level.py"),
               "slice_handoff": handoff}
    if dry_run:
        return summary
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backups = writable_path(project_root / "AEONFALLBackups" / stamp, project_root)
    def preserve(path: Path) -> None:
        target = writable_path(backups / path.relative_to(project_root), project_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    destination.mkdir(parents=True, exist_ok=True)
    package.mkdir(parents=True, exist_ok=True)
    for source, target, source_hash in plan:
        if target.exists():
            if digest(target) == source_hash:
                continue
            preserve(target)
        shutil.copy2(source, target)
    for path, old_hash in stale:
        # Remove only an unedited source we previously installed. Edited stale
        # files are preserved and surfaced for the creator to resolve.
        if digest(path) == old_hash:
            preserve(path)
            path.unlink()
        else:
            raise ValueError(f"Edited stale source requires manual resolution: {path}")
    for source, target in imports:
        if target.exists() and digest(source) != digest(target):
            preserve(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    inventory_path.write_text(json.dumps({"files": {p.name: h for _, p, h in plan},
                                        "source_layout": "one_flat_verse_module"}, indent=2))
    (package / "editor_config.json").write_text(json.dumps({
        "plugin_name": plugin.stem, "project_file": str(project_file.resolve()),
        "manifest": "assets/source/ossuary_starter/manifest.json",
        "asset_namespace": "AEONFALL", "editor_execution": "pending",
        "slice_contracts": handoff["contracts"] if handoff else [],
        "slice_handoff_state": handoff["state"] if handoff else "unavailable"
    }, indent=2))
    summary["backup_directory"] = str(backups) if backups.exists() else None
    return summary

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--plugin-name")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(install(args.project, args.source_root, args.plugin_name, args.dry_run), indent=2))
    except (ValueError, OSError, json.JSONDecodeError) as error:
        parser.exit(1, f"AEONFALL install failed: {error}\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
