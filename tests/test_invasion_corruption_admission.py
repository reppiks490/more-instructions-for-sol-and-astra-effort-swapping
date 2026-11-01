"""Corruption admission regressions for canonical living-world invasions.

Source guards and authored-data checks only; UEFN Launch Session is required
to establish native Verse compilation and physical multiplayer behavior.
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
GENERATOR = ROOT / "tools/build_region_001_living_world_registry.py"
GENERATED = ROOT / "verse/generated/region_001_living_world_bootstrap.verse"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class InvasionCorruptionAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))
        cls.validator = load_module(VALIDATOR, "aeonfall_living_world_validator")
        cls.generator = load_module(GENERATOR, "aeonfall_living_world_generator")

    def validate(self, payload):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "living_world.json"
            candidate.write_text(json.dumps(payload), encoding="utf-8")
            output = io.StringIO()
            with mock.patch.object(self.validator, "DATA", candidate):
                with redirect_stdout(output):
                    status = self.validator.main()
            return status, output.getvalue()

    def test_devouring_moon_requires_corruption_80_without_extra_ai(self):
        invasions = {row["id"]: row for row in self.data["invasions"]}
        devouring = invasions["INV-R001-005"]
        self.assertEqual(devouring["min_corruption"], 80)
        self.assertEqual(devouring["max_concurrent_ai"], 20)
        self.assertEqual(devouring["min_hostility_tier"], 4)
        self.assertTrue(all(
            row.get("min_corruption", 0) == 0
            for key, row in invasions.items() if key != "INV-R001-005"
        ))
        self.assertEqual(self.validate(self.data)[0], 0)

    def test_validator_rejects_invalid_corruption_thresholds(self):
        for value in (-1, 101, True, 80.0, "80", None):
            with self.subTest(value=value):
                payload = copy.deepcopy(self.data)
                payload["invasions"][-1]["min_corruption"] = value
                status, output = self.validate(payload)
                self.assertEqual(status, 1)
                self.assertIn("min_corruption must be an integer 0..100", output)
        for value in (0, 79, 80, 100):
            with self.subTest(valid=value):
                payload = copy.deepcopy(self.data)
                payload["invasions"][-1]["min_corruption"] = value
                self.assertEqual(self.validate(payload)[0], 0)

    def test_verse_admission_uses_canonical_state_before_reserving_event(self):
        source = (ROOT / "verse/world/invasion_runtime.verse").read_text(encoding="utf-8")
        start = source.split("    Start(InvasionId:", 1)[1].split(
            "    GetState(InvasionId:", 1
        )[0]
        guard = "RegionState.Corruption >= Definition.MinCorruption"
        reserve = "Added := GetAEONFALLRegionRuntime().AddEvent("
        for token in (
            "GetAEONFALLRegionRuntime().GetState[Definition.RegionId]",
            "RegionState.HostilityTier >= Definition.MinHostilityTier",
            guard,
            "not HasActiveInRegion(Definition.RegionId)?",
            "not RegionState.ActiveEventIds.Find[InvasionId]",
            reserve,
        ):
            self.assertIn(token, start)
        self.assertLess(start.index(guard), start.index(reserve))
        self.assertNotIn(guard, source.split("    TickAll(", 1)[1])

        contract = (ROOT / "verse/world/invasion_contract.verse").read_text(
            encoding="utf-8"
        )
        registry = (ROOT / "verse/world/invasion_registry.verse").read_text(
            encoding="utf-8"
        )
        self.assertIn("MinCorruption:int = 0", contract)
        self.assertIn("Definition.MinCorruption >= 0", registry)
        self.assertIn("Definition.MinCorruption <= 100", registry)

    def test_generated_bootstrap_matches_generator(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated.verse"
            with mock.patch.object(self.generator, "OUTPUT", output), \
                    mock.patch.object(self.generator, "ROOT", Path(directory)):
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(self.generator.main(), 0)
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                GENERATED.read_text(encoding="utf-8"),
            )
        generated = GENERATED.read_text(encoding="utf-8")
        self.assertEqual(generated.count("MinCorruption := 80,"), 1)
        self.assertEqual(generated.count("MinCorruption := 0,"), 4)


if __name__ == "__main__":
    unittest.main()
