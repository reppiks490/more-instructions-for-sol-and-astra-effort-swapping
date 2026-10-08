#!/usr/bin/env python3
import unittest
from validate_activation_transactions import validate_sources, read_sources, COORDINATOR, RUNTIME, DELIVERY

class TransactionGuardTests(unittest.TestCase):
    def setUp(self):
        self.sources = read_sources()

    def mutation(self, path, before, after, expected):
        self.assertIn(before, self.sources[path])
        self.sources[path] = self.sources[path].replace(before, after, 1)
        self.assertTrue(any(expected in error for error in validate_sources(self.sources)))

    def test_current_sources(self):
        self.assertEqual(validate_sources(self.sources), [])

    def test_tracking_absent(self):
        self.mutation(COORDINATOR, "set PendingActivations[RequestId] = Pending", "set Missing[RequestId] = Pending", "tracking")

    def test_wrong_owner_accepted(self):
        self.mutation(COORDINATOR, "Pending.OwnerKey = Result.OwnerKey", "true?", "callback guard")

    def test_wrong_adapter_accepted(self):
        self.mutation(COORDINATOR, "Result.AdapterId = Definition.AdapterId", "true?", "callback guard")

    def test_wrong_cancel_accepted(self):
        self.mutation(COORDINATOR, "Pending.OwnerKey = OwnerKey", "true?", "cancellation")

    def test_instant_latched(self):
        self.mutation(RUNTIME, "Active := Managed", "Active := true", "latch")

    def test_saturation_not_rejected(self):
        self.mutation(RUNTIME, "TryRequestAbilityEffect", "RequestAbilityEffect", "saturation")

    def test_retry_snapshot_resurrection(self):
        self.mutation(DELIVERY, "        set Pending = Updated\n        for (Retry : Retries):", "        for (Retry : Retries):", "retry callbacks")

    def test_nonatomic_status_batch(self):
        self.mutation("verse/combat/status_runtime.verse",
                      "TargetKey:string, StatusIds:[]string, SourceId:string, Magnitude:int\n    )<decides><transacts>:void=",
                      "TargetKey:string, StatusIds:[]string, SourceId:string, Magnitude:int\n    )<transacts>:void=",
                      "status batch")

    def test_stale_effect_execution(self):
        self.mutation("verse/combat/trigger_ability_adapter_device.verse", "ClaimEffectRequest(Request)", "Supports(Request.AdapterId)", "late requests")

    def test_duplicate_effect_claim(self):
        self.mutation(RUNTIME, "not EffectClaims[Request.RequestId]", "true?", "atomic current-request claim")

    def test_taming_mark_partial_commit(self):
        self.mutation("verse/npcs/royal_scent_adapter_device.verse", "        Started?", "        Started = true", "Royal Scent")

if __name__ == "__main__":
    unittest.main()
