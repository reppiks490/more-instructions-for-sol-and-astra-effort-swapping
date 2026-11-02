#!/usr/bin/env python3
"""Fail-closed source and policy guards for owner-exclusive Sovereign Armor Fusion.

This inspects source text. It does not execute Verse, simulate native devices,
verify a custom playable mesh, or validate a Fortnite Launch Session.
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
    stop = begin.end() + after.start() if after else len(value)
    return value[begin.start():stop]


def check_sources(runtime: str, device: str, policy: dict) -> list[str]:
    runtime, device = code(runtime), code(device)
    errors: list[str] = []

    def require(text: str, fragment: str, location: str):
        if fragment not in text:
            errors.append(f"{location}: missing {fragment}")

    def scoped(text: str, name: str, fragments: tuple[str, ...], label: str):
        block = method(text, name)
        if not block:
            errors.append(f"{label}: missing method {name}")
            return
        for fragment in fragments:
            require(block, fragment, f"{label}.{name}")

    def ordered(text: str, name: str, fragments: tuple[str, ...], label: str):
        block = method(text, name)
        at = 0
        for part in fragments:
            found = block.find(part, at)
            if found < 0:
                errors.append(f"{label}.{name}: required sequence missing/out of order: {part}")
                return
            at = found + len(part)

    require(runtime, "weak_map(session, aeonfall_sovereign_fusion_runtime)", "runtime")
    require(runtime, "Mode:aeonfall_sovereign_fusion_mode = aeonfall_sovereign_fusion_mode.Dormant", "runtime")
    require(runtime, "var Owner:?player = false", "runtime")
    scoped(runtime, "AcquireController", ("if (Controller?):", "return false", "set Controller = option{Device}"), "runtime")
    scoped(runtime, "ReleaseController", ("Current = Device", "set Mode = aeonfall_sovereign_fusion_mode.Dormant",
                                         "set Controller = false"), "runtime")
    scoped(runtime, "Begin", ("Current = Device", "Player.IsActive[]", "Authority.CanWield(Player)", "Authorized?",
                               "Mode = aeonfall_sovereign_fusion_mode.Dormant", "Now >= CooldownUntil",
                               "DurationSeconds >= 15.0", "DurationSeconds <= 180.0",
                               "Capacity >= 30", "Capacity <= 120", "Bound = Player",
                               "set Generation += 1", "set Mode = aeonfall_sovereign_fusion_mode.Armor"), "runtime")
    ordered(runtime, "Begin", ("Authority.CanWield(Player)", "Authorized?", "set Generation += 1",
                              "set Mode = aeonfall_sovereign_fusion_mode.Armor"), "runtime")
    scoped(runtime, "IsCurrent", ("Current = Player", "Player.IsActive[]", "Generation = Token",
                                   "GetSimulationElapsedTime() < Deadline"), "runtime")
    scoped(runtime, "Spend", ("Current = Device", "IsCurrent(Player, Token)?", "Cost > 0",
                              "Cost <= 25", "Energy >= Cost", "set Energy -= Cost"), "runtime")
    ordered(runtime, "Spend", ("Energy >= Cost", "set Energy -= Cost"), "runtime")
    scoped(runtime, "End", ("Current = Device", "Generation = Token", "CooldownSeconds >= 30.0",
                            "CooldownSeconds <= 300.0", "set Energy = 0",
                            "set CooldownUntil = GetSimulationElapsedTime() + CooldownSeconds"), "runtime")
    require(device, "Enabled:logic = false", "device")
    scoped(device, "ValidSettings", ("FuseInput <> SeparateInput", "InitialEnergy <= 120",
                                      "CooldownSeconds <= 300.0"), "device")
    scoped(device, "OnBegin", ("GetAEONFALLSovereignFusionRuntime[]", "Service.AcquireController(Self)",
                               "FuseInput.PressedEvent.Subscribe(Fuse)",
                               "SeparateInput.PressedEvent.Subscribe(Separate)",
                               "PlayerRemovedEvent().Subscribe(PlayerLeft)"), "device")
    ordered(device, "Fuse", ("Service.Begin[Self, Player, Authority, DurationSeconds, InitialEnergy]",
                              "set VisualOwner = option{Player}", "ArmorGlow.Pickup(Player)",
                              "ArmorCamera.AddTo(Player)", "FusionSequence.Play(Player)"), "device")
    scoped(device, "Separate", ("Owner = Player", "FinishActive()"), "device")
    scoped(device, "PlayerLeft", ("Owner = Player", "FinishActive()"), "device")
    scoped(device, "MaintenanceLoop", ("Sleep(1.0)", "Authority.CanWield(Player)", "Granted?",
                                       "Service.IsCurrent(Player, Token)?", "Character = OriginalCharacter",
                                       "Character.IsActive[]", "Service.Spend[Self, Player, Token, 1]",
                                       "FinishActive()"), "device")
    scoped(device, "ClearPhysical", ("FusionSequence.Stop(Owner)", "ArmorCamera.RemoveFrom(Owner)",
                                     "ArmorGlow.Clear(Owner)", "set VisualOwner = false",
                                     "set VisualCharacter = false"), "device")
    ordered(device, "OnEnd", ("set Running = false", "StopEvent.Signal()", "Subscription.Cancel()",
                               "Service.OwnsController(Self)?", "FinishActive()",
                               "Service.ReleaseController(Self)"), "device")
    for name, text in (("runtime", runtime), ("device", device)):
        for forbidden in ("weak_map(player,", "GetPlayerName", "OwnerReference.Register",
                          "GetEpicAccountId", "SetPlayerOutfit", "PossessNPC", "SpawnProp("):
            if forbidden in text:
                errors.append(f"{name}: forbidden or unsupported grant/possession path {forbidden}")
    for forbidden in (".Hide()", ".Show()", "GetTeam", "RemoveFromAll(", "ClearForAll(", "AddToAll("):
        if forbidden in device:
            errors.append(f"device: forbidden cross-system or cross-player mutation {forbidden}")
    if device.count("ArmorGlow.Pickup(") != 1 or device.count("ArmorCamera.AddTo(") != 1:
        errors.append("device: presentation must have one owner-audited activation path")
    expected = {
        "schema_version": 1,
        "parent_ability_id": "UNI-001",
        "mode_key": "sovereign_armor_fusion",
        "mode": "armor_prototype",
        "owner_limit": 1,
        "enabled_by_default": False,
        "authority": "aeonfall_sovereign_authority_device.CanWield",
        "persistent_grant": False,
        "ordinary_unlockable": False,
        "titan_possession_implemented": False,
        "session.one_controller": True,
        "session.generation_bound": True,
        "session.duration_seconds": 90,
        "session.max_duration_seconds": 180,
        "session.cooldown_seconds": 90,
        "session.min_cooldown_seconds": 30,
        "session.max_cooldown_seconds": 300,
        "energy.initial": 100,
        "energy.max_capacity": 120,
        "energy.cost_per_tick": 1,
        "energy.max_spend_per_request": 25,
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
            errors.append(f"policy drift: {path} expected {desired!r}")
    return errors


def main() -> int:
    try:
        errors = check_sources((ROOT / RUNTIME).read_text(encoding="utf-8"),
                               (ROOT / DEVICE).read_text(encoding="utf-8"),
                               json.loads((ROOT / POLICY).read_text(encoding="utf-8")))
    except (OSError, ValueError) as error:
        errors = [str(error)]
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print("Sovereign Fusion source/policy safeguards passed (not native UEFN execution).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
