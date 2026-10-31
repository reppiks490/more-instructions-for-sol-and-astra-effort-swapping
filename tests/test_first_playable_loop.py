"""Mutation tests for production source guards, not a Verse runtime emulator."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("first_play", ROOT / "tools/validate_first_playable_loop.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class FirstPlayableSourceGuards(unittest.TestCase):
    def setUp(self):
        self.sources = {key: (ROOT / path).read_text(encoding="utf-8")
                        for key, path in guard.SOURCES.items()}
        self.policy = json.loads((ROOT / guard.POLICY_PATH).read_text(encoding="utf-8"))

    def test_authored_source_passes(self):
        self.assertEqual(guard.check_sources(self.sources, self.policy), [])

    def assertMutationRejected(self, name, old, new):
        self.assertIn(old, self.sources[name])
        self.sources[name] = self.sources[name].replace(old, new, 1)
        self.assertTrue(guard.check_sources(self.sources, self.policy))

    def test_class_partial_commit_is_rejected(self):
        self.assertMutationRejected("class", "<decides><transacts>:void=\n        not HasActiveReservation",
                                    "<transacts>:void=\n        not HasActiveReservation")

    def test_class_switch_refill_is_rejected(self):
        self.assertMutationRejected("class", "SavedResource := History[ClassId]",
                                    "SavedResource := Definition.MaxResource")

    def test_harvest_unchecked_save_is_rejected(self):
        self.assertMutationRejected("harvest", "Saved?", "set Materials = Materials")

    def test_harvest_unchecked_consumption_is_rejected(self):
        self.assertMutationRejected("harvest", "Used?", "set Materials = Materials")

    def test_harvest_remote_consumption_is_rejected(self):
        self.assertMutationRejected("harvest", "Distance(Position, CorpsePosition) <= HarvestRangeCm",
                                    "HarvestRangeCm > 0.0")

    def test_unearned_meter_is_rejected(self):
        self.assertMutationRejected("heat", "ItemGate.IsHoldingItem[Agent]", "Player.IsActive[]")

    def test_devour_unlock_bypass_is_rejected(self):
        self.assertMutationRejected("harvest", 'Old.UnlockedEntityIds.Find["WPN-003"]',
                                    'Old.UnlockedEntityIds.Find["WPN-001"]')

    def test_native_failable_call_regression_is_rejected(self):
        self.assertMutationRejected("position", "GetFortCharacter[]", "GetFortCharacter()")

    def test_negated_region_registration_is_rejected(self):
        # Migration may have changed the service reference; preserve its form.
        text = self.sources["ecology"]
        line = next(line for line in text.splitlines() if "Registered := " in line)
        call = line.strip().split(" := ", 1)[1]
        self.sources["ecology"] = text.replace(line, f"        if (not {call}?):")
        self.assertTrue(guard.check_sources(self.sources, self.policy))

    def test_duplicate_horde_spawner_ownership_is_rejected(self):
        self.assertMutationRejected("ecology", "OtherAdapter.Spawner = Spawner",
                                    "OtherRegion = RegionId")

    def test_native_spawn_success_bypass_is_rejected(self):
        self.assertMutationRejected("prop", "Spawned(1) = spawn_prop_result.Ok",
                                    "Enabled?")

    def test_projected_placement_range_bypass_is_rejected(self):
        self.assertMutationRejected("prop", "Distance(Origin, Position) >= MinimumDistanceCm",
                                    "MinimumDistanceCm >= 0.0")

    def test_unbounded_position_contexts_are_rejected(self):
        self.assertMutationRejected("position", "Contexts.Length < 1024", "Contexts.Length >= 0")

    def test_boss_only_material_farming_is_rejected(self):
        changed = copy.deepcopy(self.policy)
        changed["corpse_harvest"]["material_rewards"]["MAT-011"] = 1
        self.assertTrue(guard.check_sources(self.sources, changed))

    def test_runtime_reward_drift_is_rejected(self):
        self.assertMutationRejected("harvest", 'OldBone + 12', 'OldBone + 1200')

    def test_unsupported_visibility_claim_is_rejected(self):
        self.policy["target_selection"]["line_of_sight_check"] = True
        self.assertTrue(guard.check_sources(self.sources, self.policy))


if __name__ == "__main__":
    unittest.main()
