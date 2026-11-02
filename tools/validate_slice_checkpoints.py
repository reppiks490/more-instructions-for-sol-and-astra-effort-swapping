#!/usr/bin/env python3
"""Fail-closed SLICE-001 checkpoint source/geometry contract audit.

This audits authored files only. It does not inspect placed UEFN devices, compile
Verse, or prove a Fortnite teleport occurred.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets/source/ossuary_starter/manifest.json"
CONTRACT = ROOT / "content/vertical_slice/slice_001_checkpoint_bindings.json"
VERSE = ROOT / "verse/progression/slice_001_checkpoint_device.verse"

REQUIRED_SOURCE = (
    "AEONFALLSliceCheckpointOwners",
    "ValidatePhysicalBindings()",
    "GetPhysicalDevices[]",
    "not Devices.Find[Device]",
    "Volume.AgentEntersEvent.Subscribe(Listener.OnEntered)",
    "Spawner.SpawnedEvent.Subscribe(OnSpawned)",
    "GetPlayspace().PlayerAddedEvent().Subscribe(OnPlayerAdded)",
    "GetPlayspace().PlayerRemovedEvent().Subscribe(OnPlayerRemoved)",
    "PreviousIndex < Index",
    "Old.DiscoveredPoiIds.Find[PreviousId]",
    "DiscoveredPoiIds := Old.DiscoveredPoiIds + array{Id}",
    "ProfileService.TrySaveProfile(Player, Candidate)",
    "LatestContiguousCheckpoint(Profile)",
    "Destination.Teleport(Player)",
    "SeenCharacters[Player]",
    "RestoreTokens:[player]int",
    "IsRestoreTokenCurrent(Player, Token)?",
    "ClearPendingIfCurrent(Player, Token)",
    "set RestoreTokens = map{}",
    "Subscription.Cancel()",
    "OnEnd<override>()",
)


def check_contract(manifest: dict, contract: dict, source: str) -> list[str]:
    errors: list[str] = []
    if contract.get("schema_version") != 1 or contract.get("slice_id") != "SLICE-001":
        errors.append("checkpoint schema/slice mismatch")
    if contract.get("runtime_device_class") != "aeonfall_slice_001_checkpoint_device":
        errors.append("checkpoint runtime class mismatch")
    if contract.get("persistent_profile_field") != "DiscoveredPoiIds":
        errors.append("checkpoint persistence must use the existing profile root")
    if contract.get("runtime_source") != "verse/progression/slice_001_checkpoint_device.verse":
        errors.append("checkpoint runtime path mismatch")
    spawn = contract.get("player_spawners", {})
    if spawn.get("expected_type") != "player_spawner_device" or not spawn.get("logical_ref"):
        errors.append("checkpoint player-spawner contract missing")
    if spawn.get("editor_object_paths") != []:
        errors.append("unverified player spawners must remain unplaced")
    markers = [m for m in manifest.get("markers", []) if m.get("kind") == "checkpoint"]
    by_id = {m.get("id"): m for m in markers}
    if len(markers) != 4 or len(by_id) != 4:
        errors.append("geometry must contain exactly four distinct checkpoint markers")
    checkpoints = contract.get("checkpoints", [])
    if not isinstance(checkpoints, list) or len(checkpoints) != 4:
        errors.append("exactly four ordered checkpoint bindings are required")
        checkpoints = []
    refs: set[str] = set()
    positions: set[tuple] = set()
    for index, cp in enumerate(checkpoints, 1):
        marker_id = f"CHECKPOINT-{index}"
        if cp.get("order") != index or cp.get("marker_id") != marker_id:
            errors.append(f"checkpoint {index} order/marker mismatch")
        if cp.get("persistent_id") != f"SLICE-001:{marker_id}":
            errors.append(f"checkpoint {index} persistent ID mismatch")
        marker = by_id.get(marker_id)
        if not marker or cp.get("design_anchor_location_cm") != marker.get("location_cm"):
            errors.append(f"checkpoint {index} geometry anchor mismatch")
        pos = cp.get("design_anchor_location_cm")
        if not isinstance(pos, list) or len(pos) != 3 or any(
            not isinstance(v, (int, float)) or isinstance(v, bool) for v in pos
        ):
            errors.append(f"checkpoint {index} invalid position")
        else:
            key = tuple(pos)
            if key in positions:
                errors.append(f"checkpoint {index} duplicate position")
            positions.add(key)
        for kind, expected_type in (("volume", "volume_device"), ("teleporter", "teleporter_device")):
            ref = cp.get(f"{kind}_ref")
            if cp.get(f"{kind}_type") != expected_type or ref != f"checkpoint_{index}_{kind}":
                errors.append(f"checkpoint {index} {kind} binding mismatch")
            if ref in refs:
                errors.append(f"checkpoint {index} duplicate physical ref")
            refs.add(ref)
            if cp.get(f"editor_{kind}_path") is not None:
                errors.append(f"checkpoint {index} unverified {kind} editor path")
    rules = contract.get("rules", {})
    required_rules = {
        "progression": "contiguous_only",
        "save": "checked_single_profile_copy",
        "revisit": "no_duplicate_write",
        "restore": "latest_contiguous_checkpoint_per_new_character",
        "first_spawn_without_checkpoint": "no_teleport",
        "disconnect": "clear_transient_player_state",
    }
    for name, value in required_rules.items():
        if rules.get(name) != value:
            errors.append(f"checkpoint policy mismatch: {name}")
    if contract.get("execution_evidence") != {
        "uefn_compile": "not_run",
        "device_placement": "not_run",
        "launch_session": "not_run",
    }:
        errors.append("source contract must not assert unverified editor/session evidence")
    for fragment in REQUIRED_SOURCE:
        if fragment not in source:
            errors.append(f"checkpoint runtime guard missing: {fragment}")
    for persistent_id in (f"SLICE-001:CHECKPOINT-{i}" for i in range(1, 5)):
        if persistent_id not in source:
            errors.append(f"checkpoint runtime ID missing: {persistent_id}")
    if "ProfileService.SaveProfile(" in source:
        errors.append("checkpoint writes must use checked TrySaveProfile")
    if source.find("Old.DiscoveredPoiIds.Find[PreviousId]") > source.find(
        "ProfileService.TrySaveProfile(Player, Candidate)"
    ):
        errors.append("checkpoint prerequisite must precede persistent commit")
    if "    RestoreWhenReady(" not in source or "    LatestContiguousCheckpoint(" not in source:
        errors.append("checkpoint restore task boundaries missing")
    else:
        restore = source.split("    RestoreWhenReady(", 1)[1].split(
            "    LatestContiguousCheckpoint(", 1
        )[0]
        guard = restore.find("if (not IsRestoreTokenCurrent(Player, Token)?):")
        teleport = restore.find("Destination.Teleport(Player)")
        if guard < 0 or teleport < 0 or guard > teleport:
            errors.append("stale restore task must be rejected before teleport")
        if "set PendingPlayers[Player] = false" in restore:
            errors.append("restore must not clear a newer task's pending flag")
        if restore.count("ClearPendingIfCurrent(Player, Token)") < 3:
            errors.append("all restore termination paths must clear their own pending flag")
    if "    OnPlayerRemoved(" not in source or (
        "for (Stored -> Epoch : RestoreTokens, Stored <> Player):"
        not in source.split("    OnPlayerRemoved(", 1)[1]
    ) or "set RestoreTokens = Tokens" not in source.split("    OnPlayerRemoved(", 1)[1]:
        errors.append("disconnect must invalidate pending restore generations")
    return errors


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    source = VERSE.read_text(encoding="utf-8")
    errors = check_contract(manifest, contract, source)
    for error in errors:
        print(f"ERROR: {error}")
    if not errors:
        print("SLICE-001 checkpoint source/geometry guards passed; native UEFN not assessed.")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
