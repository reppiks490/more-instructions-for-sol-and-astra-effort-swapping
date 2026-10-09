#!/usr/bin/env python3
"""Check irreversible-delivery and live-loadout source contracts, not Verse execution."""
from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "profile": "verse/persistence/profile_service.verse",
    "profile_bootstrap": "verse/persistence/profile_bootstrap_device.verse",
    "actor_bootstrap": "verse/core/actor_registry_bootstrap_device.verse",
    "shop": "verse/economy/shop_runtime.verse",
    "recipe": "verse/crafting/recipe_runtime.verse",
    "reward": "verse/progression/encounter_reward_runtime.verse",
    "delivery": "verse/economy/unlock_delivery_service.verse",
    "item_adapter": "verse/economy/unlock_item_granter_adapter_device.verse",
    "trigger_adapter": "verse/economy/unlock_delivery_adapter_device.verse",
    "loadout": "verse/progression/player_loadout_service.verse",
    "device": "verse/progression/player_loadout_device.verse",
    "activation": "verse/combat/ability_activation_service.verse",
}


def normalized(source: str) -> str:
    return re.sub(r"Get(AEONFALL[A-Za-z0-9_]+)\(\)", r"\1", source)


def check_sources(sources: dict[str, str]) -> list[str]:
    sources = {name: normalized(text) for name, text in sources.items()}
    errors: list[str] = []

    def need(name: str, fragment: str, message: str):
        if fragment not in sources[name]:
            errors.append(message)

    def ordered(name: str, *parts: str):
        positions = [sources[name].find(part) for part in parts]
        if any(position < 0 for position in positions) or positions != sorted(positions):
            errors.append(f"{name}: checked operation ordering changed")

    profile = sources["profile"]
    getter = profile.split("    GetProfile(", 1)[-1].split("    TrySaveProfile(", 1)[0]
    if "aeonfall_player_profile{}" in getter or "var Result" in getter:
        errors.append("missing profiles must fail instead of becoming fabricated defaults")
    save = profile.split("    TrySaveProfile(", 1)[-1].split("    SaveProfile(", 1)[0]
    for fragment in ("Player.IsActive[]", "FitsInPlayerMap[Candidate]", "set AEONFALLPlayerProfiles[Player] = Candidate", "return true", "false"):
        if fragment not in save:
            errors.append(f"checked save missing {fragment}")
    need("profile", ")<transacts>:logic=\n        if:\n            UnlockEntityId", "material/unlock commit must acknowledge save refusal")
    need("profile", "return TrySaveProfile(Player, Candidate)", "material/unlock commit must return checked save")
    for name in ("shop", "recipe"):
        ordered(name, "Committed := ProfileService.CommitMaterialAndUnlock(", "if (not Committed?):", "AEONFALLUnlockDeliveryService.QueueAfterCommit(")
        # The generic earlier requirement return is expected, so enforce the
        # checked-save branch locally rather than trusting the first return.
        commit = sources[name].split("Committed :=", 1)[-1]
        if "if (not Committed?):\n                    return false" not in commit:
            errors.append(f"{name}: a refused save can continue into physical delivery")
    ordered("reward", "Committed := ProfileService.CommitEncounterFirstClearReward(", "if (Committed?):", "for (EntityId : Definition.UnlockEntityIds):", "AEONFALLUnlockDeliveryService.QueueAfterCommit(")
    for fragment in ("DeferredCapacity:int = 256", "Deferred.Length >= DeferredCapacity", "PendingCapacity:int = 1024", "Pending.Length < PendingCapacity", "\n        TickDeferred()\n", "set Deferred = KeptDeferred", "State.OwnerKey = OwnerKey, State.EntityId = EntityId"):
        need("delivery", fragment, f"bounded post-commit delivery backlog missing {fragment}")
    need("reward", "not BeforeReward.UnlockedEntityIds.Find[EntityId]", "already owned boss reward equipment must not be duplicated")
    need("delivery", "CommitRequest(Agent:agent, EntityId:string, SourceId:string)<decides><transacts>", "delivery state and admission must be atomic")
    for fragment in ("Profile.UnlockedEntityIds.Find[EntityId]", "TryRequestUnlockDelivery(", "Admitted?", "not State.PhysicalClaimed?", "State.SourceId = Request.SourceId", "Character.IsActive[]", "PhysicalClaimed := true"):
        need("delivery", fragment, f"delivery guard missing {fragment}")
    request = sources["delivery"].split("    CommitRequest(", 1)[-1].split("    QueueAfterCommit(", 1)[0]
    if "Profile.UnlockedEntityIds.Find[EntityId]" not in request:
        errors.append("delivery request must require durable unlock ownership")
    if sources["delivery"].count("PhysicalClaimed := State.PhysicalClaimed") < 2:
        errors.append("delivery retry/tick must preserve the physical dispatch claim")
    for name, operation in (("item_adapter", "ItemGranter.GrantItem(OwnerAgent)"), ("trigger_adapter", "TriggerOutput.Trigger(OwnerAgent)")):
        ordered(name, "Claimed := AEONFALLUnlockDeliveryService.ClaimDelivery(Request)", "if (not Claimed?):", operation)
        need(name, "if (not Claimed?):\n", f"{name}: duplicate dispatch must be rejected")
    for fragment in ("RegisteredOwner = OwnerKey", "State.AbilityIds.Find[Definition.AbilityId]", "Profile.UnlockedEntityIds.Find[Definition.OwnerEntityId]", "Profile.EquippedWeaponIds.Find[Definition.OwnerEntityId]", 'Definition.OwnerEntityId.Slice[0, 4] = "SKL-"', "CommitWeaponSelection(Player:player, WeaponId:string)<decides><transacts>", "Saved?", "RequiredUnlockIds", 'StarterWeaponId = "WPN-001"'):
        need("loadout", fragment, f"loadout entitlement missing {fragment}")
    entitlement = sources["loadout"].split("    CanActivateForPlayer(", 1)[-1].split("    TrySelectClass(", 1)[0]
    weapon_entitlement = entitlement.split("if (WeaponOwned?):", 1)[-1].split("# Skills outside", 1)[0]
    for fragment in ("Profile.UnlockedEntityIds.Find[Definition.OwnerEntityId]", "Profile.EquippedWeaponIds.Find[Definition.OwnerEntityId]"):
        if fragment not in weapon_entitlement:
            errors.append(f"weapon activation gate missing {fragment}")
    ordered("activation", "CanActivateForPlayer(", "if (not Entitled?):", "Initialized := AEONFALLAbilityRuntime.Initialize(")
    for fragment in ("PlayerSpawners:[]player_spawner_device", "SpawnedEvent.Subscribe(OnSpawned)", "RegistriesReady(Player:player)", "Slice001ClassDefinitions", "Slice001AbilityDefinitions", "Attempt >= 100", "Seen = Character", "EnsureStarter(Player, \"WPN-001\")", "TrySelectClass(Player, ClassId)", "RequestEquipmentRestore(", "RestoreEquipmentOnFirstSpawn:logic = false", "RestoreEquipmentOnRespawn:logic = false", "Owner <> Self", "set OwnsLease = true"):
        need("device", fragment, f"live-loadout lifecycle missing {fragment}")
    for name in ("device", "profile_bootstrap", "actor_bootstrap"):
        need(name, "OnEnd<override>()", f"{name}: native subscriptions have no lifecycle cleanup")
        need(name, "Subscription.Cancel()", f"{name}: native subscriptions are not canceled")
    return errors


def check_coverage(coverage: dict, rewards: dict) -> list[str]:
    required = {entity for reward in rewards.get("rewards", []) for entity in reward.get("unlock_entity_ids", [])}
    provided = {row.get("entity_id") for row in coverage.get("delivery_bindings", [])}
    return [f"first-clear physical unlocks lack delivery bindings: {sorted(required - provided)}"] if required - provided else []


def main() -> int:
    sources = {name: (ROOT / path).read_text(encoding="utf-8") for name, path in SOURCES.items()}
    errors = check_sources(sources)
    errors += check_coverage(json.loads((ROOT / "content/vertical_slice/slice_001_delivery_coverage.json").read_text()), json.loads((ROOT / "content/vertical_slice/slice_001_rewards.json").read_text()))
    if errors:
        print("Player loadout source guards FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Player loadout source guards passed; native compile and session tests not executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
