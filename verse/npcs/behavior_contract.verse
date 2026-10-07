# Reusable AEONFALL NPC behavior contracts.
# These profiles keep the first vertical slice from becoming one script per
# creature. Project-bound npc_behavior implementations consume these profiles.

aeonfall_ai_state := enum:
    Dormant
    Idle
    Patrol
    Investigate
    Engage
    Reposition
    UseAbility
    Recover
    Flee
    Downed
    ReturnHome
    Disabled

aeonfall_behavior_archetype := enum:
    AmbushPredator
    CorpseSwarm
    BroodArtillery
    NecromancerConstructor
    NecromancerSupport
    NecromancerAdaptive
    TerritoryController
    SubterraneanAmbusher
    InfernalPursuit
    HazardFeedingPack
    HireableMedic
    HireableScout
    HireableTactician
    HireableBreach
    HireableMonsterHunter
    HireableAntiUndead
    HireableBeastCommander
    TameableScoutMount
    TameableCorpseDenial
    TameableHarvest
    TameableWarning
    TameableResourceDigger
    TameableSanctuaryMount
    BossBuilder
    BossAntiSupport
    BossNecromancerSovereign

aeonfall_behavior_profile := class:
    ProfileId:string = ""
    Archetype:aeonfall_behavior_archetype = aeonfall_behavior_archetype.AmbushPredator
    AggroRangeMeters:float = 0.0
    LeashRangeMeters:float = 0.0
    PreferredRangeMeters:float = 0.0
    RepositionIntervalSeconds:float = 0.0
    AbilityIds:[]string = array{}
    StatusImmunityIds:[]string = array{}
    CanUseCover:logic = false
    CanFlank:logic = false
    CanFlee:logic = false
    CanBeHired:logic = false
    CanBeTamed:logic = false
    CanBeDowned:logic = false
    RequiresCorpseContext:logic = false
    RequiresHazardContext:logic = false
    RequiresBossController:logic = false

aeonfall_ai_runtime_state := class:
    CanonicalId:string = ""
    ProfileId:string = ""
    State:aeonfall_ai_state = aeonfall_ai_state.Dormant
    CurrentTargetId:string = ""
    CurrentObjectiveId:string = ""
    CurrentAbilityId:string = ""
    StateTimeSeconds:float = 0.0
    Active:logic = false
