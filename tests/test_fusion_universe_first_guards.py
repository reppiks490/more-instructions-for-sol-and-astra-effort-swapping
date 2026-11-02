"""Cross-loop FUS-001 and universe-first source regressions (NOT native UEFN tests).

These checks do not grant creator access, enable a fusion form, approve source
inventory packages, establish editor device bindings, or certify Fortnite.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def member(source: str, name: str) -> str:
    code = "\n".join(line.split("#", 1)[0] for line in source.splitlines())
    match = re.search(r"^    " + re.escape(name) + r"(?:<[^>\n]+>)?\(", code, re.M)
    if not match:
        return ""
    following = re.search(r"^    [A-Za-z_][A-Za-z_0-9]*(?:<[^>\n]+>)?\(",
                          code[match.end():], re.M)
    end = match.end() + following.start() if following else len(code)
    return code[match.start():end]


def ordered(code: str, *tokens: str) -> bool:
    positions = [code.find(token) for token in tokens]
    return all(p >= 0 for p in positions) and positions == sorted(positions)


class FusionUniverseFirstGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads(read("content/implementation/universe_first_policy.json"))
        cls.contract = json.loads(read("content/sovereign/fusion_integration_contract.json"))
        cls.authority = read("verse/sovereign/sovereign_authority_device.verse")
        cls.state = read("verse/sovereign/fusion_state_runtime.verse")
        cls.avatar = read("verse/sovereign/sovereign_fusion_device.verse")
        cls.arsenal = read("verse/sovereign/sovereign_arsenal_runtime.verse")
        cls.damage = read("verse/sovereign/sovereign_arsenal_device.verse")

    def test_universe_scope_not_reduced_for_fusion(self):
        self.assertEqual(self.policy["strategy"],
                         "full_universe_source_before_playable_prototype")
        self.assertEqual(self.policy["current_phase"], "source_universe_construction")
        self.assertEqual(self.policy["playable_prototype_priority"],
                         "deferred_by_creator_until_full_source_inventory")
        self.assertGreaterEqual(self.policy["minimum_major_entities"], 800)
        self.assertGreaterEqual(len(self.policy["required_world_regions"]), 13)
        ids = {item["id"] for item in self.policy["required_systems"]}
        self.assertGreaterEqual(len(ids), 13)
        self.assertIn("SYS-OWNER-OMNIGOD-FUSION", ids)
        self.assertTrue(self.policy["no_codex_in_automation"])
        self.assertTrue(self.policy["source_complete_does_not_imply_native_complete"])

    def test_canonical_identity_and_native_gates_stay_closed(self):
        self.assertEqual(self.contract["identity"]["owner_limit"], 1)
        self.assertFalse(self.contract["identity"]["enabled_by_default"])
        self.assertEqual([f["id"] for f in self.contract["forms"]],
                         ["FUS-001", "FUS-002"])
        self.assertTrue(all(not f["enabled_for_native_activation"]
                            for f in self.contract["forms"]))
        self.assertEqual(self.contract["preservation"]["canonical_sovereign_ability_id"],
                         "UNI-001")
        self.assertFalse(self.contract["preservation"]["player_profile_schema_change"])
        for key in ("native_verse_compile", "fortnite_launch_session",
                    "physical_editor_binding", "publication"):
            self.assertEqual(self.contract["evidence"][key], "not_run")
        self.assertIn("Enabled:logic = false", self.avatar)
        self.assertIn("Enabled:logic = false", self.damage)

    def test_creator_authority_cannot_be_client_provisioned(self):
        gate = member(self.authority, "CanWield")
        self.assertIn("Enabled:logic = false", self.authority)
        self.assertIn("OwnerReference.IsReferenced[Player]", gate)
        self.assertIn("not Revoked?", gate)
        self.assertNotIn("OwnerReference.Register(", self.authority)

    def test_session_owner_stays_sticky_and_titan_stays_disabled(self):
        self.assertIn("AEONFALLFusionStateSessions:weak_map(session,", self.state)
        self.assertIn('RequestedFormId <> "FUS-001"',
                      member(self.state, "BeginActivation"))
        for name in ("Abort", "ReleaseController", "CompleteSeparation"):
            self.assertNotIn("set Owner = false", member(self.state, name))

    def test_paid_reaver_admission_is_end_to_end_ordered(self):
        issue = member(self.state, "IssueAttackReceipt")
        consume = member(self.state, "ConsumeAttackReceipt")
        attack = member(self.avatar, "Attack")
        rend = member(self.arsenal, "TryRend")
        physical = member(self.damage, "OnRend")
        self.assertTrue(ordered(issue, "Gate.CanWield(Player)",
                                "if (AttackReceiptPending?):",
                                "set AttackReceiptSequence += 1",
                                "set AttackReceiptPending = true"))
        self.assertTrue(ordered(consume, "AttackReceiptPending?",
                                "AttackReceiptGeneration = Token",
                                "GetSimulationElapsedTime() < AttackReceiptExpiresAt",
                                "Gate.CanWield(Player)", "ClearAttackReceipt()"))
        self.assertTrue(ordered(attack,
                                "Resource.Spend[Self, Player, Token, State, AttackEnergyCost]",
                                "Issued := State.IssueAttackReceipt(Self, Player, Token)",
                                "Issued?", "AttackOutput.Trigger(Player)"))
        self.assertTrue(ordered(rend, "Now >= LastRendAt + 2.0",
                                "State.ConsumeAttackReceipt[Device, Player, Token]",
                                "Budget.Spend[Device, Player, Token, State, 5]",
                                "set LastRendAt = Now"))
        self.assertTrue(ordered(physical, "Player := ValidOwner[Agent]",
                                "Target := EligibleTarget[Player, Selection.TargetKey, 350.0, 0.70]",
                                "Service.TryRend[Controller, Player, Controller.Token, State, Budget, Selection.TargetKey]",
                                "Target.Damage(18.0)"))

    def test_receipt_mutation_is_detectable(self):
        source = self.avatar.replace(
            "Issued := State.IssueAttackReceipt(Self, Player, Token)",
            "Issued := true")
        self.assertNotEqual(source, self.avatar)
        self.assertFalse(ordered(member(source, "Attack"),
                                 "Resource.Spend[Self, Player, Token, State, AttackEnergyCost]",
                                 "Issued := State.IssueAttackReceipt(Self, Player, Token)",
                                 "Issued?", "AttackOutput.Trigger(Player)"))

    def test_arsenal_receipt_bypass_is_detectable(self):
        source = self.arsenal.replace(
            "State.ConsumeAttackReceipt[Device, Player, Token]", "Token >= 0")
        self.assertNotEqual(source, self.arsenal)
        self.assertFalse(ordered(member(source, "TryRend"),
                                 "State.ConsumeAttackReceipt[Device, Player, Token]",
                                 "Budget.Spend[Device, Player, Token, State, 5]"))

    def test_damage_before_authorization_is_detectable(self):
        physical = member(self.damage, "OnRend")
        changed = physical.replace(
            "if (Service.TryRend[Controller, Player, Controller.Token, State, Budget, Selection.TargetKey]):",
            "Target.Damage(18.0)\n            if (Service.TryRend[Controller, Player, Controller.Token, State, Budget, Selection.TargetKey]):")
        self.assertNotEqual(changed, physical)
        self.assertFalse(ordered(changed,
                                 "Service.TryRend[Controller, Player, Controller.Token, State, Budget, Selection.TargetKey]",
                                 "Target.Damage(18.0)"))


if __name__ == "__main__":
    unittest.main()
