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

def install(project_file: Path, source_root: Path = ROOT, plugin_name: str | None = None,
            dry_run: bool = False) -> dict:
    plugin = discover_plugin(project_file, plugin_name)
    project_root = project_file.resolve().parent
    sources = source_plan(source_root)
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
    for relative in ["assets/source/ossuary_starter", "tools/uefn_editor", "docs"]:
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
               "editor_script": str(package / "tools/uefn_editor/build_ossuary_level.py")}
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
        "asset_namespace": "AEONFALL", "editor_execution": "pending"
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
