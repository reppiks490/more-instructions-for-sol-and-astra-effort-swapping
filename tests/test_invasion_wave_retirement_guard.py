"""Authored NPC wave budgets require cleanup of outgoing physical actors.

These are source-level admission tests; the UEFN editor still owns native
spawn limits and streaming relevance.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "verse/world/npc_spawn_group_adapter_device.verse"


class InvasionWaveRetirementGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = ADAPTER.read_text(encoding="utf-8")

    def test_false_retirement_setting_is_rejected_before_lease_and_io(self):
        startup = self.source.split("    OnBegin<override>()", 1)[1].split(
            "    OnEnd<override>()", 1
        )[0]
        self.assertIn("not DespawnOnRelease?", startup)
        self.assertIn("not StartDisabled?", startup)
        self.assertIn("Spawners.Length = 0", startup)
        self.assertLess(startup.index("not DespawnOnRelease?"),
                        startup.index("Leased := AcquireAdapterLease()"))
        self.assertLess(startup.index("if (RegionId ="),
                        startup.index("DisableAll()"))
        self.assertLess(startup.index("Leased := AcquireAdapterLease()"),
                        startup.index("RuntimeEvent.Subscribe(OnRuntimeEvent)"))
        self.assertIn("return\n        Leased := AcquireAdapterLease()", startup)

    def test_previous_editor_bindings_remain_compatible(self):
        self.assertIn("@editable\n    DespawnOnRelease:logic = true", self.source)
        self.assertIn("@editable\n    StartDisabled:logic = true", self.source)

    def test_retired_groups_require_released_requester_and_physical_despawn(self):
        handler = self.source.split(
            "    OnRuntimeEvent(Event:aeonfall_runtime_event):void=", 1
        )[1]
        release = handler.split('Event.EventType = "invasion.spawn_group_released"', 1)[1].split(
            'Event.EventType = "invasion.completed"', 1
        )[0]
        self.assertIn("IsValidWaveRelease(Event.SourceId, Event.Amount)?", release)
        self.assertIn("RemovedWave := RemoveRequester(Event.SourceId)", release)
        self.assertIn("ActiveInvasionIds.Length = 0", release)
        self.assertIn("DisableAll()", release)
        self.assertIn("if (DespawnOnRelease?):\n                    DespawnAll()", release)
        self.assertLess(release.index("DisableAll()"), release.index("DespawnAll()"))

    def test_canonical_wave_transition_releases_only_groups_not_reused(self):
        source = (ROOT / "verse/world/invasion_runtime.verse").read_text(
            encoding="utf-8"
        )
        transition = source.split("    TransitionWave(", 1)[1].split(
            "    Start(InvasionId:", 1
        )[0]
        self.assertIn("if (not NewWave.Find[OldGroupId]):", transition)
        self.assertIn("ReleaseSpawnGroup(", transition)
        self.assertIn("if (not OldWave.Find[NewGroupId]):", transition)

    def test_no_second_director_or_population_reserve(self):
        self.assertIn("AEONFALLInvasionSpawnerLeases:weak_map(session,", self.source)
        self.assertIn("AEONFALLHordeAdapterLeases[GetSession()]", self.source)
        self.assertIn("if (Owners.Length >= 128):", self.source)


if __name__ == "__main__":
    unittest.main()
