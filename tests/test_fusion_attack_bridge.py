"""Mutation tests for FUS-001 attack request; no UEFN runtime assertions."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "fusion_attack_guard", ROOT / "tools/validate_fusion_attack_bridge.py"
)
assert SPEC and SPEC.loader
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class FusionAttackSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = guard.SOURCE.read_text(encoding="utf-8")

    def mutate(self, before: str, after: str):
        self.assertIn(before, self.source)
        self.assertTrue(guard.check_source(self.source.replace(before, after, 1)))

    def test_baseline(self):
        self.assertEqual(guard.check_source(self.source), [])

    def test_no_cross_player_attack(self):
        self.mutate("Owner = Player", "Owner <> Player")

    def test_canonical_generation_required(self):
        self.mutate(
            "Authorized := State.IsAuthorizedActive(Self, Player, Token)",
            "Authorized := true",
        )

    def test_character_swap_rejected(self):
        self.mutate("Character = OriginalCharacter", "Character <> OriginalCharacter")

    def test_cooldown_required(self):
        self.mutate(
            "Now >= LastAttackAt + AttackCooldownSeconds",
            "Now >= 0.0",
        )

    def test_resource_reservation_required(self):
        self.mutate(
            "Resource.Spend[Self, Player, Token, State, AttackEnergyCost]",
            "AttackEnergyCost > 0",
        )

    def test_energy_cost_is_bounded(self):
        self.mutate("AttackEnergyCost <= 25", "AttackEnergyCost <= 250")

    def test_input_must_be_distinct(self):
        self.mutate("SeparateInput <> AttackInput", "SeparateInput = AttackInput")

    def test_attack_cooldown_reset_on_exit(self):
        self.mutate("set LastAttackAt = -1000.0", "set LastAttackAt = 0.0")

    def test_single_physical_producer(self):
        self.assertTrue(guard.check_source(
            self.source + "\n    Bad():void=\n        AttackOutput.Trigger(Player)\n"
        ))


if __name__ == "__main__":
    unittest.main()
