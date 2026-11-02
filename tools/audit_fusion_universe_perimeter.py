#!/usr/bin/env python3
"""Cross-owner source perimeter audit. Not a Verse compiler or native UEFN proof.

No authority or native status is granted by this audit. It deliberately spans
Architect, Avatar, Arsenal and Titan contracts without modifying their owners.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = {
    "identity": "content/sovereign/owner_identity.json",
    "contract": "content/sovereign/fusion_integration_contract.json",
    "titan": "content/sovereign/titan_proxy_experiment.json",
    "policy": "content/implementation/universe_first_policy.json",
    "authority": "verse/sovereign/sovereign_authority_device.verse",
    "state": "verse/sovereign/fusion_state_runtime.verse",
    "avatar": "verse/sovereign/sovereign_fusion_device.verse",
    "budget": "verse/sovereign/sovereign_fusion_runtime.verse",
    "arsenal": "verse/sovereign/sovereign_arsenal_runtime.verse",
    "arsenal_device": "verse/sovereign/sovereign_arsenal_device.verse",
}
JSON_KEYS = {"identity", "contract", "titan", "policy"}


def read_sources(root: Path = ROOT) -> dict[str, str]:
    return {name: (root / path).read_text(encoding="utf-8")
            for name, path in PATHS.items()}


def uncomment(source: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in source.splitlines())


def section(source: str, method: str) -> str:
    code = uncomment(source)
    start = re.search(r"^    " + re.escape(method) + r"(?:<[^>\n]+>)*\(", code, re.M)
    if start is None:
        return ""
    tail = re.search(r"^    [A-Za-z_]\w*(?:<[^>\n]+>)*\(", code[start.end():], re.M)
    end = start.end() + tail.start() if tail else len(code)
    return code[start.start():end]


def audit(sources: dict[str, str]) -> list[str]:
    errors: list[str] = []
    def need(condition: bool, reason: str) -> None:
        if not condition:
            errors.append(reason)
    def has(key: str, fragment: str, reason: str) -> None:
        need(fragment in uncomment(sources[key]), reason)
    def ordered(body: str, *fragments: str) -> bool:
        position = 0
        for fragment in fragments:
            found = body.find(fragment, position)
            if found < 0:
                return False
            position = found + len(fragment)
        return True

    try:
        data = {key: json.loads(sources[key]) for key in JSON_KEYS}
    except (ValueError, KeyError, TypeError) as exc:
        return [f"invalid source data: {exc}"]
    identity, contract, titan, policy = (data[key] for key in
                                          ("identity", "contract", "titan", "policy"))
    need(identity.get("ability_id") == "UNI-001" and identity.get("owner_limit") == 1,
         "creator identity / UNI-001 exclusivity drift")
    need(contract.get("identity", {}).get("existing_authority") ==
         "aeonfall_sovereign_authority_device.CanWield", "alternate owner authority")
    need([form.get("id") for form in contract.get("forms", [])] ==
         ["FUS-001", "FUS-002"], "canonical fusion form IDs drift")
    need(all(form.get("enabled_for_native_activation") is False
             for form in contract.get("forms", [])), "unverified fusion native enablement")
    if identity.get("authority_enabled") or identity.get("native_player_reference_provisioned"):
        need(identity.get("account_identity_verified") is True and
             identity.get("epic_account_id"), "owner grant lacks verified native account evidence")
        need(False, "source-only review cannot approve native owner provisioning")
    need(policy.get("strategy") == "full_universe_source_before_playable_prototype"
         and policy.get("no_cutdown_scope") is True
         and policy.get("minimum_major_entities", 0) >= 800,
         "universe-first/no-sample policy weakened")
    need(policy.get("no_codex_in_automation") is True and
         policy.get("source_complete_does_not_imply_native_complete") is True,
         "Codex or native-truth policy weakened")
    need("SYS-OWNER-OMNIGOD-FUSION" in
         [entry.get("id") for entry in policy.get("required_systems", [])],
         "universe source gate lost owner fusion system")
    need(titan.get("canonical_form") == "FUS-002" and
         titan.get("f002_activation") == "disabled" and
         titan.get("activation_default") is False and
         titan.get("attack", {}).get("direct_damage") is False,
         "experimental Titan enabled or damaging")
    need(titan.get("native_evidence", {}).get("uefn_compile") == "not_run",
         "Titan native compilation fabricated")

    authority = uncomment(sources["authority"])
    has("authority", "AEONFALLSovereignAuthorityLease:weak_map(session,", "missing authority lease")
    has("authority", "Enabled:logic = false", "authority default must deny")
    need("OwnerReference.Register(" not in authority, "untrusted owner reference registration")
    need(ordered(section(sources["authority"], "CanWield"), "Enabled?", "Running?",
                 "not Revoked?", "Bound = Player", "OwnerReference.IsReferenced[Player]"),
         "native owner CanWield lost live reference/revocation checks")
    need(ordered(section(sources["authority"], "OnEnd"),
                 "set Running = false", "set Revoked = true"),
         "authority shutdown must revoke")

    has("state", "AEONFALLFusionStateSessions:weak_map(session,", "fusion state not session scoped")
    need(ordered(section(sources["state"], "BeginActivation"),
                 'RequestedFormId <> "FUS-001"', "Gate.CanWield(Player)",
                 "Existing <> Player", "set Generation += 1",
                 "set Phase = aeonfall_fusion_phase.Activating"),
         "fusion admission bypasses form/owner/generation")
    need(ordered(section(sources["state"], "ReleaseController"),
                 'Phase <> aeonfall_fusion_phase.Dormant or FormId <> ""',
                 "return false", "ClearAttackReceipt()", "set Controller = false"),
         "controller released before canonical cleanup")
    need("set Owner = false" not in section(sources["state"], "ReleaseController"),
         "fusion owner rebound during session")
    need(ordered(section(sources["state"], "Abort"), "ClearAttackReceipt()",
                 "set Phase = aeonfall_fusion_phase.Dormant", "set Generation += 1"),
         "abort must invalidate pending attacks and generations")
    need(ordered(section(sources["state"], "ConsumeAttackReceipt"),
                 "AttackReceiptPending?", "AttackReceiptGeneration = Token",
                 "GetSimulationElapsedTime() < AttackReceiptExpiresAt",
                 "Gate.CanWield(Player)", "ClearAttackReceipt()"),
         "paid attack replay / expiry / authority guard missing")

    has("avatar", "Enabled:logic = false", "fusion adapter enabled without native evidence")
    need(ordered(section(sources["avatar"], "Fuse"),
                 'State.BeginActivation(Self, Player, "FUS-001")',
                 "Resource.Start(Self, Started", "ArmorGlow.Pickup(Player)",
                 "ArmorGlow.HasEffect[Player]", "State.ConfirmActivated(Self, Player, Started)"),
         "fusion confirmation precedes native acknowledgement")
    need(ordered(section(sources["avatar"], "FinishActive"),
                 "ClearPhysical()", "State.BeginSeparation(", "State.CompleteSeparation("),
         "fusion physical teardown does not precede canonical separation")
    need(ordered(section(sources["avatar"], "OnEnd"),
                 "FinishActive()", "State.ReleaseController(Self)",
                 "Resource.ReleaseController(Self)"),
         "shutdown releases leases before cleanup")
    need(ordered(section(sources["avatar"], "Attack"),
                 "State.IsAuthorizedActive(Self, Player, Token)",
                 "Resource.Spend[Self, Player, Token, State, AttackEnergyCost]",
                 "State.IssueAttackReceipt(Self, Player, Token)",
                 "AttackOutput.Trigger(Player)"),
         "Avatar attack lacks paid admission handoff")
    need(ordered(section(sources["budget"], "Spend"),
                 "State.IsAuthorizedActive(Device, Player, NewToken)",
                 "Remaining >= Cost", "set Remaining -= Cost"),
         "energy spend not tied to live fusion and bounded balance")
    need(ordered(section(sources["arsenal"], "TryRend"),
                 "State.ConsumeAttackReceipt[Device, Player, Token]",
                 "Budget.Spend[Device, Player, Token, State, 5]",
                 "set LastRendAt = Now"),
         "Arsenal paid attack not transactionally admitted")
    need(ordered(section(sources["arsenal_device"], "OnRend"),
                 "Service.TryRend[Controller, Player, Controller.Token",
                 "Target.Damage(18.0)"),
         "native damage not downstream of paid receipt")
    need(section(sources["arsenal_device"], "OnRend").count("Target.Damage(18.0)") == 1,
         "Reaver must apply damage exactly once")
    has("arsenal_device", "Enabled:logic = false", "Arsenal adapter enabled without native evidence")
    need("not player[Candidate]" in section(sources["arsenal_device"], "EligibleTarget"),
         "Reaver target selection admits players")
    return errors


def main() -> int:
    try:
        errors = audit(read_sources())
    except (OSError, ValueError) as exc:
        errors = [str(exc)]
    for error in errors:
        print("FAIL:", error)
    if not errors:
        print("PASS: source-only fusion universe security perimeter; native UEFN not tested")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
