# The Choosing is the final one-time gate after Zero Candidate qualification.

aeonfall_choosing_definition := class:
    ChoosingId:string = "CHOOSING-001"
    ObjectiveIds:[]string = array{}
    TimeLimitSeconds:float = 0.0

aeonfall_choosing_runtime_state := class:
    OwnerKey:string = ""
    ChoosingId:string = ""
    CompletedObjectiveIds:[]string = array{}
    RemainingSeconds:float = 0.0
    Active:logic = false
    Failed:logic = false
