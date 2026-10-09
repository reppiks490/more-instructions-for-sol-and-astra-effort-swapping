using { /Verse.org/Verse }
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

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLClassRegistrySessions:weak_map(session, aeonfall_class_registry) = map{}

GetAEONFALLClassRegistry()<transacts>:aeonfall_class_registry=
    CurrentSession := GetSession()
    if (Existing := AEONFALLClassRegistrySessions[CurrentSession]):
        return Existing
    Created := aeonfall_class_registry{}
    if (set AEONFALLClassRegistrySessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLClassRegistry in its session")

aeonfall_class_runtime := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}

    var States:[string]aeonfall_class_runtime_state = map{}
    var Reservations:[string]aeonfall_class_resource_reservation = map{}
    var ResourceHistory:[string][string]int = map{}

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

    # Re-selecting the active class is idempotent. Switching saves each class's
    # current resource so selecting another class cannot manufacture a refill.
    ActivateClass(OwnerKey:string, ClassId:string)<transacts>:logic=
        if (Current := States[OwnerKey], Current.Active?, Current.ClassId = ClassId):
            return true
        if (CommitClassActivation[OwnerKey, ClassId]):
            return true
        false

    # All logical effects and the persistent selection share one failure scope.
    # Missing abilities, a full status/event queue, or a refused save rolls back
    # the old passives, resources, ability initialization and profile together.
    CommitClassActivation(OwnerKey:string, ClassId:string)<decides><transacts>:void=
        not HasActiveReservation(OwnerKey)?
        Agent := GetAEONFALLActorRegistry().GetAgent[OwnerKey]
        Definition := GetAEONFALLClassRegistry().Get[ClassId]

        if (Player := player[Agent]):
            Profile := ProfileService.GetProfile[Player]
            for (UnlockId : Definition.RequiredUnlockIds):
                Profile.UnlockedEntityIds.Find[UnlockId]

        for (AbilityId : Definition.AbilityIds):
            AbilityDefinition := GetAEONFALLAbilityRegistry().Get[AbilityId]
            Initialized := GetAEONFALLAbilityRuntime().Initialize(OwnerKey, AbilityDefinition)
            Initialized?

        var History:[string]int = map{}
        if (Saved := ResourceHistory[OwnerKey]):
            set History = Saved
        if (OldState := States[OwnerKey]):
            set History[OldState.ClassId] = OldState.CurrentResource
            OldDefinition := GetAEONFALLClassRegistry().Get[OldState.ClassId]
            for (StatusId : OldDefinition.PassiveStatusIds):
                if (GetAEONFALLStatusRuntime().HasStatus(OwnerKey, StatusId)?):
                    Removed := GetAEONFALLStatusRuntime().RemoveStatus(OwnerKey, StatusId)
                    Removed?

        GetAEONFALLStatusRuntime().ApplyBatch[
            OwnerKey, Definition.PassiveStatusIds, ClassId, 0
        ]

        var Resource:int = Definition.MaxResource
        if (SavedResource := History[ClassId]):
            set Resource = SavedResource
        if (Resource < 0):
            set Resource = 0
        if (Resource > Definition.MaxResource):
            set Resource = Definition.MaxResource

        set ResourceHistory[OwnerKey] = History
        set States[OwnerKey] = aeonfall_class_runtime_state{
            ClassId := ClassId,
            CurrentResource := Resource,
            MaxResource := Definition.MaxResource,
            AbilityIds := Definition.AbilityIds,
            Active := true
        }

        if (Player := player[Agent]):
            OldProfile := ProfileService.GetProfile[Player]
            Candidate := aeonfall_player_profile:
                MakeAEONFALLPlayerProfile<constructor>(OldProfile)
                EquippedClassId := ClassId
            Saved := ProfileService.TrySaveProfile(Player, Candidate)
            Saved?

        Admitted := AEONFALLRuntimeBus.TryEmit(aeonfall_runtime_event{
            EventType := "class.activated",
            SourceId := OwnerKey,
            TargetId := ClassId,
            Amount := Resource
        })
        Admitted?

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

    TransferReservation(
        OldRequestId:string,
        NewRequestId:string
    )<transacts>:logic=
        if:
            OldRequestId <> ""
            NewRequestId <> ""
            OldRequestId <> NewRequestId
            Reservation := Reservations[OldRequestId]
        then:
            if:
                Existing := Reservations[NewRequestId]
            then:
                return false
            else:
                Updated := aeonfall_class_resource_reservation:
                    RequestId := NewRequestId
                    OwnerKey := Reservation.OwnerKey
                    ClassId := Reservation.ClassId
                    Amount := Reservation.Amount
                    HoldWhileActive := true

                if:
                    set Reservations[NewRequestId] = Updated
                then:
                    Removed := RemoveReservation(OldRequestId)
                    if (Removed?):
                        AEONFALLRuntimeBus.Emit(
                            aeonfall_runtime_event{
                                EventType := "class.resource_transferred",
                                SourceId := Reservation.OwnerKey,
                                TargetId := Reservation.ClassId,
                                ContextId := NewRequestId,
                                Amount := GetAvailableResource(Reservation.OwnerKey)
                            }
                        )
                        return true
                    else:
                        Rollback := RemoveReservation(NewRequestId)

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

    ClearOwner(OwnerKey:string)<transacts>:void=
        var UpdatedStates:[string]aeonfall_class_runtime_state = map{}
        var UpdatedReservations:[string]aeonfall_class_resource_reservation = map{}

        for (StoredOwnerKey -> State : States):
            if (StoredOwnerKey <> OwnerKey):
                if:
                    set UpdatedStates[StoredOwnerKey] = State
                then:
                    set UpdatedStates = UpdatedStates

        for (RequestId -> Reservation : Reservations):
            if (Reservation.OwnerKey <> OwnerKey):
                if:
                    set UpdatedReservations[RequestId] = Reservation
                then:
                    set UpdatedReservations = UpdatedReservations

        var KeptHistory:[string][string]int = map{}
        for (StoredOwnerKey -> History : ResourceHistory):
            if (StoredOwnerKey <> OwnerKey):
                if (set KeptHistory[StoredOwnerKey] = History):
                    set KeptHistory = KeptHistory
        set ResourceHistory = KeptHistory
        set States = UpdatedStates
        set Reservations = UpdatedReservations

        AEONFALLRuntimeBus.Emit(
            aeonfall_runtime_event{
                EventType := "class.owner_cleared",
                SourceId := OwnerKey
            }
        )

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLClassRuntimeSessions:weak_map(session, aeonfall_class_runtime) = map{}

GetAEONFALLClassRuntime()<transacts>:aeonfall_class_runtime=
    CurrentSession := GetSession()
    if (Existing := AEONFALLClassRuntimeSessions[CurrentSession]):
        return Existing
    Created := aeonfall_class_runtime{}
    if (set AEONFALLClassRuntimeSessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLClassRuntime in its session")
