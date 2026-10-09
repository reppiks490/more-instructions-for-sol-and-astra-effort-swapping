#!/usr/bin/env python3
"""Package exact Git-indexed source and explicit verification provenance.

This is a source/import bundle, not an editor-produced UEFN project or island.
No untracked files, symlinks, modified indexed files, or .git data are included.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import zipfile


class BundleError(ValueError):
    pass


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args])


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data: bytes, algorithm: str) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.new(algorithm, header + data).hexdigest()


def tracked_sources(root: Path) -> list[tuple[str, str, bytes]]:
    root = root.resolve(strict=True)
    algorithm = git(root, "rev-parse", "--show-object-format").decode().strip()
    records = git(root, "ls-files", "--stage", "-z").split(b"\0")
    sources = []
    seen = set()
    for record in records:
        if not record:
            continue
        metadata, path_bytes = record.split(b"\t", 1)
        mode, object_sha, stage = metadata.decode("ascii").split()
        name = path_bytes.decode("utf-8", errors="strict")
        relative = PurePosixPath(name)
        if (mode not in {"100644", "100755"} or stage != "0"
                or relative.is_absolute() or ".." in relative.parts
                or ".git" in relative.parts or "\\" in name or ":" in name
                or not relative.parts or name in seen):
            raise BundleError(f"Unsupported or unsafe indexed path: {name!r}")
        seen.add(name)
        path = root.joinpath(*relative.parts)
        if not path.is_file() or path.is_symlink():
            raise BundleError(f"Indexed source is absent or not a regular file: {name}")
        for parent in path.parents:
            if parent == root:
                break
            if parent.is_symlink():
                raise BundleError(f"Indexed source has a symlink parent: {name}")
        if not path.resolve(strict=True).is_relative_to(root):
            raise BundleError(f"Indexed source escapes repository: {name}")
        data = path.read_bytes()
        if git_blob_sha(data, algorithm) != object_sha:
            raise BundleError(f"Indexed source bytes changed: {name}")
        sources.append((name, object_sha, data))
    if not sources:
        raise BundleError("Repository has no indexed source files")
    return sorted(sources)


def verify_bundle(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise BundleError("Archive CRC verification failed")
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise BundleError("Archive contains duplicate names")
        prefix = "AEONFALL/"
        manifest = json.loads(archive.read(prefix + "SOURCE_MANIFEST.json"))
        provenance = json.loads(archive.read(prefix + "BUILD_PROVENANCE.json"))
        expected = {prefix + row["path"] for row in manifest["files"]}
        expected.update({prefix + "SOURCE_MANIFEST.json",
                         prefix + "BUILD_PROVENANCE.json", prefix + "CHECKSUMS.sha256"})
        if set(names) != expected:
            raise BundleError("Archive inventory differs from manifest")
        for row in manifest["files"]:
            data = archive.read(prefix + row["path"])
            if len(data) != row["bytes"] or sha256(data) != row["sha256"]:
                raise BundleError(f"Archive source hash differs: {row['path']}")
        checksums = archive.read(prefix + "CHECKSUMS.sha256").decode().splitlines()
        if len(checksums) != len(names) - 1:
            raise BundleError("Checksum inventory is incomplete")
        checksum_names = set()
        for line in checksums:
            expected_hash, name = line.split("  ", 1)
            if name in checksum_names:
                raise BundleError("Duplicate checksum name")
            checksum_names.add(name)
            if sha256(archive.read(name)) != expected_hash:
                raise BundleError(f"Archive checksum differs: {name}")
        if checksum_names != set(names) - {prefix + "CHECKSUMS.sha256"}:
            raise BundleError("Checksum paths differ from archive inventory")
        return {"source_files": len(manifest["files"]), "commit": provenance["commit"],
                "tree": provenance["tree"], "sha256": sha256(path.read_bytes())}


def build_bundle(root: Path, output: Path, verification: str = "not_run",
                 run_url: str = "") -> dict:
    root = root.resolve(strict=True)
    sources = tracked_sources(root)
    reserved = {"SOURCE_MANIFEST.json", "BUILD_PROVENANCE.json", "CHECKSUMS.sha256"}
    if any(name in reserved for name, _, _ in sources):
        raise BundleError("A tracked path conflicts with bundle metadata")
    head_tree = git(root, "rev-parse", "HEAD^{tree}").decode().strip()
    index_tree = git(root, "write-tree").decode().strip()
    if index_tree != head_tree:
        raise BundleError("Index differs from the committed tree")
    commit = git(root, "rev-parse", "HEAD").decode().strip()
    provenance = {
        "format_version": 1,
        "kind": "UEFN source and import package",
        "commit": commit,
        "tree": head_tree,
        "source_checks": {"result": verification, "workflow_run_url": run_url},
        "uefn_editor_import": "not_run",
        "verse_engine_compile": "not_run",
        "fortnite_launch_session": "not_run",
        "published_island_code": None,
    }
    manifest = {"format_version": 1, "files": [
        {"path": name, "git_blob": blob_sha, "sha256": sha256(data), "bytes": len(data)}
        for name, blob_sha, data in sources
    ]}
    prefix = "AEONFALL/"
    entries = {prefix + name: data for name, _, data in sources}
    entries[prefix + "SOURCE_MANIFEST.json"] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    entries[prefix + "BUILD_PROVENANCE.json"] = (
        json.dumps(provenance, indent=2, sort_keys=True) + "\n").encode()
    entries[prefix + "CHECKSUMS.sha256"] = "".join(
        f"{sha256(data)}  {name}\n" for name, data in sorted(entries.items())
    ).encode()
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=9) as archive:
            for name, data in sorted(entries.items()):
                info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data)
        result = verify_bundle(temporary)
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    output.with_suffix(output.suffix + ".sha256").write_text(
        f"{result['sha256']}  {output.name}\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-checks", choices=["passed", "not_run"], default="not_run")
    parser.add_argument("--run-url", default="")
    args = parser.parse_args()
    print(json.dumps(build_bundle(args.root, args.output, args.source_checks, args.run_url),
                     indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
