#!/usr/bin/env python3
"""Fail-closed fusion integration contract checks. NOT a Verse compiler."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "content/sovereign/fusion_integration_contract.json"
SOURCE = ROOT / "verse/sovereign/fusion_state_runtime.verse"


def method(source: str, name: str) -> str:
    match = re.search(r"^    " + re.escape(name) + r"\(", source, re.M)
    if not match:
        return ""
    following = re.search(r"^    [A-Za-z_][A-Za-z0-9_]*\(", source[match.end():], re.M)
    end = match.end() + following.start() if following else len(source)
    return source[match.start():end]


def check_contract(contract: dict, source: str) -> list[str]:
    errors: list[str] = []
    def need(condition: bool, reason: str) -> None:
        if not condition:
            errors.append(reason)
    def require(name: str, *tokens: str) -> None:
        body = method(code, name)
        for token in tokens:
            need(token in body, f"{name}: missing {token}")
    def ordered(name: str, *tokens: str) -> None:
        body = method(code, name)
        offsets = [body.find(token) for token in tokens]
        need(all(i >= 0 for i in offsets) and offsets == sorted(offsets),
             f"{name}: missing/reordered safety sequence")

    code = "\n".join(line.split("#", 1)[0] for line in source.splitlines())
    need(contract.get("schema_version") == 1, "schema drift")
    need(contract.get("feature") == "one_true_omnigod_sovereign_fusion", "feature drift")
    identity = contract.get("identity", {})
    need(identity.get("existing_authority") == "aeonfall_sovereign_authority_device.CanWield",
         "must reuse existing owner authority")
    need(identity.get("owner_limit") == 1 and identity.get("enabled_by_default") is False,
         "creator entitlement must remain disabled and exclusive")
    need(identity.get("owner_rebind_policy") == "no_rebind_within_session",
         "session owner cannot transfer")
    forms = contract.get("forms", [])
    need(isinstance(forms, list) and len(forms) == 2, "expected exactly two fusion form definitions")
    if isinstance(forms, list) and len(forms) == 2:
        need([f.get("id") for f in forms] == ["FUS-001", "FUS-002"],
             "canonical fusion IDs/order drift")
        need(forms[0].get("enabled_for_native_activation") is False
             and forms[1].get("enabled_for_native_activation") is False,
             "unverified fusion form may not claim native activation")
        need(forms[1].get("status") == "experimental_design_only", "Titan must remain experimental")
    need(contract.get("states") == ["Dormant", "Activating", "Active", "Separating"],
         "phase state list drift")
    need(contract.get("transitions") == [["Dormant", "Activating"], ["Activating", "Active"],
                                        ["Active", "Separating"], ["Separating", "Dormant"]],
         "transition graph drift")
    need(contract.get("abort_to") == "Dormant", "abort must return to Dormant")
    runtime = contract.get("runtime", {})
    need(runtime.get("source") == "verse/sovereign/fusion_state_runtime.verse",
         "runtime path drift")
    need(runtime.get("single_controller_lease") is True, "single-owner controller lease required")
    need(runtime.get("max_simultaneous_fusions") == 1, "fusion concurrency limit drift")
    need(runtime.get("physical_effects") == "adapter_owned_not_implemented",
         "native effect implementation must not be falsely claimed")
    preservation = contract.get("preservation", {})
    need(preservation.get("canonical_sovereign_ability_id") == "UNI-001"
         and preservation.get("player_profile_schema_change") is False
         and preservation.get("ordinary_unlockable") is False,
         "existing sovereign identity/profile must be preserved")
    evidence = contract.get("evidence", {})
    for key in ("native_verse_compile", "fortnite_launch_session",
                "physical_editor_binding", "publication"):
        need(evidence.get(key) == "not_run", f"unsupported native evidence: {key}")

    for token in (
        "aeonfall_fusion_phase := enum:", "Dormant", "Activating", "Active", "Separating",
        "var Controller:?creative_device = false",
        "var Authority:?aeonfall_sovereign_authority_device = false",
        "var Owner:?player = false", "var Generation:int = 0",
        "AEONFALLFusionStateSessions:weak_map(session, aeonfall_fusion_state_runtime)",
        "GetAEONFALLFusionStateRuntime()<decides><transacts>",
        "set AEONFALLFusionStateSessions[GetSession()] = Created",
    ):
        need(token in code, f"missing session/runtime contract: {token}")

    require("AcquireController", "if (Controller?):", "set Controller = option{Device}",
            "set Authority = option{VerifiedAuthority}")
    require("OwnsController", "Current = Device")
    require("BeginActivation", 'RequestedFormId <> "FUS-001"', "Current = Device",
            "Gate := Authority?", "Player.IsActive[]", "Gate.CanWield(Player)",
            "not Authorized?", "Existing <> Player", "set Generation += 1",
            "set Phase = aeonfall_fusion_phase.Activating", "return option{Generation}")
    ordered("BeginActivation", "Current = Device", "Gate.CanWield(Player)",
            "not Authorized?", "Existing <> Player", "set Generation += 1")
    require("ConfirmActivated", "Current = Device", "Existing = Player", "Generation = Token",
            "Phase = aeonfall_fusion_phase.Activating", "Gate.CanWield(Player)",
            "set Phase = aeonfall_fusion_phase.Active")
    require("BeginSeparation", "Current = Device", "Existing = Player", "Generation = Token",
            "Phase = aeonfall_fusion_phase.Active", "Gate.CanWield(Player)",
            "set Phase = aeonfall_fusion_phase.Separating")
    require("CompleteSeparation", "Current = Device", "Generation = Token",
            "Phase = aeonfall_fusion_phase.Separating", "set FormId = \"\"",
            "set Generation += 1")
    require("IsAuthorizedActive", "Current = Device", "Existing = Player",
            "Generation = Token", "Gate.CanWield(Player)")
    require("Abort", "Current = Device", "Generation = Token",
            "set Phase = aeonfall_fusion_phase.Dormant", "set Generation += 1")
    require("ReleaseController", "Current = Device", "set Generation += 1",
            "set Controller = false", "set Authority = false")
    for name in ("Abort", "ReleaseController", "CompleteSeparation"):
        need("Gate.CanWield" not in method(code, name),
             f"{name}: cleanup must work after authority revocation")
    for name in ("Abort", "ReleaseController", "CompleteSeparation"):
        need("set Owner = false" not in method(code, name),
             f"{name}: owner rebind forbidden")
    for forbidden in ("OwnerReference.Register(", "GetPlayerName(", "GetTeam(",
                      "AEONFALLPlayerProfiles[", "SaveProfile(", '"FUS-002"'):
        need(forbidden not in code, f"forbidden authority/persistence/Titan pattern: {forbidden}")
    return errors


def main() -> int:
    try:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        source = SOURCE.read_text(encoding="utf-8")
        errors = check_contract(contract, source)
    except (OSError, ValueError, TypeError) as exc:
        errors = [str(exc)]
    for error in errors:
        print("ERROR:", error)
    if not errors:
        print("Fusion architecture source guards passed; native UEFN not assessed.")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
