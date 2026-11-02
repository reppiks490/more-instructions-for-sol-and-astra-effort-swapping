"""Mutation guards across canonical fusion, owner, avatar and arsenal lanes."""
import copy
import json
import unittest

from tools.audit_fusion_universe_perimeter import audit, read_sources


class FusionUniversePerimeterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = read_sources()

    def test_authored_source_perimeter(self):
        self.assertEqual(audit(self.sources), [])

    def mutate(self, key, old, new):
        sources = dict(self.sources)
        self.assertIn(old, sources[key])
        sources[key] = sources[key].replace(old, new, 1)
        self.assertTrue(audit(sources), f"unsafe {key} mutation passed: {old}")

    def mutate_json(self, key, edit):
        sources = dict(self.sources)
        data = copy.deepcopy(json.loads(sources[key]))
        edit(data)
        sources[key] = json.dumps(data)
        self.assertTrue(audit(sources), f"unsafe {key} policy mutation passed")

    def test_reject_owner_grant_without_native_proof(self):
        self.mutate_json("identity", lambda d: d.update(authority_enabled=True))

    def test_reject_native_reference_without_verified_identity(self):
        self.mutate_json("identity", lambda d: d.update(native_player_reference_provisioned=True))

    def test_reject_alternate_authority(self):
        self.mutate_json("contract", lambda d: d["identity"].update(existing_authority="cosmetic"))

    def test_reject_titan_activation(self):
        self.mutate_json("titan", lambda d: d.update(f002_activation="enabled"))

    def test_reject_titan_damage(self):
        self.mutate_json("titan", lambda d: d["attack"].update(direct_damage=True))

    def test_reject_prototype_priority(self):
        self.mutate_json("policy", lambda d: d.update(strategy="first_playable"))

    def test_reject_codex_policy_weakening(self):
        self.mutate_json("policy", lambda d: d.update(no_codex_in_automation=False))

    def test_reject_public_reference_registration(self):
        self.mutate("authority", "    CanWield<public>",
                    "    OwnerReference.Register(Player)\n    CanWield<public>")

    def test_reject_authority_revocation_bypass(self):
        self.mutate("authority", "not Revoked?", "Revoked?")

    def test_reject_foreign_fusion_form(self):
        self.mutate("state", 'RequestedFormId <> "FUS-001"',
                    'RequestedFormId <> "FUS-002"')

    def test_reject_owner_rebind(self):
        self.mutate("state", "Existing <> Player", "Existing = Player")

    def test_reject_release_without_cleanup(self):
        self.mutate("state", 'Phase <> aeonfall_fusion_phase.Dormant or FormId <> ""',
                    'Phase = aeonfall_fusion_phase.Dormant')

    def test_reject_stale_receipt_replay(self):
        self.mutate("state", "        AttackReceiptGeneration = Token",
                    "        AttackReceiptGeneration >= 0")

    def test_reject_unacknowledged_visual_activation(self):
        self.mutate("avatar", "if (ArmorGlow.HasEffect[Player]):", "if (true?):")

    def test_reject_shutdown_without_cleanup(self):
        self.mutate("avatar", "        FinishActive()\n        if (State := Runtime?",
                    "        Print(\"skipped teardown\")\n        if (State := Runtime?")

    def test_reject_unpaid_avatar_attack(self):
        self.mutate("avatar", "State.IssueAttackReceipt(Self, Player, Token)", "true")

    def test_reject_budget_without_live_authority(self):
        self.mutate("budget", "State.IsAuthorizedActive(Device, Player, NewToken)", "true")

    def test_reject_arsenal_receipt_bypass(self):
        self.mutate("arsenal", "State.ConsumeAttackReceipt[Device, Player, Token]", "true?")

    def test_reject_duplicate_reaver_damage(self):
        self.mutate("arsenal_device", "Target.Damage(18.0)",
                    "Target.Damage(18.0)\n                Target.Damage(18.0)")

    def test_reject_player_targeting(self):
        self.mutate("arsenal_device", "not player[Candidate]", "player[Candidate]")


if __name__ == "__main__":
    unittest.main()
