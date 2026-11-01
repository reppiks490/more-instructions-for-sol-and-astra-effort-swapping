"""Fail-closed horde physical binding guards.

These source checks cannot substitute for UEFN Verse compilation or editor
inspection of NPC Spawner start/limit settings.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HORDE = ROOT / "verse/npcs/horde_ecology_adapter_device.verse"
LIFECYCLE = ROOT / "verse/npcs/npc_lifecycle_behavior.verse"


class HordeBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HORDE.read_text(encoding="utf-8")

    def test_startup_fails_closed_before_spawner_enable(self):
        source = self.source
        self.assertIn("StartDisabled:logic = true", source)
        startup = source.split("    OnBegin<override>()", 1)[1].split(
            "    AcquireAdapterLease()", 1
        )[0]
        for guard in (
            'RegionId = ""',
            'CanonicalId = ""',
            'not StartDisabled?',
            'FeedingRadiusCm <= 0.0',
            'CorpseBiomass <= 0',
            'CorpseBiomass > GetAEONFALLHordeRuntime().Policy.CrownedBiomass',
        ):
            with self.subTest(guard=guard):
                self.assertIn(guard, startup)
        self.assertLess(startup.index("Leased := AcquireAdapterLease()"),
                        startup.index("Spawner.Enable()"))
        self.assertLess(startup.index("RegisterRegion(RegionId)"),
                        startup.index("Spawner.Enable()"))
        self.assertLess(startup.index("Spawner.SpawnedEvent.Subscribe(OnSpawned)"),
                        startup.index("Spawner.Enable()"))

    def test_existing_lifecycle_identity_is_preserved_and_checked(self):
        source = self.source
        spawned = source.split("    OnSpawned(Agent:agent):void=", 1)[1].split(
            "    RecordDeath(", 1
        )[0]
        self.assertIn("GetRuntimeKey[Agent]", spawned)
        self.assertIn("GetCanonicalId[Key] = CanonicalId", spawned)
        self.assertLess(spawned.index("GetCanonicalId[Key] = CanonicalId"),
                        spawned.index("RegisterBrood(Key, RegionId)"))
        self.assertIn("if (not ExistingIdentity?):", spawned)
        self.assertIn("ReleaseOwnedActor(Key)", spawned)
        self.assertIn("GetAEONFALLActorRegistry().Register[CanonicalId, Agent]",
                      LIFECYCLE.read_text(encoding="utf-8"))

    def test_delayed_death_rechecks_canonical_identity(self):
        death = self.source.split("    RecordDeath(ActorKey:", 1)[1].split(
            "    FindNearest(", 1
        )[0]
        for guard in (
            "Running?",
            "DeathSubscriptions[ActorKey]",
            "Brood.RegionId = RegionId",
            "GetCanonicalId[ActorKey] = CanonicalId",
        ):
            self.assertIn(guard, death)
            self.assertLess(death.index(guard), death.index("AddCorpse("))


if __name__ == "__main__":
    unittest.main()
