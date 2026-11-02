#!/usr/bin/env python3
"""Audit the ENTIRE AEONFALL universe before prioritizing a playable prototype.

This is an honest source/delivery ledger: catalog *specifications* are not
shippable assets; source bundles do not establish native UEFN compilation.
Every catalog entity and required region/system is enumerated without samples.
"""
from __future__ import annotations

import argparse
import hashlib
from collections import Counter
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
POLICY = "content/implementation/universe_first_policy.json"
INVENTORY = "content/implementation/universe_source_delivery_inventory.json"
EVIDENCE = "content/implementation/implementation_evidence.json"
TOPOLOGY = "content/world/world_topology.json"
CATALOG = "content/catalog"

APPROVED = "approved_source"
NATIVE_FIELDS = (
    "uefn_asset_bound", "verse_compiled", "launch_session_verified",
    "multiplayer_verified", "cleanup_verified", "performance_profiled",
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def real_file(root: Path, relative: str) -> bool:
    if not isinstance(relative, str) or not relative.strip():
        return False
    path = Path(relative)
    if path.is_absolute() or any(piece in ("..", "") for piece in path.parts):
        return False
    resolved = (root / path).resolve()
    return (resolved.is_relative_to(root.resolve()) and resolved.is_file()
            and resolved.stat().st_size > 0)


def complete_value(value) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value) and all(complete_value(item) for item in value)
    if isinstance(value, dict):
        return bool(value)
    return value is not None


def catalog_scan(root: Path, policy: dict):
    entities = {}
    errors = []
    counters = Counter()
    statuses = Counter()
    files = sorted((root / CATALOG).glob("wave_*.json"))
    if not files:
        errors.append("No canonical wave_*.json catalog files found.")
    for path in files:
        payload = read_json(path)
        if isinstance(payload, list):
            items = payload
        elif isinstance(payload, dict):
            items = payload.get("entities", [])
        else:
            errors.append(f"{path.name}: malformed catalog payload {type(payload).__name__}")
            continue
        if not isinstance(items, list):
            errors.append(f"{path.name}: non-list entities payload")
            continue
        for item in items:
            if not isinstance(item, dict):
                errors.append(f"{path.name}: non-object entity")
                continue
            ident = item.get("id")
            if not isinstance(ident, str) or not re.fullmatch(r"[A-Z]{3}-[0-9]{3,4}", ident):
                errors.append(f"{path.name}: missing/invalid entity ID {ident!r}")
                continue
            if ident in entities:
                errors.append(f"Duplicate canonical entity ID: {ident}")
                continue
            entities[ident] = item
            family = item.get("family")
            if not isinstance(family, str):
                errors.append(f"{ident}: malformed content family {family!r}")
                family = None
            else:
                counters[family] += 1
            status = item.get("status")
            if not isinstance(status, str):
                errors.append(f"{ident}: malformed catalog status {status!r}")
            else:
                statuses[status] += 1
            if family not in policy["entity_source_categories"]:
                errors.append(f"{ident}: unsupported content family {family!r}")
            for key in policy["required_catalog_fields"]:
                if not complete_value(item.get(key)):
                    errors.append(f"{ident}: incomplete catalog specification field {key}")
            for group, keys in (
                ("identity", policy["required_identity_fields"]),
                ("mechanics", policy["required_mechanics_fields"]),
                ("presentation", policy["required_presentation_fields"]),
                ("performance", policy["required_performance_fields"]),
            ):
                value = item.get(group)
                if not isinstance(value, dict):
                    errors.append(f"{ident}: missing {group} object")
                    continue
                for key in keys:
                    if not complete_value(value.get(key)):
                        errors.append(f"{ident}: incomplete {group}.{key}")
    quota_counts = dict(counters)
    quota_counts["class_skill"] = counters["class"] + counters["skill"]
    for family, target in policy["minimum_family_counts"].items():
        if quota_counts.get(family, 0) < target:
            errors.append(f"Under minimum {family}: {quota_counts.get(family, 0)} / {target}")
    if sum(counters.values()) < policy["minimum_major_entities"]:
        errors.append("Under 800 major-entity universe minimum")
    return entities, counters, statuses, files, errors


def inspect_package(root: Path, item: dict, key: str, valid_ids: set[str],
                    required: dict[str, list[str]], require_region: bool,
                    region_ids: set[str]):
    errors = []
    ident = item.get(key)
    if not isinstance(ident, str) or ident not in valid_ids:
        errors.append(f"Unknown {key} {ident!r} in source registry")
        return False, errors
    categories = required.get(ident, [])
    sources = item.get("sources")
    if not isinstance(sources, dict):
        return False, [f"{ident}: missing source-category map"]
    extra = set(sources) - set(categories)
    if extra:
        errors.append(f"{ident}: unexpected source categories {sorted(extra)}")
    complete = True
    all_paths = []
    for category in categories:
        paths = sources.get(category)
        if not isinstance(paths, list) or not paths:
            complete = False
            continue
        for path in paths:
            if not real_file(root, path):
                errors.append(f"{ident}/{category}: missing/unsafe source path {path!r}")
                complete = False
            else:
                all_paths.append(path)
    if len(all_paths) != len(set(all_paths)):
        errors.append(f"{ident}: duplicated evidence paths across categories")
        complete = False
    if require_region:
        regions = item.get("regions")
        if not isinstance(regions, list) or not regions:
            errors.append(f"{ident}: no explicit region scope")
            complete = False
        else:
            for region in regions:
                if not isinstance(region, str) or (region not in region_ids and region != "GLOBAL"):
                    errors.append(f"{ident}: unrecognized region scope {region!r}")
                    complete = False
    # Review is an explicit governance claim, NOT proof of native UEFN play.
    review = item.get("source_review")
    if not isinstance(review, dict) or review.get("state") != APPROVED:
        complete = False
    else:
        if not complete_value(review.get("reviewer")) or not complete_value(review.get("evidence")):
            errors.append(f"{ident}: unsubstantiated source review")
            complete = False
    if item.get("native_uefn_verified") is True or item.get("publicly_playable") is True:
        errors.append(f"{ident}: source delivery falsely claims native/playable verification")
        complete = False
    return complete and not errors, errors



def source_payload_fingerprint(root: Path, paths: list[str]) -> tuple[str, ...]:
    """Content identity, not filenames: cloned files cannot inflate source coverage.

    Chunked SHA-256 avoids loading high-resolution meshes/textures into RAM.
    Called only after inspect_package validates real local paths.
    """
    digests = []
    for relative in paths:
        digest = hashlib.sha256()
        with (root / relative).open("rb") as asset:
            for chunk in iter(lambda: asset.read(1024 * 1024), b""):
                digest.update(chunk)
        digests.append(digest.hexdigest())
    return tuple(sorted(digests))


def inspect_inventory(root: Path, policy: dict, inventory: dict,
                      entities: dict, region_ids: set[str], system_ids: set[str]):
    errors = []
    if inventory.get("schema_version") != 1:
        errors.append("Unsupported source inventory schema")
    catalogs = {
        "entity_packs": (
            "canonical_id", set(entities),
            {ident: policy["entity_source_categories"].get(
                entity.get("family") if isinstance(entity.get("family"), str) else None, []
            ) for ident, entity in entities.items()},
            True,
        ),
        "region_packs": (
            "region_id", region_ids,
            {ident: policy["region_source_categories"] for ident in region_ids},
            False,
        ),
        "system_packs": (
            "system_id", system_ids,
            {ident: policy["required_system_source_categories"] for ident in system_ids},
            False,
        ),
    }
    approvals = {}
    for collection, (key, ids, categories, require_region) in catalogs.items():
        packages = inventory.get(collection)
        if not isinstance(packages, list):
            errors.append(f"{collection}: expected a list")
            packages = []
        seen = set()
        ready = set()
        approved_visual_keys = {}
        approved_source_fingerprints = {}
        for package in packages:
            if not isinstance(package, dict):
                errors.append(f"{collection}: non-object source package")
                continue
            ident = package.get(key)
            if not isinstance(ident, str):
                errors.append(f"{collection}: malformed {key} {ident!r}")
                continue
            if ident in seen:
                errors.append(f"{collection}: duplicate source package for {ident!r}")
                continue
            seen.add(ident)
            # Entity region scopes are validated against the actual world,
            # not against content entity IDs.
            complete, problems = inspect_package(
                root, package, key, ids, categories, require_region, region_ids
            )
            errors.extend(problems)
            if complete:
                if require_region:
                    visual_key = package.get("unique_visual_key")
                    if not isinstance(visual_key, str) or not visual_key.strip():
                        errors.append(f"{ident}: missing/invalid unique_visual_key")
                        continue
                    normalized_key = visual_key.strip().casefold()
                    previous = approved_visual_keys.get(normalized_key)
                    if previous is not None:
                        errors.append(
                            f"{ident}: duplicate unique_visual_key shared with {previous}"
                        )
                        continue
                    approved_visual_keys[normalized_key] = ident

                # Cross-pack source provenance: same bytes under different paths
                # are not two independently authored visual/terrain identities.
                # Other categories MAY share validated family runtime/assets.
                signature_category = (
                    "terrain" if collection == "region_packs" else
                    "visual" if "visual" in categories.get(ident, []) else
                    "visual_identity" if "visual_identity" in categories.get(ident, []) else
                    None
                )
                if signature_category is not None:
                    fingerprints = source_payload_fingerprint(
                        root, package["sources"][signature_category]
                    )
                    signature = (signature_category, fingerprints)
                    other = approved_source_fingerprints.get(signature)
                    if other is not None:
                        errors.append(
                            f"{ident}: cloned {signature_category} source payload shared with {other}"
                        )
                        continue
                    approved_source_fingerprints[signature] = ident
                ready.add(ident)
        approvals[collection] = {"approved": len(ready), "total": len(ids),
                                 "pending": sorted(ids - ready), "approved_ids": sorted(ready)}
    # No global claim of a completed native island can originate here.
    if inventory.get("native_complete") is True or inventory.get("island_published") is True:
        errors.append("Source inventory must not claim published/native completion")
    return approvals, errors


def audit(root: Path = ROOT, *, policy_override=None, inventory_override=None):
    root = root.resolve()
    policy = policy_override if policy_override is not None else read_json(root / POLICY)
    inventory = inventory_override if inventory_override is not None else read_json(root / INVENTORY)
    world = read_json(root / TOPOLOGY)
    ledger = read_json(root / EVIDENCE)
    errors = []
    if policy.get("schema_version") != 1:
        errors.append("Unsupported universe-first policy version")
    if policy.get("strategy") != "full_universe_source_before_playable_prototype":
        errors.append("Universe-first strategy changed without explicit review")
    if policy.get("no_cutdown_scope") is not True or policy.get("no_codex_in_automation") is not True:
        errors.append("Scope-preservation or Codex prohibition policy changed")
    if policy.get("source_complete_does_not_imply_native_complete") is not True:
        errors.append("Source/native completion must remain separate")
    if policy.get("minimum_major_entities", 0) < 800 or len(policy.get("required_world_regions", [])) < 13:
        errors.append("Unauthorized reduction of universe scope")
    entities, families, statuses, files, catalog_errors = catalog_scan(root, policy)
    errors.extend(catalog_errors)

    worlds = world.get("regions", [])
    if not isinstance(worlds, list):
        errors.append("Malformed world topology: regions must be a list")
        worlds = []
    world_ids = []
    for region in worlds:
        if not isinstance(region, dict):
            errors.append("Invalid world region object")
            continue
        ident = region.get("id")
        if not isinstance(ident, str):
            errors.append(f"Malformed world region ID {ident!r}")
            continue
        world_ids.append(ident)
    if len(world_ids) != len(set(world_ids)):
        errors.append("Duplicated canonical world region ID")
    required_regions = set(policy["required_world_regions"])
    missing_regions = sorted(required_regions - set(world_ids))
    if missing_regions:
        errors.append(f"Missing canonical world regions: {missing_regions}")
    if len(world_ids) < 13:
        errors.append("World topology shrank below 13 regions")
    for region in worlds:
        if not isinstance(region, dict):
            continue
        for key in ("id", "name", "theme", "role", "neighbors", "streaming_band"):
            if not complete_value(region.get(key)):
                errors.append(f"{region.get('id')}: missing world topology {key}")
        neighbors = region.get("neighbors", [])
        if not isinstance(neighbors, list):
            errors.append(f"{region.get('id')}: malformed neighbor list")
            continue
        for neighbor in neighbors:
            if not isinstance(neighbor, str) or neighbor not in world_ids:
                errors.append(f"{region.get('id')}: unknown neighboring region {neighbor!r}")

    system_rows = policy.get("required_systems", [])
    if not isinstance(system_rows, list):
        errors.append("Malformed required systems policy")
        system_rows = []
    system_ids = set()
    for system in system_rows:
        ident = system.get("id") if isinstance(system, dict) else None
        if not isinstance(ident, str) or not ident:
            errors.append(f"Malformed required system ID {ident!r}")
        elif ident in system_ids:
            errors.append(f"Duplicate required system in universe-first policy: {ident}")
        else:
            system_ids.add(ident)
    approved, inventory_errors = inspect_inventory(root, policy, inventory, entities,
                                                     required_regions, system_ids)
    errors.extend(inventory_errors)
    evidence_entities = {x["canonical_id"]: x for x in ledger.get("entity_records", [])}
    evidence_systems = {x["system_id"]: x for x in ledger.get("system_records", [])}
    verified_entities = sum(
        all(evidence_entities.get(ident, {}).get(flag) is True for flag in NATIVE_FIELDS)
        for ident in entities
    )
    verified_systems = sum(
        all(evidence_systems.get(ident, {}).get(flag) is True
            for flag in NATIVE_FIELDS[1:])
        for ident in system_ids
    )
    native_records = sum(bool(x.get("verse_compiled")) for x in evidence_entities.values())
    native_system_records = sum(bool(x.get("verse_compiled")) for x in evidence_systems.values())
    fully_delivered = (not errors and all(group["approved"] == group["total"]
                                          for group in approved.values()))
    native_complete = (fully_delivered and verified_entities == len(entities)
                       and verified_systems == len(system_ids))
    entity_rows = []
    for ident in sorted(entities):
        entity = entities[ident]
        record = evidence_entities.get(ident)
        entity_rows.append({
            "id": ident, "name": entity.get("name"), "family": entity.get("family"),
            "tier": entity.get("tier"), "catalog_status": entity.get("status"),
            "source_package_approved": ident in approved["entity_packs"]["approved_ids"],
            "native_evidence_recorded": record is not None,
            "uefn_asset_bound_verified": bool(record and record.get("uefn_asset_bound") is True),
            "native_verse_compiled_verified": bool(record and record.get("verse_compiled") is True),
            "launch_session_verified": bool(record and record.get("launch_session_verified") is True),
        })
    return {
        "schema_version": 1, "audit_type": "full_catalog_no_samples",
        "strategy": policy["strategy"], "target_platform": policy["target_platform"],
        "source_complete": fully_delivered, "native_uefn_complete": native_complete,
        "playable_prototype_deferred": True,
        "catalog": {
            "file_count": len(files), "major_entities": len(entities),
            "minimum_target": policy["minimum_major_entities"],
            "by_family": dict(sorted(families.items())),
            "by_status": dict(sorted((str(k), v) for k, v in statuses.items())),
            "minimums": policy["minimum_family_counts"],
            "catalog_design_valid": not catalog_errors, "entity_rows": entity_rows,
        },
        "world": {
            "region_count": len(world_ids), "required_regions": sorted(required_regions),
            "regions": [{"id": item.get("id"), "name": item.get("name")}
                        for item in worlds if isinstance(item, dict)],
            "missing_regions": missing_regions,
        },
        "source_delivery": approved,
        "native_evidence": {
            "entity_evidence_records": len(evidence_entities),
            "verified_native_entities": verified_entities,
            "native_verse_compiled_entity_records": native_records,
            "system_evidence_records": len(evidence_systems),
            "native_verse_compiled_system_records": native_system_records,
            "verified_native_systems": verified_systems,
        },
        "validation_errors": errors,
        "interpretation": (
            "Source audit is not UEFN compilation, imported assets, a played session "
            "or proof of production readiness. All source packages require review."
        )
    }


def markdown(report: dict) -> str:
    catalog = report["catalog"]
    delivery = report["source_delivery"]
    world = report["world"]
    evidence = report["native_evidence"]
    out = [
        "# AEONFALL — Full-Universe Source Completion Audit",
        "",
        "**Source complete:** " + ("YES" if report["source_complete"] else "NO"),
        "**Native UEFN verified:** " + ("YES" if report["native_uefn_complete"] else "NO"),
        "**Creator directive:** Finish the full universe source before a playable prototype.",
        "",
        f"**Major entities examined without sampling:** {catalog['major_entities']}",
        f"**Catalog source files:** {catalog['file_count']}",
        f"**World regions:** {world['region_count']}",
        "",
        "## Canonical authored catalog",
        "",
        "| Content family | Definitions | Minimum |",
        "|---|---:|---:|",
    ]
    for family, count in catalog["by_family"].items():
        required = catalog["minimums"].get(family, "—")
        out.append(f"| {family} | {count} | {required} |")
    out += ["", "## File-backed source delivery", "",
            "| Scope | Reviewed source packages | Required |",
            "|---|---:|---:|"]
    for key, display in [("entity_packs", "All major entities"),
                         ("region_packs", "Every region"),
                         ("system_packs", "Cross-universe systems")]:
        row = delivery[key]
        out.append(f"| {display} | {row['approved']} | {row['total']} |")
    out += ["", "## UEFN-native proof (separate gate)", "",
            f"- Native compilation recorded for {evidence['native_verse_compiled_entity_records']} "
            f"of {evidence['entity_evidence_records']} tracked entity-evidence records.",
            f"- Fully UEFN-verified entities across entire catalog: "
            f"{evidence['verified_native_entities']} / {catalog['major_entities']}.",
            f"- Native-compiled system evidence records: "
            f"{evidence['native_verse_compiled_system_records']} / "
            f"{evidence['system_evidence_records']}.",
            "",
            "## Current blocking work", "",
            "- Produce and independently review every entity's required source categories.",
            "- Produce complete source packages for every world region and cross-universe system.",
            "- After source completeness: use actual Windows UEFN to import, compile, bind, "
            "profile and multiplayer-test the full universe.",
            "- Optimize for Fortnite mobile including streaming, LODs, "
            "touch controls, native cooked memory and runtime profiling.",
            "- Never promote source-only tests to native UEFN proof.",
            "",
            f"**Structural/policy errors:** {len(report['validation_errors'])}.",
    ]
    out += ["", "## Full coverage record", "",
            "The sibling JSON report includes **every** canonical ID, its real source "
            "delivery state and its native verification state; it is not a sample.",
            ""]
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--require-source-complete", action="store_true")
    parser.add_argument("--require-native-complete", action="store_true")
    args = parser.parse_args()
    try:
        report = audit()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("Universe audit could not inspect required source files:", error,
              file=sys.stderr)
        return 1
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown(report), encoding="utf-8")
    print(f"AEONFALL: {report['catalog']['major_entities']} canonical entities, "
          f"{report['world']['region_count']} regions, "
          f"{report['source_delivery']['entity_packs']['approved']} reviewed entity packages, "
          f"{report['native_evidence']['verified_native_entities']} native-verified entities.")
    print("Source complete:", report["source_complete"],
          "| Native verified:", report["native_uefn_complete"])
    for error in report["validation_errors"][:50]:
        print("ERROR:", error, file=sys.stderr)
    if report["validation_errors"]:
        if len(report["validation_errors"]) > 50:
            print(f"... and {len(report['validation_errors'])-50} more errors.", file=sys.stderr)
        return 1
    if args.require_source_complete and not report["source_complete"]:
        print("Full universe source-completion gate is NOT satisfied.", file=sys.stderr)
        return 2
    if args.require_native_complete and not report["native_uefn_complete"]:
        print("Native UEFN completion gate is NOT satisfied.", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
