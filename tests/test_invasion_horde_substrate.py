"""Source/data guard for ecological Devouring Moon admission.

Python checks validate authored and static contracts only. UEFN compilation,
physical NPC counts, and multiplayer admission still need editor evidence.
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
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DevouringMoonHordeSubstrateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))
        cls.validator = load_module(VALIDATOR, "living_world_horde_validator")
        cls.generator = load_module(GENERATOR, "living_world_horde_generator")

    def validate(self, payload):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "world.json"
            candidate.write_text(json.dumps(payload), encoding="utf-8")
            output = io.StringIO()
            with mock.patch.object(self.validator, "DATA", candidate), redirect_stdout(output):
                status = self.validator.main()
            return status, output.getvalue()

    def test_devouring_moon_needs_real_biomass_and_evolved_brood(self):
        inv = {row["id"]: row for row in self.data["invasions"]}
        moon = inv["INV-R001-005"]
        self.assertEqual(moon["min_corruption"], 80)
        self.assertEqual(moon["min_regional_horde_biomass"], 600)
        self.assertEqual(moon["min_horde_tier"], 4)
        self.assertEqual(moon["max_concurrent_ai"], 20)
        self.assertTrue(all(
            row.get("min_regional_horde_biomass", 0) == 0 and
            row.get("min_horde_tier", 0) == 0
            for key, row in inv.items() if key != "INV-R001-005"
        ))
        self.assertEqual(self.validate(self.data)[0], 0)

    def test_authoring_rejects_invalid_biomass_and_tiers(self):
        for field, values, label in (
            ("min_regional_horde_biomass", (-1, 6001, True, 600.0, "600", None),
             "min_regional_horde_biomass must be an integer 0..6000"),
            ("min_horde_tier", (-1, 6, True, 4.0, "4", None),
             "min_horde_tier must be an integer 0..5"),
        ):
            for value in values:
                with self.subTest(field=field, value=value):
                    data = copy.deepcopy(self.data)
                    data["invasions"][-1][field] = value
                    status, output = self.validate(data)
                    self.assertEqual(status, 1)
                    self.assertIn(label, output)
        for biomass, tier in ((0, 0), (599, 3), (600, 4), (6000, 5)):
            with self.subTest(biomass=biomass, tier=tier):
                data = copy.deepcopy(self.data)
                data["invasions"][-1]["min_regional_horde_biomass"] = biomass
                data["invasions"][-1]["min_horde_tier"] = tier
                self.assertEqual(self.validate(data)[0], 0)

    def test_verse_admission_reads_both_canonical_horde_sources_before_reserve(self):
        runtime = (ROOT / "verse/world/invasion_runtime.verse").read_text(encoding="utf-8")
        admission = runtime.split("    HasRequiredHordeSubstrate(", 1)[1].split(
            "    RequestWave(", 1
        )[0]
        start = runtime.split("    Start(InvasionId:", 1)[1].split(
            "    GetState(InvasionId:", 1
        )[0]
        self.assertIn("Horde.GetRegionalBiomass(Definition.RegionId)", admission)
        self.assertIn("Horde.HasBroodAtLeastTier(Definition.RegionId, Definition.MinHordeTier)?", admission)
        self.assertIn("Definition.MinRegionalHordeBiomass <= 0", admission)
        self.assertIn("Definition.MinHordeTier <= 0", admission)
        self.assertIn("HasRequiredHordeSubstrate(Definition)?", start)
        self.assertLess(start.index("HasRequiredHordeSubstrate(Definition)?"),
                        start.index("Added := GetAEONFALLRegionRuntime().AddEvent("))
        self.assertIn("RegionState.Corruption >= Definition.MinCorruption", start)
        self.assertNotIn("HasRequiredHordeSubstrate(Definition)?", runtime.split("    TickAll(", 1)[1])

    def test_horde_query_is_bounded_and_session_only(self):
        horde = (ROOT / "verse/npcs/horde_runtime.verse").read_text(encoding="utf-8")
        method = horde.split("    HasBroodAtLeastTier(", 1)[1].split(
            "    NextTier(", 1
        )[0]
        self.assertIn("for (ActorKey -> Member : Brood):", method)
        self.assertIn("Member.RegionId = RegionId", method)
        self.assertIn("Member.Tier >= MinimumTier", method)
        self.assertIn("MinimumTier < 1 or MinimumTier > 5", method)
        self.assertIn("MaxBrood:int = 128", (
            ROOT / "verse/npcs/horde_contract.verse").read_text(encoding="utf-8"))
        self.assertIn("var Brood:[string]aeonfall_horde_brood = map{}", horde)
        self.assertIn("var RegionalBiomass:[string]int = map{}", horde)
        self.assertIn("GetRegionalBiomass(RegionId:string)", horde)
        clear = horde.split("    ClearRegion(", 1)[1].split("    TickAll(", 1)[0]
        self.assertIn("set Brood = KeptBrood", clear)
        self.assertIn("set RegionalBiomass = KeptBiomass", clear)

    def test_registry_bounds_and_generated_parity(self):
        contract = (ROOT / "verse/world/invasion_contract.verse").read_text(encoding="utf-8")
        registry = (ROOT / "verse/world/invasion_registry.verse").read_text(encoding="utf-8")
        for token in ("MinRegionalHordeBiomass:int = 0", "MinHordeTier:int = 0"):
            self.assertIn(token, contract)
        for token in ("Definition.MinRegionalHordeBiomass >= 0",
                      "Definition.MinRegionalHordeBiomass <= 6000",
                      "Definition.MinHordeTier >= 0",
                      "Definition.MinHordeTier <= 5"):
            self.assertIn(token, registry)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated.verse"
            with mock.patch.object(self.generator, "ROOT", Path(directory)), \
                 mock.patch.object(self.generator, "OUTPUT", output), \
                 redirect_stdout(io.StringIO()):
                self.assertEqual(self.generator.main(), 0)
            self.assertEqual(output.read_text(encoding="utf-8"), GENERATED.read_text(encoding="utf-8"))
        rendered = GENERATED.read_text(encoding="utf-8")
        self.assertEqual(rendered.count("MinRegionalHordeBiomass := 600,"), 1)
        self.assertEqual(rendered.count("MinRegionalHordeBiomass := 0,"), 4)
        self.assertEqual(rendered.count("MinHordeTier := 4,"), 1)
        self.assertEqual(rendered.count("MinHordeTier := 0,"), 4)

    def test_no_new_ai_reservations(self):
        groups = {g["id"]: g["max_active"] for g in self.data["spawn_groups"]}
        for invasion in self.data["invasions"]:
            for wave in invasion["waves"]:
                self.assertLessEqual(sum(groups[group] for group in wave),
                                     invasion["max_concurrent_ai"])
        self.assertEqual(max(x["max_concurrent_ai"] for x in self.data["invasions"]), 20)
        self.assertEqual(len(self.data["spawn_groups"]), 6)
        self.assertEqual(len(self.data["invasions"]), 5)


if __name__ == "__main__":
    unittest.main()
