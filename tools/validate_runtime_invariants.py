#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_TOKENS = {
    "verse/combat/ability_contract.verse": [
        "RequiredTransformationId",
        "TransformationId:string",
    ],
    "verse/core/runtime_tick_device.verse": [
        "AEONFALLActivationCoordinator.TickPendingActivations",
        "AEONFALLAbilityRuntime.TickAll",
        "AEONFALLStatusRuntime.TickAll",
        "AEONFALLTargetingRuntime.TickAll",
        "AEONFALLPositionTargetingRuntime.TickAll",
        "AEONFALLSpawnRuntime.TickAll",
        "AEONFALLUnlockDeliveryService.TickAll",
        "AEONFALLAscensionTrialRuntime.TickAll",
        "AEONFALLChoosingRuntime.TickAll",
        "AEONFALLAscendedFormRuntime.TickAll",
        "AEONFALLTranscendentRuntime.TickAll",
        "AEONFALLHallOfAscendants.TickAll",
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
        "AEONFALLAscensionTrialRuntime.ClearOwner",
        "AEONFALLChoosingRuntime.ClearOwner",
        "AEONFALLAscendedFormRuntime.ClearOwner",
        "AEONFALLTranscendentRuntime.ClearOwner",
        "AEONFALLHallOfAscendants.RemoveOwner",
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
        "RequiredTransformationId",
        "Context.TransformationId",
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
        "TransformationId",
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
    "verse/transcendent/choosing_runtime.verse": [
        "CommitChoosingSuccess",
        "TickAll",
        "ClearOwner",
    ],
    "verse/transcendent/hall_of_ascendants_runtime.verse": [
        "RefreshIfReady",
        "GetAuthorityDepth",
        "TickAll",
        "RemoveOwner",
        "TranscendentHistoryCount",
    ],
    "verse/transcendent/ascended_form_runtime.verse": [
        "Profile.AscensionRank",
        "not Flags.TransformationActive?",
        "AEONFALLActorContextRuntime.SetTransformation",
        "StopFormAbilities",
        "AEONFALLActivationCoordinator.CancelPending",
        "AEONFALLActivationCoordinator.EndActivation",
        "TickAll",
        "ClearOwner",
    ],
    "verse/transcendent/transcendent_runtime.verse": [
        "ProfileService.IncrementTranscendentHistory",
        "AEONFALLActorContextRuntime.SetTransformation",
        "StopAuthorityAbilities",
        "AEONFALLActivationCoordinator.CancelPending",
        "AEONFALLActivationCoordinator.EndActivation",
        "TickAll",
        "ClearOwner",
    ],
}

FORBIDDEN_TOKENS = {
    "verse/combat/targeted_ability_input_device.verse": [
        "EncounterActive:logic = false",
        "TransformationActive:logic = false",
    ],
}

def main() -> int:
    errors: list[str] = []

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

    # Transcendent history policy: never award on activation start.
    # Award must occur inside EndActive, after the Active -> Exhausted map write,
    # and only for natural duration expiry.
    transcendent_path = ROOT / "verse/transcendent/transcendent_runtime.verse"
    transcendent_text = transcendent_path.read_text(encoding="utf-8")
    activate_pos = transcendent_text.find("    Activate(")
    end_active_pos = transcendent_text.find("    EndActive(")
    history_pos = transcendent_text.find("ProfileService.IncrementTranscendentHistory")
    exhausted_write_pos = transcendent_text.find(
        "set StatesByOwner[OwnerKey] = Exhausted"
    )

    if min(activate_pos, end_active_pos, history_pos, exhausted_write_pos) < 0:
        errors.append("transcendent history policy markers are incomplete")
    else:
        if activate_pos < history_pos < end_active_pos:
            errors.append(
                "transcendent history policy violation: history increments during Activate"
            )
        if history_pos < exhausted_write_pos:
            errors.append(
                "transcendent history policy violation: history is awarded before Exhausted state commits"
            )

    if 'Reason = "duration_expired"' not in transcendent_text:
        errors.append(
            "transcendent history policy violation: natural-duration guard missing"
        )
    if "transcendent.history_awarded" not in transcendent_text:
        errors.append("transcendent history award observability event missing")

        workflow = (ROOT / ".github/workflows/catalog-validation.yml").read_text(
        encoding="utf-8"
    )
    if '"verse/**"' not in workflow:
        errors.append("validation workflow does not watch verse/**")
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
