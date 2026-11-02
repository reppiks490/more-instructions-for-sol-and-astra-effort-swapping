#!/usr/bin/env python3
"""Fail-closed fusion integration contract checks. NOT a Verse compiler."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "content/sovereign/fusion_integration_contract.json"
SOURCE = ROOT / "verse/sovereign/fusion_state_runtime.verse"
AVATAR = ROOT / "verse/sovereign/sovereign_fusion_device.verse"
ARSENAL = ROOT / "verse/sovereign/sovereign_arsenal_device.verse"
ARSENAL_RUNTIME = ROOT / "verse/sovereign/sovereign_arsenal_runtime.verse"


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
    need(runtime.get("controller_release") ==
         "only_dormant_after_physical_cleanup_and_canonical_teardown",
         "controller release must fail closed while fusion is not dormant")
    receipt = runtime.get("attack_receipt", {})
    need(receipt.get("form_id") == "FUS-001"
         and receipt.get("scope") == "session_one_outstanding"
         and receipt.get("ttl_seconds") == 1,
         "attack receipt must be single-use, generation-bound and short-lived")
    need(receipt.get("issue") == "avatar_upstream_energy_debit_same_deciding_transaction"
         and receipt.get("consume") == "arsenal_secondary_energy_debit_same_deciding_transaction"
         and receipt.get("native_adapter_wiring") == "pending",
         "upstream/downstream receipt wiring must not claim unverified completion")
    need(receipt.get("invalidated_by") == [
         "begin_activation", "begin_separation", "complete_separation",
         "abort", "release_controller"],
         "every fusion phase reset must invalidate outstanding attack receipts")
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
        "GetAEONFALLFusionState()<transacts>",
        "set AEONFALLFusionStateSessions[CurrentSession] = Created",
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
    # Receipt admission is tied to live owner, form and generation; consumption
    # is transactional and must happen only once before downstream damage.
    require("ClearAttackReceipt", "set AttackReceiptPending = false",
            "set AttackReceiptGeneration = 0", "set AttackReceiptExpiresAt = 0.0")
    require("IssueAttackReceipt", "Current = Device", "Existing = Player",
            "Generation = Token", "Phase = aeonfall_fusion_phase.Active",
            'FormId = "FUS-001"', "Gate.CanWield(Player)",
            "if (AttackReceiptPending?):",
            "GetSimulationElapsedTime() < AttackReceiptExpiresAt",
            "set AttackReceiptSequence += 1",
            "set AttackReceiptGeneration = Token",
            "set AttackReceiptExpiresAt = GetSimulationElapsedTime() + 1.0",
            "set AttackReceiptPending = true")
    ordered("IssueAttackReceipt", "Gate.CanWield(Player)",
            "if (AttackReceiptPending?):", "set AttackReceiptSequence += 1",
            "set AttackReceiptPending = true")
    require("ConsumeAttackReceipt", "Current = Device", "Existing = Player",
            "Generation = Token", "Phase = aeonfall_fusion_phase.Active",
            'FormId = "FUS-001"', "Player.IsActive[]",
            "AttackReceiptPending?", "AttackReceiptGeneration = Token",
            "GetSimulationElapsedTime() < AttackReceiptExpiresAt",
            "Gate.CanWield(Player)", "ClearAttackReceipt()",
            "<decides><transacts>:int=")
    ordered("ConsumeAttackReceipt", "AttackReceiptPending?",
            "AttackReceiptGeneration = Token",
            "GetSimulationElapsedTime() < AttackReceiptExpiresAt",
            "Gate.CanWield(Player)", "ClearAttackReceipt()")
    for name in ("BeginActivation", "BeginSeparation", "CompleteSeparation",
                 "Abort", "ReleaseController"):
        require(name, "ClearAttackReceipt()")
    ordered("BeginActivation", "ClearAttackReceipt()", "set Generation += 1")
    ordered("BeginSeparation", "ClearAttackReceipt()", "set Phase = aeonfall_fusion_phase.Separating")
    ordered("CompleteSeparation", "ClearAttackReceipt()", "set Phase = aeonfall_fusion_phase.Dormant")
    ordered("Abort", "ClearAttackReceipt()", "set Phase = aeonfall_fusion_phase.Dormant")
    ordered("ReleaseController", "ClearAttackReceipt()", "set Controller = false")
    require("ReleaseController", "Current = Device", "set Generation += 1",
            "set Controller = false", "set Authority = false",
            'if (Phase <> aeonfall_fusion_phase.Dormant or FormId <> ""):',
            "return false")
    ordered("ReleaseController",
            'if (Phase <> aeonfall_fusion_phase.Dormant or FormId <> ""):',
            "return false", "if (Current := Controller?, Current = Device):",
            "set Controller = false")
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


def check_adapter_attack_handoff(
    avatar_source: str, arsenal_source: str | None,
    arsenal_runtime_source: str | None = None,
) -> list[str]:
    """Conditional fusion adapter source check, NOT Verse execution."""
    errors: list[str] = []
    avatar = "\n".join(
        line.split("#", 1)[0] for line in avatar_source.splitlines()
    )
    arsenal = None if arsenal_source is None else "\n".join(
        line.split("#", 1)[0] for line in arsenal_source.splitlines()
    )

    # The ordinary, already-merged fusion controller has no AttackOutput.
    # Enforce this only when the Avatar team's optional attack bridge lands.
    if re.search(r"\bAttackOutput\s*:\s*trigger_device\b", avatar):
        attack = method(avatar, "Attack")
        if not attack:
            errors.append("Avatar AttackOutput must have an owned Attack method")
        else:
            # Both the upstream energy debit and receipt issuance must occur
            # in one deciding admission before any external trigger signal.
            admission = ""
            if "        if:\n" in attack and "        then:" in attack:
                admission = attack.split("        if:\n", 1)[1].split(
                    "        then:", 1
                )[0]
            spend = admission.find(
                "Resource.Spend[Self, Player, Token, State, AttackEnergyCost]"
            )
            issue = re.search(
                r"([A-Za-z_]\w*)\s*:=\s*State\.IssueAttackReceipt"
                r"\(Self,\s*Player,\s*Token\)",
                admission,
            )
            signal = attack.find("AttackOutput.Trigger(Player)")
            if spend < 0 or issue is None or signal < 0:
                errors.append(
                    "Avatar attack must debit energy, issue canonical receipt "
                    "in the same deciding guard and then signal output"
                )
            else:
                acknowledged = admission.find(issue.group(1) + "?", issue.end())
                if not (spend < issue.start() < acknowledged and
                        acknowledged >= 0 and
                        attack.find("        then:") < signal):
                    errors.append(
                        "Avatar must verify paid receipt before physical output"
                    )

    # The Arsenal-owned file does not exist on main until its draft lands.
    # If present, the Reaver path must reject triggers lacking a paid receipt.
    if arsenal is not None:
        # The native OnRend callback belongs to the Arsenal *device*, while
        # TryRend and the transactional energy receipt belong to its runtime.
        # Synthetic tests may pass a combined fixture as the second argument.
        receipt_runtime = (
            arsenal if arsenal_runtime_source is None else
            "\n".join(line.split("#", 1)[0]
                      for line in arsenal_runtime_source.splitlines())
        )
        rend = method(receipt_runtime, "TryRend")
        if not rend:
            errors.append("Arsenal must expose transactional TryRend")
        else:
            receipt = re.search(
                r"State\.ConsumeAttackReceipt\[\s*Device,\s*Player,"
                r"\s*Token\s*\]",
                rend,
            )
            spend = rend.find("Budget.Spend[Device, Player, Token, State, 5]")
            cooldown = rend.find("set LastRendAt = Now")
            if "<decides><transacts>:void=" not in rend or (
                receipt is None or spend < 0 or cooldown < 0 or
                not (receipt.start() < spend < cooldown)
            ):
                errors.append(
                    "Arsenal TryRend must consume one paid receipt with its "
                    "secondary 5-energy debit and cooldown in a deciding transaction"
                )
        on_rend = method(arsenal, "OnRend")
        if on_rend:
            approved = on_rend.find("Service.TryRend[")
            damage = on_rend.find("Target.Damage(")
            if approved < 0 or damage < approved:
                errors.append(
                    "Arsenal must acknowledge TryRend before attempting native damage"
                )
    return errors


def main() -> int:
    try:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        source = SOURCE.read_text(encoding="utf-8")
        errors = check_contract(contract, source)
        avatar = AVATAR.read_text(encoding="utf-8") if AVATAR.exists() else ""
        arsenal = ARSENAL.read_text(encoding="utf-8") if ARSENAL.exists() else None
        arsenal_runtime = (
            ARSENAL_RUNTIME.read_text(encoding="utf-8")
            if ARSENAL_RUNTIME.exists() else None
        )
        if (arsenal is None) != (arsenal_runtime is None):
            errors.append("Arsenal device/runtime must be present together")
        errors.extend(check_adapter_attack_handoff(
            avatar, arsenal, arsenal_runtime
        ))
    except (OSError, ValueError, TypeError) as exc:
        errors = [str(exc)]
    for error in errors:
        print("ERROR:", error)
    if not errors:
        print("Fusion architecture source guards passed; native UEFN not assessed.")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
