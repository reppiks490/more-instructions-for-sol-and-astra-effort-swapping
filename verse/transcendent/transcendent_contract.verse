# Transcendent Zero transformation and Authority contracts.
# Persistent eligibility lives in aeonfall_player_profile.
# Active/cooldown state is strictly session-only.

aeonfall_transcendent_phase := enum:
    Dormant
    Active
    Exhausted

aeonfall_transcendent_authority_definition := class:
    AuthorityId:string = ""
    DisplayName:string = ""
    Fantasy:string = ""
    ActiveSeconds:float = 30.0
    ExhaustionSeconds:float = 300.0
    MinHistoryActivations:int = 0
    AbilityIds:[]string = array{}
    PresentationId:string = ""
    AudioId:string = ""

aeonfall_transcendent_runtime_state := class:
    OwnerKey:string = ""
    AuthorityId:string = ""
    Phase:aeonfall_transcendent_phase = aeonfall_transcendent_phase.Dormant
    ActiveRemainingSeconds:float = 0.0
    ExhaustionRemainingSeconds:float = 0.0
    SessionActivationCount:int = 0
