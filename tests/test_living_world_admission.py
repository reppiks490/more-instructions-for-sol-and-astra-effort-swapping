"""REG-001 authored AI-budget regressions and Verse source admission guards.

These tests do not execute Verse or substitute for native UEFN NPC/streaming tests.
"""
from __future__ import annotations

import copy
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "content/world/region_001_living_world.json"
VALIDATOR = ROOT / "tools/validate_region_001_living_world.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("living_world_validator", VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("living-world validator could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LivingWorldAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = json.loads(DATA.read_text(encoding="utf-8"))
        cls.validator = load_validator()

    def validate(self, payload):
        with tempfile.TemporaryDirectory() as temp:
            data_path = Path(temp) / "living_world.json"
            data_path.write_text(json.dumps(payload), encoding="utf-8")
            output = io.StringIO()
            with mock.patch.object(self.validator, "DATA", data_path):
                with redirect_stdout(output):
                    code = self.validator.main()
            return code, output.getvalue()

    def test_current_authored_waves_fit_their_reserves(self):
        groups = {g["id"]: g["max_active"] for g in self.baseline["spawn_groups"]}
        for invasion in self.baseline["invasions"]:
            for index, wave in enumerate(invasion["waves"]):
                with self.subTest(invasion=invasion["id"], wave=index):
                    self.assertLessEqual(
                        sum(groups[group_id] for group_id in wave),
                        invasion["max_concurrent_ai"],
                    )
        code, output = self.validate(copy.deepcopy(self.baseline))
        self.assertEqual(code, 0, output)

    def test_oversubscribed_wave_is_rejected(self):
        doc = copy.deepcopy(self.baseline)
        doc["spawn_groups"][0]["max_active"] = 9
        code, output = self.validate(doc)
        self.assertEqual(code, 1)
        self.assertIn("reserves 13 AI", output)

    def test_duplicate_group_cannot_double_admit(self):
        doc = copy.deepcopy(self.baseline)
        doc["invasions"][0]["waves"][0].append(
            doc["invasions"][0]["waves"][0][0]
        )
        code, output = self.validate(doc)
        self.assertEqual(code, 1)
        self.assertIn("duplicate group in wave 0", output)

    def test_unknown_group_is_rejected(self):
        doc = copy.deepcopy(self.baseline)
        doc["invasions"][0]["waves"][0] = ["SG-DOES-NOT-EXIST"]
        code, output = self.validate(doc)
        self.assertEqual(code, 1)
        self.assertIn("missing spawn group SG-DOES-NOT-EXIST", output)

    def test_invalid_group_cap_is_rejected(self):
        doc = copy.deepcopy(self.baseline)
        doc["spawn_groups"][0]["max_active"] = 25
        code, output = self.validate(doc)
        self.assertEqual(code, 1)
        self.assertIn("max_active must be 1..24", output)

    def test_invasion_admission_source_guards(self):
        source = (ROOT / "verse/world/invasion_runtime.verse").read_text(
            encoding="utf-8"
        )
        start = source.split("    Start(InvasionId:", 1)[1].split(
            "    GetState(InvasionId:", 1
        )[0]
        self.assertIn("not HasActiveInRegion(Definition.RegionId)?", start)
        self.assertIn("not RegionState.ActiveEventIds.Find[InvasionId]", start)
        self.assertLess(
            start.index("Added := GetAEONFALLRegionRuntime().AddEvent("),
            start.index("set States[InvasionId] = Initial"),
        )
        self.assertIn("Added?", start)
        objective = source.split("    MarkObjectiveComplete(", 1)[1].split(
            "    AdvanceWave(", 1
        )[0]
        self.assertIn("Definition.ObjectiveIds.Find[ObjectiveId]", objective)

    def test_spawn_adapter_rejects_stale_cross_region_requests(self):
        source = (ROOT / "verse/world/npc_spawn_group_adapter_device.verse").read_text(
            encoding="utf-8"
        )
        for guard in (
            'RegionId:string = ""',
            'Definition.RegionId = RegionId',
            'State.Active?',
            'State.RegionId = RegionId',
            'State.CurrentWaveIndex = WaveIndex',
            'Wave.Find[SpawnGroupId]',
            'Event.ContextId = RegionId',
            'IsActiveWaveRequest(Event.SourceId, Event.Amount)?',
            'Event.TargetId = RegionId',
            'set ActiveInvasionIds = array{}',
            'DespawnAll()',
        ):
            with self.subTest(guard=guard):
                self.assertIn(guard, source)


    def test_spawn_adapters_lease_physical_devices_before_touching_them(self):
        source = (ROOT / "verse/world/npc_spawn_group_adapter_device.verse").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "AEONFALLInvasionSpawnerLeases:weak_map(session, "
            "[string]aeonfall_npc_spawn_group_adapter_device)", source
        )
        startup = source.split("    OnBegin<override>()", 1)[1].split(
            "    OnEnd<override>()", 1
        )[0]
        self.assertLess(
            startup.index("Leased := AcquireAdapterLease()"),
            startup.index("DisableAll()"),
        )
        self.assertLess(
            startup.index("set OwnsLease = true"),
            startup.index("RuntimeEvent.Subscribe(OnRuntimeEvent)"),
        )
        self.assertIn("Spawners.Length = 0", startup)
        self.assertIn("not StartDisabled?", startup)

        acquire = source.split("    AcquireAdapterLease()", 1)[1].split(
            "    ReleaseAdapterLease()", 1
        )[0]
        self.assertIn("Owners[Key]", acquire)
        self.assertIn("Index <> OtherIndex", acquire)
        self.assertIn("OtherAdapter.Spawners", acquire)
        self.assertIn("Spawner = OwnedSpawner", acquire)
        self.assertIn("Owners.Length >= 128", acquire)

        shutdown = source.split("    OnEnd<override>()", 1)[1].split(
            "    AcquireAdapterLease()", 1
        )[0]
        self.assertLess(
            shutdown.index("if (not OwnsLease?):"),
            shutdown.index("DisableAll()"),
        )
        self.assertLess(
            shutdown.index("DespawnAll()"),
            shutdown.index("ReleaseAdapterLease()"),
        )

    def test_spawn_adapter_ignores_stale_and_spoofed_lifecycle_events(self):
        source = (ROOT / "verse/world/npc_spawn_group_adapter_device.verse").read_text(
            encoding="utf-8"
        )
        for guard in (
            "if (not OwnsLease?):",
            "State.CurrentWaveIndex > OldWaveIndex",
            "not CurrentWave.Find[SpawnGroupId]",
            "IsValidWaveRelease(Event.SourceId, Event.Amount)?",
            "IsTerminalInvasion(Event.SourceId, true)?",
            "IsTerminalInvasion(Event.SourceId, false)?",
            "not State.Active?",
            "State.Completed?",
            "State.Failed?",
        ):
            with self.subTest(guard=guard):
                self.assertIn(guard, source)

    def test_horde_and_invasion_spawners_are_mutually_exclusive(self):
        horde = (ROOT / "verse/npcs/horde_ecology_adapter_device.verse").read_text(
            encoding="utf-8"
        )
        invasion = (ROOT / "verse/world/npc_spawn_group_adapter_device.verse").read_text(
            encoding="utf-8"
        )
        horde_acquire = horde.split("    AcquireAdapterLease()", 1)[1].split(
            "    ReleaseAdapterLease()", 1
        )[0]
        invasion_acquire = invasion.split("    AcquireAdapterLease()", 1)[1].split(
            "    ReleaseAdapterLease()", 1
        )[0]
        self.assertIn("AEONFALLInvasionSpawnerLeases[GetSession()]", horde_acquire)
        self.assertIn("for (OwnedSpawner : OtherAdapter.Spawners):", horde_acquire)
        self.assertIn("OwnedSpawner = Spawner", horde_acquire)
        self.assertLess(
            horde_acquire.index("OwnedSpawner = Spawner"),
            horde_acquire.index("set Owners[RegionId] = Self"),
        )
        self.assertIn("AEONFALLHordeAdapterLeases[GetSession()]", invasion_acquire)
        self.assertIn("for (CandidateSpawner : Spawners):", invasion_acquire)
        self.assertIn("OtherAdapter.Spawner = CandidateSpawner", invasion_acquire)
        self.assertLess(
            invasion_acquire.index("OtherAdapter.Spawner = CandidateSpawner"),
            invasion_acquire.index("set Owners[Key] = Self"),
        )

    def test_horde_stale_death_cannot_mint_corpse_or_clear_foreign_actor(self):
        horde = (ROOT / "verse/npcs/horde_ecology_adapter_device.verse").read_text(
            encoding="utf-8"
        )
        death = horde.split("    RecordDeath(ActorKey:", 1)[1].split(
            "    FindNearest(", 1
        )[0]
        for guard in (
            "Running?",
            "DeathSubscriptions[ActorKey]",
            "GetAEONFALLHordeRuntime().GetBrood[ActorKey]",
            "Brood.RegionId = RegionId",
        ):
            self.assertIn(guard, death)
            self.assertLess(death.index(guard), death.index("AddCorpse("))
        self.assertLess(death.index("then:"), death.index("RemoveBrood(ActorKey)"))
        self.assertLess(death.index("then:"), death.index("ReleaseOwnedActor(ActorKey)"))
        for callback in ("OpenApex", "CloseApex"):
            body = horde.split(f"    {callback}(MaybeAgent:?agent):void=", 1)[1]
            self.assertIn("if (Running?):", body.split("\n\n", 1)[0])


if __name__ == "__main__":
    unittest.main()
