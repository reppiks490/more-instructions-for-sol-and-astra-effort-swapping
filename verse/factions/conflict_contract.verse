# Data-driven faction conflict definitions.

aeonfall_faction_conflict_definition := class:
    ConflictId:string = ""
    RegionId:string = ""
    FactionAId:string = ""
    FactionBId:string = ""
    VictoryScore:int = 100
    MinHostilityTier:int = 0
    ObjectiveIds:[]string = array{}
    HazardIds:[]string = array{}
