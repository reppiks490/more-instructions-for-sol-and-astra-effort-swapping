#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

from migrate_session_services import load_services, read_sources, validate_sources as validate_session_sources

ROOT = Path(__file__).resolve().parents[1]
VERSE = ROOT / "verse"

FORBIDDEN_PRODUCTION_IMPORTS = (
    "/Fortnite.com/Abilities",
    "/UnrealEngine.com/Abilities",
)

def noncomment_lines(text: str):
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            yield line

def check_empty_blocks(path: Path, text: str, errors: list[str]):
    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped not in {"then:", "else:", "loop:"}:
            continue

        indent = len(line) - len(line.lstrip())
        found_body = False
        for following in lines[i + 1:]:
            s = following.strip()
            if not s or s.startswith("#"):
                continue
            next_indent = len(following) - len(following.lstrip())
            if next_indent > indent:
                found_body = True
            break

        if not found_body:
            errors.append(f"{path.relative_to(ROOT)}:{i+1}: empty {stripped} block")

def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    files = sorted(VERSE.rglob("*.verse"))

    if not files:
        errors.append("no Verse source files found")

    persistent_roots = 0

    sources = read_sources(ROOT)
    errors.extend(validate_session_sources(sources, load_services(ROOT, sources)))

    for path in files:
        text = path.read_text(encoding="utf-8")

        if "experimental_adapters/" not in str(path).replace("\\", "/"):
            for forbidden in FORBIDDEN_PRODUCTION_IMPORTS:
                if forbidden in text:
                    errors.append(
                        f"{path.relative_to(ROOT)}: production Verse imports currently unpublishable Ability API {forbidden}"
                    )

        check_empty_blocks(path, text, errors)

        if "weak_map(player," in text:
            persistent_roots += text.count("weak_map(player,")

        for line_no, line in enumerate(text.splitlines(), start=1):
            if re.search(r"\bloop\s*:", line) and "Sleep(" not in text:
                warnings.append(
                    f"{path.relative_to(ROOT)}:{line_no}: loop exists but file contains no Sleep(); review for runaway loop"
                )

        if "spawn{" in text and not any(
            token in text for token in ("cleanup", "Cleanup", "OnEnd", "Cancel", "Dispose", "Remove")
        ):
            warnings.append(
                f"{path.relative_to(ROOT)}: spawn{{}} used without an obvious cleanup/cancel symbol"
            )

    if persistent_roots > 1:
        errors.append(
            f"found {persistent_roots} player weak_map roots; AEONFALL policy allows one primary persistent player root"
        )

    print("AEONFALL Verse static validation")
    print(f"- Verse files: {len(files)}")
    print(f"- player weak_map roots: {persistent_roots}")
    print(f"- warnings: {len(warnings)}")
    for warning in warnings:
        print(f"WARNING: {warning}")

    if errors:
        print("VERSE STATIC VALIDATION FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("VERSE STATIC VALIDATION PASSED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
