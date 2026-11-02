"""World-event region binding notifications must reconcile canonical state.

Source-level guards only. Test the actual Trigger devices and World Partition
handoff in UEFN with two clients and physical NPC counts.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "verse/events/world_event_region_binding_device.verse"
SERVICE = ROOT / "verse/events/world_event_runtime.verse"


class WorldEventRegionBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adapter = BINDING.read_text(encoding="utf-8")
        cls.service = SERVICE.read_text(encoding="utf-8")

    def test_registry_and_runtime_state_must_exist_before_lease(self):
        start = self.adapter.split("    OnBegin<override>()", 1)[1].split(
            "    AcquireLease()", 1
        )[0]
        for marker in (
            'RegionId <> ""',
            "GetAEONFALLRegionRegistry().IsRegistered[RegionId]",
            "GetAEONFALLRegionRuntime().GetState[RegionId]",
            "RegionEntered <> RegionReleased",
        ):
            self.assertIn(marker, start)
            self.assertLess(start.index(marker), start.index("Leased := AcquireLease()"))
        self.assertLess(start.index("Leased := AcquireLease()"),
                        start.index("RuntimeEvent.Subscribe(OnRuntimeEvent)"))
        self.assertLess(start.index("set OwnsLease = true"),
                        start.index("ReconcileRegion()"))

    def test_one_adapter_per_region_and_owner_only_teardown(self):
        self.assertIn(
            "AEONFALLWorldEventRegionBindings:weak_map(session, [string]",
            self.adapter,
        )
        claim = self.adapter.split("    AcquireLease()", 1)[1].split(
            "    ReleaseLease()", 1
        )[0]
        self.assertIn("if (Owners[RegionId]):", claim)
        self.assertIn("Owners.Length >= 32", claim)
        self.assertLess(claim.index("if (Owners[RegionId]):"),
                        claim.index("set Owners[RegionId] = Self"))
        release = self.adapter.split("    ReleaseLease()", 1)[1].split(
            "    ReconcileRegion()", 1
        )[0]
        self.assertIn("Owners[RegionId] = Self", release)
        end = self.adapter.split("    OnEnd<override>():void=", 1)[1]
        self.assertLess(end.index("if (not OwnsLease?):"),
                        end.index("RegionReleased.Trigger()"))
        self.assertLess(end.index("Bound.Cancel()"), end.index("ReleaseLease()"))

    def test_reconcile_only_changes_outputs_when_owner_changes(self):
        body = self.adapter.split("    ReconcileRegion():void=", 1)[1].split(
            "    OnRuntimeEvent(", 1
        )[0]
        self.assertIn(
            "GetAEONFALLWorldEventRuntime().ActiveEventForRegion(RegionId)",
            body,
        )
        self.assertIn("if (DesiredEventId = ActiveEventId):\n            return", body)
        self.assertLess(body.index("RegionReleased.Trigger()"),
                        body.index("RegionEntered.Trigger()"))
        self.assertIn('if (ActiveEventId <> ""):', body)
        self.assertIn('if (DesiredEventId <> ""):', body)
        self.assertNotIn("npc_spawner_device", body)

    def test_reconciles_existing_events_and_periodically_recovers_dropped_bus(self):
        start = self.adapter.split("    OnBegin<override>()", 1)[1].split(
            "    AcquireLease()", 1
        )[0]
        self.assertIn("ReconcileRegion()", start)
        self.assertIn("Sleep(1.0)", start)
        handler = self.adapter.split("    OnRuntimeEvent(", 1)[1].split(
            "    OnEnd<override>", 1
        )[0]
        for event in ("started", "stage_advanced", "completed", "failed"):
            self.assertIn(f'Event.EventType = "world_event.{event}"', handler)
        self.assertIn("ReconcileRegion()", handler)
        self.assertNotIn("Event.SourceId =", handler)

    def test_multiline_event_predicate_is_explicitly_grouped(self):
        handler = self.adapter.split("    OnRuntimeEvent(", 1)[1].split(
            "    OnEnd<override>", 1
        )[0]
        self.assertIn('if:\\n            (\\n                Event.EventType = "world_event.started"', handler)
        self.assertIn('Event.EventType = "world_event.failed"\\n            )\\n        then:', handler)

    def test_service_queries_only_active_canonical_claims(self):
        body = self.service.split("    ActiveEventForRegion(", 1)[1].split(
            "    CanClaimRegions(", 1
        )[0]
        self.assertIn('if (RegionId = ""):', body)
        self.assertIn("State.Active?", body)
        self.assertIn("State.ActiveRegionIds.Find[RegionId]", body)
        self.assertIn('        ""', body)

    def test_no_physical_spawner_or_persistent_state_added(self):
        for forbidden in ("npc_spawner_device", "Spawner.Enable()", "Spawner.DespawnAll("):
            self.assertNotIn(forbidden, self.adapter)
        self.assertIn("AEONFALLRuntimeBus.RuntimeEvent.Subscribe(OnRuntimeEvent)", self.adapter)
        self.assertIn("RegionEntered:trigger_device", self.adapter)
        self.assertIn("RegionReleased:trigger_device", self.adapter)


if __name__ == "__main__":
    unittest.main()
