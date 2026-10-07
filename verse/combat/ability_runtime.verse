# Publish-safe AEONFALL ability resource runtime.
#
# This file deliberately does not import Epic's Experimental Ability API.
# Activation is two-phase:
# 1. RequestActivation reserves the ability without spending resources.
# 2. A project-bound adapter executes/preflights the effect and reports a result.
# 3. ResolveActivation commits cooldown/charges/meter only on success.

aeonfall_ability_runtime := class():

    var States:[string]aeonfall_ability_runtime_state = map{}
    var OwnerByStateKey:[string]string = map{}

    MakeStateKey(OwnerKey:string, AbilityId:string):string=
        OwnerKey + "::" + AbilityId

    Initialize(
        OwnerKey:string,
        Definition:aeonfall_ability_definition
    )<transacts>:logic=
        if:
            OwnerKey <> ""
            Definition.AbilityId <> ""
        then:
            Key := MakeStateKey(OwnerKey, Definition.AbilityId)

            if:
                Existing := States[Key]
            then:
                if:
                    set OwnerByStateKey[Key] = OwnerKey
                then:
                    return true
                return false
            else:
                InitialCharges:int =
                    if (Definition.ResourcePolicy = aeonfall_resource_policy.Charges):
                        Definition.MaxCharges
                    else:
                        0

                Initial := aeonfall_ability_runtime_state:
                    AbilityId := Definition.AbilityId
                    CurrentCharges := InitialCharges
                    CurrentMeter := 0
                    CooldownRemainingSeconds := 0.0
                    ChargeRechargeRemainingSeconds := 0.0
                    Active := false
                    ActiveRequestId := ""
                    Pending := false
                    PendingRequestId := ""
                    Locked := false

                if:
                    set States[Key] = Initial
                    set OwnerByStateKey[Key] = OwnerKey
                then:
                    AEONFALLRuntimeBus.Emit(
                        aeonfall_runtime_event{
                            EventType := "ability.initialized",
                            SourceId := OwnerKey,
                            TargetId := Definition.AbilityId
                        }
                    )
                    return true

        false

    GetState(
        OwnerKey:string,
        AbilityId:string
    )<decides><transacts>:aeonfall_ability_runtime_state=
        Key := MakeStateKey(OwnerKey, AbilityId)
        States[Key]

    CanActivate(
        OwnerKey:string,
        Definition:aeonfall_ability_definition,
        Context:aeonfall_ability_context_flags
    )<transacts>:logic=
        if:
            State := GetState[OwnerKey, Definition.AbilityId]
        then:
            if (State.Locked?):
                return false

            if (State.Pending?):
                return false

            if:
                State.Active?
                not Definition.AllowWhileActive?
            then:
                return false

            if:
                Definition.RequiresEncounterContext?
                not Context.EncounterActive?
            then:
                return false

            if:
                Definition.RequiresTransformationContext?
                not Context.TransformationActive?
            then:
                return false

            if:
                Definition.RequiredTransformationId <> ""
                Context.TransformationId <> Definition.RequiredTransformationId
            then:
                return false

            if (Definition.ResourcePolicy = aeonfall_resource_policy.Cooldown):
                return State.CooldownRemainingSeconds <= 0.0

            if (Definition.ResourcePolicy = aeonfall_resource_policy.Charges):
                return State.CurrentCharges > 0

            if (Definition.ResourcePolicy = aeonfall_resource_policy.Meter):
                return State.CurrentMeter >= Definition.ActivationCost

            if (Definition.ResourcePolicy = aeonfall_resource_policy.EncounterOnly):
                return Context.EncounterActive?

            if (Definition.ResourcePolicy = aeonfall_resource_policy.TransformationOnly):
                return Context.TransformationActive?

            if (Definition.ResourcePolicy = aeonfall_resource_policy.ExternalClassResource):
                return true

        false

    RequestActivation(
        RequestId:string,
        OwnerKey:string,
        Definition:aeonfall_ability_definition,
        Context:aeonfall_ability_context_flags,
        TargetKey:string,
        RuntimeContextId:string,
        Magnitude:int
    )<transacts>:logic=
        if:
            RequestId <> ""
            Definition.AdapterId <> ""
            CanActivate(OwnerKey, Definition, Context)?
            Old := GetState[OwnerKey, Definition.AbilityId]
        then:
            Reserved := aeonfall_ability_runtime_state:
                AbilityId := Old.AbilityId
                CurrentCharges := Old.CurrentCharges
                CurrentMeter := Old.CurrentMeter
                CooldownRemainingSeconds := Old.CooldownRemainingSeconds
                ChargeRechargeRemainingSeconds := Old.ChargeRechargeRemainingSeconds
                Active := Old.Active
                ActiveRequestId := Old.ActiveRequestId
                Pending := true
                PendingRequestId := RequestId
                Locked := Old.Locked

            Key := MakeStateKey(OwnerKey, Definition.AbilityId)
            if:
                set States[Key] = Reserved
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "ability.effect_requested",
                        SourceId := OwnerKey,
                        TargetId := Definition.AbilityId,
                        ContextId := RequestId
                    }
                )

                AEONFALLRuntimeBus.RequestAbilityEffect(
                    aeonfall_ability_effect_request{
                        RequestId := RequestId,
                        OwnerKey := OwnerKey,
                        AbilityId := Definition.AbilityId,
                        AdapterId := Definition.AdapterId,
                        TargetKey := TargetKey,
                        ContextId := RuntimeContextId,
                        Magnitude := Magnitude
                    }
                )
                return true

        false

    ResolveActivation(
        Definition:aeonfall_ability_definition,
        Result:aeonfall_adapter_result
    )<transacts>:logic=
        if:
            Result.RequestId <> ""
            Result.AbilityId = Definition.AbilityId
            Result.AdapterId = Definition.AdapterId
            Old := GetState[Result.OwnerKey, Result.AbilityId]
            Old.Pending?
            Old.PendingRequestId = Result.RequestId
        then:
            if (not Result.Succeeded?):
                Cancelled := aeonfall_ability_runtime_state:
                    AbilityId := Old.AbilityId
                    CurrentCharges := Old.CurrentCharges
                    CurrentMeter := Old.CurrentMeter
                    CooldownRemainingSeconds := Old.CooldownRemainingSeconds
                    ChargeRechargeRemainingSeconds := Old.ChargeRechargeRemainingSeconds
                    Active := Old.Active
                    ActiveRequestId := Old.ActiveRequestId
                    Pending := false
                    PendingRequestId := ""
                    Locked := Old.Locked

                Key := MakeStateKey(Result.OwnerKey, Result.AbilityId)
                if:
                    set States[Key] = Cancelled
                then:
                    AEONFALLRuntimeBus.Emit(
                        aeonfall_runtime_event{
                            EventType := "ability.effect_rejected",
                            SourceId := Result.OwnerKey,
                            TargetId := Result.AbilityId,
                            ContextId := Result.ResultCode
                        }
                    )
                    return true

            var Charges:int = Old.CurrentCharges
            var Meter:int = Old.CurrentMeter
            var Cooldown:float = Old.CooldownRemainingSeconds
            var Recharge:float = Old.ChargeRechargeRemainingSeconds

            if (Definition.ResourcePolicy = aeonfall_resource_policy.Cooldown):
                set Cooldown = Definition.CooldownSeconds

            if (Definition.ResourcePolicy = aeonfall_resource_policy.Charges):
                set Charges = Old.CurrentCharges - 1
                if:
                    Charges < Definition.MaxCharges
                    Recharge <= 0.0
                then:
                    set Recharge = Definition.RechargeSeconds

            if (Definition.ResourcePolicy = aeonfall_resource_policy.Meter):
                set Meter = Old.CurrentMeter - Definition.ActivationCost

            Committed := aeonfall_ability_runtime_state:
                AbilityId := Old.AbilityId
                CurrentCharges := Charges
                CurrentMeter := Meter
                CooldownRemainingSeconds := Cooldown
                ChargeRechargeRemainingSeconds := Recharge
                Active := true
                ActiveRequestId := Result.RequestId
                Pending := false
                PendingRequestId := ""
                Locked := Old.Locked

            Key := MakeStateKey(Result.OwnerKey, Result.AbilityId)
            if:
                set States[Key] = Committed
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "ability.activation_committed",
                        SourceId := Result.OwnerKey,
                        TargetId := Result.AbilityId,
                        ContextId := Result.RequestId,
                        Amount := Meter
                    }
                )
                return true

        false

    CancelPending(
        OwnerKey:string,
        AbilityId:string,
        RequestId:string
    )<transacts>:logic=
        if:
            Old := GetState[OwnerKey, AbilityId]
            Old.Pending?
            Old.PendingRequestId = RequestId
        then:
            Updated := aeonfall_ability_runtime_state:
                AbilityId := Old.AbilityId
                CurrentCharges := Old.CurrentCharges
                CurrentMeter := Old.CurrentMeter
                CooldownRemainingSeconds := Old.CooldownRemainingSeconds
                ChargeRechargeRemainingSeconds := Old.ChargeRechargeRemainingSeconds
                Active := Old.Active
                ActiveRequestId := Old.ActiveRequestId
                Pending := false
                PendingRequestId := ""
                Locked := Old.Locked

            Key := MakeStateKey(OwnerKey, AbilityId)
            if:
                set States[Key] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "ability.pending_cancelled",
                        SourceId := OwnerKey,
                        TargetId := AbilityId,
                        ContextId := RequestId
                    }
                )
                return true

        false

    EndActivation(OwnerKey:string, AbilityId:string)<transacts>:logic=
        if:
            Old := GetState[OwnerKey, AbilityId]
        then:
            Updated := aeonfall_ability_runtime_state:
                AbilityId := Old.AbilityId
                CurrentCharges := Old.CurrentCharges
                CurrentMeter := Old.CurrentMeter
                CooldownRemainingSeconds := Old.CooldownRemainingSeconds
                ChargeRechargeRemainingSeconds := Old.ChargeRechargeRemainingSeconds
                Active := false
                ActiveRequestId := ""
                Pending := Old.Pending
                PendingRequestId := Old.PendingRequestId
                Locked := Old.Locked

            Key := MakeStateKey(OwnerKey, AbilityId)
            if:
                set States[Key] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "ability.ended",
                        SourceId := OwnerKey,
                        TargetId := AbilityId
                    }
                )
                return true

        false

    AddMeter(
        OwnerKey:string,
        Definition:aeonfall_ability_definition,
        Amount:int
    )<transacts>:logic=
        if:
            Amount > 0
            Old := GetState[OwnerKey, Definition.AbilityId]
        then:
            NewMeter:int =
                if (Old.CurrentMeter + Amount > Definition.MaxMeter):
                    Definition.MaxMeter
                else:
                    Old.CurrentMeter + Amount

            Updated := aeonfall_ability_runtime_state:
                AbilityId := Old.AbilityId
                CurrentCharges := Old.CurrentCharges
                CurrentMeter := NewMeter
                CooldownRemainingSeconds := Old.CooldownRemainingSeconds
                ChargeRechargeRemainingSeconds := Old.ChargeRechargeRemainingSeconds
                Active := Old.Active
                ActiveRequestId := Old.ActiveRequestId
                Pending := Old.Pending
                PendingRequestId := Old.PendingRequestId
                Locked := Old.Locked

            Key := MakeStateKey(OwnerKey, Definition.AbilityId)
            if:
                set States[Key] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "ability.meter_changed",
                        SourceId := OwnerKey,
                        TargetId := Definition.AbilityId,
                        Amount := NewMeter
                    }
                )
                return true

        false

    AddCharge(
        OwnerKey:string,
        Definition:aeonfall_ability_definition,
        Amount:int
    )<transacts>:logic=
        if:
            Amount > 0
            Definition.ResourcePolicy = aeonfall_resource_policy.Charges
            Old := GetState[OwnerKey, Definition.AbilityId]
        then:
            NewCharges:int =
                if (Old.CurrentCharges + Amount > Definition.MaxCharges):
                    Definition.MaxCharges
                else:
                    Old.CurrentCharges + Amount

            Updated := aeonfall_ability_runtime_state:
                AbilityId := Old.AbilityId
                CurrentCharges := NewCharges
                CurrentMeter := Old.CurrentMeter
                CooldownRemainingSeconds := Old.CooldownRemainingSeconds
                ChargeRechargeRemainingSeconds := Old.ChargeRechargeRemainingSeconds
                Active := Old.Active
                ActiveRequestId := Old.ActiveRequestId
                Pending := Old.Pending
                PendingRequestId := Old.PendingRequestId
                Locked := Old.Locked

            Key := MakeStateKey(OwnerKey, Definition.AbilityId)
            if:
                set States[Key] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "ability.charges_changed",
                        SourceId := OwnerKey,
                        TargetId := Definition.AbilityId,
                        Amount := NewCharges
                    }
                )
                return true

        false

    SetLocked(
        OwnerKey:string,
        AbilityId:string,
        Locked:logic
    )<transacts>:logic=
        if:
            Old := GetState[OwnerKey, AbilityId]
        then:
            Updated := aeonfall_ability_runtime_state:
                AbilityId := Old.AbilityId
                CurrentCharges := Old.CurrentCharges
                CurrentMeter := Old.CurrentMeter
                CooldownRemainingSeconds := Old.CooldownRemainingSeconds
                ChargeRechargeRemainingSeconds := Old.ChargeRechargeRemainingSeconds
                Active := Old.Active
                ActiveRequestId := Old.ActiveRequestId
                Pending := Old.Pending
                PendingRequestId := Old.PendingRequestId
                Locked := Locked

            Key := MakeStateKey(OwnerKey, AbilityId)
            if:
                set States[Key] = Updated
            then:
                return true

        false

    TickAbility(
        OwnerKey:string,
        Definition:aeonfall_ability_definition,
        DeltaSeconds:float
    )<transacts>:void=
        if (DeltaSeconds <= 0.0):
            return

        if:
            Old := GetState[OwnerKey, Definition.AbilityId]
        then:
            var Cooldown:float = Old.CooldownRemainingSeconds
            var Charges:int = Old.CurrentCharges
            var Recharge:float = Old.ChargeRechargeRemainingSeconds

            if (Cooldown > 0.0):
                set Cooldown = Cooldown - DeltaSeconds
                if (Cooldown < 0.0):
                    set Cooldown = 0.0

            if:
                Definition.ResourcePolicy = aeonfall_resource_policy.Charges
                Charges < Definition.MaxCharges
            then:
                if (Recharge > 0.0):
                    set Recharge = Recharge - DeltaSeconds

                if (Recharge <= 0.0):
                    set Charges = Charges + 1
                    if (Charges < Definition.MaxCharges):
                        set Recharge = Definition.RechargeSeconds
                    else:
                        set Recharge = 0.0

            Updated := aeonfall_ability_runtime_state:
                AbilityId := Old.AbilityId
                CurrentCharges := Charges
                CurrentMeter := Old.CurrentMeter
                CooldownRemainingSeconds := Cooldown
                ChargeRechargeRemainingSeconds := Recharge
                Active := Old.Active
                ActiveRequestId := Old.ActiveRequestId
                Pending := Old.Pending
                PendingRequestId := Old.PendingRequestId
                Locked := Old.Locked

            Key := MakeStateKey(OwnerKey, Definition.AbilityId)
            if:
                set States[Key] = Updated
            then:
                return

    TickAll(DeltaSeconds:float)<transacts>:void=
        if (DeltaSeconds <= 0.0):
            return

        var UpdatedStates:[string]aeonfall_ability_runtime_state = map{}

        for (Key -> Old : States):
            var Cooldown:float = Old.CooldownRemainingSeconds
            var Charges:int = Old.CurrentCharges
            var Recharge:float = Old.ChargeRechargeRemainingSeconds

            if:
                Definition := AEONFALLAbilityRegistry.Get[Old.AbilityId]
            then:
                if (Cooldown > 0.0):
                    set Cooldown = Cooldown - DeltaSeconds
                    if (Cooldown < 0.0):
                        set Cooldown = 0.0

                if:
                    Definition.ResourcePolicy = aeonfall_resource_policy.Charges
                    Charges < Definition.MaxCharges
                then:
                    if (Recharge > 0.0):
                        set Recharge = Recharge - DeltaSeconds

                    if (Recharge <= 0.0):
                        set Charges = Charges + 1
                        if (Charges < Definition.MaxCharges):
                            set Recharge = Definition.RechargeSeconds
                        else:
                            set Recharge = 0.0

            Updated := aeonfall_ability_runtime_state:
                AbilityId := Old.AbilityId
                CurrentCharges := Charges
                CurrentMeter := Old.CurrentMeter
                CooldownRemainingSeconds := Cooldown
                ChargeRechargeRemainingSeconds := Recharge
                Active := Old.Active
                ActiveRequestId := Old.ActiveRequestId
                Pending := Old.Pending
                PendingRequestId := Old.PendingRequestId
                Locked := Old.Locked

            if:
                set UpdatedStates[Key] = Updated
            then:
                set UpdatedStates = UpdatedStates

        set States = UpdatedStates

    ClearOwner(OwnerKey:string)<transacts>:void=
        var UpdatedStates:[string]aeonfall_ability_runtime_state = map{}
        var UpdatedOwners:[string]string = map{}

        for (Key -> State : States):
            var Keep:logic = true

            if:
                StoredOwner := OwnerByStateKey[Key]
            then:
                if (StoredOwner = OwnerKey):
                    set Keep = false

            if (Keep?):
                if:
                    set UpdatedStates[Key] = State
                then:
                    if:
                        StoredOwner := OwnerByStateKey[Key]
                        set UpdatedOwners[Key] = StoredOwner
                    then:
                        set UpdatedOwners = UpdatedOwners

        set States = UpdatedStates
        set OwnerByStateKey = UpdatedOwners

        AEONFALLRuntimeBus.Emit(
            aeonfall_runtime_event{
                EventType := "ability.owner_cleared",
                SourceId := OwnerKey
            }
        )

AEONFALLAbilityRuntime:aeonfall_ability_runtime = aeonfall_ability_runtime{}
