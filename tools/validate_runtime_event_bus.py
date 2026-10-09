#!/usr/bin/env python3
"""Validate the project bus API and callers; this is not a Verse compiler."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUS = "verse/core/runtime_event_bus.verse"
CHANNELS = {
    "RuntimeEvent": ("aeonfall_runtime_event", "aeonfall_runtime_event_channel"),
    "AbilityEffectRequested": ("aeonfall_ability_effect_request", "aeonfall_ability_request_channel"),
    "AdapterResult": ("aeonfall_adapter_result", "aeonfall_adapter_result_channel"),
    "UnlockDeliveryRequested": ("aeonfall_unlock_delivery_request", "aeonfall_unlock_request_channel"),
    "UnlockDeliveryResult": ("aeonfall_unlock_delivery_result", "aeonfall_unlock_result_channel"),
}
EMITTERS = {
    "Emit": "aeonfall_runtime_event",
    "RequestAbilityEffect": "aeonfall_ability_effect_request",
    "ReportAdapterResult": "aeonfall_adapter_result",
    "RequestUnlockDelivery": "aeonfall_unlock_delivery_request",
    "ReportUnlockDelivery": "aeonfall_unlock_delivery_result",
}
ABILITY_ADAPTERS = (
    "verse/combat/trigger_ability_adapter_device.verse",
    "verse/combat/status_ability_adapter_device.verse",
    "verse/combat/composite_ability_adapter_device.verse",
    "verse/npcs/royal_scent_adapter_device.verse",
)
UNLOCK_ADAPTERS = (
    "verse/economy/unlock_delivery_adapter_device.verse",
    "verse/economy/unlock_item_granter_adapter_device.verse",
)
NATIVE_HANDLERS = {
    "verse/combat/trigger_ability_adapter_device.verse": ("OnRequest",),
    "verse/combat/composite_ability_adapter_device.verse": ("OnRequest",),
    "verse/combat/status_device_bridge.verse": ("OnRuntimeEvent", "Cleanup"),
    "verse/economy/unlock_delivery_adapter_device.verse": ("OnDeliveryRequested",),
    "verse/economy/unlock_item_granter_adapter_device.verse": ("OnDeliveryRequested",),
}


def code_only(source: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in source.splitlines())


def method_body(source: str, name: str) -> str:
    pattern = rf"^    {name}(?:<override>)?\([^)]*\)(?:<\w+>)*:[^\n=]+=\n((?: {{8}}[^\n]*\n|\n)*)"
    match = re.search(pattern, code_only(source) + "\n", re.M)
    return match.group(1) if match else ""


def validate_sources(sources: dict[str, str]) -> list[str]:
    errors: list[str] = []
    bus = code_only(sources.get(BUS, ""))
    for field, (payload, channel) in CHANNELS.items():
        declaration = rf"\b{field}\s*:\s*{channel}\b"
        if not re.search(declaration, bus):
            errors.append(f"{BUS}: {field} must use {channel}; raw event({payload}) has no Subscribe")
        channel_body = re.search(rf"^{channel}\s*:=\s*class[^\n]*:\n((?:[ \t]+[^\n]*\n|\n)*)", bus, re.M)
        if channel_body is None:
            errors.append(f"{BUS}: missing channel class {channel}")
        else:
            body = channel_body.group(1)
            for method in ("Subscribe", "Signal", "TrySignal", "Await"):
                if not re.search(rf"^    {method}\(", body, re.M):
                    errors.append(f"{BUS}: {channel} lacks {method}")
            if not re.search(r"TrySignal\([^)]*\)<transacts>:logic", body):
                errors.append(f"{BUS}: {channel}.TrySignal must expose transactional admission")

    for method, payload in EMITTERS.items():
        for name, result in ((method, "void"), ("Try" + method, "logic")):
            if not re.search(rf"\b{name}\(\w+:{payload}\)<transacts>:{result}", bus):
                errors.append(f"{BUS}: {name} must return {result} with transacts")
    if not re.search(r"\bPump\(\):void", bus):
        errors.append(f"{BUS}: missing no_rollback Pump() dispatch boundary")
    if not re.search(r"weak_map\(session,\s*aeonfall_event_bus_state\)", bus):
        errors.append(f"{BUS}: mutable bus state must be session scoped")
    if not re.search(r"Cancel<override>\(\)<transacts>:void", bus):
        errors.append(f"{BUS}: missing transactional cancelable token")
    if re.search(r"Cancel<override>\(\)[^\n]*\n(?:[ \t]+[^\n]*\n)*?[^\n]*\.Signal\(", bus):
        errors.append(f"{BUS}: cancellation must not signal a native event inside transacts")

    for path in ABILITY_ADAPTERS:
        if "AEONFALLAdapterResultDelivery.Report(" not in code_only(sources.get(path, "")):
            errors.append(f"{path}: physical ability results require the admission/fallback delivery helper")
    delivery_path = "verse/combat/adapter_result_delivery.verse"
    delivery = code_only(sources.get(delivery_path, ""))
    if "AEONFALLRuntimeBus.TryReportAdapterResult(Result)" not in delivery or "GetAEONFALLActivationCoordinator().ResolveAdapterResult(Definition, Result)" not in delivery:
        errors.append(f"{delivery_path}: rejected result admission requires direct canonical resolution")
    for path in UNLOCK_ADAPTERS:
        adapter = code_only(sources.get(path, ""))
        if "AEONFALLRuntimeBus.TryReportUnlockDelivery(Result)" not in adapter or "GetAEONFALLUnlockDeliveryService().Resolve(Result)" not in adapter:
            errors.append(f"{path}: rejected unlock result admission requires direct canonical resolution")
    for path, handlers in NATIVE_HANDLERS.items():
        adapter = code_only(sources.get(path, ""))
        for handler in handlers:
            if re.search(rf"\b{handler}\([^)]*\)<transacts>:void", adapter):
                errors.append(f"{path}: {handler} dispatches native device effects and must have no_rollback")

    status_path = "verse/combat/status_runtime.verse"
    status = code_only(sources.get(status_path, ""))
    commit = method_body(status, "CommitStatusChange")
    if not re.search(r"CommitStatusChange\([^)]*\)<decides><transacts>:void", status) or "EventBus.TryEmit(Event)" not in commit or not re.search(r"^        Admitted\?\s*$", commit, re.M):
        errors.append(f"{status_path}: status commands require atomic deciding queue admission")
    for method in ("ApplyStatus", "RemoveStatus"):
        if "CommitStatusChange[" not in method_body(status, method):
            errors.append(f"{status_path}: {method} must commit canonical state and its command atomically")
    expiry = method_body(status, "CommitStatusTick")
    if "EventBus.TryEmit(" not in expiry or not re.search(r"if \(not Admitted\?\):\s*set Updated = Updated \+ array\{Instance\}", expiry):
        errors.append(f"{status_path}: saturated expiry must retain the original positive-duration instance for retry")
    if "Tick(TargetKey, DeltaSeconds)" not in method_body(status, "TickAll"):
        errors.append(f"{status_path}: TickAll must share per-target expiry admission and retry")
    clear = method_body(status, "ClearTarget")
    if "set StatusesByTarget[TargetKey] = array{}" not in clear or "EventBus.Emit(" not in clear:
        errors.append(f"{status_path}: forced target cleanup must clear canonical state without requiring queue admission")

    bridge_path = "verse/combat/status_device_bridge.verse"
    bridge = code_only(sources.get(bridge_path, ""))
    if "var AppliedAgents:[string]agent" not in bridge or "Sleep(0.1)" not in method_body(bridge, "ReconcileLoop") or "CleanupIfStale(TargetKey)" not in method_body(bridge, "Reconcile"):
        errors.append(f"{bridge_path}: physical statuses require tracked-agent periodic reconciliation")
    stale = method_body(bridge, "CleanupIfStale")
    for required in ("GetAEONFALLStatusRuntime().HasStatus(TargetKey, StatusId)?", "GetAEONFALLActorRegistry().GetAgent[TargetKey]", "CurrentAgent = TrackedAgent", "Cleanup(TrackedAgent)"):
        if required not in stale:
            errors.append(f"{bridge_path}: stale cleanup missing {required}")
    applied = method_body(bridge, "ApplyTracked")
    tracking = applied.find("CommitTracking[TargetKey, TargetAgent]")
    triggering = applied.find("ApplyTrigger.Trigger(TargetAgent)")
    committed = method_body(bridge, "CommitTracking")
    if (tracking < 0 or triggering < tracking or
        "<decides><transacts>" not in bridge or
        "set AppliedAgents[TargetKey] = TargetAgent" not in committed or
        "set AppliedCharacters[TargetKey] = Character" not in committed):
        errors.append(f"{bridge_path}: track each application before applying physical effects")
    reconcile = method_body(bridge, "Reconcile")
    for required in ("GetAEONFALLStatusRuntime().StatusesByTarget", "not AppliedCharacters[TargetKey]", "ApplyTracked(TargetKey, TargetAgent)"):
        if required not in reconcile:
            errors.append(f"{bridge_path}: discover canonical statuses and replacement characters: {required}")
    if "CurrentCharacter = TrackedCharacter" not in stale:
        errors.append(f"{bridge_path}: track physical character generation across respawn")
    if "CleanupAll()" not in method_body(bridge, "OnEnd") or "ReconciliationStopped.Signal()" not in method_body(bridge, "OnEnd"):
        errors.append(f"{bridge_path}: OnEnd must stop reconciliation and clean all tracked effects")

    harness_path = "verse/testing/status_saturation_test_device.verse"
    harness = sources.get(harness_path, "")
    labels = set(re.findall(r'Check\("([^"]+)"', harness))
    coverage = {
        "full queue rejects application", "rejected application leaves no state",
        "full queue rejects refresh", "rejected refresh preserves instance",
        "full queue rejects removal", "rejected removal preserves instance",
        "single target expiry retries positive duration", "single target expiry commits after drain",
        "tick all expiry retries positive duration", "tick all expiry commits after drain",
        "saturated batch restores all canonical state", "saturated batch restores queued commands",
        "zero duration remains persistent", "forced clear commits under saturation",
    }
    for missing in sorted(coverage - labels):
        errors.append(f"{harness_path}: missing UEFN saturation assertion {missing}")
    if "Enabled:logic = false" not in harness:
        errors.append(f"{harness_path}: saturation harness must default disabled")

    for path, source in sources.items():
        code = code_only(source)
        subscriptions = list(re.finditer(r"AEONFALLRuntimeBus\.(\w+)\.Subscribe\((\w+)\)", code))
        if subscriptions:
            if re.search(r"option\{[^}]*AEONFALLRuntimeBus\.\w+\.Subscribe\(", code):
                errors.append(f"{path}: Subscribe has no_rollback; capture its token before constructing option{{}}")
            if re.search(r"^\s*AEONFALLRuntimeBus\.\w+\.Subscribe\([^\n]+\)\s*$", code, re.M):
                errors.append(f"{path}: bus subscription token is discarded")
            cleanup = re.search(r"^    OnEnd<override>\(\):void=\n((?: {8}[^\n]*\n|\n)*)", code + "\n", re.M)
            if cleanup is None or ".Cancel()" not in cleanup.group(1):
                errors.append(f"{path}: bus subscription requires cancellation in OnEnd")
        for match in subscriptions:
            field, callback = match.groups()
            if field not in CHANNELS:
                errors.append(f"{path}: unknown bus channel {field}")
                continue
            payload = CHANNELS[field][0]
            if not re.search(rf"\b{callback}\(\s*\w+\s*:\s*{payload}\s*\)(?:<\w+>)*:void", code):
                errors.append(f"{path}: {field} callback {callback} must accept {payload} and return void")
        for match in re.finditer(r"AEONFALLRuntimeBus\.(\w+)\.(?:Await|Signal|TrySignal)\(", code):
            if match.group(1) not in CHANNELS:
                errors.append(f"{path}: unknown bus channel {match.group(1)}")
    return errors


def main() -> int:
    sources = {
        str(path.relative_to(ROOT)): path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "verse").rglob("*.verse"))
    }
    errors = validate_sources(sources)
    if errors:
        print("RUNTIME EVENT BUS VALIDATION FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    count = sum(len(re.findall(r"AEONFALLRuntimeBus\.\w+\.Subscribe\(", code_only(source))) for source in sources.values())
    print(f"RUNTIME EVENT BUS VALIDATION PASSED: {len(CHANNELS)} typed channels, {count} checked callbacks")
    print("Static API checks only; compile and run the event bus and status saturation test devices in UEFN.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
