# Shared ability/resource contracts.
# These definitions separate authored mechanics from devices, input bindings,
# animation/VFX assets, and player inventory implementation.

aeonfall_resource_policy := enum:
    Cooldown
    Charges
    Meter
    EncounterOnly
    TransformationOnly

aeonfall_target_policy := enum:
    Self
    Ally
    Enemy
    Position
    Direction
    Area
    AuthoredObjective

aeonfall_ability_definition := class:
    AbilityId:string = ""
    DisplayName:string = ""
    OwnerEntityId:string = ""
    ResourcePolicy:aeonfall_resource_policy = aeonfall_resource_policy.Cooldown
    TargetPolicy:aeonfall_target_policy = aeonfall_target_policy.Enemy

    # Cooldown policy.
    CooldownSeconds:float = 0.0

    # Charge policy.
    MaxCharges:int = 0
    RechargeSeconds:float = 0.0

    # Meter policy.
    MaxMeter:int = 0
    ActivationCost:int = 0

    # Context gates.
    RequiresEncounterContext:logic = false
    RequiresTransformationContext:logic = false
    AllowWhileActive:logic = false

    StatusIds:[]string = array{}
    SpawnIds:[]string = array{}
    EventIds:[]string = array{}
    PresentationId:string = ""
    AudioId:string = ""
    AdapterId:string = ""
    BossSafe:logic = true

aeonfall_ability_runtime_state := class:
    AbilityId:string = ""
    CurrentCharges:int = 0
    CurrentMeter:int = 0
    CooldownRemainingSeconds:float = 0.0
    ChargeRechargeRemainingSeconds:float = 0.0
    Active:logic = false
    Pending:logic = false
    PendingRequestId:string = ""
    Locked:logic = false

aeonfall_ability_context_flags := class:
    EncounterActive:logic = false
    TransformationActive:logic = false
