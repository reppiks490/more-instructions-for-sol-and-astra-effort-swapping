#!/usr/bin/env python3
"""Source guards for the FUS-001 presentation adapter and finite budget.

Not a native Verse compiler or UEFN Launch Session test.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = "verse/sovereign/sovereign_fusion_runtime.verse"
DEVICE = "verse/sovereign/sovereign_fusion_device.verse"
POLICY = "content/sovereign/sovereign_fusion.json"


def code(value: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in value.splitlines())


def method(value: str, name: str) -> str:
    begin = re.search(rf"^    {re.escape(name)}(?:<[^\n]*>)?\(", value, re.M)
    if not begin:
        return ""
    after = re.search(r"^    [A-Za-z_][A-Za-z0-9_]*(?:<[^\n]*>)?\(", value[begin.end():], re.M)
    end = begin.end() + after.start() if after else len(value)
    return value[begin.start():end]


def check_sources(runtime: str, device: str, policy: dict) -> list[str]:
    runtime, device = code(runtime), code(device)
    errors: list[str] = []

    def need(value: str, fragment: str, context: str):
        # Reject a numeric prefix mutation (e.g. <= 120 becoming <= 1200).
        numeric_boundary = r"(?![0-9.])" if fragment[-1:].isdigit() else ""
        if not re.search(re.escape(fragment) + numeric_boundary, value):
            errors.append(f"{context}: missing {fragment}")

    def scoped(value: str, name: str, *fragments: str):
        block = method(value, name)
        if not block:
            errors.append(f"missing method: {name}")
        for fragment in fragments:
            need(block, fragment, name)

    def ordered(value: str, name: str, *fragments: str):
        block = method(value, name)
        cursor = 0
        for fragment in fragments:
            index = block.find(fragment, cursor)
            if index < 0:
                errors.append(f"{name}: missing or reordered {fragment}")
                return
            cursor = index + len(fragment)

    need(runtime, "weak_map(session, aeonfall_sovereign_fusion_budget_runtime)", "budget")
    need(runtime, "var Controller:?creative_device = false", "budget")
    for forbidden in ("var Owner:?player", "aeonfall_fusion_phase := enum:", "GetPlayerName", "SaveProfile(", "weak_map(player,"):
        if forbidden in runtime + device:
            errors.append(f"parallel entitlement, state or persistence forbidden: {forbidden}")
    scoped(runtime, "AcquireController", "if (Controller?):", "set Controller = option{Device}")
    scoped(runtime, "CanBegin", "Current = Device", "not Active?", "GetSimulationElapsedTime() >= CooldownUntil")
    scoped(runtime, "Start", "CanBegin(Device)?", "NewToken > 0", "DurationSeconds <= 180.0",
           "Capacity >= 30", "Capacity <= 120", "set Token = NewToken", "set Active = true")
    scoped(runtime, "Spend", "Current = Device", "Token = NewToken",
           "GetSimulationElapsedTime() < Deadline", "State.IsAuthorizedActive(Device, Player, NewToken)",
           "Authorized?", "Cost > 0", "Cost <= 25", "Remaining >= Cost", "set Remaining -= Cost")
    ordered(runtime, "Spend", "State.IsAuthorizedActive(Device, Player, NewToken)",
            "Authorized?", "Remaining >= Cost", "set Remaining -= Cost")
    scoped(runtime, "Stop", "Current = Device", "Token = NewToken", "CooldownSeconds >= 30.0",
           "CooldownSeconds <= 300.0", "set Remaining = 0", "set CooldownUntil = GetSimulationElapsedTime() + CooldownSeconds")
    scoped(runtime, "ReleaseController", "Current = Device", "set Active = false", "set Controller = false")
    if "set CooldownUntil = 0.0" in method(runtime, "ReleaseController"):
        errors.append("ReleaseController must preserve cooldown against controller replacement")
    need(device, "Enabled:logic = false", "device")
    need(device, "var Runtime:?aeonfall_fusion_state_runtime = false", "device")
    need(device, "var Budget:?aeonfall_sovereign_fusion_budget_runtime = false", "device")
    scoped(device, "OnBegin", "GetAEONFALLFusionState[]", "GetAEONFALLSovereignFusionBudget[]",
           "State.AcquireController(Self, Authority)", "Resource.AcquireController(Self)",
           "FuseInput.PressedEvent.Subscribe(Fuse)", "SeparateInput.PressedEvent.Subscribe(Separate)")
    scoped(device, "ValidSettings", "FuseInput <> SeparateInput", "DurationSeconds <= 180.0",
           "InitialEnergy <= 120")
    ordered(device, "Fuse", "Resource.CanBegin(Self)", 'State.BeginActivation(Self, Player, "FUS-001")',
            "Resource.Start(Self, Started, DurationSeconds, InitialEnergy)", "ArmorGlow.Pickup(Player)",
            "ArmorCamera.AddTo(Player)", "FusionSequence.Play(Player)",
            "ArmorGlow.HasEffect[Player]", "State.ConfirmActivated(Self, Player, Started)")
    scoped(device, "Separate", "Owner = Player", "FinishActive()")
    scoped(device, "PlayerLeft", "Owner = Player", "FinishActive()")
    ordered(device, "FinishActive", "ClearPhysical()", "State.BeginSeparation(Self, Player, LocalToken)",
            "State.CompleteSeparation(Self, LocalToken)")
    scoped(device, "FinishActive", "State.Abort(Self, LocalToken)",
           "Resource.Stop(Self, LocalToken, CooldownSeconds)")
    scoped(device, "ClearPhysical", "FusionSequence.Stop(Owner)", "ArmorCamera.RemoveFrom(Owner)",
           "ArmorGlow.Clear(Owner)", "set VisualOwner = false")
    scoped(device, "MaintenanceLoop", "Sleep(1.0)", "State.IsAuthorizedActive(Self, Player, Token)",
           "Character = OriginalCharacter", "Character.IsActive[]",
           "Resource.Spend[Self, Player, Token, State, 1]", "FinishActive()")
    scoped(device, "OnEnd", "StopEvent.Signal()", "Subscription.Cancel()",
           "FinishActive()", "State.ReleaseController(Self)", "Resource.ReleaseController(Self)")
    for forbidden in (".Hide()", ".Show()", "GetTeam", "RemoveFromAll(", "ClearForAll(", "AddToAll(",
                      "OwnerReference.Register", "PossessNPC", "SpawnProp("):
        if forbidden in device:
            errors.append(f"unsupported physical or grant path: {forbidden}")
    if device.count("ArmorGlow.Pickup(") != 1 or device.count("ArmorCamera.AddTo(") != 1:
        errors.append("physical request must have one audited activation path")
    expected = {
        "schema_version": 1, "parent_ability_id": "UNI-001", "form_id": "FUS-001",
        "canonical_state_runtime": "verse/sovereign/fusion_state_runtime.verse",
        "resource_runtime": RUNTIME, "mode_key": "sovereign_armor_fusion",
        "owner_limit": 1, "enabled_by_default": False,
        "authority": "aeonfall_sovereign_authority_device.CanWield",
        "persistent_grant": False, "ordinary_unlockable": False,
        "titan_possession_implemented": False, "session.one_controller": True,
        "session.generation_bound": True, "session.duration_seconds": 90,
        "session.max_duration_seconds": 180, "session.cooldown_seconds": 90,
        "session.min_cooldown_seconds": 30, "session.max_cooldown_seconds": 300,
        "energy.initial": 100, "energy.max_capacity": 120,
        "energy.cost_per_tick": 1, "energy.max_spend_per_request": 25,
        "physical.native_visual": "visual_effect_powerup_device",
        "physical.native_camera": "gameplay_camera_orbit_device",
        "physical.native_cinematic": "cinematic_sequence_device",
        "physical.instigator_only": True,
        "physical.arbitrary_custom_player_mesh": False,
        "engine_verification.compile": "not_run",
        "engine_verification.launch_session": "not_run",
        "engine_verification.multiplayer": "not_run",
    }
    for path, desired in expected.items():
        value = policy
        for part in path.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        if type(value) is not type(desired) or value != desired:
            errors.append(f"fusion policy drift: {path}")
    return errors


def main() -> int:
    try:
        errors = check_sources((ROOT / RUNTIME).read_text(encoding="utf-8"),
                               (ROOT / DEVICE).read_text(encoding="utf-8"),
                               json.loads((ROOT / POLICY).read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError) as error:
        errors = [str(error)]
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print("Fusion adapter source guards passed. Native UEFN execution not verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
