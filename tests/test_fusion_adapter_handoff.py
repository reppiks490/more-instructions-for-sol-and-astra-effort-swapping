"""Conditional source-mutation tests for Avatar/Arsenal paid Reaver handoff.

These fixtures are contract models only, not UEFN compilation or Verse execution.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "fusion_architecture_guard", ROOT / "tools/validate_fusion_architecture.py"
)
assert SPEC and SPEC.loader
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)

AVATAR = """
aeonfall_sovereign_fusion_device := class(creative_device):
    AttackOutput:trigger_device = trigger_device{}
    Attack(Agent:agent):void=
        if:
            Resource.Spend[Self, Player, Token, State, AttackEnergyCost]
            Issued := State.IssueAttackReceipt(Self, Player, Token)
            Issued?
        then:
            set LastAttackAt = Now
            AttackOutput.Trigger(Player)
    OnEnd<override>():void=
        return
"""

ARSENAL = """
aeonfall_sovereign_arsenal_runtime := class:
    TryRend(
        Device:creative_device, Player:player, Token:int
    )<decides><transacts>:void=
        State.ConsumeAttackReceipt[Device, Player, Token]
        Budget.Spend[Device, Player, Token, State, 5]
        set LastRendAt = Now
    OnRend(MaybeAgent:?agent):void=
        if (Service.TryRend[Controller, Player, Controller.Token,
                           State, Budget, Selection.TargetKey]):
            Target.Damage(18.0)
    OnEnd<override>():void=
        return
"""


class FusionHandoffGuards(unittest.TestCase):
    def check(self, avatar=AVATAR, arsenal=ARSENAL):
        return guard.check_adapter_attack_handoff(avatar, arsenal)

    def test_valid_paid_handoff(self):
        self.assertEqual(self.check(), [])

    def test_old_main_without_attack_bridge_remains_valid(self):
        self.assertEqual(self.check("    Fuse(Agent:agent):void=\n        return\n", None), [])

    def test_avatar_can_land_before_arsenal_when_receipt_wired(self):
        self.assertEqual(self.check(AVATAR, None), [])

    def test_avatar_without_paid_receipt_rejected(self):
        self.assertTrue(self.check(
            AVATAR.replace("Issued := State.IssueAttackReceipt(Self, Player, Token)",
                           "Issued := true")
        ))

    def test_avatar_receipt_issued_after_guard_rejected(self):
        self.assertTrue(self.check(
            AVATAR.replace("            Issued := State.IssueAttackReceipt(Self, Player, Token)\n",
                           "").replace("            AttackOutput.Trigger(Player)",
                                        "            Issued := State.IssueAttackReceipt(Self, Player, Token)\n"
                                        "            AttackOutput.Trigger(Player)")
        ))

    def test_avatar_missing_receipt_ack_rejected(self):
        self.assertTrue(self.check(AVATAR.replace("            Issued?\n", "")))

    def test_avatar_no_upstream_debit_rejected(self):
        self.assertTrue(self.check(
            AVATAR.replace("Resource.Spend[Self, Player, Token, State, AttackEnergyCost]",
                           "true?")
        ))

    def test_arsenal_without_receipt_rejected(self):
        self.assertTrue(self.check(
            arsenal=ARSENAL.replace(
                "State.ConsumeAttackReceipt[Device, Player, Token]", "true?"
            )
        ))

    def test_arsenal_receipt_after_secondary_debit_rejected(self):
        receipt = "        State.ConsumeAttackReceipt[Device, Player, Token]\n"
        spend = "        Budget.Spend[Device, Player, Token, State, 5]\n"
        self.assertTrue(self.check(
            arsenal=ARSENAL.replace(receipt + spend, spend + receipt)
        ))

    def test_arsenal_must_be_deciding_transaction(self):
        self.assertTrue(self.check(
            arsenal=ARSENAL.replace("<decides><transacts>:void=", ":void=")
        ))

    def test_arsenal_cannot_damage_before_authorized_commit(self):
        on_rend = ARSENAL.replace(
            "        if (Service.TryRend[Controller, Player, Controller.Token,\n"
            "                           State, Budget, Selection.TargetKey]):\n"
            "            Target.Damage(18.0)",
            "        Target.Damage(18.0)\n"
            "        if (Service.TryRend[Controller, Player, Controller.Token,\n"
            "                           State, Budget, Selection.TargetKey]):\n"
            "            return"
        )
        self.assertNotEqual(on_rend, ARSENAL)
        self.assertTrue(self.check(arsenal=on_rend))


if __name__ == "__main__":
    unittest.main()
