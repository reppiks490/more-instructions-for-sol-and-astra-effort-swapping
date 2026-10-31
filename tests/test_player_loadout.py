#!/usr/bin/env python3
"""Mutate committed source contracts to catch real integration guard removal."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("player_loadout_guard", ROOT / "tools/validate_player_loadout.py")
assert SPEC and SPEC.loader
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


class PlayerLoadoutContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {name: (ROOT / path).read_text(encoding="utf-8") for name, path in GUARD.SOURCES.items()}

    def mutation(self, name: str, old: str, new: str, count: int = 1):
        sources = copy.deepcopy(self.sources)
        self.assertIn(old, sources[name], f"mutation anchor absent: {old}")
        sources[name] = sources[name].replace(old, new, count)
        self.assertTrue(GUARD.check_sources(sources), f"unguarded mutation in {name}")

    def test_current_source_contracts(self):
        self.assertEqual([], GUARD.check_sources(self.sources))

    def test_inactive_save_rejected(self):
        self.mutation("profile", "            Player.IsActive[]\n            FitsInPlayerMap[Candidate]", "            FitsInPlayerMap[Candidate]")

    def test_persistent_size_check_required(self):
        self.mutation("profile", "            FitsInPlayerMap[Candidate]\n", "")

    def test_missing_profile_cannot_be_fabricated(self):
        self.mutation("profile", "        Saved := AEONFALLPlayerProfiles[Player]", "        var Result:aeonfall_player_profile = aeonfall_player_profile{}\n        Saved := AEONFALLPlayerProfiles[Player]")

    def test_shop_refused_save_never_grants(self):
        self.mutation("shop", "if (not Committed?):\n                    return false", "if (not Committed?):\n                    set Eligible = true")

    def test_craft_refused_save_never_grants(self):
        self.mutation("recipe", "if (not Committed?):\n                    return false", "if (not Committed?):\n                    set RequirementsMet = true")

    def test_first_clear_delivery_requires_committed_reward(self):
        self.mutation("reward", "if (Committed?):", "if (not Committed?):")

    def test_weapon_ownership_required(self):
        self.mutation("loadout", "                    Profile.UnlockedEntityIds.Find[Definition.OwnerEntityId]\n", "", 1)
        # A separately unlocked skill cannot replace the weapon-specific check.

    def test_equipped_weapon_required(self):
        self.mutation("loadout", "                    Profile.EquippedWeaponIds.Find[Definition.OwnerEntityId]\n", "")

    def test_class_ability_membership_required(self):
        self.mutation("loadout", "                State.AbilityIds.Find[Definition.AbilityId]\n", "")

    def test_active_owner_identity_cannot_be_substituted(self):
        self.mutation("loadout", "            RegisteredOwner = OwnerKey\n", "")

    def test_activation_cannot_skip_entitlement(self):
        self.mutation("activation", "CanActivateForPlayer(", "UncheckedCapability(")

    def test_bootstrap_wait_checks_all_abilities(self):
        self.mutation("device", "for (AbilityDefinition : Slice001AbilityDefinitions):", "for (AbilityDefinition : array{}):")

    def test_startup_wait_is_bounded(self):
        self.mutation("device", "Attempt >= 100", "Attempt >= 2147483647")

    def test_retained_inventory_not_regranted_by_default(self):
        self.mutation("device", "RestoreEquipmentOnRespawn:logic = false", "RestoreEquipmentOnRespawn:logic = true")

    def test_physical_dispatch_claim_is_required(self):
        self.mutation("item_adapter", "Claimed := GetAEONFALLUnlockDeliveryService().ClaimDelivery(Request)", "Claimed := true")

    def test_trigger_dispatch_claim_is_required(self):
        self.mutation("trigger_adapter", "Claimed := GetAEONFALLUnlockDeliveryService().ClaimDelivery(Request)", "Claimed := true")

    def test_retries_cannot_reset_dispatch_claim(self):
        self.mutation("delivery", "PhysicalClaimed := State.PhysicalClaimed", "PhysicalClaimed := false", 2)

    def test_full_queue_cannot_leave_phantom_request(self):
        self.mutation("delivery", "        Admitted?\n", "")

    def test_request_requires_durable_unlock(self):
        self.mutation("delivery", "        Profile.UnlockedEntityIds.Find[EntityId]\n", "")

    def test_stale_forged_delivery_source_is_rejected(self):
        self.mutation("delivery", "            State.SourceId = Request.SourceId\n", "")

    def test_duplicate_loadout_owner_is_rejected(self):
        self.mutation("device", "            Owner <> Self\n", "")

    def test_profile_native_subscription_cancellation(self):
        self.mutation("profile_bootstrap", "Subscription.Cancel()", "Print(\"leaked\")")

    def test_actor_native_subscription_cancellation(self):
        self.mutation("actor_bootstrap", "Subscription.Cancel()", "Print(\"leaked\")")

    def test_post_commit_delivery_backlog_is_bounded(self):
        self.mutation("delivery", "Deferred.Length >= DeferredCapacity", "Deferred.Length >= 2147483647")

    def test_deferred_delivery_is_retried(self):
        self.mutation("delivery", "        TickDeferred()\n", "")

    def test_owned_first_clear_items_not_granted_again(self):
        self.mutation("reward", "not BeforeReward.UnlockedEntityIds.Find[EntityId]", "BeforeReward.UnlockedEntityIds.Find[EntityId]")

    def test_first_clear_all_delivery_bindings_present(self):
        coverage = json.loads((ROOT / "content/vertical_slice/slice_001_delivery_coverage.json").read_text())
        rewards = json.loads((ROOT / "content/vertical_slice/slice_001_rewards.json").read_text())
        self.assertEqual([], GUARD.check_coverage(coverage, rewards))
        coverage["delivery_bindings"] = [row for row in coverage["delivery_bindings"] if row["entity_id"] != "WPN-126"]
        self.assertTrue(GUARD.check_coverage(coverage, rewards))


if __name__ == "__main__":
    unittest.main()
