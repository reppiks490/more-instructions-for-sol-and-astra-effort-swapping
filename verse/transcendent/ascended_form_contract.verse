# God and Absolute temporary transformation contracts.
# Permanent eligibility is represented by AscensionRank.
# Active/cooldown state remains session-only.

aeonfall_ascended_form_phase := enum:
    Dormant
    Active
    Exhausted

aeonfall_ascended_form_definition := class:
    FormId:string = ""
    DisplayName:string = ""
    TransformationId:string = ""
    RequiredAscensionRank:int = 0
    ActiveSeconds:float = 30.0
    ExhaustionSeconds:float = 120.0
    AbilityIds:[]string = array{}
    PresentationId:string = ""
    AudioId:string = ""

aeonfall_ascended_form_runtime_state := class:
    OwnerKey:string = ""
    FormId:string = ""
    TransformationId:string = ""
    Phase:aeonfall_ascended_form_phase = aeonfall_ascended_form_phase.Dormant
    ActiveRemainingSeconds:float = 0.0
    ExhaustionRemainingSeconds:float = 0.0
    SessionActivationCount:int = 0
