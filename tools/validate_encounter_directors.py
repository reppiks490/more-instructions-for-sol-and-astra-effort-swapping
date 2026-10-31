#!/usr/bin/env python3
"""Validate authored gate identity, generated drift and editor acceptance coverage.

This is static evidence; it does not compile or execute Verse.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from build_slice_encounter_directors import OUT, POLICY, SOURCE, render

ROOT = Path(__file__).resolve().parents[1]


def validate_policy(policy: dict, source: dict) -> list[str]:
    errors: list[str] = []
    expected = {boss["boss_id"]: ("Boss", boss["phases"]) for boss in source["boss_encounters"]}
    event = source["world_event"]
    expected[event["event_id"]] = ("WorldEvent", event["stages"])
    encounters = policy.get("encounters", [])
    ids = [encounter.get("id") for encounter in encounters]
    if policy.get("schema_version") != 1:
        errors.append("unsupported director policy schema")
    if len(ids) != len(set(ids)) or set(ids) != set(expected):
        errors.append("director encounter IDs must match the canonical first slice exactly")

    for encounter in encounters:
        encounter_id = encounter.get("id")
        if encounter_id not in expected:
            continue
        kind, authored_phases = expected[encounter_id]
        phases = encounter.get("phases", [])
        if encounter.get("kind") != kind:
            errors.append(f"{encounter_id}: kind mismatch")
        if [phase.get("phase_id") for phase in phases] != [phase["id"] for phase in authored_phases]:
            errors.append(f"{encounter_id}: phase IDs/order must match canonical data")
            continue
        for index, (phase, authored) in enumerate(zip(phases, authored_phases, strict=True)):
            label = f"{encounter_id}/{index}"
            objectives = set(authored["objectives"])
            weakpoints = set(authored.get("weak_points", []))
            counts = phase.get("objective_counts", {})
            if not set(counts) <= objectives:
                errors.append(f"{label}: unknown objective counter")
            if any(type(count) is not int or count < 1 for count in counts.values()):
                errors.append(f"{label}: objective counts must be positive integers")
            signals = phase.get("signals", [])
            signal_ids = [signal.get("id") for signal in signals]
            if len(signal_ids) != len(set(signal_ids)):
                errors.append(f"{label}: duplicate progression signal")
            for signal in signals:
                signal_id = signal.get("id")
                prefix = f"SIG-{encounter_id.replace('-', '')}-"
                if not isinstance(signal_id, str) or not signal_id.startswith(prefix):
                    errors.append(f"{label}: invalid/scoped signal ID")
                if type(signal.get("count")) is not int or signal["count"] < 1:
                    errors.append(f"{label}: signal counts must be positive integers")
                health = signal.get("boss_health_percent", 0)
                defeat = signal.get("boss_defeat", False)
                if type(health) is not int or not 0 <= health < 100 or type(defeat) is not bool:
                    errors.append(f"{label}: malformed physical boss signal")
                if kind == "WorldEvent" and (health or defeat):
                    errors.append(f"{label}: world-event signal cannot impersonate a boss body")
                if (health or defeat) and signal.get("count") != 1:
                    errors.append(f"{label}: physical boss signals must be one-shot")
                if health and defeat:
                    errors.append(f"{label}: health and defeat signal sources are exclusive")
                if defeat and index != len(phases) - 1:
                    errors.append(f"{label}: boss defeat is final-phase only")
            gates = phase.get("transition_alternatives", [])
            if not gates:
                errors.append(f"{label}: no executable transition alternatives")
            for gate in gates:
                if not any(gate.get(key) for key in ("objectives", "weak_points", "signals")):
                    errors.append(f"{label}: empty transition bypass")
                for key, allowed in (("objectives", objectives), ("weak_points", weakpoints), ("signals", set(signal_ids))):
                    references = gate.get(key, [])
                    if len(references) != len(set(references)) or not set(references) <= allowed:
                        errors.append(f"{label}: invalid {key} gate references")
            if kind == "Boss" and index == len(phases) - 1:
                defeat_ids = {signal["id"] for signal in signals if signal.get("boss_defeat")}
                if len(defeat_ids) != 1 or any(not (set(gate.get("signals", [])) & defeat_ids) for gate in gates):
                    errors.append(f"{label}: every boss victory alternative must require physical elimination")

    by_id = {encounter["id"]: encounter for encounter in encounters if encounter.get("id") in expected}
    # These are meaningful first-slice mechanics, not optional editor toggles.
    mason = by_id.get("BOS-005", {}).get("phases", [])
    if len(mason) == 3:
        anchors = set(expected["BOS-005"][1][1]["objectives"])
        gates = mason[1].get("transition_alternatives", [])
        if len(gates) != 1 or set(gates[0].get("objectives", [])) != anchors:
            errors.append("BOS-005: all three stair anchors are required")
    saint = by_id.get("BOS-006", {}).get("phases", [])
    if len(saint) == 3:
        gates = saint[0].get("transition_alternatives", [])
        if len(gates) != 1 or set(gates[0].get("objectives", [])) != {"OBJ-BOS006-BAIT-POUNCE"} or set(gates[0].get("signals", [])) != {"SIG-BOS006-HEALTH-70"}:
            errors.append("BOS-006: health threshold AND failed bite are required")
    king = by_id.get("BOS-011", {}).get("phases", [])
    if len(king) == 4 and king[2].get("objective_counts", {}).get("OBJ-BOS011-SOLVE-DECREES") != 3:
        errors.append("BOS-011: three successful decrees are required")
    market = by_id.get("EVT-011", {}).get("phases", [])
    if len(market) == 4 and market[0].get("signals") != [{"id": "SIG-EVT011-LOT-RESOLVED", "count": 3}]:
        errors.append("EVT-011: three resolved lots are required")
    return errors


def main() -> int:
    policy = json.loads(POLICY.read_text())
    errors = validate_policy(policy, json.loads(SOURCE.read_text()))
    if not OUT.exists() or OUT.read_text() != render():
        errors.append("generated director contracts are stale; run tools/build_slice_encounter_directors.py")
    source = (ROOT / "verse/bosses/encounter_director_device.verse").read_text()
    required = (
        "GetSlice001EncounterDirector[EncounterId]", "ValidateBindings(Definition)",
        "BossService.StartEncounter(EncounterId)", "EventService.StartEvent(EncounterId",
        "BossService.AdvancePhase(EncounterId, NextIndex)", "EventService.AdvanceStage(EncounterId, NextIndex",
        "Character.SetVulnerability(Phase.AllowsDirectBossDamage)", "Character.DamagedEvent().Subscribe",
        "Character.EliminatedEvent().Subscribe", "Character.GetHealth() > 0.0",
        "Alive := BossIsAlive()",
        "ExpectedGeneration <> Generation", "DeathPhase <> Runtime.PhaseIndex",
        "BossSpawnTimeoutSeconds", "RunStopped.Await()", "Spawner.Reset()", "Spawner.DespawnAll(false)",
        "Subscription.Cancel()", "Player.IsActive[]", "ParticipantVolume.GetAgentsInVolume()",
        "Target.BossHealthPercent = 0, not Target.BossDefeat?", "encounter.director_reward_not_ready",
        "not PendingBossElimination?", "ExistingAgent = Agent",
        "GetPhysicalDevices()<decides><transacts>", "Device.IsValid[]", "not Devices.Find[Device]",
        "OtherDevices.Find[Device]", "AcquireDirectorLease()", "ReleaseDirectorLease()",
        "AEONFALLEncounterDirectorLeases:weak_map(session", "encounter.director_duplicate_owner",
        "Input.DestructionSource.DestroyedEvent.Subscribe", "ParticipantVolume.GetAgentsInVolume().Find[Instigator]",
        "OnNativeDestruction", "if (not OwnsLease?):",
    )
    for token in required:
        if token not in source:
            errors.append(f"director is missing integration guard: {token}")
    begin = source.split("\n    OnBegin<override>", 1)[1].split("\n    Report(", 1)[0]
    if not (begin.index("ValidateBindings(Definition)") < begin.index("AcquireDirectorLease()") < begin.index("DisableAll(false)")):
        errors.append("binding validation and physical ownership must precede all initial cleanup")
    end = source.split("\n    OnEnd<override>", 1)[1]
    if not (end.index("if (not OwnsLease?):") < end.index("RunStopped.Signal()") < end.index("ReleaseDirectorLease()")):
        errors.append("rejected directors must not cancel, clear participants or manipulate another owner's devices")
    finish = source.split("\n    Finish(", 1)[1].split("\n    OnEnd", 1)[0]
    if not (finish.index("Runtime.Stop()") < finish.index("CancelBossSubscriptions()") < finish.index("BossService.CompleteEncounter") < finish.index("ExitPhase(CurrentIndex, true)")):
        errors.append("terminal ingress/cancellation/reward/cleanup order changed")
    harness = (ROOT / "verse/bosses/encounter_director_test_device.verse").read_text()
    labels = set(re.findall(r'Check\("([^"]+)"', harness))
    coverage = {
        "unknown objective rejected", "future objective rejected", "premature death signal rejected",
        "objective replay rejected", "outgoing phase input rejected", "two anchors insufficient",
        "three anchors resolve", "repeated authored weakpoint accepted in new phase",
        "final objective cannot award victory", "final death enables completion",
        "final cannot advance out of bounds", "restart resets phase and counters",
        "saint requires failed bite as well", "saint AND gate resolves", "two decrees insufficient",
        "three decrees resolve", "fourth decree rejected", "two lots insufficient",
        "market requires ledger destruction", "failure stops ingress", "unknown encounter lookup fails",
    }
    for label in sorted(coverage - labels):
        errors.append(f"missing UEFN gate assertion: {label}")
    if "Enabled:logic = false" not in harness:
        errors.append("editor harness must default disabled")
    if errors:
        print("Encounter director static validation FAILED")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(f"Encounter director static validation PASSED: {len(policy['encounters'])} encounters, {sum(len(e['phases']) for e in policy['encounters'])} phases, {len(labels)} editor assertion labels")
    print("Static evidence only; UEFN compilation and Launch Session acceptance are pending.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
