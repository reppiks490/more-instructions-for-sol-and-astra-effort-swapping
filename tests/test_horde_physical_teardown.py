"""Physical horde spawner teardown source invariants.

These tests do not execute Verse. Verify the actual NPC DespawnAll API,
streaming relevance and multiplayer callbacks in UEFN Launch Session.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HORDE_ADAPTER = ROOT / "verse/npcs/horde_ecology_adapter_device.verse"
HORDE_RUNTIME = ROOT / "verse/npcs/horde_runtime.verse"


class HordePhysicalTeardownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adapter = HORDE_ADAPTER.read_text(encoding="utf-8")
        cls.runtime = HORDE_RUNTIME.read_text(encoding="utf-8")
        cls.shutdown = cls.adapter.split("    OnEnd<override>():void=", 1)[1]

    def test_running_guard_prevents_rejected_adapter_despawn(self):
        body = self.shutdown
        self.assertIn("if (not Running?):\n            return", body)
        self.assertLess(body.index("if (not Running?):"),
                        body.index("Spawner.Disable()"))
        self.assertLess(body.index("if (not Running?):"),
                        body.index("Spawner.DespawnAll(false)"))
        self.assertEqual(body.count("Spawner.DespawnAll(false)"), 1)

    def test_callbacks_cancelled_before_physical_despawn(self):
        body = self.shutdown
        for marker in ("set Running = false", "StopEvent.Signal()",
                       "for (Subscription : Subscriptions):",
                       "for (Key -> Subscription : DeathSubscriptions):",
                       "Subscription.Cancel()"):
            self.assertIn(marker, body)
            self.assertLess(body.index(marker),
                            body.index("Spawner.DespawnAll(false)"))
        self.assertLess(body.index("Spawner.Disable()"),
                        body.index("Spawner.DespawnAll(false)"))

    def test_physical_bodies_cleared_before_logical_ledger_and_lease(self):
        body = self.shutdown
        spawn = body.index("Spawner.DespawnAll(false)")
        self.assertLess(spawn,
                        body.index("GetAEONFALLHordeRuntime().ClearRegion(RegionId)"))
        self.assertLess(spawn, body.index("ReleaseAdapterLease()"))
        self.assertLess(spawn, body.index("set OwnedActorKeys = map{}"))
        self.assertLess(body.index("GetAEONFALLHordeRuntime().ClearRegion(RegionId)"),
                        body.index("ReleaseAdapterLease()"))

    def test_spawn_admission_lease_and_late_death_guard_remain(self):
        begin = self.adapter.split("    OnBegin<override>()", 1)[1].split(
            "    AcquireAdapterLease()", 1
        )[0]
        self.assertLess(begin.index("Leased := AcquireAdapterLease()"),
                        begin.index("Spawner.Enable()"))
        self.assertIn("if (not Leased?):", begin)
        death = self.adapter.split("    RecordDeath(ActorKey:", 1)[1].split(
            "    FindNearest(", 1
        )[0]
        self.assertLess(death.index("Running?"), death.index("AddCorpse("))
        self.assertIn("DeathSubscriptions[ActorKey]", death)

    def test_no_extra_populations_or_persistent_ledger(self):
        self.assertEqual(self.adapter.count("Spawner:npc_spawner_device ="), 1)
        self.assertIn("AEONFALLHordeAdapterLeases:weak_map(session,", self.adapter)
        self.assertIn("var Brood:[string]aeonfall_horde_brood = map{}", self.runtime)
        self.assertIn("var RegionalBiomass:[string]int = map{}", self.runtime)
        self.assertNotIn("persistent", self.shutdown)


if __name__ == "__main__":
    unittest.main()
