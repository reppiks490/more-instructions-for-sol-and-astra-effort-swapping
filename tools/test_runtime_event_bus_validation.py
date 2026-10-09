#!/usr/bin/env python3
"""Mutation checks for bus source validation, not tests of Verse execution."""
from __future__ import annotations

import unittest

from validate_runtime_event_bus import BUS, ROOT, validate_sources


class RuntimeEventBusValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = {
            str(path.relative_to(ROOT)): path.read_text(encoding="utf-8")
            for path in (ROOT / "verse").rglob("*.verse")
        }

    def mutated(self, path: str, old: str, new: str) -> list[str]:
        sources = dict(self.sources)
        self.assertIn(old, sources[path], "mutation must touch the actual checked source")
        sources[path] = sources[path].replace(old, new, 1)
        return validate_sources(sources)

    def test_current_bus_and_consumers_pass(self) -> None:
        self.assertEqual(validate_sources(self.sources), [])

    def test_raw_event_subscription_regression_is_rejected(self) -> None:
        errors = self.mutated(BUS, "RuntimeEvent:aeonfall_runtime_event_channel", "RuntimeEvent:event(aeonfall_runtime_event)")
        self.assertTrue(any("raw event(aeonfall_runtime_event) has no Subscribe" in error for error in errors))

    def test_callback_payload_mismatch_is_rejected(self) -> None:
        path = "verse/combat/ability_result_router_device.verse"
        errors = self.mutated(path, "OnAdapterResult(Result:aeonfall_adapter_result)", "OnAdapterResult(Result:aeonfall_runtime_event)")
        self.assertTrue(any("callback OnAdapterResult must accept aeonfall_adapter_result" in error for error in errors))

    def test_unknown_channel_is_rejected(self) -> None:
        path = "verse/combat/ability_result_router_device.verse"
        errors = self.mutated(path, "AEONFALLRuntimeBus.AdapterResult.Subscribe", "AEONFALLRuntimeBus.TypoResult.Subscribe")
        self.assertTrue(any("unknown bus channel TypoResult" in error for error in errors))

    def test_nontransactional_admission_is_rejected(self) -> None:
        errors = self.mutated(BUS, "TryRequestAbilityEffect(Request:aeonfall_ability_effect_request)<transacts>:logic", "TryRequestAbilityEffect(Request:aeonfall_ability_effect_request):logic")
        self.assertTrue(any("TryRequestAbilityEffect must return logic with transacts" in error for error in errors))

    def test_transactional_pump_is_rejected(self) -> None:
        errors = self.mutated(BUS, "Pump():void", "Pump()<transacts>:void")
        self.assertTrue(any("missing no_rollback Pump() dispatch boundary" in error for error in errors))

    def test_non_session_state_is_rejected(self) -> None:
        errors = self.mutated(BUS, "weak_map(session, aeonfall_event_bus_state)", "weak_map(player, aeonfall_event_bus_state)")
        self.assertTrue(any("mutable bus state must be session scoped" in error for error in errors))

    def test_native_signal_in_cancel_is_rejected(self) -> None:
        errors = self.mutated(BUS, "set Canceled = true", "set Canceled = true\n        Stop.Signal()")
        self.assertTrue(any("cancellation must not signal a native event inside transacts" in error for error in errors))

    def test_subscription_inside_option_failure_context_is_rejected(self) -> None:
        path = "verse/combat/ability_result_router_device.verse"
        errors = self.mutated(path, "Subscription := AEONFALLRuntimeBus.AdapterResult.Subscribe(OnAdapterResult)", "Subscription := option{AEONFALLRuntimeBus.AdapterResult.Subscribe(OnAdapterResult)}")
        self.assertTrue(any(path in error and "capture its token before constructing option" in error for error in errors))

    def test_subscription_cleanup_removal_is_rejected(self) -> None:
        path = "verse/combat/ability_result_router_device.verse"
        errors = self.mutated(path, "Subscription.Cancel()", "IgnoreCancellation()")
        self.assertTrue(any(path in error and "requires cancellation in OnEnd" in error for error in errors))

    def test_discarded_subscription_is_rejected(self) -> None:
        path = "verse/combat/ability_result_router_device.verse"
        errors = self.mutated(path, "Subscription := AEONFALLRuntimeBus.AdapterResult.Subscribe(OnAdapterResult)", "AEONFALLRuntimeBus.AdapterResult.Subscribe(OnAdapterResult)")
        self.assertTrue(any(path in error and "subscription token is discarded" in error for error in errors))

    def test_ability_adapter_cannot_bypass_saturation_fallback(self) -> None:
        path = "verse/combat/trigger_ability_adapter_device.verse"
        errors = self.mutated(path, "AEONFALLAdapterResultDelivery.Report(", "AEONFALLRuntimeBus.ReportAdapterResult(")
        self.assertTrue(any(path in error and "require the admission/fallback delivery helper" in error for error in errors))

    def test_ability_result_resolution_fallback_removal_is_rejected(self) -> None:
        path = "verse/combat/adapter_result_delivery.verse"
        errors = self.mutated(path, "GetAEONFALLActivationCoordinator().ResolveAdapterResult(Definition, Result)", "IgnoreCanonicalResolution(Definition, Result)")
        self.assertTrue(any(path in error and "requires direct canonical resolution" in error for error in errors))

    def test_unlock_result_resolution_fallback_removal_is_rejected(self) -> None:
        path = "verse/economy/unlock_delivery_adapter_device.verse"
        errors = self.mutated(path, "GetAEONFALLUnlockDeliveryService().Resolve(Result)", "IgnoreCanonicalResolution(Result)")
        self.assertTrue(any(path in error and "requires direct canonical resolution" in error for error in errors))

    def test_native_effect_handler_cannot_claim_transactional_effects(self) -> None:
        path = "verse/combat/status_device_bridge.verse"
        errors = self.mutated(path, "OnRuntimeEvent(Event:aeonfall_runtime_event):void", "OnRuntimeEvent(Event:aeonfall_runtime_event)<transacts>:void")
        self.assertTrue(any(path in error and "dispatches native device effects and must have no_rollback" in error for error in errors))

    def test_status_commit_must_fail_when_admission_fails(self) -> None:
        path = "verse/combat/status_runtime.verse"
        errors = self.mutated(path, "        Admitted?", "        logic{Admitted?}")
        self.assertTrue(any(path in error and "require atomic deciding queue admission" in error for error in errors))

    def test_status_removal_cannot_bypass_atomic_admission(self) -> None:
        path = "verse/combat/status_runtime.verse"
        errors = self.mutated(path, "Removed?\n            CommitStatusChange[", "Removed?\n            IgnoreStatusCommand[")
        self.assertTrue(any(path in error and "RemoveStatus must commit canonical state and its command atomically" in error for error in errors))

    def test_expiry_must_retry_rejected_admission(self) -> None:
        path = "verse/combat/status_runtime.verse"
        errors = self.mutated(path, "if (not Admitted?):", "if (Admitted?):")
        self.assertTrue(any(path in error and "saturated expiry must retain" in error for error in errors))

    def test_forced_clear_cannot_wait_for_queue_capacity(self) -> None:
        path = "verse/combat/status_runtime.verse"
        errors = self.mutated(path, "set StatusesByTarget[TargetKey] = array{}", "EventBus.TryEmit(aeonfall_runtime_event{})?")
        self.assertTrue(any(path in error and "forced target cleanup must clear canonical state" in error for error in errors))

    def test_bridge_shutdown_must_clean_physical_effects(self) -> None:
        path = "verse/combat/status_device_bridge.verse"
        errors = self.mutated(path, "        CleanupAll()", "        IgnorePhysicalCleanup()")
        self.assertTrue(any(path in error and "OnEnd must stop reconciliation and clean all tracked effects" in error for error in errors))

    def test_bridge_must_track_before_applying_effects(self) -> None:
        path = "verse/combat/status_device_bridge.verse"
        errors = self.mutated(path, "set AppliedAgents[TargetKey] = TargetAgent", "RecordNothing()")
        self.assertTrue(any(path in error and "track each application before applying physical effects" in error for error in errors))

    def test_bridge_must_discover_pre_subscription_statuses(self) -> None:
        path = "verse/combat/status_device_bridge.verse"
        errors = self.mutated(path, "GetAEONFALLStatusRuntime().StatusesByTarget", "AppliedAgents")
        self.assertTrue(any("discover canonical statuses" in error for error in errors))

    def test_bridge_must_detect_replacement_character(self) -> None:
        path = "verse/combat/status_device_bridge.verse"
        errors = self.mutated(path, "CurrentCharacter = TrackedCharacter", "CurrentAgent = TrackedAgent")
        self.assertTrue(any("character generation across respawn" in error for error in errors))

    def test_bridge_character_tracking_commits_before_native_effects(self) -> None:
        path = "verse/combat/status_device_bridge.verse"
        errors = self.mutated(path, "set AppliedCharacters[TargetKey] = Character", "RecordNothing()")
        self.assertTrue(any("track each application before applying physical effects" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
