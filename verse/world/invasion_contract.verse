# Dynamic regional invasion contracts.

aeonfall_invasion_definition := class:
    InvasionId:string = ""
    RegionId:string = ""
    AggressorId:string = ""
    MinHostilityTier:int = 0
    WaveSpawnGroupIds:[][]string = array{}
    ObjectiveIds:[]string = array{}
    HazardIds:[]string = array{}
    DurationSeconds:float = 0.0
    MaxConcurrentAi:int = 0
    TimeoutIsFailure:logic = true

aeonfall_invasion_runtime_state := class:
    InvasionId:string = ""
    RegionId:string = ""
    CurrentWaveIndex:int = 0
    CompletedObjectiveIds:[]string = array{}
    RemainingSeconds:float = 0.0
    Active:logic = false
    Completed:logic = false
    Failed:logic = false
