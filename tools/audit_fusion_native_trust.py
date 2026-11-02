#!/usr/bin/env python3
"""AEONFALL sovereign-fusion source trust-boundary ledger.

Reports specific unclosed native integration boundaries. This is NOT a Verse
compiler, editor binding test, or security attestation. Do not use it to grant
entitlements or infer completed universe source packages.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "identity": "content/sovereign/owner_identity.json",
    "contract": "content/sovereign/fusion_integration_contract.json",
    "avatar": "verse/sovereign/sovereign_fusion_device.verse",
    "arsenal": "verse/sovereign/sovereign_arsenal_device.verse",
    "arsenal_runtime": "verse/sovereign/sovereign_arsenal_runtime.verse",
    "state": "verse/sovereign/fusion_state_runtime.verse",
    "actor_registry": "verse/core/actor_registry.verse",
}


def read_sources(root: Path = ROOT) -> dict[str, str]:
    return {key: (root / path).read_text(encoding="utf-8")
            for key, path in FILES.items()}


def method(source: str, name: str) -> str:
    """Extract a class-level Verse method for a conservative structural check."""
    code = "\n".join(line.split("#", 1)[0] for line in source.splitlines())
    start = re.search(r"^    " + re.escape(name) + r"(?:<[^>\n]+>)*\(", code, re.M)
    if not start:
        return ""
    end = re.search(r"^    [A-Za-z_]\w*(?:<[^>\n]+>)*\(",
                    code[start.end():], re.M)
    return code[start.start():start.end() + end.start()] if end else code[start.start():]


def evaluate(sources: dict[str, str]) -> list[dict[str, str]]:
    """Return unresolved boundaries; absence of findings is NOT native proof."""
    findings: list[dict[str, str]] = []

    def flag(code: str, owner: str, observation: str, acceptance: str) -> None:
        findings.append({"id": code, "owner": owner,
                         "observation": observation, "required_acceptance": acceptance})

    identity = json.loads(sources["identity"])
    contract = json.loads(sources["contract"])
    avatar, arsenal = sources["avatar"], sources["arsenal"]
    arsenal_runtime, state = sources["arsenal_runtime"], sources["state"]
    actor_registry = sources["actor_registry"]

    # The user-facing display-name reference must never become an owner grant.
    if (identity.get("account_identity_verified") is not True or
            identity.get("native_player_reference_provisioned") is not True or
            not identity.get("epic_account_id") or
            identity.get("authority_enabled") is not True):
        flag("FNT-001", "Architect / Avatar",
             "Creator account and trusted native Player Reference are not provisioned.",
             "Verify the intended account out of band, secure native provisioning, "
             "and independently deny a second client and spoofed input in UEFN.")

    forms = {f.get("id"): f for f in contract.get("forms", [])}
    if not forms.get("FUS-001", {}).get("enabled_for_native_activation"):
        flag("FNT-002", "Architect / Avatar / QA",
             "FUS-001 remains disabled for native activation by contract.",
             "Require real compiled, bound, two-client and teardown evidence "
             "before a separately authorized enablement change.")
    if forms.get("FUS-002", {}).get("enabled_for_native_activation"):
        flag("FNT-003", "Architect / Avatar",
             "Experimental FUS-002 was enabled without a native acceptance record.",
             "Re-disable FUS-002; require independent NPC and session proof.")

    # One-use receipt is an admission capability, not a correlation ID. A
    # separate trigger subscriber can race the legitimate event while a valid
    # receipt is pending. Do not silently mark this as fixed by the receipt.
    if ("RendRequest.TriggeredEvent.Subscribe(OnRend)" in arsenal and
            "AttackOutput.Trigger(Player)" in avatar):
        flag("FNT-004", "Architect / Avatar / Arsenal",
             "An instigator-only trigger can consume an outstanding paid receipt "
             "without binding the exact emitted request sequence.",
             "Use a trusted non-public request channel or bind a server-owned "
             "request ID to the same receipt and exact native callback; test "
             "preemption and replay with two clients.")

    # A canonical runtime key is not a catalog whitelist. The current
    # registry accepts any nonempty canonical ID; a MON- prefix is insufficient.
    register = method(actor_registry, "Register")
    monster = method(arsenal, "IsMonsterId")
    if ("CanonicalId <> \"\"" in register or
            ("Id.Length >= 4" in monster and "Id[3] = '-'" in monster)):
        flag("FNT-005", "Runtime Forge / Arsenal / QA",
             "The registry/Arsenal identity boundary still accepts nonempty "
             "or prefix-only MON values without a complete canonical catalog check.",
             "Bind native actor registration to canonical catalog membership "
             "and exact MON-[0-9]{3,4} ASCII syntax, retaining runtime key "
             "and live agent/character identity at settlement.")

    eligible = method(arsenal, "EligibleTarget")
    if not re.search(r"\b(?:LineOfSight|HasLineOfSight|CoverValidated|VerifiedLOS)\b", eligible):
        flag("FNT-006", "Arsenal / QA",
             "Target eligibility checks range/cone but contains no explicit "
             "verified cover/line-of-sight admission.",
             "Implement a UEFN-supported authoritative cover/LOS policy and "
             "prove occluded targets cannot be damaged in native sessions.")

    begin = method(arsenal, "OnBegin")
    noneditable_gate = bool(re.search(
        r"(?m)^    NativeSourceGate:logic = false\s*$", arsenal
    )) and not bool(re.search(r"@editable\s*\n\s*NativeSourceGate", arsenal))
    gate_at = begin.find("not NativeSourceGate?")
    subscriptions_at = begin.find("Subscribe(")
    if not (noneditable_gate and gate_at >= 0 and
            (subscriptions_at < 0 or gate_at < subscriptions_at)):
        flag("FNT-007", "Arsenal / QA",
             "The Arsenal device's editable Enabled flag is not protected "
             "by a non-editable universe-first native source gate.",
             "Keep input subscriptions hard-disabled until source, LOS, "
             "native bindings and release approval are independently proven.")

    cooldown = re.search(r"AttackCooldownSeconds:float\s*=\s*(\d+(?:\.\d+)?)", avatar)
    minimum = re.search(r"AttackCooldownSeconds\s*>=\s*(\d+(?:\.\d+)?)", avatar)
    reaver = re.search(r"Now\s*>=\s*LastRendAt\s*\+\s*(\d+(?:\.\d+)?)", arsenal_runtime)
    if not (cooldown and minimum and reaver):
        flag("FNT-008", "Avatar / Arsenal",
             "The Avatar-to-Reaver cooldown contract cannot be structurally verified.",
             "Establish and test matching minimum/default upstream and "
             "downstream cooldowns before enabling native attacks.")
    elif (float(cooldown.group(1)) < float(reaver.group(1)) or
          float(minimum.group(1)) < float(reaver.group(1))):
        flag("FNT-008", "Avatar / Arsenal",
             "Avatar cooldown default/minimum permit admissions faster than "
             "Arsenal Reaver's 2-second reservation.",
             "Align both Avatar bounds with the actual downstream cooldown "
             "and rerun exact-head source and native timing tests.")

    # A JSON evidence marker is NOT independently verifiable native proof.
    # This tool has no editor access; never let changing a status string make
    # the native release blocker disappear.
    evidence = contract.get("evidence", {})
    native_fields = ("native_verse_compile", "fortnite_launch_session",
                     "physical_editor_binding")
    if any(evidence.get(field) != "not_run" for field in native_fields):
        observation = "Native evidence fields changed; this source audit cannot authenticate them."
    else:
        observation = "No UEFN compile, editor bindings or Launch Session are verified."
    flag("FNT-009", "QA / UEFN operator", observation,
         "Attach independently inspectable editor revision, compiler output, "
         "two-client trace, Fortnite-mobile profile and actual cooked 300 MiB "
         "calculation; validate outside this source-only tool.")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, help="Write source-only blocker ledger")
    parser.add_argument("--require-source-trust", action="store_true",
                        help="Fail while source/native trust boundaries remain")
    args = parser.parse_args()
    try:
        findings = evaluate(read_sources())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("SOURCE AUDIT ERROR:", exc)
        return 1
    report = {
        "schema_version": 1,
        "scope": "architect_cross_loop_native_trust_source_inspection",
        "native_uefn_verified": False,
        "universe_source_complete": "not_assessed",
        "findings": findings,
        "count": len(findings),
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8")
    for item in findings:
        print(f"{item['id']} [{item['owner']}]: {item['observation']}")
    print("SOURCE-ONLY: native UEFN, mobile, multiplayer and cooked memory NOT assessed")
    return 2 if args.require_source_trust and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
