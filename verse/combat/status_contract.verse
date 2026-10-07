# Shared status-effect contracts.
# Individual weapons, monsters, armor, skills, and bosses should request status
# changes through one service instead of each implementing bespoke stacking.

aeonfall_status_stack_rule := enum:
    RefreshDuration
    AddStack
    ReplaceIfStronger
    RejectDuplicate

aeonfall_status_category := enum:
    Buff
    Debuff
    CrowdControl
    DamageOverTime
    HealingOverTime
    Reveal
    Mark
    Environmental

aeonfall_status_definition := class:
    StatusId:string = ""
    DisplayName:string = ""
    Category:aeonfall_status_category = aeonfall_status_category.Mark
    StackRule:aeonfall_status_stack_rule = aeonfall_status_stack_rule.RefreshDuration
    MaxStacks:int = 1
    BaseDurationSeconds:float = 0.0
    Dispellable:logic = true
    BossEligible:logic = false
    PresentationId:string = ""
    AudioId:string = ""

aeonfall_status_instance := class:
    StatusId:string = ""
    SourceId:string = ""
    StackCount:int = 1
    Magnitude:int = 0
    RemainingSeconds:float = 0.0
