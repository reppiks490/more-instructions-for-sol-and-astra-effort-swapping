# AEONFALL hireable/tameable companion data contracts.
# Actual NPC movement/combat remains inside project-bound NPC Character
# Definitions and npc_behavior implementations.

aeonfall_companion_kind := enum:
    Hireable
    Tameable
    Summoned

aeonfall_companion_order := enum:
    Follow
    Guard
    FocusTarget
    HoldPosition
    Flank
    Retreat

aeonfall_companion_contract := class:
    EntityId:string = ""
    FactionId:string = ""
    Kind:aeonfall_companion_kind = aeonfall_companion_kind.Hireable
    RequiredReputation:int = 0
    RequiredUnlockIds:[]string = array{}
    AbilityIds:[]string = array{}
    AllowedOrderIds:[]string = array{}
    MaxSimultaneousPerPlayer:int = 1
    CanEnterBossArenas:logic = true
    CanBeRevived:logic = false

aeonfall_companion_runtime_state := class:
    EntityId:string = ""
    CurrentOrder:aeonfall_companion_order = aeonfall_companion_order.Follow
    IsHired:logic = false
    IsTamed:logic = false
    IsActive:logic = false
    IsDowned:logic = false
