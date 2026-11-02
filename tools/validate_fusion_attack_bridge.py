#!/usr/bin/env python3
"""Static/mutation guard for the opt-in FUS-001 attack signal bridge.

This inspects text only. It is NOT a Verse compiler, UEFN device test, damage
acknowledgement, network replication proof, or Fortnite Launch Session.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "verse/sovereign/sovereign_fusion_device.verse"


def method(source: str, name: str) -> str:
    source = "\n".join(line.split("#", 1)[0] for line in source.splitlines())
    match = re.search(rf"^    {re.escape(name)}(?:<[^>\\n]+>)?\(", source, re.M)
    if not match:
        return ""
    next_method = re.search(r"^    [A-Za-z_][A-Za-z_0-9]*(?:<[^>\\n]+>)?\(", source[match.end():], re.M)
    return source[match.start():match.end() + next_method.start()] if next_method else source[match.start():]


def check_source(source: str) -> list[str]:
    errors: list[str] = []
    attack = method(source, "Attack")
    settings = method(source, "ValidSettings")
    begin = method(source, "OnBegin")
    finish = method(source, "FinishActive")
    expected = (
        "Running?", "Player := player[Agent]", "Player.IsActive[]",
        "Owner := VisualOwner?", "Owner = Player",
        "OriginalCharacter := VisualCharacter?",
        "Character := Player.GetFortCharacter[]",
        "Character = OriginalCharacter", "Character.IsActive[]",
        "State := Runtime?", "Resource := Budget?",
        "Authorized := State.IsAuthorizedActive(Self, Player, Token)",
        "Authorized?", "Now := GetSimulationElapsedTime()",
        "Now >= LastAttackAt + AttackCooldownSeconds",
        "Resource.Spend[Self, Player, Token, State, AttackEnergyCost]",
        "Issued := State.IssueAttackReceipt(Self, Player, Token)",
        "Issued?", "set LastAttackAt = Now", "AttackOutput.Trigger(Player)"
    )
    offset = 0
    for fragment in expected:
        at = attack.find(fragment, offset)
        if at < 0:
            errors.append("Attack missing or reordered: " + fragment)
            break
        offset = at + len(fragment)
    for fragment in (
        "FuseInput <> AttackInput", "SeparateInput <> AttackInput",
        "AttackEnergyCost >= 1", "AttackEnergyCost <= 25",
        "AttackCooldownSeconds >= 2.0", "AttackCooldownSeconds <= 10.0"
    ):
        numeric_end = r"(?![0-9.])" if fragment[-1:].isdigit() else ""
        if not re.search(re.escape(fragment) + numeric_end, settings):
            errors.append("Invalid attack binding/limit: " + fragment)
    if "AttackInput.PressedEvent.Subscribe(Attack)" not in begin:
        errors.append("Missing attack subscription")
    if "set LastAttackAt = -1000.0" not in finish:
        errors.append("Missing cooldown reset after teardown")
    if source.count("AttackOutput.Trigger(") != 1:
        errors.append("Attack physical request must have exactly one producer")
    if any(s in attack for s in ("Trigger()", "TriggerAll(", "AddToAll(", "RemoveFromAll(", "OwnerReference.Register")):
        errors.append("Attack has a global or unauthorized side effect")
    for fragment in (
        "Enabled:logic = false",
        "AttackInput:input_trigger_device",
        "AttackOutput:trigger_device",
        "AttackEnergyCost:int = 10",
        "AttackCooldownSeconds:float = 2.0",
    ):
        if fragment not in source:
            errors.append("Missing safe default: " + fragment)
    return errors


def main() -> int:
    errors = check_source(SOURCE.read_text(encoding="utf-8"))
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print("FUS-001 attack source guard passed; no native Verse/UEFN validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
