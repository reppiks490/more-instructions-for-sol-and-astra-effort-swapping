"""Faction pressure, exclusion and registry generation regressions.

Source/data guards only: not native Verse compilation or UEFN tests.
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


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LivingWorldFactionPressureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(
            (ROOT / "content/world/region_001_living_world.json").read_text(encoding="utf-8")
        )
        cls.validator = load(
            ROOT / "tools/validate_region_001_living_world.py", "living_world_faction_validator"
        )
        cls.generator = load(
            ROOT / "tools/build_region_001_living_world_registry.py", "living_world_faction_generator"
        )

    def validate(self, payload):
        with tempfile.TemporaryDirectory() as folder:
            candidate = Path(folder) / "world.json"
            candidate.write_text(json.dumps(payload), encoding="utf-8")
            output = io.StringIO()
            with mock.patch.object(self.validator, "DATA", candidate), redirect_stdout(output):
                status = self.validator.main()
            return status, output.getvalue()

    def test_authored_faction_gates_use_existing_influence_transfers(self):
        seeds = {x["faction_id"]: x["influence"] for x in self.data["initial_faction_influence"]}
        expected = {"INV-R001-002": ("FAC-002", 30),
                    "INV-R001-003": ("FAC-004", 20),
                    "INV-R001-004": ("FAC-007", 15)}
        for invasion in self.data["invasions"]:
            gate = invasion.get("min_aggressor_influence", 0)
            if invasion["id"] in expected:
                faction, minimum = expected[invasion["id"]]
                self.assertEqual((invasion["aggressor_id"], gate), (faction, minimum))
                self.assertGreaterEqual(seeds[faction], minimum)
                self.assertLess(seeds[faction] - 10, minimum)
            else:
                self.assertEqual(gate, 0)
        self.assertEqual(self.validate(self.data)[0], 0)

    def test_invalid_values_and_ecological_impostors_are_rejected(self):
        for value in (-1, 101, True, 15.0, "15", None):
            with self.subTest(value=value):
                candidate = copy.deepcopy(self.data)
                candidate["invasions"][1]["min_aggressor_influence"] = value
                status, message = self.validate(candidate)
                self.assertEqual(status, 1)
                self.assertIn("min_aggressor_influence must be an integer 0..100", message)
        candidate = copy.deepcopy(self.data)
        candidate["invasions"][0]["min_aggressor_influence"] = 5
        status, message = self.validate(candidate)
        self.assertEqual(status, 1)
        self.assertIn("influence gate requires a canonical faction aggressor", message)

    def test_verse_admission_checks_canonical_influence_before_reservation(self):
        src = (ROOT / "verse/world/invasion_runtime.verse").read_text(encoding="utf-8")
        start = src.split("    Start(InvasionId:", 1)[1].split("    GetState(InvasionId:", 1)[0]
        self.assertIn("RegionState.FactionInfluence[Definition.AggressorId]", src)
        self.assertIn("Definition.MinAggressorInfluence <= 0", src)
        self.assertIn("HasRequiredAggressorInfluence(Definition, RegionState)?", start)
        self.assertLess(start.index("HasRequiredAggressorInfluence(Definition, RegionState)?"),
                        start.index("Added := GetAEONFALLRegionRuntime().AddEvent("))
        contract = (ROOT / "verse/world/invasion_contract.verse").read_text(encoding="utf-8")
        registry = (ROOT / "verse/world/invasion_registry.verse").read_text(encoding="utf-8")
        self.assertIn("MinAggressorInfluence:int = 0", contract)
        self.assertIn("Definition.MinAggressorInfluence >= 0", registry)
        self.assertIn("Definition.MinAggressorInfluence <= 100", registry)
        self.assertIn("RegionState.Corruption >= Definition.MinCorruption", start)

    def test_mutual_region_exclusion_and_initialization_fail_closed(self):
        invasion = (ROOT / "verse/world/invasion_runtime.verse").read_text(encoding="utf-8")
        faction = (ROOT / "verse/factions/conflict_runtime.verse").read_text(encoding="utf-8")
        i_start = invasion.split("    Start(InvasionId:", 1)[1].split(
            "    GetState(InvasionId:", 1)[0]
        f_start = faction.split("    StartConflict(", 1)[1].split(
            "    StartRegistered(", 1)[0]
        self.assertIn("ConflictRuntime := GetAEONFALLFactionConflictRuntime()", i_start)
        self.assertIn("not ConflictRuntime.HasActiveInRegion(Definition.RegionId)?", i_start)
        self.assertIn("InvasionRuntime := GetAEONFALLInvasionRuntime()", f_start)
        self.assertIn("not InvasionRuntime.HasActiveInRegion(RegionId)?", f_start)
        self.assertIn("not HasActiveInRegion(RegionId)?", f_start)
        self.assertIn("GetAEONFALLRegionRuntime().GetState[RegionId]", f_start)
        self.assertIn("if (Conflict.RegionId = RegionId, Conflict.Active?):", faction)
        self.assertLess(f_start.index("not InvasionRuntime.HasActiveInRegion(RegionId)?"),
                        f_start.index("set Conflicts[ConflictId] = Initial"))

    def test_generated_registry_parity(self):
        generated = ROOT / "verse/generated/region_001_living_world_bootstrap.verse"
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "generated.verse"
            with mock.patch.object(self.generator, "ROOT", Path(folder)), \
                 mock.patch.object(self.generator, "OUTPUT", destination), \
                 redirect_stdout(io.StringIO()):
                self.assertEqual(self.generator.main(), 0)
            self.assertEqual(destination.read_text(encoding="utf-8"),
                             generated.read_text(encoding="utf-8"))
        output = generated.read_text(encoding="utf-8")
        for value, count in ((0, 2), (30, 1), (20, 1), (15, 1)):
            self.assertEqual(output.count(f"MinAggressorInfluence := {value},"), count)

    def test_no_additional_ai(self):
        groups = {x["id"]: x["max_active"] for x in self.data["spawn_groups"]}
        self.assertEqual(len(groups), 6)
        self.assertEqual(len(self.data["invasions"]), 5)
        for invasion in self.data["invasions"]:
            self.assertLessEqual(max(sum(groups[g] for g in wave)
                                     for wave in invasion["waves"]),
                                 invasion["max_concurrent_ai"])
        self.assertEqual(max(x["max_concurrent_ai"] for x in self.data["invasions"]), 20)


if __name__ == "__main__":
    unittest.main()
