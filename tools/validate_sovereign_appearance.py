#!/usr/bin/env python3
"""Source regression guards for owner-only native disguise; does not execute Verse."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = "verse/sovereign/sovereign_appearance_device.verse"
POLICY_PATH = "content/sovereign/sovereign_appearance.json"


def code(text: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


def method(source: str, name: str) -> str:
    match = re.search(rf"^    {re.escape(name)}(?:<[^\n]*?>)?\(", source, re.M)
    if not match:
        return ""
    following = re.search(r"^    [A-Za-z_][A-Za-z0-9_]*(?:<[^\n]*?>)?\(", source[match.end():], re.M)
    end = match.end() + following.start() if following else len(source)
    return source[match.start():end]


def check_source(source: str, policy: dict) -> list[str]:
    source = code(source)
    errors: list[str] = []

    def contains(text: str, fragment: str) -> bool:
        suffix = r"(?![0-9.])" if fragment[-1:].isdigit() else ""
        return bool(re.search(re.escape(fragment) + suffix, text))

    def need(fragment: str):
        if not contains(source, fragment):
            errors.append(f"appearance: missing {fragment}")

    def scoped(name: str, *fragments: str):
        block = method(source, name)
        for fragment in fragments:
            if not contains(block, fragment):
                errors.append(f"appearance.{name}: missing {fragment}")

    def ordered(name: str, *fragments: str):
        block = method(source, name)
        cursor = 0
        for fragment in fragments:
            position = block.find(fragment, cursor)
            if position < 0:
                errors.append(f"appearance.{name}: missing or reordered lifecycle gates")
                return
            cursor = position + len(fragment)

    need("Enabled:logic = false")
    need("weak_map(session, ?aeonfall_sovereign_appearance_device)")
    need("Authority:aeonfall_sovereign_authority_device")
    need("Disguise:disguise_device")
    scoped("AcquireLease", "Existing = Self", "set AEONFALLSovereignAppearanceLease[Session] = option{Self}")
    scoped("SpawnConfigurationSafe", "Automatic := Disguise.ShouldApplyDisguiseOnPlayerSpawn?", "not Automatic?", "return true", "false")
    ordered("OnBegin", "SpawnConfigurationSafe()", "not Disguise.IsEnabled[]", "AcquireLease[]", "Disguise.Enable()")
    startup = method(source, "OnBegin")
    if startup.find("Disguise.Enable()") < startup.find("AcquireLease[]"):
        errors.append("appearance.OnBegin: native enable cannot precede sole-controller acquisition")
    scoped("FindAuthorizedTarget", "Player.IsActive[]", "Character := Player.GetFortCharacter[]",
           "Character.IsActive[]", "Authorized := Authority.CanWield(Player)", "Authorized?", "GetPlayers().Length <= 512")
    scoped("Reconcile", "Previous <> Target.Character", "ClearOwnedDisguise()", "set Attempts = 0",
           "Disguise.IsDisguiseApplied[Target.Player]", "Attempts >= 16", "set Attempts += 1")
    scoped("Reconcile", "if (Disguise.IsDisguiseApplied[Target.Player]):\n            set Confirmed = true\n            return")
    ordered("Reconcile", "Disguise.ApplyDisguise(Target.Player)", "Disguise.IsDisguiseApplied[Target.Player]", "set Confirmed = true")
    scoped("MaintenanceLoop", "SpawnConfigurationSafe()", "FindAuthorizedTarget()", "Reconcile(Target)",
           "ClearOwnedDisguise()", "Sleep(1.0)")
    scoped("ClearOwnedDisguise", "OwnedPlayer?", "Player.IsActive[]", "Disguise.RemoveDisguise(Player)",
           "set OwnedPlayer = false", "set OwnedCharacter = false", "set Attempts = 0", "set Confirmed = false")
    scoped("OnEnd", "StopEvent.Signal()", "ClearOwnedDisguise()", "Disguise.Disable()",
           "Existing = Self", "set AEONFALLSovereignAppearanceLease[Session] = false")
    for forbidden in ("RemoveAnyDisguise", ".Show()", ".Hide()", "GetPlayerName", "GetTeam", "OwnerReference.Register",
                      "SpawnProp(", "npc_spawner_device", "Service.IsActive", "SovereignRuntime"):
        if forbidden in source:
            errors.append(f"appearance: forbidden appearance or authorization mechanism {forbidden}")
    if source.count("Disguise.ApplyDisguise(") != 1:
        errors.append("appearance: one audited native application site required")
    for block_name in ("Reconcile", "ClearOwnedDisguise", "OnBegin", "OnEnd"):
        header = method(source, block_name).splitlines()[0:1]
        if header and "<transacts>" in header[0]:
            errors.append(f"appearance.{block_name}: native effects cannot use transactional method")
    if re.search(r"if\s*\([^\n]*Disguise\.(?:ApplyDisguise|RemoveDisguise|Enable|Disable)\(", source):
        errors.append("appearance: irreversible native calls cannot be failure conditions")
    if "GetFortCharacter()" in source:
        errors.append("appearance: native failable GetFortCharacter requires []")
    expected = {
        "id": "UNI-001-APPEARANCE", "enabled_by_default": False, "owner_limit": 1,
        "authorization": "aeonfall_sovereign_authority_device.CanWield",
        "independent_of_world_manifestation": True,
        "native.device": "disguise_device", "native.palette": "fixed_combat_or_casual_catalog",
        "native.arbitrary_uploaded_player_skin": False,
        "native.required_options.apply_disguise_on_player_spawn": False,
        "native.required_options.start_enabled": False,
        "native.required_options.disguise_breaks_on_attack": "Off",
        "native.required_options.disguise_breaks_on_damage": "Off",
        "retry.interval_seconds": 1, "retry.maximum_attempts_per_character": 16,
        "engine_verification.compile": "not_run", "engine_verification.session": "not_run",
    }
    for key, expected_value in expected.items():
        value = policy
        for part in key.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        if type(value) is not type(expected_value) or value != expected_value:
            errors.append(f"appearance policy drift: {key}")
    return errors


def main() -> int:
    try:
        source = (ROOT / SOURCE_PATH).read_text(encoding="utf-8")
        policy = json.loads((ROOT / POLICY_PATH).read_text(encoding="utf-8"))
        errors = check_source(source, policy)
    except (OSError, ValueError) as error:
        errors = [str(error)]
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print("Sovereign appearance source and authored policy guards passed; engine execution not run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
