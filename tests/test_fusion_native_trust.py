"""Adversarial tests for Architect's source-only native trust ledger."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from tools.audit_fusion_native_trust import ROOT, evaluate, read_sources


class NativeTrustLedgerTests(unittest.TestCase):
    def setUp(self):
        self.sources = {
            "identity": json.dumps({"account_identity_verified": False,
                                    "native_player_reference_provisioned": False,
                                    "epic_account_id": None, "authority_enabled": False}),
            "contract": json.dumps({"forms": [
                {"id": "FUS-001", "enabled_for_native_activation": False},
                {"id": "FUS-002", "enabled_for_native_activation": False}],
                "evidence": {"native_verse_compile": "not_run",
                             "fortnite_launch_session": "not_run",
                             "physical_editor_binding": "not_run"}}),
            "avatar": "AttackCooldownSeconds:float = 1.5\n"
                      "AttackCooldownSeconds >= 0.2\nAttackOutput.Trigger(Player)\n",
            "arsenal": "Enabled:logic = false\n"
                       "    OnBegin<override>()<suspends>:void=\n"
                       "        if (not Enabled?):\n            return\n"
                       "    IsMonsterId(Id:string)<transacts>:logic=\n"
                       "        if (Id.Length >= 4, Id[0] = 'M', Id[3] = '-'):\n"
                       "            return true\n"
                       "    EligibleTarget()<decides><transacts>:fort_character=\n"
                       "        Range <= MaxRange\n"
                       "    OnRend(MaybeAgent:?agent):void=\n"
                       "        RendRequest.TriggeredEvent.Subscribe(OnRend)\n",
            "arsenal_runtime": "Now >= LastRendAt + 2.0\n",
            "state": "    ConsumeAttackReceipt(\n"
                     "        Device:creative_device, Player:player, Token:int\n"
                     "    )<decides><transacts>:int=\n"
                     "        ConsumedSequence := AttackReceiptSequence\n",
            "actor_registry": "    Register(CanonicalId:string)<decides><transacts>:string=\n"
                              "        CanonicalId <> \"\"\n",
        }

    def ids(self, sources=None):
        return {item["id"] for item in evaluate(sources or self.sources)}

    def test_known_trust_boundaries_are_not_mistaken_for_native_proof(self):
        self.assertEqual(self.ids(), {f"FNT-{i:03d}" for i in (1, 2, 4, 5, 6, 7, 8, 9)})

    def test_verified_identity_reduces_only_owner_provisioning_blocker(self):
        s = copy.deepcopy(self.sources)
        d = json.loads(s["identity"])
        d.update(account_identity_verified=True, native_player_reference_provisioned=True,
                 epic_account_id="TEST-ONLY", authority_enabled=True)
        s["identity"] = json.dumps(d)
        self.assertNotIn("FNT-001", self.ids(s))
        self.assertIn("FNT-004", self.ids(s))

    def test_f002_enablement_is_flagged(self):
        s = copy.deepcopy(self.sources)
        d = json.loads(s["contract"])
        d["forms"][1]["enabled_for_native_activation"] = True
        s["contract"] = json.dumps(d)
        self.assertIn("FNT-003", self.ids(s))

    def test_request_id_alone_cannot_authenticate_public_trigger(self):
        s = copy.deepcopy(self.sources)
        s["state"] = s["state"].replace("Token:int", "Token:int, ReceiptSequence:int")
        self.assertIn("FNT-004", self.ids(s))
        self.assertIn("FNT-005", self.ids(s))

    def test_registration_and_monster_validation_both_need_hardening(self):
        s = copy.deepcopy(self.sources)
        s["actor_registry"] = s["actor_registry"].replace(
            'CanonicalId <> ""', "CanonicalCatalogContains[CanonicalId]")
        self.assertIn("FNT-005", self.ids(s))
        s["arsenal"] = s["arsenal"].replace("Id.Length >= 4", "ExactCatalogMonsterId[Id]")
        self.assertNotIn("FNT-005", self.ids(s))

    def test_los_must_be_explicit_in_target_eligibility(self):
        s = copy.deepcopy(self.sources)
        s["arsenal"] = s["arsenal"].replace(
            "        Range <= MaxRange", "        Range <= MaxRange\n        VerifiedLOS[Target]")
        self.assertNotIn("FNT-006", self.ids(s))

    def test_native_source_gate_must_precede_subscriptions(self):
        s = copy.deepcopy(self.sources)
        s["arsenal"] = s["arsenal"].replace(
            "        if (not Enabled?):", "        if (not NativeSourceGate? or not Enabled?):")
        self.assertIn("FNT-007", self.ids(s))
        s["arsenal"] = "    NativeSourceGate:logic = false\n" + s["arsenal"]
        self.assertNotIn("FNT-007", self.ids(s))

    def test_gate_after_subscription_is_not_a_security_boundary(self):
        s = copy.deepcopy(self.sources)
        s["arsenal"] = (
            "    NativeSourceGate:logic = false\n" +
            s["arsenal"].replace(
                "        if (not Enabled?):",
                "        RendRequest.TriggeredEvent.Subscribe(OnRend)\n"
                "        if (not NativeSourceGate? or not Enabled?):"
            )
        )
        self.assertIn("FNT-007", self.ids(s))

    def test_both_avatar_cooldown_bounds_must_match_reaver(self):
        s = copy.deepcopy(self.sources)
        s["avatar"] = s["avatar"].replace("= 1.5", "= 2.0")
        self.assertIn("FNT-008", self.ids(s))
        s["avatar"] = s["avatar"].replace(">= 0.2", ">= 2.0")
        self.assertNotIn("FNT-008", self.ids(s))

    def test_missing_cooldown_data_fails_closed(self):
        s = copy.deepcopy(self.sources)
        s["arsenal_runtime"] = "# no admission clock\n"
        self.assertIn("FNT-008", self.ids(s))

    def test_missing_native_proof_never_becomes_automatic_success(self):
        s = copy.deepcopy(self.sources)
        d = json.loads(s["contract"])
        d["evidence"]["native_verse_compile"] = "passed_python_tests"
        s["contract"] = json.dumps(d)
        self.assertIn("FNT-009", self.ids(s))

    @unittest.skipUnless((ROOT / "verse/core/actor_registry.verse").is_file(),
                         "Full repository not materialized in local test environment")
    def test_actual_repository_has_documented_unclosed_native_boundaries(self):
        ids = {finding["id"] for finding in evaluate(read_sources())}
        self.assertTrue({"FNT-001", "FNT-002", "FNT-004", "FNT-005",
                         "FNT-006", "FNT-008", "FNT-009"}.issubset(ids))


if __name__ == "__main__":
    unittest.main()
