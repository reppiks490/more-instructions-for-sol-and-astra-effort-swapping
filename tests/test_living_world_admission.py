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


if __name__ == "__main__":
    unittest.main()
