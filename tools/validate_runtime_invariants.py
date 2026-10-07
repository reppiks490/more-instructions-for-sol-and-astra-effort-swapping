#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_TOKENS = {
    "verse/core/runtime_tick_device.verse": [
        "AEONFALLActivationCoordinator.TickPendingActivations",
        "AEONFALLAbilityRuntime.TickAll",
        "AEONFALLStatusRuntime.TickAll",
        "AEONFALLTargetingRuntime.TickAll",
        "AEONFALLPositionTargetingRuntime.TickAll",
        "AEONFALLSpawnRuntime.TickAll",
        "AEONFALLUnlockDeliveryService.TickAll",
    ],
    "verse/core/actor_registry.verse": [
        "AEONFALLActivationCoordinator.ClearOwnerPending",
        "AEONFALLCompanionRuntime.ReleaseAllForOwner",
        "AEONFALLCompanionRuntime.ReleaseByCompanionKey",
        "AEONFALLTargetingRuntime.Clear",
        "AEONFALLActorContextRuntime.Clear",
        "AEONFALLPositionTargetingRuntime.ClearOwner",
        "AEONFALLSpawnRuntime.ClearOwner",
        "AEONFALLUnlockDeliveryService.ClearOwner",
        "AEONFALLStatusRuntime.ClearTarget",
        "AEONFALLAbilityRuntime.ClearOwner",
        "AEONFALLClassRuntime.ClearOwner",
    ],
    "verse/combat/activation_coordinator.verse": [
        "PendingActivations",
        "TickPendingActivations",
        "CancelPending",
        "ReleaseReservation",
        "ClearOwnerPending",
        "ability.adapter_timeout",
    ],
    "verse/combat/ability_runtime.verse": [
        "OwnerByStateKey",
        "ClearOwner",
        "TickAll",
        "PendingRequestId",
    ],
    "verse/progression/class_runtime.verse": [
        "Reservations",
        "ClearOwner",
        "ReleaseReservation",
        "TransferReservation",
    ],
    "verse/npcs/companion_runtime.verse": [
        "ReleaseCompanion",
        "ReleaseAllForOwner",
        "ReleaseByCompanionKey",
        "ReservationId",
    ],
    "verse/combat/targeting_runtime.verse": [
        "RemainingSeconds",
        "TickAll",
        "Clear",
    ],
    "verse/combat/position_targeting_runtime.verse": [
        "CreateFromView",
        "RemainingSeconds",
        "TickAll",
        "ClearOwner",
    ],
    "verse/combat/actor_context_runtime.verse": [
        "EncounterDepth",
        "GetFlags",
        "EnterEncounter",
        "ExitEncounter",
        "SetTransformation",
        "Clear",
    ],
    "verse/combat/status_runtime.verse": [
        "TickAll",
        "status.expired",
        "ClearTarget",
    ],
    "verse/core/spawn_runtime.verse": [
        "Reserve",
        "Release",
        "ClearOwner",
        "TickAll",
        "MaxPerOwner",
    ],
    "verse/economy/unlock_delivery_service.verse": [
        "Request",
        "Resolve",
        "ClearOwner",
        "TickAll",
        "RequestUnlockDelivery",
    ],
    "verse/combat/ability_activation_service.verse": [
        "AEONFALLActorContextRuntime.GetFlags",
    ],
    "verse/combat/targeted_ability_input_device.verse": [
        "AEONFALLActorContextRuntime.GetFlags",
        "AEONFALLTargetingRuntime.GetSelection",
    ],
}

FORBIDDEN_TOKENS = {
    "verse/combat/targeted_ability_input_device.verse": [
        "EncounterActive:logic = false",
        "TransformationActive:logic = false",
    ],
}

def check_runtime_clock(text: str) -> list[str]:
    """Guard elapsed-time wiring; this is source validation, not Verse execution."""
    errors: list[str] = []
    code = "\n".join(line.split("#", 1)[0] for line in text.splitlines())
    required = [
        "var PreviousTime:float = GetSimulationElapsedTime()",
        "CurrentTime:float = GetSimulationElapsedTime()",
        "DeltaSeconds:float = CurrentTime - PreviousTime",
        "set PreviousTime = CurrentTime",
        "if (DeltaSeconds > 0.0):",
        "OnEnd<override>():void=",
        "set Running = false",
    ]
    for token in required:
        if token not in code:
            errors.append(f"runtime clock missing {token!r}")
    sleep = code.find("Sleep(Interval)")
    guard = code.find("if (not Running?):", sleep)
    advance = code.find("AdvanceRuntime(DeltaSeconds)", sleep)
    if sleep < 0 or guard < sleep or advance < guard:
        errors.append("runtime clock must check shutdown after Sleep and before advance")
    for service in REQUIRED_TOKENS["verse/core/runtime_tick_device.verse"]:
        if f"{service}(DeltaSeconds)" not in code:
            errors.append(f"runtime clock must pass measured delta to {service}")
        if f"{service}(Interval)" in code:
            errors.append(f"runtime clock must not use requested sleep for {service}")
    return errors

def main() -> int:
    errors: list[str] = []
    clock_path = ROOT / "verse/core/runtime_tick_device.verse"
    if clock_path.exists():
        errors.extend(check_runtime_clock(clock_path.read_text(encoding="utf-8")))

    for rel, tokens in REQUIRED_TOKENS.items():
        path = ROOT / rel
        if not path.exists():
            errors.append(f"missing required runtime file: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                errors.append(f"{rel}: missing invariant token {token!r}")

    for rel, tokens in FORBIDDEN_TOKENS.items():
        path = ROOT / rel
        if not path.exists():
            errors.append(f"missing runtime file for forbidden-token check: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        for token in tokens:
            if token in text:
                errors.append(f"{rel}: forbidden stale runtime pattern {token!r}")

    adapter_files = [
        ROOT / "verse/combat/status_ability_adapter_device.verse",
        ROOT / "verse/combat/trigger_ability_adapter_device.verse",
        ROOT / "verse/combat/composite_ability_adapter_device.verse",
    ]
    for path in adapter_files:
        if not path.exists():
            errors.append(f"missing adapter implementation: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        if "AEONFALLRuntimeBus.ReportAdapterResult" not in text:
            errors.append(
                f"{path.relative_to(ROOT)}: adapter does not report two-phase result"
            )

    workflow = (ROOT / ".github/workflows/catalog-validation.yml").read_text(
        encoding="utf-8"
    )
    for event in ("push", "pull_request"):
        # Path entries have six spaces; stop at the next event/top-level stanza.
        match = re.search(rf"(?ms)^  {event}:\n(.*?)(?=^  [a-z_]+:|^[a-z_]+:|\Z)", workflow)
        if not match or '"verse/**"' not in match.group(1):
            errors.append(f"validation workflow {event} does not watch verse/**")
    if "python tools/validate_verse_static.py" not in workflow:
        errors.append("validation workflow does not run static Verse validation")
    if "python tools/validate_runtime_invariants.py" not in workflow:
        errors.append("validation workflow does not run runtime invariant validation")

    if errors:
        print("AEONFALL runtime invariant validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AEONFALL runtime invariant validation PASSED")
    print(f"- invariant files: {len(REQUIRED_TOKENS)}")
    print(f"- two-phase adapters: {len(adapter_files)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
