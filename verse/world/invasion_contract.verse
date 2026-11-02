# Dynamic regional invasion contracts.

aeonfall_invasion_definition := class:
    InvasionId:string = ""
    RegionId:string = ""
    AggressorId:string = ""
    MinHostilityTier:int = 0
    # Minimum canonical corruption for ecology-specific encounter admission.
    MinCorruption:int = 0
    # Canonical territorial strength required for faction-led admission.
    MinAggressorInfluence:int = 0
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
