"""Source-only mutation regressions; these fixtures do not execute Verse."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "fusion_paid_audit", ROOT / "tools/audit_fusion_paid_attack.py"
)
assert SPEC and SPEC.loader
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)

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

RUNTIME = """
aeonfall_sovereign_arsenal_runtime := class:
    TryRend(
        Device:creative_device, Player:player, Token:int,
        State:aeonfall_fusion_state_runtime,
        Budget:aeonfall_sovereign_fusion_budget_runtime,
        TargetKey:string
    )<decides><transacts>:void=
        State.ConsumeAttackReceipt[Device, Player, Token]
        Budget.Spend[Device, Player, Token, State, 5]
        set LastRendAt = Now
    TryCollapse()<transacts>:void=
        return
"""

DEVICE = """
aeonfall_sovereign_arsenal_device := class(creative_device):
    OnBegin<override>()<suspends>:void=
        RendRequest.TriggeredEvent.Subscribe(OnRend)
    ValidOwner(Agent:agent)<decides><transacts>:player=
        Owner = Player
        Character = Original
        State.IsAuthorizedActive(Controller, Player, Controller.Token)
        Player
    OnRend(MaybeAgent:?agent):void=
        if (Service.TryRend[Controller, Player, Controller.Token, State, Budget, Key]):
            Target.Damage(18.0)
    OnEnd<override>():void=
        return
"""


class PaidAttackHandoffQA(unittest.TestCase):
    def check(self, avatar=AVATAR, runtime=RUNTIME, device=DEVICE):
        return audit.check_sources(avatar, runtime, device)

    def test_compliant_three_file_fixture(self):
        self.assertEqual(self.check(), [])

    def test_missing_upstream_payment(self):
        self.assertTrue(self.check(avatar=AVATAR.replace(
            "Resource.Spend[Self, Player, Token, State, AttackEnergyCost]", "true?"
        )))

    def test_missing_receipt_issuance(self):
        self.assertTrue(self.check(avatar=AVATAR.replace(
            "Issued := State.IssueAttackReceipt(Self, Player, Token)", "Issued := true"
        )))

    def test_unacknowledged_receipt(self):
        self.assertTrue(self.check(avatar=AVATAR.replace("            Issued?\n", "")))

    def test_receipt_issued_after_output(self):
        self.assertTrue(self.check(avatar=AVATAR.replace(
            "            Issued := State.IssueAttackReceipt(Self, Player, Token)\n", ""
        ).replace(
            "            AttackOutput.Trigger(Player)",
            "            Issued := State.IssueAttackReceipt(Self, Player, Token)\n"
            "            AttackOutput.Trigger(Player)"
        )))

    def test_duplicate_physical_producer(self):
        self.assertTrue(self.check(avatar=AVATAR + "\n    Bad():void=\n"
                                   "        AttackOutput.Trigger(Player)\n"))

    def test_missing_receipt_consumer(self):
        self.assertTrue(self.check(runtime=RUNTIME.replace(
            "State.ConsumeAttackReceipt[Device, Player, Token]", "true?"
        )))

    def test_consumer_after_secondary_spend(self):
        self.assertTrue(self.check(runtime=RUNTIME.replace(
            "        State.ConsumeAttackReceipt[Device, Player, Token]\n"
            "        Budget.Spend[Device, Player, Token, State, 5]",
            "        Budget.Spend[Device, Player, Token, State, 5]\n"
            "        State.ConsumeAttackReceipt[Device, Player, Token]"
        )))

    def test_nontransactional_consumer(self):
        self.assertTrue(self.check(runtime=RUNTIME.replace(
            "<decides><transacts>:void=", ":void="
        )))

    def test_damage_before_authorized_commit(self):
        self.assertTrue(self.check(device=DEVICE.replace(
            "        if (Service.TryRend[Controller, Player, Controller.Token, State, Budget, Key]):\n"
            "            Target.Damage(18.0)",
            "        Target.Damage(18.0)\n"
            "        if (Service.TryRend[Controller, Player, Controller.Token, State, Budget, Key]):\n"
            "            return"
        )))

    def test_missing_owner_match(self):
        self.assertTrue(self.check(device=DEVICE.replace("Owner = Player", "Owner <> Player")))

    def test_missing_canonical_authorization(self):
        self.assertTrue(self.check(device=DEVICE.replace(
            "State.IsAuthorizedActive(Controller, Player, Controller.Token)", "true?"
        )))

    def test_missing_trigger_subscription(self):
        self.assertTrue(self.check(device=DEVICE.replace(
            "RendRequest.TriggeredEvent.Subscribe(OnRend)", "return"
        )))


if __name__ == "__main__":
    unittest.main()
