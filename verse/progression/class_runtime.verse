using { /Verse.org/Simulation }

# Session class runtime with persistent equipped-class selection for players.
aeonfall_class_registry := class():

    var Definitions:[string]aeonfall_class_definition = map{}

    Register(Definition:aeonfall_class_definition)<transacts>:logic=
        if:
            Definition.ClassId <> ""
            Definition.MaxResource >= 0
            Definition.BaseMaxCompanions >= 0
            set Definitions[Definition.ClassId] = Definition
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "class.definition_registered",
                    SourceId := Definition.ClassId
                }
            )
            return true

        false

    Get(ClassId:string)<decides><transacts>:aeonfall_class_definition=
        Definitions[ClassId]

AEONFALLClassRegistry:aeonfall_class_registry = aeonfall_class_registry{}

aeonfall_class_runtime := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}

    var States:[string]aeonfall_class_runtime_state = map{}
    var Reservations:[string]aeonfall_class_resource_reservation = map{}

    GetState(OwnerKey:string)<decides><transacts>:aeonfall_class_runtime_state=
        States[OwnerKey]

    GetReservedTotal(OwnerKey:string)<transacts>:int=
        var Total:int = 0
        for (RequestId -> Reservation : Reservations):
            if (Reservation.OwnerKey = OwnerKey):
                set Total += Reservation.Amount
        Total

    GetAvailableResource(OwnerKey:string)<transacts>:int=
        if:
            State := States[OwnerKey]
        then:
            Available:int = State.CurrentResource - GetReservedTotal(OwnerKey)
            if (Available > 0):
                Available
            else:
                0
        else:
            0

    HasActiveReservation(OwnerKey:string)<transacts>:logic=
        for (RequestId -> Reservation : Reservations):
            if (Reservation.OwnerKey = OwnerKey):
                return true
        false

    ActivateClass(
        OwnerKey:string,
        ClassId:string
    )<transacts>:logic=
        if (HasActiveReservation(OwnerKey)?):
            return false

        if:
            Agent := AEONFALLActorRegistry.GetAgent[OwnerKey]
            Definition := AEONFALLClassRegistry.Get[ClassId]
        then:
            # Resolve every ability before mutating class state.
            var Ready:logic = true
            for (AbilityId : Definition.AbilityIds):
                if:
                    AbilityDefinition := AEONFALLAbilityRegistry.Get[AbilityId]
                then:
                    Initialized := AEONFALLAbilityRuntime.Initialize(
                        OwnerKey,
                        AbilityDefinition
                    )
                    if (not Initialized?):
                        set Ready = false
                else:
                    set Ready = false

            if (Ready?):
                # Remove previous permanent/passive class statuses.
                if:
                    OldState := States[OwnerKey]
                    OldDefinition := AEONFALLClassRegistry.Get[OldState.ClassId]
                then:
                    for (StatusId : OldDefinition.PassiveStatusIds):
                        Removed := AEONFALLStatusRuntime.RemoveStatus(
                            OwnerKey,
                            StatusId
                        )
                        if (Removed?):
                            set Ready = Ready

                # Apply the new class passives only after all references resolve.
                for (StatusId : Definition.PassiveStatusIds):
                    if:
                        StatusDefinition := AEONFALLStatusRegistry.Get[StatusId]
                    then:
                        Applied := AEONFALLStatusRuntime.ApplyStatus(
                            OwnerKey,
                            StatusDefinition,
                            ClassId,
                            0
                        )
                        if (not Applied?):
                            set Ready = false
                    else:
                        set Ready = false

            if (Ready?):
                NewState := aeonfall_class_runtime_state:
                    ClassId := ClassId
                    CurrentResource := Definition.MaxResource
                    MaxResource := Definition.MaxResource
                    AbilityIds := Definition.AbilityIds
                    Active := true

                if:
                    set States[OwnerKey] = NewState
                then:
                    if:
                        Player := player[Agent]
                    then:
                        ProfileService.SetEquippedClass(Player, ClassId)

                    AEONFALLRuntimeBus.Emit(
                        aeonfall_runtime_event{
                            EventType := "class.activated",
                            SourceId := OwnerKey,
                            TargetId := ClassId,
                            Amount := Definition.MaxResource
                        }
                    )
                    return true

        false

    AddResource(
        OwnerKey:string,
        Amount:int
    )<transacts>:logic=
        if:
            Amount > 0
            Old := States[OwnerKey]
            Old.Active?
        then:
            NewValue:int =
                if (Old.CurrentResource + Amount > Old.MaxResource):
                    Old.MaxResource
                else:
                    Old.CurrentResource + Amount

            Updated := aeonfall_class_runtime_state:
                ClassId := Old.ClassId
                CurrentResource := NewValue
                MaxResource := Old.MaxResource
                AbilityIds := Old.AbilityIds
                Active := Old.Active

            if:
                set States[OwnerKey] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "class.resource_changed",
                        SourceId := OwnerKey,
                        TargetId := Old.ClassId,
                        Amount := GetAvailableResource(OwnerKey)
                    }
                )
                return true

        false

    SpendResource(
        OwnerKey:string,
        Amount:int
    )<transacts>:logic=
        if:
            Amount > 0
            Old := States[OwnerKey]
            Old.Active?
            GetAvailableResource(OwnerKey) >= Amount
        then:
            NewValue:int = Old.CurrentResource - Amount
            Updated := aeonfall_class_runtime_state:
                ClassId := Old.ClassId
                CurrentResource := NewValue
                MaxResource := Old.MaxResource
                AbilityIds := Old.AbilityIds
                Active := Old.Active

            if:
                set States[OwnerKey] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "class.resource_changed",
                        SourceId := OwnerKey,
                        TargetId := Old.ClassId,
                        Amount := GetAvailableResource(OwnerKey)
                    }
                )
                return true

        false

    ReserveResource(
        RequestId:string,
        OwnerKey:string,
        ClassId:string,
        Amount:int,
        HoldWhileActive:logic
    )<transacts>:logic=
        if:
            RequestId <> ""
            Amount > 0
            State := States[OwnerKey]
            State.Active?
            State.ClassId = ClassId
            GetAvailableResource(OwnerKey) >= Amount
        then:
            if:
                Existing := Reservations[RequestId]
            then:
                return false
            else:
                Reservation := aeonfall_class_resource_reservation:
                    RequestId := RequestId
                    OwnerKey := OwnerKey
                    ClassId := ClassId
                    Amount := Amount
                    HoldWhileActive := HoldWhileActive

                if:
                    set Reservations[RequestId] = Reservation
                then:
                    AEONFALLRuntimeBus.Emit(
                        aeonfall_runtime_event{
                            EventType := "class.resource_reserved",
                            SourceId := OwnerKey,
                            TargetId := ClassId,
                            ContextId := RequestId,
                            Amount := GetAvailableResource(OwnerKey)
                        }
                    )
                    return true

        false

    CommitReservation(RequestId:string)<transacts>:logic=
        if:
            Reservation := Reservations[RequestId]
            State := States[Reservation.OwnerKey]
            State.Active?
            State.ClassId = Reservation.ClassId
            State.CurrentResource >= Reservation.Amount
        then:
            NewValue:int = State.CurrentResource - Reservation.Amount
            Updated := aeonfall_class_runtime_state:
                ClassId := State.ClassId
                CurrentResource := NewValue
                MaxResource := State.MaxResource
                AbilityIds := State.AbilityIds
                Active := State.Active

            if:
                set States[Reservation.OwnerKey] = Updated
            then:
                Released := RemoveReservation(RequestId)
                if (Released?):
                    AEONFALLRuntimeBus.Emit(
                        aeonfall_runtime_event{
                            EventType := "class.resource_committed",
                            SourceId := Reservation.OwnerKey,
                            TargetId := Reservation.ClassId,
                            ContextId := RequestId,
                            Amount := GetAvailableResource(Reservation.OwnerKey)
                        }
                    )
                    return true

        false

    HoldReservation(RequestId:string)<transacts>:logic=
        if:
            Reservation := Reservations[RequestId]
        then:
            Updated := aeonfall_class_resource_reservation:
                RequestId := Reservation.RequestId
                OwnerKey := Reservation.OwnerKey
                ClassId := Reservation.ClassId
                Amount := Reservation.Amount
                HoldWhileActive := true

            if:
                set Reservations[RequestId] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "class.resource_held",
                        SourceId := Reservation.OwnerKey,
                        TargetId := Reservation.ClassId,
                        ContextId := RequestId,
                        Amount := GetAvailableResource(Reservation.OwnerKey)
                    }
                )
                return true

        false

    ReleaseReservation(RequestId:string)<transacts>:logic=
        if:
            Reservation := Reservations[RequestId]
        then:
            Released := RemoveReservation(RequestId)
            if (Released?):
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "class.resource_released",
                        SourceId := Reservation.OwnerKey,
                        TargetId := Reservation.ClassId,
                        ContextId := RequestId,
                        Amount := GetAvailableResource(Reservation.OwnerKey)
                    }
                )
                return true

        false

    RemoveReservation(RequestId:string)<transacts>:logic=
        if:
            Existing := Reservations[RequestId]
        then:
            var UpdatedReservations:[string]aeonfall_class_resource_reservation = map{}
            var Valid:logic = true

            for (StoredRequestId -> Reservation : Reservations):
                if (StoredRequestId <> RequestId):
                    if:
                        set UpdatedReservations[StoredRequestId] = Reservation
                    then:
                        set Valid = Valid
                    else:
                        set Valid = false

            if (Valid?):
                set Reservations = UpdatedReservations
                return true

        false

AEONFALLClassRuntime:aeonfall_class_runtime = aeonfall_class_runtime{}
