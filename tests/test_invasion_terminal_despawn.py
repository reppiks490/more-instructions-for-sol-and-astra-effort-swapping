"""Regression source checks for exclusive invasion NPC terminal cleanup.

The runtime already emits canonical completion/failure events. This suite
ensures their existing owning adapter cannot strand live bodies after a
terminal transition. Native Verse/UEFN still required.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "verse/world/npc_spawn_group_adapter_device.verse"
INVASION = ROOT / "verse/world/invasion_runtime.verse"


class InvasionTerminalDespawnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adapter = ADAPTER.read_text(encoding="utf-8")
        cls.runtime = INVASION.read_text(encoding="utf-8")

    def test_canonical_terminal_events_already_sent(self):
        complete = self.runtime.split("    Complete(InvasionId:", 1)[1].split(
            "    Fail(InvasionId:", 1
        )[0]
        failed = self.runtime.split("    Fail(InvasionId:", 1)[1].split(
            "    TickAll(", 1
        )[0]
        self.assertIn('EventType := "invasion.completed"', complete)
        self.assertIn('EventType := "invasion.failed"', failed)
        self.assertNotIn("spawn_group_released", complete)
        self.assertNotIn("spawn_group_released", failed)

    def test_terminal_events_require_authoritative_state_and_lease(self):
        handler = self.adapter.split(
            "    OnRuntimeEvent(Event:aeonfall_runtime_event):void=", 1
        )[1]
        self.assertIn("if (not OwnsLease?):", handler)
        self.assertIn("IsTerminalInvasion(Event.SourceId, true)?", handler)
        self.assertIn("IsTerminalInvasion(Event.SourceId, false)?", handler)
        guard = self.adapter.split("    IsTerminalInvasion(", 1)[1].split(
            "    AddRequester(", 1
        )[0]
        for token in (
            "Definition.RegionId = RegionId",
            "State.RegionId = RegionId",
            "not State.Active?",
            "State.Completed?",
            "State.Failed?",
        ):
            self.assertIn(token, guard)

    def test_completion_and_failure_unconditionally_despawn_last_owner(self):
        handler = self.adapter.split(
            "    OnRuntimeEvent(Event:aeonfall_runtime_event):void=", 1
        )[1]
        completion = handler.split('Event.EventType = "invasion.completed"', 1)[1].split(
            'Event.EventType = "invasion.failed"', 1
        )[0]
        failure = handler.split('Event.EventType = "invasion.failed"', 1)[1]
        for section, requester in ((completion, "RemovedCompleted"), (failure, "RemovedFailed")):
            with self.subTest(requester=requester):
                self.assertIn(f"if ({requester}?, ActiveInvasionIds.Length = 0):", section)
                self.assertLess(section.index("DisableAll()"), section.index("DespawnAll()"))
                self.assertNotIn("if (DespawnOnRelease?):", section)
        wave = handler.split('Event.EventType = "invasion.spawn_group_released"', 1)[1].split(
            'Event.EventType = "invasion.completed"', 1
        )[0]
        self.assertIn("if (DespawnOnRelease?):", wave)

    def test_device_shutdown_unconditionally_despawns_owned_bodies(self):
        shutdown = self.adapter.split("    OnEnd<override>():void=", 1)[1].split(
            "    AcquireAdapterLease()", 1
        )[0]
        self.assertLess(shutdown.index("if (not OwnsLease?):"), shutdown.index("DisableAll()"))
        self.assertIn("Subscription.Cancel()", shutdown)
        self.assertNotIn("if (DespawnOnRelease?):", shutdown)
        self.assertLess(shutdown.index("DisableAll()"), shutdown.index("DespawnAll()"))
        self.assertLess(shutdown.index("DespawnAll()"), shutdown.index("ReleaseAdapterLease()"))

    def test_no_new_spawner_authority_or_ai_capacity(self):
        self.assertIn("if (ActiveInvasionIds.Length >= 1):", self.adapter)
        self.assertIn("if (Owners.Length >= 128):", self.adapter)
        self.assertIn("AEONFALLHordeAdapterLeases[GetSession()]", self.adapter)
        self.assertEqual(self.adapter.count("Spawners:[]npc_spawner_device"), 1)


if __name__ == "__main__":
    unittest.main()
