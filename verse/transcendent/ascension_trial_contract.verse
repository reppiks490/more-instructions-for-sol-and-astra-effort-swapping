# Canonical Ascension Trial definitions and session state.

aeonfall_ascension_trial_definition := class:
    TrialId:string = ""
    Index:int = 0
    DisplayName:string = ""
    RequiredPreviousTrialId:string = ""
    ObjectiveIds:[]string = array{}
    TimeLimitSeconds:float = 0.0
    RequiresAxiomHeart:logic = false
    UnlocksAxiomForge:logic = false
    AllowsCompanions:logic = true
    AllowsGodAbilities:logic = true
    AllowsAbsoluteAbilities:logic = true

aeonfall_ascension_trial_runtime_state := class:
    OwnerKey:string = ""
    TrialId:string = ""
    CompletedObjectiveIds:[]string = array{}
    RemainingSeconds:float = 0.0
    Active:logic = false
    Failed:logic = false
