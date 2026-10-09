#!/usr/bin/env python3
"""Move mutable Verse service allocation into the current session.

This is a deterministic source migration, not an engine compiler. The manifest
keeps existing accessor names stable when the tool is run after regeneration.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "content/runtime/session_services.json"
DECLARATION = re.compile(
    r"^(?P<name>AEONFALL\w+):(?P<type>\w+)\s*=\s*"
    r"(?P<constructor>\w+)\{\}[ \t]*(?:\n|$)", re.MULTILINE
)
CLASS_HEADER = re.compile(r"^(\w+)\s*:=\s*class[^\n]*\n", re.MULTILINE)
SESSION_DECLARATION = re.compile(
    r"^var (AEONFALL\w+Sessions):weak_map\(session, (\w+)\) = map\{\}$", re.MULTILINE
)


@dataclass(frozen=True)
class Service:
    name: str
    type: str
    path: str

    @property
    def getter(self) -> str:
        return "Get" + self.name

    @property
    def sessions(self) -> str:
        return self.name + "Sessions"


def class_bodies(sources: dict[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for source in sources.values():
        for match in CLASS_HEADER.finditer(source):
            following = source[match.end():]
            end = re.search(r"^[^\s#]", following, re.MULTILINE)
            result[match.group(1)] = following[:end.start()] if end else following
    return result


def mutable_classes(sources: dict[str, str]) -> set[str]:
    """Include indirect mutable default allocations, not just a class's vars."""
    bodies = class_bodies(sources)
    mutable = {name for name, body in bodies.items() if re.search(r"^    var ", body, re.MULTILINE)}
    dependencies = {
        name: set(re.findall(r"^    \w+:(\w+)\s*=", body, re.MULTILINE))
        for name, body in bodies.items()
    }
    while True:
        more = {name for name, deps in dependencies.items() if deps & mutable}
        if more <= mutable:
            return mutable
        mutable |= more


def discover(sources: dict[str, str]) -> list[Service]:
    mutable = mutable_classes(sources)
    return sorted(
        (Service(match["name"], match["type"], path)
         for path, source in sources.items()
         for match in DECLARATION.finditer(source)
         if match["type"] in mutable),
        key=lambda service: service.name,
    )


def accessor(service: Service) -> str:
    return f"""# Mutable service allocation is scoped to the current Verse session.
var {service.sessions}:weak_map(session, {service.type}) = map{{}}

{service.getter}()<transacts>:{service.type}=
    CurrentSession := GetSession()
    if (Existing := {service.sessions}[CurrentSession]):
        return Existing
    Created := {service.type}{{}}
    if (set {service.sessions}[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain {service.name} in its session")
"""


def rewrite_references(source: str, services: list[Service]) -> str:
    if not services:
        return source
    replacements = {service.name: service.getter + "()" for service in services}
    names = "|".join(re.escape(name) for name in sorted(replacements, key=len, reverse=True))
    return re.sub(r"\b(?:" + names + r")\b", lambda match: replacements[match.group()], source)


def migrate(sources: dict[str, str], services: list[Service]) -> dict[str, str]:
    output = dict(sources)
    for service in services:
        source = output[service.path]
        pattern = re.compile(
            r"^" + re.escape(service.name) + ":" + re.escape(service.type)
            + r"\s*=\s*" + re.escape(service.type) + r"\{\}[ \t]*(?:\n|$)",
            re.MULTILINE,
        )
        source, changed = pattern.subn(accessor(service), source)
        if changed:
            for module in ("/Verse.org/Simulation", "/Verse.org/Verse"):
                import_line = "using { " + module + " }"
                if import_line not in source:
                    source = import_line + "\n" + source
            output[service.path] = source
    for path, source in output.items():
        output[path] = rewrite_references(source, services)
    # Rewriting exact names must not alter diagnostic strings inside generated
    # accessors, otherwise a second migration pass would change their bytes.
    for service in services:
        output[service.path] = output[service.path].replace(
            f"retain {service.getter}() in its session", f"retain {service.name} in its session"
        )
    return output


def read_sources(root: Path = ROOT) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
            for path in sorted((root / "verse").rglob("*.verse"))}


def load_services(root: Path, sources: dict[str, str]) -> list[Service]:
    path = root / MANIFEST
    existing = []
    if path.exists():
        existing = [Service(**row) for row in json.loads(path.read_text())["services"]]
    by_name = {service.name: service for service in existing}
    by_name.update({service.name: service for service in discover(sources)})
    return sorted(by_name.values(), key=lambda service: service.name)


def validate_sources(sources: dict[str, str], services: list[Service] | None = None) -> list[str]:
    errors = []
    for service in discover(sources):
        errors.append(f"{service.path}: mutable module-scope allocation {service.name}")
    for path, source in sources.items():
        code = "\n".join(line.split("#", 1)[0] for line in source.splitlines())
        for forbidden in ("FitsInPlayerMap(", ".GetFortCharacter("):
            if forbidden in code:
                errors.append(f"{path}: native failable call must use []: {forbidden}")
        # A successful query followed by the same bare comparison is not a
        # valid void body. Keep the result capture; remove the empty branch.
        if re.search(r"(?m)^( +)if \((\w+)\?\):\n\1    \2 = true\s*$", code):
            errors.append(f"{path}: bare no-op comparison outside a failure context")
        if re.search(r"(?m)^    \w+:[^\n=]+ = GetAEONFALL\w+\(\)", code):
            errors.append(f"{path}: class defaults must not resolve transactional session services")
        if "GetAEONFALLBusState()<transacts>:" in code:
            found = re.search(
                r"(?m)^GetAEONFALLBusState\(\)<transacts>:[^\n]+\n(?P<body>(?:[ \t].*\n|\n)*)",
                code + "\n",
            )
            if not found or "Err(" not in found["body"]:
                errors.append(f"{path}: event bus retention failure must fail with Err")
        for match in SESSION_DECLARATION.finditer(code):
            sessions, service_type = match.groups()
            name = sessions[:-len("Sessions")]
            getter = "Get" + name
            pattern = re.compile(r"^" + getter + r"\(\)<transacts>:" + service_type + r"=\n(?P<body>(?:[ \t].*\n|\n)*)", re.MULTILINE)
            found = pattern.search(code + "\n")
            if not found:
                errors.append(f"{path}: missing transactional session accessor {getter}")
                continue
            body = found["body"]
            for required in (
                "CurrentSession := GetSession()",
                f"Existing := {sessions}[CurrentSession]",
                f"Created := {service_type}{{}}",
                f"set {sessions}[CurrentSession] = Created",
                "return Existing", "return Created", "Err(",
            ):
                if required not in body:
                    errors.append(f"{path}: {getter} lacks retained-session guard {required}")
            if re.search(r"(?m)^    " + re.escape(service_type) + r"\{", body):
                errors.append(f"{path}: {getter} returns an unretained fallback")
    for service in services or []:
        source = sources.get(service.path, "")
        if service.getter + "()<transacts>:" + service.type not in source:
            errors.append(f"{service.path}: registered session accessor is absent: {service.getter}")
        for path, candidate in sources.items():
            # Strings include diagnostic names. A stale executable identifier
            # is any occurrence outside strings/comments.
            code = re.sub(r'"(?:[^"\\]|\\.)*"', '""', candidate)
            code = "\n".join(line.split("#", 1)[0] for line in code.splitlines())
            if re.search(r"\b" + re.escape(service.name) + r"\b", code):
                errors.append(f"{path}: stale mutable service reference {service.name}")
    return errors


def plan(root: Path = ROOT) -> tuple[dict[str, str], list[Service]]:
    verse = read_sources(root)
    services = load_services(root, verse)
    changes = migrate(verse, services)
    # Generators and their source-level regression guards must use the same
    # accessors so regeneration and mutation tests continue to be meaningful.
    python_sources = sorted((root / "tools").glob("*.py")) + sorted((root / "tests").glob("*.py"))
    for path in python_sources:
        if path.name == Path(__file__).name:
            continue
        original = path.read_text(encoding="utf-8")
        # These guards intentionally normalize both accessor and legacy source
        # into legacy identifiers before matching their fragments. Their
        # expected fragments must remain in that normalized representation.
        if "def normalized(source: str)" in original:
            continue
        changes[path.relative_to(root).as_posix()] = rewrite_references(original, services)
    changes[MANIFEST] = json.dumps({"schema_version": 1, "services": [
        {"name": service.name, "type": service.type, "path": service.path}
        for service in services]}, indent=2) + "\n"
    return {path: content for path, content in changes.items()
            if not (root / path).exists() or (root / path).read_text(encoding="utf-8") != content}, services


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    changes, services = plan(args.root)
    if args.write:
        for path, content in changes.items():
            destination = args.root / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")
    errors = validate_sources(read_sources(args.root), services) if args.check or args.write else []
    print(f"Session service migration: {len(services)} services; {len(changes)} files {'written' if args.write else 'need migration'}")
    for error in errors:
        print(error)
    if args.check and changes:
        print("SESSION MIGRATION FAILED: generated references or manifest differ")
        return 1
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
