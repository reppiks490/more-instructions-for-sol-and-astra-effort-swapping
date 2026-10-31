#!/usr/bin/env python3
"""Source-level integration guards; these do not compile or execute Verse."""
from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "class": "verse/progression/class_runtime.verse",
    "position": "verse/combat/position_targeting_runtime.verse",
    "selector": "verse/combat/actor_target_selector_device.verse",
    "harvest": "verse/npcs/corpse_harvest_device.verse",
    "heat": "verse/combat/weapon_meter_device.verse",
    "ecology": "verse/npcs/horde_ecology_adapter_device.verse",
    "prop": "verse/core/prop_spawn_adapter_device.verse",
}
POLICY_PATH = "content/vertical_slice/slice_001_player_loop.json"


def normalized(source: str) -> str:
    return re.sub(r"Get(AEONFALL[A-Za-z0-9_]+)\(\)", r"\1", source)


def check_sources(sources: dict[str, str], policy: dict) -> list[str]:
    errors = []
    def need(name: str, fragment: str, description: str):
        suffix = r"(?![0-9.])" if fragment[-1:].isdigit() else ""
        if not re.search(re.escape(fragment) + suffix, normalized(sources[name])):
            errors.append(description)
    def order(name: str, *fragments: str):
        text = normalized(sources[name])
        positions = [text.find(part) for part in fragments]
        if any(pos < 0 for pos in positions) or positions != sorted(positions):
            errors.append(f"{name}: missing or reordered commit guards")
    need("class", "CommitClassActivation(OwnerKey:string, ClassId:string)<decides><transacts>",
         "class activation must have a single transactional failure scope")
    need("class", "Current.ClassId = ClassId", "same-class selection must be idempotent")
    need("class", "var ResourceHistory:[string][string]int", "per-class resource history is missing")
    need("class", "set History[OldState.ClassId] = OldState.CurrentResource",
         "switching must retain the old class resource")
    need("class", "SavedResource := History[ClassId]", "class switching must restore saved resource")
    need("class", "ApplyBatch[", "class passives must apply atomically")
    need("class", "ProfileService.TrySaveProfile(Player, Candidate)", "class save must be checked")
    need("class", "Profile.UnlockedEntityIds.Find[UnlockId]", "class unlock prerequisites must be authoritative")
    need("class", "set ResourceHistory = KeptHistory", "class history must be cleared on unregister")
    need("class", "Admitted?", "class activation must check event admission")
    order("class", "Current.ClassId = ClassId", "if (CommitClassActivation[OwnerKey, ClassId])")
    for name in ("position", "selector", "harvest", "heat", "ecology", "prop"):
        if "GetFortCharacter()" in sources[name]:
            errors.append(f"{name}: native failable GetFortCharacter requires []")
    need("position", "/UnrealEngine.com/Temporary/SpatialMath",
         "view APIs require compatible Temporary SpatialMath vectors")
    for fragment in ("TargetCanonicalIds.Find[CanonicalId]", "IsUnboundNPC(Key)?", "TargetCharacter.IsActive[]",
                     "Range <= BestDistance", "DotProduct(Delta, Forward)",
                     "AEONFALLTargetingRuntime.SetRuntimeTarget(", "AEONFALLTargetingRuntime.Clear("):
        need("selector", fragment, f"selector guard missing: {fragment}")
    for fragment in ("CommitHarvest(Agent:agent)<decides><transacts>",
                     "Player.IsActive[]", "Character.IsActive[]",
                     "Ecology.CorpsePositions[CorpseId]",
                     "Distance(Position, CorpsePosition) <= HarvestRangeCm",
                     "Corpse.RemainingSeconds > 0.0", "aeonfall_corpse_use.Harvest",
                     'ClassState.ClassId = "CLS-006"',
                     'Old.UnlockedEntityIds.Find["WPN-003"]',
                     'Old.EquippedWeaponIds.Find["WPN-003"]', "Admitted?"):
        need("harvest", fragment, f"harvest guard missing: {fragment}")
    order("harvest", "Used := AEONFALLHordeRuntime.UseCorpse(", "Used?",
          "Saved := ProfileService.TrySaveProfile(Player, Candidate)", "Saved?",
          'EventType := "progression.corpse_harvested"', "Admitted?")
    need("ecology", "Registered := AEONFALLHordeRuntime.RegisterRegion(RegionId)",
         "region registration must run outside negation's rollback context")
    for fragment in ("AcquireAdapterLease()", "OtherAdapter.Spawner = Spawner",
                     "Owners[RegionId] = Self", "ReleasedLease := ReleaseAdapterLease()"):
        need("ecology", fragment, f"horde ownership guard missing: {fragment}")
    order("ecology", "Leased := AcquireAdapterLease()", "if (not Leased?)",
          "Registered := AEONFALLHordeRuntime.RegisterRegion(RegionId)", "Spawner.Enable()")
    if "not AEONFALLHordeRuntime.RegisterRegion(" in normalized(sources["ecology"]):
        errors.append("negated region registration rolls back successful registration")
    for fragment in ("Enabled:logic = false", "ItemGate.IsHoldingItem[Agent]",
                     "Instigator.GetInstigatorAgent[]", "Result.Amount > 0.0",
                     'Profile.UnlockedEntityIds.Find["WPN-007"]',
                     'Profile.EquippedWeaponIds.Find["WPN-007"]', "Now - Last >= 0.25"):
        need("heat", fragment, f"heat guard missing: {fragment}")
    for fragment in ("Contexts.Length < 1024", "OwnerContexts < 16", "LifetimeSeconds <= 30.0"):
        need("position", fragment, f"position context bound missing: {fragment}")
    for fragment in ("Enabled:logic = false", "AEONFALLAbilityRuntime.ClaimEffectRequest(Request)",
                     "Context.OwnerKey = Request.OwnerKey", "Context.AbilityId = Request.AbilityId",
                     "Distance(Origin, Position) >= MinimumDistanceCm",
                     "AEONFALLSpawnRuntime.Reserve(", "Spawned := SpawnProp(",
                     "Spawned(1) = spawn_prop_result.Ok", "Prop.Dispose()",
                     "AEONFALLSpawnRuntime.Release(", "AEONFALLStatusRuntime.ApplyBatch[",
                     "set PhysicalProps[Handle] = Prop", "Record.RemainingSeconds > 0.0",
                     "MakeRotationFromYawPitchRollDegrees(Yaw, 0.0, 0.0)"):
        need("prop", fragment, f"physical spawn guard missing: {fragment}")
    order("prop", "Claimed := AEONFALLAbilityRuntime.ClaimEffectRequest(Request)",
          "Prepared := PrepareSpawn[Request]", "Spawned := SpawnProp(",
          "CommitSpawnTracking[Request, Prepared.HandleId, Prop]", "Succeeded := true")
    for name in ("selector", "harvest", "heat", "prop"):
        need(name, "OnEnd<override>", f"{name}: subscription cleanup missing")
        need(name, ".Cancel()", f"{name}: retained subscriptions must be cancelled")
    for fragment in ('set Materials["MAT-008"] = OldBone + 12',
                     'set Materials["MAT-003"] = OldIron + 4',
                     'set Reputation["FAC-002"] = OldReputation + 5',
                     "NewXP:int = Old.XP + 20",
                     "AEONFALLClassRuntime.AddResource(OwnerKey, 20)",
                     "AEONFALLAbilityRuntime.AddMeter(OwnerKey, Definition, 25)"):
        need("harvest", fragment, f"harvest authored reward differs: {fragment}")
    need("heat", "AEONFALLAbilityRuntime.AddMeter(OwnerKey, Definition, 10)",
         "heat damage award differs from authored policy")
    if policy.get("default_class_id") != "CLS-006" or policy.get("starter_weapon_id") != "WPN-001":
        errors.append("starter loadout policy differs from production defaults")
    harvest = policy.get("corpse_harvest", {})
    if harvest.get("material_rewards") != {"MAT-008": 12, "MAT-003": 4}:
        errors.append("ordinary corpse material reward differs from authored runtime")
    if harvest.get("faction_reputation") != {"FAC-002": 5} or harvest.get("xp") != 20:
        errors.append("harvest progression reward differs from authored runtime")
    if harvest.get("class_resource") != {"class_id": "CLS-006", "resource_id": "corpse_charge", "amount": 20}:
        errors.append("harvest must replenish corpse charge only")
    if harvest.get("persistent_save_failure") != "rollback reward and corpse consumption":
        errors.append("harvest persistence policy must preserve unconsumed corpse on refusal")
    if policy.get("target_selection", {}).get("line_of_sight_check") is not False:
        errors.append("aim selector must not promise unavailable line-of-sight validation")
    return errors


def main() -> int:
    sources = {name: (ROOT / path).read_text(encoding="utf-8") for name, path in SOURCES.items()}
    policy = json.loads((ROOT / POLICY_PATH).read_text(encoding="utf-8"))
    errors = check_sources(sources, policy)
    for error in errors:
        print(f"ERROR: {error}")
    if not errors:
        print("First playable loop source guards passed; UEFN compile/session not executed.")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
