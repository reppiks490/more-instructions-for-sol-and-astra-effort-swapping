"""Source mutation checks for the Avatar-to-Arsenal paid Reaver handoff.

These DO NOT compile Verse or prove native damage / collision / replication.
Cross-file independent QA and Architect validators are tracked separately.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
AVATAR=ROOT/"verse/sovereign/sovereign_fusion_device.verse"
ARSENAL=ROOT/"verse/sovereign/sovereign_arsenal_runtime.verse"
DEVICE=ROOT/"verse/sovereign/sovereign_arsenal_device.verse"


def method(source: str, name: str) -> str:
    source="\n".join(line.split("#",1)[0] for line in source.splitlines())
    start=re.search(r"^    "+re.escape(name)+r"\(",source,re.M)
    if not start:
        return ""
    rest=re.search(r"^    [A-Za-z_]\w*\(",source[start.end():],re.M)
    end=start.end()+rest.start() if rest else len(source)
    return source[start.start():end]


def checks(avatar:str, arsenal:str, device:str) -> list[str]:
    errors=[]
    attack=method(avatar,"Attack")
    rend=method(arsenal,"TryRend")
    hit=method(device,"OnRend")
    def gate(name:str,body:str,required:list[str]):
        cursor=0
        for fragment in required:
            next_pos=body.find(fragment,cursor)
            if next_pos<0:
                errors.append(name+" missing/reordered: "+fragment)
                return
            cursor=next_pos+len(fragment)
    if not attack or not rend or not hit:
        errors.append("missing paid-attack method")
        return errors
    # All three upstream decisions must happen before exiting the if admission
    # and triggering irreversible external device effects.
    if "        if:\n" not in attack or "        then:\n" not in attack:
        errors.append("missing deciding admission")
    else:
        admission=attack.split("        if:\n",1)[1].split("        then:\n",1)[0]
        gate("Avatar admission",admission,[
            "Authorized := State.IsAuthorizedActive(Self, Player, Token)",
            "Authorized?",
            "Resource.Spend[Self, Player, Token, State, AttackEnergyCost]",
            "Issued := State.IssueAttackReceipt(Self, Player, Token)",
            "Issued?"
        ])
        gate("Avatar output",attack,["        then:",
              "AttackOutput.Trigger(Player)"])
    if "<decides><transacts>:void=" not in rend:
        errors.append("TryRend must be transactional deciding")
    gate("Arsenal admission",rend,[
        "Now >= LastRendAt + 2.0",
        "State.ConsumeAttackReceipt[Device, Player, Token]",
        "Budget.Spend[Device, Player, Token, State, 5]",
        "set LastRendAt = Now"
    ])
    gate("Arsenal damage",hit,[
        "Service.TryRend[Controller, Player, Controller.Token",
        "Target.Damage(18.0)"
    ])
    if attack.count("AttackOutput.Trigger(Player)")!=1:
        errors.append("more than one Avatar physical output")
    if rend.count("ConsumeAttackReceipt[")!=1:
        errors.append("more than one or missing paid receipt consumer")
    if hit.count("Target.Damage(18.0)")!=1:
        errors.append("Reaver damage must be applied only once")
    if "Enabled:logic = false" not in avatar or "Enabled:logic = false" not in device:
        errors.append("unverified player damage may not enable by default")
    return errors


class PaidReaverHandoffTests(unittest.TestCase):
    def setUp(self):
        self.avatar=AVATAR.read_text(encoding="utf-8")
        self.arsenal=ARSENAL.read_text(encoding="utf-8")
        self.device=DEVICE.read_text(encoding="utf-8")

    def mutated(self,target,old,new):
        s=getattr(self,target)
        self.assertIn(old,s)
        setattr(self,target,s.replace(old,new,1))
        self.assertTrue(checks(self.avatar,self.arsenal,self.device))

    def test_real_authored_sources_pass(self):
        self.assertEqual(checks(self.avatar,self.arsenal,self.device),[])

    def test_reject_missing_upstream_debit(self):
        self.mutated("avatar","Resource.Spend[Self, Player, Token, State, AttackEnergyCost]","true?")

    def test_reject_missing_receipt_issue(self):
        self.mutated("avatar","Issued := State.IssueAttackReceipt(Self, Player, Token)","Issued := true")

    def test_reject_missing_issue_ack(self):
        self.mutated("avatar","Issued?","Player.IsActive[]")

    def test_reject_receipt_issued_outside_atomic_admission(self):
        self.mutated("avatar","Issued := State.IssueAttackReceipt(Self, Player, Token)\n            Issued?",
                     "Issued := true\n            Issued?")

    def test_reject_missing_authoritative_fusion(self):
        self.mutated("avatar","Authorized := State.IsAuthorizedActive(Self, Player, Token)","Authorized := true")

    def test_reject_missing_downstream_receipt(self):
        self.mutated("arsenal","State.ConsumeAttackReceipt[Device, Player, Token]","true?")

    def test_reject_consume_after_secondary_debit(self):
        self.mutated("arsenal","ReceiptSequence := State.ConsumeAttackReceipt[Device, Player, Token]",
                     "ReceiptSequence := 1")

    def test_reject_secondary_spend_removed(self):
        self.mutated("arsenal","Budget.Spend[Device, Player, Token, State, 5]","true?")

    def test_reject_downstream_cooldown_removed(self):
        self.mutated("arsenal","set LastRendAt = Now","set LastCollapseAt = Now")

    def test_reject_damage_before_commit(self):
        self.mutated("device","Target.Damage(18.0)","Target.Damage(18.0)\n                Target.Damage(18.0)")

    def test_reject_public_arsenal(self):
        self.mutated("device","Enabled:logic = false","Enabled:logic = true")


if __name__=="__main__":
    unittest.main()
