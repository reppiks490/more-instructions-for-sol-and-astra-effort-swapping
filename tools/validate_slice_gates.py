#!/usr/bin/env python3
"""Source-only, fail-closed audit for SLICE-001 admission and progression passages.

Never treats source assertions as native Verse compilation or editor evidence.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "content/vertical_slice/slice_001_gate_bindings.json"
CHECKPOINTS = ROOT / "content/vertical_slice/slice_001_checkpoint_bindings.json"
ENCOUNTERS = ROOT / "content/vertical_slice/slice_001_encounters.json"
POLICY = ROOT / "verse/progression/slice_001_gate_policy.verse"
GATE = ROOT / "verse/progression/slice_001_progression_gate_device.verse"
DIRECTOR = ROOT / "verse/bosses/encounter_director_device.verse"

ROUTES = (
    ("RED-MASON", 1, (), (), "BOS-005", "CHECKPOINT-1"),
    ("SAINTLESS", 2, ("BOS-005",), (), "BOS-006", "CHECKPOINT-2"),
    ("GRAVE-MARKET", 3, ("BOS-005", "BOS-006"), (), "EVT-011", "CHECKPOINT-3"),
    ("BLACK-THRONE", 4, ("BOS-005", "BOS-006"), ("EVT-011",), "BOS-011", "CHECKPOINT-4"),
    ("EXIT", 4, ("BOS-005", "BOS-006", "BOS-011"), ("EVT-011",), None, "CHECKPOINT-4"),
)

POLICY_GUARDS = (
    "GateIndex < 0 or GateIndex > 4",
    "Index <= RequiredLastCheckpoint",
    "Profile.DiscoveredPoiIds.Find[Id]",
    'Profile.CompletedBossIds.Find["BOS-005"]',
    'Profile.CompletedBossIds.Find["BOS-006"]',
    'Profile.CompletedBossIds.Find["BOS-011"]',
    'Profile.CompletedWorldEventIds.Find["EVT-011"]',
    'EncounterId = "BOS-005"',
    'EncounterId = "BOS-006"',
    'EncounterId = "BOS-011"',
    'EncounterId = "EVT-011"',
)
GATE_GUARDS = (
    "AEONFALLSliceGateOwners",
    "ValidatePhysicalBindings()",
    "GateVolumes.Length <> 5",
    "GateTeleporters.Length <> 5",
    "not Devices.Find[Device]",
    "Volume.AgentEntersEvent.Subscribe(Listener.OnEntered)",
    "Volume.AgentExitsEvent.Subscribe(Listener.OnExited)",
    "PlayerRemovedEvent().Subscribe(OnPlayerRemoved)",
    "ProfileService.GetProfile[Player]",
    "AEONFALLSlice001GateAllowed(Profile, Index)?",
    "Destination.Teleport(Player)",
    "set Latched[Player]",
    "Subscription.Cancel()",
    "set Latched = map{}",
    "OnEnd<override>()",
)
DIRECTOR_GUARDS = (
    "StartInput.TriggeredEvent.Subscribe(OnStart)",
    "AdmittingAgent := Instigator?",
    "AdmittingPlayer := player[AdmittingAgent]",
    "AdmittingPlayer.IsActive[]",
    "AdmittingCharacter.IsActive[]",
    "ParticipantVolume.GetAgentsInVolume().Find[AdmittingAgent]",
    "ProfileService.GetProfile[AdmittingPlayer]",
    "AEONFALLSlice001CanStart(Profile, EncounterId)?",
    'Report("encounter.director_admission_rejected")',
    "PlayerRemovedEvent().Subscribe(OnPlayerRemoved)",
    "FailIfArenaEmpty()",
    "GetAEONFALLEncounterParticipation().GetParticipants(EncounterId).Length = 0",
    "OnFail(false)",
    "set ServiceAcknowledged = BossService.CompleteEncounter(EncounterId)",
    "set ServiceAcknowledged = EventService.CompleteEvent(EncounterId)",
    "if (Success? and ServiceAcknowledged?):",
    "CompletedOutput.Trigger()",
    "FailedOutput.Trigger()",
)


def check_contract(
    contract: dict, checkpoints: dict, encounters: dict,
    policy: str, gate_source: str, director: str,
) -> list[str]:
    errors: list[str] = []
    if contract.get("schema_version") != 1 or contract.get("slice_id") != "SLICE-001":
        errors.append("gate schema/slice mismatch")
    if contract.get("status") != "editor_bindings_required":
        errors.append("gate state cannot assert installed editor objects")
    for key, value in {
        "runtime_class": "aeonfall_slice_001_progression_gate_device",
        "runtime_source": "verse/progression/slice_001_progression_gate_device.verse",
        "policy_source": "verse/progression/slice_001_gate_policy.verse",
        "director_source": "verse/bosses/encounter_director_device.verse",
        "lease": "one_gate_owner_per_session",
        "feedback_ref": "slice_gate_hud",
        "feedback_type": "hud_message_device",
    }.items():
        if contract.get(key) != value:
            errors.append(f"incorrect gate contract {key}")
    if contract.get("profile_fields") != [
        "DiscoveredPoiIds", "CompletedBossIds", "CompletedWorldEventIds"
    ]:
        errors.append("gate policy must reuse the existing player profile")
    if contract.get("editor_feedback_path") is not None:
        errors.append("invented gate feedback editor path")
    actual_cps = checkpoints.get("checkpoints", [])
    if [c.get("persistent_id") for c in actual_cps] != [
        f"SLICE-001:CHECKPOINT-{i}" for i in range(1, 5)
    ]:
        errors.append("checkpoint prerequisite source mismatch")
    existing = {boss.get("boss_id") for boss in encounters.get("boss_encounters", [])}
    existing.add(encounters.get("world_event", {}).get("event_id"))
    if not {"BOS-005", "BOS-006", "BOS-011", "EVT-011"}.issubset(existing):
        errors.append("missing boss/world-event progression source")

    routes = contract.get("gates")
    if not isinstance(routes, list) or len(routes) != 5:
        errors.append("exactly five canonical Ossuary gates required")
        routes = []
    refs = set()
    for index, row in enumerate(routes):
        if not isinstance(row, dict):
            errors.append(f"gate {index} is not an object")
            continue
        name, cp_count, bosses, events, encounter, marker = ROUTES[index]
        expected = {
            "index": index,
            "id": f"SLICE-001:GATE-{name}",
            "near_marker_id": marker,
            "required_checkpoint_ids": [f"SLICE-001:CHECKPOINT-{n}" for n in range(1, cp_count + 1)],
            "required_boss_ids": list(bosses),
            "required_world_event_ids": list(events),
            "unlocks_encounter_id": encounter,
            "entry_volume_ref": f"gate_{index + 1}_entry",
            "entry_volume_type": "volume_device",
            "destination_ref": f"gate_{index + 1}_destination",
            "destination_type": "teleporter_device",
            "editor_entry_path": None,
            "editor_destination_path": None,
        }
        for key, value in expected.items():
            if row.get(key) != value:
                errors.append(f"gate {index} {key} mismatch")
        for key in ("entry_volume_ref", "destination_ref"):
            ref = row.get(key)
            if not isinstance(ref, str) or ref in refs:
                errors.append(f"gate {index} duplicate/nonstring physical ref")
            refs.add(ref)
    if len(refs) != 10:
        errors.append("gate physical refs must be unique")

    ingress = contract.get("encounter_ingress", {})
    for key in ("require_player_agent", "require_live_character",
                "require_arena_membership", "require_full_checkpoint_prefix",
                "require_prior_first_clears"):
        if ingress.get(key) is not True:
            errors.append(f"encounter ingress must enforce {key}")
    for key, value in {
        "event_source": "StartInput.TriggeredEvent",
        "unsupported_encounter_id": "reject",
        "world_event_id": "EVT-011",
        "director_owner_class": "aeonfall_encounter_director_device",
    }.items():
        if ingress.get(key) != value:
            errors.append(f"encounter ingress {key} mismatch")
    cleanup = contract.get("result_cleanup", {})
    for key in ("fail_when_arena_empty", "disconnect_rebuilds_membership",
                "completed_output_requires_service_ack", "failure_never_awards"):
        if cleanup.get(key) is not True:
            errors.append(f"encounter cleanup {key} disabled")
    if cleanup.get("persistent_rewards") != "existing_first_clear_commit_only":
        errors.append("must reuse current first-clear rewards")
    if contract.get("native_evidence") != {
        "uefn_compile": "not_run",
        "physical_placement": "not_run",
        "launch_session": "not_run",
    }:
        errors.append("unverified native-editor evidence")

    for name, source, required in (
        ("gate policy", policy, POLICY_GUARDS),
        ("passage device", gate_source, GATE_GUARDS),
        ("encounter director", director, DIRECTOR_GUARDS),
    ):
        for fragment in required:
            if fragment not in source:
                errors.append(f"{name} lacks required guard: {fragment}")
    admission = director.find("AEONFALLSlice001CanStart(Profile, EncounterId)?")
    started = director.find("BossService.StartEncounter(EncounterId)")
    if admission < 0 or started < 0 or admission >= started:
        errors.append("admission policy must precede encounter activation")
    reward_ack = director.find("if (Success? and ServiceAcknowledged?):")
    completed = director.find("CompletedOutput.Trigger()")
    if reward_ack < 0 or completed < 0 or reward_ack >= completed:
        errors.append("completion output is not gated on service acknowledgement")
    if "weak_map(player," in policy + gate_source:
        errors.append("gate runtime cannot allocate a second persistent player root")
    return errors


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    checkpoints = json.loads(CHECKPOINTS.read_text(encoding="utf-8"))
    encounters = json.loads(ENCOUNTERS.read_text(encoding="utf-8"))
    errors = check_contract(
        contract, checkpoints, encounters,
        POLICY.read_text(encoding="utf-8"),
        GATE.read_text(encoding="utf-8"),
        DIRECTOR.read_text(encoding="utf-8"),
    )
    for error in errors:
        print("ERROR:", error)
    if not errors:
        print("SLICE-001 per-player gate/admission/cleanup source contracts valid; UEFN native acceptance NOT RUN.")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
