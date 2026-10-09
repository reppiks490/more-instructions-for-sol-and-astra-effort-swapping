#!/usr/bin/env python3
"""Regression guards for activation transactions/lifetimes; not a compiler."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COORDINATOR = "verse/combat/activation_coordinator.verse"
RUNTIME = "verse/combat/ability_runtime.verse"
DELIVERY = "verse/economy/unlock_delivery_service.verse"

def method(source: str, name: str) -> str:
    marker = "    " + name + "("
    start = source.find(marker)
    if start < 0:
        return ""
    # Only another class method, not a nested body, ends the method.
    import re
    match = re.search(r"\n    [A-Za-z_][A-Za-z0-9_]*\(", source[start + len(marker):])
    return source[start:] if not match else source[start:start + len(marker) + match.start()]

def validate_sources(sources: dict[str, str]) -> list[str]:
    errors = []
    request = method(sources.get(COORDINATOR, ""), "RequestActivation")
    reserve = request.find("set PendingActivations[RequestId] = Pending")
    dispatch = request.find("GetAEONFALLAbilityRuntime().RequestActivation")
    if reserve < 0 or dispatch < 0 or reserve > dispatch:
        errors.append("pending tracking must commit before effect dispatch")
    if "PendingActivations[RequestId]" not in request or 'RequestId = ""' not in request:
        errors.append("request admission must reject empty/duplicate identity")
    resolve = method(sources.get(COORDINATOR, ""), "ResolveAdapterResult")
    if "IsMatchingPending(Definition, Result)" not in resolve or resolve.find("IsMatchingPending") > resolve.find("RemovePendingRecord"):
        errors.append("result identity validation must precede pending removal")
    matching = method(sources.get(COORDINATOR, ""), "IsMatchingPending")
    for guard in ["Pending.OwnerKey = Result.OwnerKey", "Pending.AbilityId = Result.AbilityId",
                  "Result.AdapterId = Definition.AdapterId", "State.PendingRequestId = Result.RequestId"]:
        if guard not in matching:
            errors.append("missing callback guard: " + guard)
    cancel = method(sources.get(COORDINATOR, ""), "CancelPending")
    for guard in ["Pending.OwnerKey = OwnerKey", "Pending.AbilityId = AbilityId", "State.PendingRequestId = RequestId"]:
        if guard not in cancel:
            errors.append("missing cancellation guard: " + guard)
    runtime = sources.get(RUNTIME, "")
    claim = method(runtime, "ClaimEffectRequest")
    if "IsCurrentEffectRequest(Request)?" not in claim or "not EffectClaims[Request.RequestId]" not in claim:
        errors.append("physical effects require an atomic current-request claim")
    for name in ["ResolveActivation", "CancelPending"]:
        if "RemoveEffectClaim" not in method(runtime, name):
            errors.append("effect claims must release on " + name)
    if "Active := Managed" not in method(runtime, "ResolveActivation"):
        errors.append("instant actions must not latch Active forever")
    if "aeonfall_activation_lifetime.Managed" not in runtime or "ReserveWhileActive" not in runtime:
        errors.append("managed and reserved activations must retain explicit end semantics")
    if "TryRequestAbilityEffect" not in method(runtime, "RequestActivation") or "Cancelled := CancelPending" not in method(runtime, "RequestActivation"):
        errors.append("request queue saturation must release the ability reservation")
    retry = method(sources.get(DELIVERY, ""), "TickAll")
    if retry.find("set Pending = Updated") < 0 or retry.find("set Pending = Updated") > retry.find("RequestUnlockDelivery"):
        errors.append("retry callbacks must see committed state; do not resurrect resolved deliveries")
    status = sources.get("verse/combat/status_runtime.verse", "")
    if ")<decides><transacts>:void=" not in method(status, "ApplyBatch"):
        errors.append("status batch must support atomic failure-context rollback")
    scent = sources.get("verse/npcs/royal_scent_adapter_device.verse", "")
    marked = method(scent, "StartMarkedChallenge")
    if ")<decides><transacts>:void=" not in marked or "Marked?" not in marked or "Started?" not in marked:
        errors.append("Royal Scent mark and challenge must commit atomically")
    if "RemoveStatus" in scent:
        errors.append("Royal Scent failure must restore an existing mark, not delete it")
    for path in ["verse/combat/status_ability_adapter_device.verse", "verse/combat/composite_ability_adapter_device.verse",
                 "verse/combat/trigger_ability_adapter_device.verse", "verse/npcs/royal_scent_adapter_device.verse"]:
        adapter = sources.get(path, "")
        if "Claimed := GetAEONFALLAbilityRuntime().ClaimEffectRequest(Request)" not in adapter or "if (not Claimed?):" not in adapter:
            errors.append(path + ": canceled/late requests may execute free effects")
        if "AEONFALLAdapterResultDelivery.Report" not in adapter:
            errors.append(path + ": missing reliable result delivery")
    helper = sources.get("verse/combat/adapter_result_delivery.verse", "")
    if "TryReportAdapterResult" not in helper or "ResolveAdapterResult" not in helper:
        errors.append("result saturation must resolve canonical resources directly")
    return errors

def read_sources(root: Path = ROOT) -> dict[str, str]:
    return {str(p.relative_to(root)): p.read_text() for p in (root / "verse").rglob("*.verse")}

def main() -> int:
    errors = validate_sources(read_sources())
    if errors:
        print("ACTIVATION TRANSACTION VALIDATION FAILED\n" + "\n".join(errors))
        return 1
    print("ACTIVATION TRANSACTION VALIDATION PASSED: request identity, ordering, lifetime, rollback and saturation")
    print("Static guards only; run activation_transaction_test_device in UEFN.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
