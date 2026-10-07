# AEONFALL world-event contracts.
# World events are state machines with explicit activation, escalation, cleanup,
# and streaming boundaries rather than unbounded background loops.

aeonfall_world_event_stage_contract := class:
    StageId:string = ""
    DisplayName:string = ""
    RegionIds:[]string = array{}
    ObjectiveIds:[]string = array{}
    SpawnGroupIds:[]string = array{}
    HazardIds:[]string = array{}
    PresentationIds:[]string = array{}
    EscalatesOnFailure:logic = false
    MaxConcurrentAi:int = 0
    MaxConcurrentVfx:int = 0

aeonfall_world_event_contract := class:
    EventId:string = ""
    StageContracts:[]aeonfall_world_event_stage_contract = array{}
    EntryRequirementIds:[]string = array{}
    CompletionRewardIds:[]string = array{}
    PersistsCompletion:logic = true
    CanEscalateAcrossRegions:logic = false

aeonfall_world_event_runtime_state := class:
    EventId:string = ""
    CurrentStageIndex:int = 0
    CompletedObjectiveIds:[]string = array{}
    ActiveRegionIds:[]string = array{}
    Active:logic = false
    Failed:logic = false
    Completed:logic = false
