# AEONFALL species-specific taming challenge contracts.

aeonfall_taming_step_kind := enum:
    Approach
    Feed
    Evade
    Calm
    Track
    Protect
    DenyCorpse

aeonfall_taming_definition := class:
    SpeciesId:string = ""
    DisplayName:string = ""
    RequiredClassId:string = "CLS-007"
    AbilityId:string = "ABL-003"
    Steps:[]aeonfall_taming_step_kind = array{}
    MaxChallengeSeconds:float = 0.0
    FailureEventId:string = ""
    SuccessEventId:string = ""

aeonfall_taming_challenge_state := class:
    RequestId:string = ""
    OwnerKey:string = ""
    TargetKey:string = ""
    SpeciesId:string = ""
    AbilityId:string = ""
    CurrentStepIndex:int = 0
    Active:logic = false
    Completed:logic = false
    Failed:logic = false
