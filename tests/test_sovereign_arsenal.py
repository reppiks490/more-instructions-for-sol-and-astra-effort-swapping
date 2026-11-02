"""Mutation and deterministic-model tests; NOT Verse compile/Launch Session."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


guard = load("arsenal_guard", ROOT / "tools/validate_sovereign_arsenal.py")
model = load("arsenal_model", ROOT / "tools/simulate_sovereign_arsenal.py")


class ArsenalSourceGuards(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads(guard.POLICY.read_text(encoding="utf-8"))
        self.runtime = guard.RUNTIME.read_text(encoding="utf-8")
        self.device = guard.DEVICE.read_text(encoding="utf-8")

    def check(self):
        return guard.check_sources(self.policy, self.runtime, self.device)

    def mutate(self, source: str, before: str, after: str):
        value = getattr(self, source)
        self.assertIn(before, value)
        setattr(self, source, value.replace(before, after, 1))
        self.assertTrue(self.check())

    def test_baseline(self):
        self.assertEqual(self.check(), [])

    def test_disabled_default(self):
        self.mutate("device", "Enabled:logic = false", "Enabled:logic = true")

    def test_owner_spoof(self):
        self.mutate("device", "Owner = Player", "Owner <> Player")

    def test_character_swap(self):
        self.mutate("device", "Character = Original", "Character <> Original")

    def test_canonical_generation(self):
        self.mutate("device", "State.IsAuthorizedActive(Controller, Player, Controller.Token)",
                    "State.IsAuthorizedActive(Controller, Player, 0)")

    def test_energy_bypass(self):
        self.mutate("runtime", "Budget.Spend[Device, Player, Token, State, 20]",
                    "Budget.Spend[Device, Player, Token, State, 0]")

    def test_rend_cooldown_bypass(self):
        self.mutate("runtime", "Now >= LastRendAt + 2.0", "Now >= 0.0")

    def test_collapse_cooldown_bypass(self):
        self.mutate("runtime", "Now >= LastCollapseAt + 8.0", "Now >= 0.0")

    def test_bulwark_cooldown_bypass(self):
        self.mutate("runtime", "Now >= LastBulwarkAt + 18.0", "Now >= 0.0")

    def test_boss_eligibility(self):
        self.mutate("device", "IsMonsterId(Canonical)?", "Canonical <> \"\"")

    def test_companion_immunity(self):
        self.mutate("device", "Binding.Active?", "false?")

    def test_player_immunity(self):
        self.mutate("device", "not player[Candidate]", "player[Candidate]")

    def test_target_vulnerability(self):
        self.mutate("device", "Target.IsVulnerable[]", "Target.IsActive[]")

    def test_shield_cap(self):
        self.mutate("runtime", "PreviouslyGranted + Amount <= 40.0",
                    "PreviouslyGranted + Amount <= 400.0")

    def test_class_gate(self):
        self.mutate("device", 'Equipped.ClassId = "CLS-006"',
                    'Equipped.ClassId <> "CLS-006"')

    def test_damage_cap(self):
        self.mutate("device", "Target.Damage(18.0)", "Target.Damage(1800.0)")

    def test_no_cooldown_reset_on_release(self):
        self.runtime = self.runtime.replace("set Controller = false",
                                            "set LastRendAt = -1000.0\n            set Controller = false")
        self.assertTrue(self.check())

    def test_policy_cap(self):
        self.policy["weapons"][1]["max_targets"] = 99
        self.assertTrue(self.check())


class ArsenalPolicyModelTests(unittest.TestCase):
    def test_owner_and_generation(self):
        a = model.ArsenalModel()
        self.assertFalse(a.request("rend", 1, "other", 1, target="MON-001", distance=100)[0])
        self.assertFalse(a.request("rend", 1, "creator", 2, target="MON-001", distance=100)[0])
        self.assertEqual(a.energy, 100)

    def test_boss_player_and_friendly_immune(self):
        a = model.ArsenalModel()
        for target, hostile in (("BOS-001", True), ("PLAYER", True), ("MON-001", False)):
            self.assertFalse(a.request("rend", 1, "creator", 1,
                                       target=target, distance=100, hostile=hostile)[0])
        self.assertEqual(a.energy, 100)

    def test_rend_cost_and_cooldown(self):
        a = model.ArsenalModel()
        self.assertEqual(a.request("rend", 1, "creator", 1, target="MON-001", distance=100),
                         (True, 18.0))
        self.assertEqual(a.energy, 85)
        self.assertFalse(a.request("rend", 2, "creator", 1, target="MON-001", distance=100)[0])
        self.assertTrue(a.request("rend", 3, "creator", 1, target="MON-001", distance=100)[0])

    def test_class_combo_is_bounded(self):
        a = model.ArsenalModel()
        a.request("rend", 1, "creator", 1, target="MON-001", distance=100)
        self.assertEqual(a.request("collapse", 2, "creator", 1, target="MON-001",
                                   distance=400, class_id="CLS-006", target_count=3),
                         (True, 34.0))

    def test_combo_no_class_no_bonus(self):
        a = model.ArsenalModel()
        a.request("rend", 1, "creator", 1, target="MON-001", distance=100)
        self.assertEqual(a.request("collapse", 2, "creator", 1, target="MON-001",
                                   distance=400, class_id="CLS-007", target_count=3),
                         (True, 30.0))

    def test_bulwark_native_cap_and_generation_allowance(self):
        a = model.ArsenalModel()
        self.assertEqual(a.request("bulwark", 1, "creator", 1, shield=90),
                         (True, 10.0))
        self.assertEqual(a.request("bulwark", 19, "creator", 1, shield=0),
                         (True, 20.0))
        self.assertEqual(a.request("bulwark", 37, "creator", 1, shield=0),
                         (True, 10.0))
        self.assertFalse(a.request("bulwark", 55, "creator", 1, shield=0)[0])

    def test_deadline_and_insufficient_energy(self):
        a = model.ArsenalModel(energy=5)
        self.assertFalse(a.request("collapse", 1, "creator", 1,
                                   target="MON-001", distance=200)[0])
        a.energy = 100
        self.assertFalse(a.request("collapse", 90, "creator", 1,
                                   target="MON-001", distance=200)[0])

    def test_range_and_target_cap(self):
        a = model.ArsenalModel()
        self.assertFalse(a.request("rend", 1, "creator", 1,
                                   target="MON-001", distance=400)[0])
        self.assertFalse(a.request("collapse", 1, "creator", 1,
                                   target="MON-001", distance=400, target_count=4)[0])


if __name__ == "__main__":
    unittest.main()
