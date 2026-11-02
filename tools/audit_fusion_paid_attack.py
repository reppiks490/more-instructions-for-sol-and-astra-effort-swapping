#!/usr/bin/env python3
"""Independent source-only audit of FUS-001 paid Reaver handoff.

Run explicitly during integration. This is NOT a Verse compiler, a proof of
physical trigger provenance, or a Fortnite multiplayer Launch Session.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
AVATAR = ROOT / "verse/sovereign/sovereign_fusion_device.verse"
ARSENAL_RUNTIME = ROOT / "verse/sovereign/sovereign_arsenal_runtime.verse"
ARSENAL_DEVICE = ROOT / "verse/sovereign/sovereign_arsenal_device.verse"


def uncomment(source: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in source.splitlines())


def method(source: str, name: str) -> str:
    """Read one four-space Verse member, not an unrelated method or comment."""
    start = re.search(rf"^    {re.escape(name)}(?:<[^>\n]+>)?\(", source, re.M)
    if start is None:
        return ""
    tail = source[start.end():]
    following = re.search(r"^    [A-Za-z_]\w*(?:<[^>\n]+>)?\(", tail, re.M)
    return source[start.start():start.end() + following.start()] if following else source[start.start():]


def check_sources(avatar_source: str, runtime_source: str, device_source: str) -> list[str]:
    """Return integration violations; individual valid-owner checks are insufficient."""
    errors: list[str] = []
    avatar = uncomment(avatar_source)
    runtime = uncomment(runtime_source)
    device = uncomment(device_source)

    if "AttackOutput:trigger_device" not in avatar:
        errors.append("Avatar has no instigator-scoped AttackOutput binding")
    attack = method(avatar, "Attack")
    if not attack:
        errors.append("Avatar Attack admission is absent")
    else:
        guard = re.search(r"\n        if:\s*\n(.*?)\n        then:", attack, re.S)
        admission = guard.group(1) if guard else ""
        spend = admission.find("Resource.Spend[Self, Player, Token, State, AttackEnergyCost]")
        issue = re.search(
            r"\b([A-Za-z_]\w*)\s*:=\s*State\.IssueAttackReceipt\(Self,\s*Player,\s*Token\)",
            admission,
        )
        if spend < 0:
            errors.append("Avatar must pay upstream energy in its deciding admission")
        if issue is None or spend < 0 or issue.start() <= spend:
            errors.append("Avatar must issue a receipt after payment in the same admission")
        elif not re.search(rf"\b{re.escape(issue.group(1))}\?", admission[issue.end():]):
            errors.append("Avatar must acknowledge successful receipt issuance before output")
        signal = attack.find("AttackOutput.Trigger(Player)")
        then = attack.find("\n        then:")
        if signal < 0 or then < 0 or signal < then:
            errors.append("Avatar physical signal must follow paid admission")
    if avatar.count("AttackOutput.Trigger(") != 1:
        errors.append("Avatar must have exactly one physical attack-output producer")

    rend = method(runtime, "TryRend")
    if not rend:
        errors.append("Arsenal runtime TryRend missing (do not scan device for this method)")
    else:
        header = rend.split("=", 1)[0]
        if "<decides><transacts>" not in header:
            errors.append("Arsenal TryRend must be a deciding transaction")
        receipt = rend.find("State.ConsumeAttackReceipt[Device, Player, Token]")
        spend = rend.find("Budget.Spend[Device, Player, Token, State, 5]")
        cooldown = rend.find("set LastRendAt = Now")
        if min(receipt, spend, cooldown) < 0 or not receipt < spend < cooldown:
            errors.append("Arsenal must consume one paid receipt before secondary spend/cooldown")

    on_rend = method(device, "OnRend")
    if "RendRequest.TriggeredEvent.Subscribe(OnRend)" not in device:
        errors.append("Arsenal RendRequest callback binding missing")
    if not on_rend:
        errors.append("Arsenal OnRend callback missing")
    else:
        approved = on_rend.find("Service.TryRend[")
        damage = on_rend.find("Target.Damage(")
        if approved < 0 or damage < approved:
            errors.append("Arsenal must gate native damage behind successful TryRend")
    owner = method(device, "ValidOwner")
    for required in ("Owner = Player", "Character = Original", "State.IsAuthorizedActive("):
        if required not in owner:
            errors.append("Arsenal ValidOwner missing: " + required)
    return errors


def main() -> int:
    try:
        errors = check_sources(
            AVATAR.read_text(encoding="utf-8"),
            ARSENAL_RUNTIME.read_text(encoding="utf-8"),
            ARSENAL_DEVICE.read_text(encoding="utf-8"),
        )
    except OSError as exc:
        errors = [str(exc)]
    for error in errors:
        print("FUSION QA BLOCKER:", error, file=sys.stderr)
    if not errors:
        print("FUS-001 paid-attack source handoff checks passed; native UEFN NOT RUN.")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
