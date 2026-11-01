"""Source mutation guards for one-use-per-God/Absolute-form activation epochs.

These are NOT a Verse compiler or physical adapter integration test.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "verse/combat/ability_runtime.verse"
FORMS = ROOT / "content/transcendent/ascended_forms.json"
MECHANICS = ROOT / "content/transcendent/ascended_ability_mechanics.json"


class ApexUseEpochTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = RUNTIME.read_text(encoding="utf-8")
        cls.forms = json.loads(FORMS.read_text(encoding="utf-8"))
        cls.mechanics = json.loads(MECHANICS.read_text(encoding="utf-8"))

    def test_canonical_one_use_policy_is_not_expanded(self):
        canonical = {a["id"] for form in self.forms["forms"] for a in form["abilities"]}
        self.assertEqual(canonical, {m["ability_id"] for m in self.mechanics["mechanics"]})
        self.assertEqual({m["limits"]["uses_per_form"] for m in self.mechanics["mechanics"]}, {1})

    def test_active_form_identity_and_epoch_are_required(self):
        helper = self.source.split("    GetApexEpoch(", 1)[1].split("    Initialize(", 1)[0]
        for guard in (
            "FormState.Phase = aeonfall_ascended_form_phase.Active",
            "FormState.ActiveRemainingSeconds > 0.0",
            "FormState.FormId = Definition.OwnerEntityId",
            "FormState.TransformationId = Definition.RequiredTransformationId",
            'Definition.RequiredTransformationId <> ""',
            "FormState.SessionActivationCount > 0",
        ):
            self.assertIn(guard, helper)

    def test_pre_dispatch_use_gate(self):
        can = self.source.split("    CanActivate(", 1)[1].split("    RequestActivation(", 1)[0]
        self.assertIn("Epoch := GetApexEpoch[OwnerKey, Definition]", can)
        self.assertIn("CommittedEpoch >= Epoch", can)
        self.assertLess(can.index("CommittedEpoch >= Epoch"), can.index("Definition.ResourcePolicy = aeonfall_resource_policy.Cooldown"))

    def test_callback_rechecks_form_before_success_commit(self):
        resolve = self.source.split("    ResolveActivation(", 1)[1].split("    CancelPending(", 1)[0]
        for guard in (
            "CurrentEpoch := GetApexEpoch[Result.OwnerKey, Definition]",
            "CommittedEpoch >= ApexEpoch",
            'set FailureCode = "apex_use_already_committed"',
            'set FailureCode = "apex_form_not_active"',
            "if (not EffectiveSucceeded?):",
        ):
            self.assertIn(guard, resolve)
        self.assertLess(resolve.index("if (not EffectiveSucceeded?):"), resolve.index("var Charges:int"))

    def test_atomic_commit_and_no_charge_on_rejection(self):
        resolve = self.source.split("    ResolveActivation(", 1)[1].split("    CancelPending(", 1)[0]
        self.assertIn("set States[Key] = Committed\n                    set ApexCommittedEpochByStateKey[Key] = ApexEpoch", resolve)
        self.assertLess(resolve.index("if (not EffectiveSucceeded?):"), resolve.index("set ApexCommittedEpochByStateKey[Key] = ApexEpoch"))
        self.assertIn("if (Saved?):\n                RemoveEffectClaim(Result.RequestId)", resolve)

    def test_request_binds_the_original_epoch_before_dispatch(self):
        request = self.source.split("    RequestActivation(", 1)[1].split("    IsCurrentEffectRequest(", 1)[0]
        self.assertIn("RequestedApexEpoch", request)
        self.assertIn("set ApexPendingByRequest[RequestId] = aeonfall_apex_pending_epoch{", request)
        self.assertLess(
            request.index("set ApexPendingByRequest[RequestId]"),
            request.index("AEONFALLRuntimeBus.TryRequestAbilityEffect("),
        )

    def test_stale_callback_cannot_borrow_new_form_epoch(self):
        resolve = self.source.split("    ResolveActivation(", 1)[1].split("    CancelPending(", 1)[0]
        self.assertIn("PendingApex := ApexPendingByRequest[Result.RequestId]", resolve)
        self.assertIn("PendingApex.OwnerKey = Result.OwnerKey", resolve)
        self.assertIn("PendingApex.Epoch = CurrentEpoch", resolve)
        self.assertIn('set FailureCode = "apex_request_epoch_mismatch"', resolve)
        self.assertIn("RemovePendingApexEpoch(Result.RequestId)", resolve)

    def test_cancel_releases_pending_epoch_without_refund(self):
        cancel = self.source.split("    CancelPending(", 1)[1].split("    EndActivation(", 1)[0]
        self.assertIn("RemovePendingApexEpoch(RequestId)", cancel)
        self.assertNotIn("set ApexCommittedEpochByStateKey", cancel)

    def test_owner_cleanup_purges_ledger(self):
        clear = self.source.split("    ClearOwner(", 1)[1].split("# Mutable service allocation", 1)[0]
        self.assertIn("for (Key -> Epoch : ApexCommittedEpochByStateKey):", clear)
        self.assertIn("StoredOwner <> OwnerKey", clear)
        self.assertIn("set ApexCommittedEpochByStateKey = KeptApexEpochs", clear)
        self.assertIn("set ApexPendingByRequest = KeptPendingApex", clear)

    def test_only_god_absolute_use_this_ledger(self):
        helper = self.source.split("    IsGodAbsoluteAbility(", 1)[1].split("    GetApexEpoch(", 1)[0]
        self.assertIn('Definition.OwnerEntityId = "FORM-GOD"', helper)
        self.assertIn('Definition.OwnerEntityId = "FORM-ABSOLUTE"', helper)
        self.assertNotIn("TRANSCENDENT_ZERO", helper)


if __name__ == "__main__":
    unittest.main()
