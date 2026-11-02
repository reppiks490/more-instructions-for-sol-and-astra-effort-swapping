#!/usr/bin/env python3
"""Fail-closed static guard for FUS-001 Arsenal; NOT a Verse compiler."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "content/sovereign/sovereign_arsenal.json"
RUNTIME = ROOT / "verse/sovereign/sovereign_arsenal_runtime.verse"
DEVICE = ROOT / "verse/sovereign/sovereign_arsenal_device.verse"


def method(source: str, name: str) -> str:
    source = "\n".join(line.split("#", 1)[0] for line in source.splitlines())
    match = re.search(rf"^    {re.escape(name)}(?:<[^>\n]+>)?\(", source, re.M)
    if not match:
        return ""
    following = re.search(r"^    [A-Za-z_][A-Za-z0-9_]*(?:<[^>\n]+>)?\(", source[match.end():], re.M)
    return source[match.start():match.end() + following.start()] if following else source[match.start():]


def check_sources(policy: dict, runtime: str, device: str) -> list[str]:
    errors: list[str] = []

    def need(text: str, fragment: str, context: str) -> None:
        suffix = r"(?![0-9.])" if fragment[-1:].isdigit() else ""
        if not re.search(re.escape(fragment) + suffix, text):
            errors.append(f"{context}: missing {fragment}")

    def ordered(text: str, context: str, *parts: str) -> None:
        offset = 0
        for part in parts:
            position = text.find(part, offset)
            if position < 0:
                errors.append(f"{context}: missing or reordered {part}")
                return
            offset = position + len(part)

    expected = {
        "schema_version": 1,
        "form_id": "FUS-001",
        "parent_ability_id": "UNI-001",
        "enabled_by_default": False,
        "owner_limit": 1,
        "ordinary_unlockable": False,
        "persistent_grant": False,
        "authority": "aeonfall_fusion_state_runtime.IsAuthorizedActive",
        "budget": "aeonfall_sovereign_fusion_budget_runtime.Spend",
        "targeting.only_registered_canonical_prefix": "MON-",
        "targeting.players": False,
        "targeting.bosses": False,
        "targeting.companions": False,
        "targeting.sovereign_army": False,
        "targeting.max_hits_per_request": 3,
        "targeting.raycast_line_of_sight": "not_implemented",
        "engine_verification.verse_compile": "not_run",
        "engine_verification.two_client_launch_session": "not_run",
        "synergy.class_id": "CLS-006",
        "armor.shield_restoration_per_generation": 40,
    }
    for key, value in expected.items():
        found = policy
        for part in key.split("."):
            found = found.get(part) if isinstance(found, dict) else None
        if type(found) is not type(value) or found != value:
            errors.append(f"policy drift: {key}")
    weapons = policy.get("weapons", [])
    if not isinstance(weapons, list) or len(weapons) != 3:
        errors.append("policy must contain exactly three weapons")
    else:
        expected_weapons = (
            ("FWA-001", "SFA-001", 5, 2, 18),
            ("FWA-002", "SFA-002", 20, 8, 10),
            ("FWA-003", "SFA-003", 15, 18, 20),
        )
        for weapon, (identifier, ability, cost, cooldown, magnitude) in zip(weapons, expected_weapons):
            if (weapon.get("id"), weapon.get("ability"), weapon.get("energy_cost"),
                weapon.get("cooldown_seconds")) != (identifier, ability, cost, cooldown):
                errors.append(f"weapon contract drift: {identifier}")
            key = {"FWA-001": "damage", "FWA-002": "base_damage_each",
                   "FWA-003": "shield_restore"}[identifier]
            if weapon.get(key) != magnitude:
                errors.append(f"weapon magnitude drift: {identifier}")
        if weapons[0].get("upstream_avatar_energy_cost") != 10:
            errors.append("Rend must account for Avatar's upstream 10 energy")
        if weapons[1].get("max_targets") != 3 or weapons[1].get("sepulchral_mark_bonus_each") != 4:
            errors.append("Collapse target/bonus cap drift")
    need(runtime, "weak_map(session, aeonfall_sovereign_arsenal_runtime)", "runtime")
    need(runtime, "var Controller:?creative_device = false", "runtime")
    for name, delay, cost in (("TryRend", "2.0", "5"),
                              ("TryCollapse", "8.0", "20"),
                              ("TryBulwark", "18.0", "15")):
        block = method(runtime, name)
        ordered(block, name, "Current := Controller?", "Current = Device",
                "Now := GetSimulationElapsedTime()", f"Now >= Last{name[3:]}At + {delay}",
                f"Budget.Spend[Device, Player, Token, State, {cost}]",
                f"set Last{name[3:]}At = Now")
    ordered(method(runtime, "TryRend"), "paid Reaver receipt",
            "Now >= LastRendAt + 2.0",
            "State.ConsumeAttackReceipt[Device, Player, Token]",
            "Budget.Spend[Device, Player, Token, State, 5]",
            "set LastRendAt = Now")
    for part in ("set MarkToken = Token", "set MarkUntil = Now + 4.0",
                 "MarkToken = Token", "GetSimulationElapsedTime() < MarkUntil",
                 "PreviouslyGranted + Amount <= 40.0",
                 "Amount <= 20.0", "Amount >= 1.0"):
        need(runtime, part, "combo/shield")
    release = method(runtime, "ReleaseController")
    need(release, "set Controller = false", "release")
    if "set LastRendAt" in release or "set LastCollapseAt" in release or "set LastBulwarkAt" in release:
        errors.append("release must not reset cooldowns")
    need(device, "Enabled:logic = false", "device")
    need(method(device, "OnBegin"), "Service.AcquireController(Controller)", "lease")
    need(method(device, "OnEnd"), "Subscription.Cancel()", "cleanup")
    need(method(device, "OnEnd"), "Service.ReleaseController(Controller)", "cleanup")
    valid = method(device, "ValidOwner")
    ordered(valid, "owner", "Running?", "Controller.Running?",
            "Player := player[Agent]", "Owner := Controller.VisualOwner?",
            "Owner = Player", "Original := Controller.VisualCharacter?",
            "Character = Original", "Controller.Token > 0",
            "State.IsAuthorizedActive(Controller, Player, Controller.Token)", "Authorized?")
    target = method(device, "EligibleTarget")
    ordered(target, "target", "Registry.IsRegistered[Key]",
            "not player[Candidate]", "IsMonsterId(Canonical)?",
            "Hostile := IsHostileMonster(Key, Candidate)", "Hostile?",
            "Target.IsActive[]", "Target.IsVulnerable[]",
            "Range <= MaxRange", "DotProduct(Delta, Source.GetViewRotation().GetForwardAxis())")
    hostile = method(device, "IsHostileMonster")
    for part in ("GetAEONFALLCompanionRuntime().GetBinding[Key]",
                 "Binding.Active?", "Sovereign.GetCommand[Candidate]"):
        need(hostile, part, "faction")
    need(method(device, "IsMonsterId"), "Id[0] = 'M'", "MON prefix")
    need(method(device, "IsMonsterId"), "Id[3] = '-'", "MON prefix")
    ordered(method(device, "OnRend"), "rend", "ValidOwner[Agent]",
            "EligibleTarget[Player, Selection.TargetKey, 350.0, 0.70]",
            "Service.TryRend[Controller, Player, Controller.Token, State, Budget, Selection.TargetKey]",
            "Target.Damage(18.0)")
    ordered(method(device, "OnCollapse"), "collapse", "ValidOwner[Agent]",
            "for (Pass := 1..3)", "ChosenKeys.Length > 0",
            "Service.TryCollapse[Controller, Player, Controller.Token, State, Budget]",
            "Target.Damage(Amount)")
    for part in ("GetAEONFALLClassRuntime().GetState[OwnerKey]",
                 'Equipped.ClassId = "CLS-006"',
                 "Service.HasMark(Controller.Token, Key)?",
                 "set Amount = 14.0"):
        need(device, part, "class synergy")
    ordered(method(device, "OnBulwark"), "bulwark", "ValidOwner[Agent]",
            "Maximum > Current and Maximum <= 500.0",
            "Service.RemainingBulwark(Controller.Token)",
            "Service.TryBulwark[Controller, Player, Controller.Token, State, Budget, Restore]",
            "Character.SetShield(Current + Restore)")
    if device.count("Target.Damage(") != 2 or device.count("Character.SetShield(") != 1:
        errors.append("physical effect producers must be exactly audited 2 damage / 1 shield")
    for forbidden in ("SaveProfile(", "OwnerReference.Register", "SetVulnerability(false)",
                      "AddToAll(", "DamageAll(", "Player.Damage(", "1000000.0",
                      "SetMaxShield(", "SetMaxHealth(", "FUS-002"):
        if forbidden in runtime + device:
            errors.append(f"forbidden privilege or effect: {forbidden}")
    return errors


def main() -> int:
    try:
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        runtime = RUNTIME.read_text(encoding="utf-8")
        device = DEVICE.read_text(encoding="utf-8")
        errors = check_sources(policy, runtime, device)
    except (OSError, ValueError, TypeError) as exc:
        errors = [str(exc)]
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print("Sovereign Arsenal source contract passed; native Verse/UEFN unverified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
