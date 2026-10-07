# AEONFALL boss encounter data contracts.
# These are intentionally asset-agnostic so UEFN devices, NPC behaviors,
# Scene Graph entities, and cinematic/VFX bindings can consume the same state.

aeonfall_boss_phase_contract := class:
    PhaseId:string = ""
    DisplayName:string = ""
    ObjectiveIds:[]string = array{}
    RequiredWeakPointIds:[]string = array{}
    ActiveHazardIds:[]string = array{}
    ActiveSpawnGroupIds:[]string = array{}
    AllowsDirectBossDamage:logic = false
    MaxActiveAdds:int = 0
    VfxBudgetBand:int = 0
    ReplicationBudgetBand:int = 0

aeonfall_boss_encounter_contract := class:
    BossId:string = ""
    RegionId:string = ""
    PhaseContracts:[]aeonfall_boss_phase_contract = array{}
    RequiredPlayerObjectiveIds:[]string = array{}
    RewardUnlockIds:[]string = array{}
    IsDistributedEncounter:logic = false
    IsWorldScalePresentation:logic = false
    MaxConcurrentAdds:int = 0
    MaxConcurrentHazards:int = 0

# Runtime state remains separate from the authored contract so phase transitions
# do not mutate design-time data.
aeonfall_boss_runtime_state := class:
    BossId:string = ""
    CurrentPhaseIndex:int = 0
    CompletedObjectiveIds:[]string = array{}
    BrokenWeakPointIds:[]string = array{}
    EncounterActive:logic = false
    EncounterFailed:logic = false
    EncounterCompleted:logic = false
