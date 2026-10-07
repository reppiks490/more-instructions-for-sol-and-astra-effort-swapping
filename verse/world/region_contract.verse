# AEONFALL streamed-region contracts.

aeonfall_region_streaming_band := enum:
    Low
    Medium
    High
    Cinematic

aeonfall_region_definition := class:
    RegionId:string = ""
    DisplayName:string = ""
    NeighborRegionIds:[]string = array{}
    StreamingBand:aeonfall_region_streaming_band = aeonfall_region_streaming_band.Medium
    VerticalSlice:logic = false

aeonfall_region_runtime_state := class:
    RegionId:string = ""
    ControllingFactionId:string = ""
    FactionInfluence:[string]int = map{}
    Corruption:int = 0
    HostilityTier:int = 0
    ActiveEventIds:[]string = array{}
    MutationIds:[]string = array{}
