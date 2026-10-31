using { /Verse.org/Verse }
using { /Verse.org/Simulation }
# One adapter request reserved by the coordinator until success, failure,
# explicit cancellation, or timeout.
aeonfall_pending_activation := class:
    RequestId:string = ""
    OwnerKey:string = ""
    AbilityId:string = ""
    TimeoutRemainingSeconds:float = 5.0

# Coordinates AEONFALL ability resources with class resources.
# This is the public activation path for abilities. It keeps the canonical
# ability reservation and class-resource reservation synchronized.

aeonfall_activation_coordinator := class():

    var PendingActivations:[string]aeonfall_pending_activation = map{}

    RemovePendingRecord(RequestId:string)<transacts>:logic=
        if:
            Existing := PendingActivations[RequestId]
        then:
            var Updated:[string]aeonfall_pending_activation = map{}
            var Valid:logic = true

            for (StoredId -> Pending : PendingActivations):
                if (StoredId <> RequestId):
                    if:
                        set Updated[StoredId] = Pending
                    then:
                        set Valid = Valid
                    else:
                        set Valid = false

            if (Valid?):
                set PendingActivations = Updated
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
        # Register timeout ownership BEFORE dispatch: an adapter may report
        # its result synchronously while RequestActivation is still executing.
        if (RequestId = "" or OwnerKey = ""):
            return false
        if (PendingActivations[RequestId]):
            return false
        if (not GetAEONFALLAbilityRuntime().CanActivate(OwnerKey, Definition, Context)?):
            return false

        var ClassReserved:logic = false
        if (Definition.ClassResourceMode <> aeonfall_class_resource_mode.None):
            HoldWhileActive:logic = logic{Definition.ClassResourceMode = aeonfall_class_resource_mode.ReserveWhileActive}
            Reserved := GetAEONFALLClassRuntime().ReserveResource(
                RequestId, OwnerKey, Definition.RequiredClassId,
                Definition.ClassResourceCost, HoldWhileActive
            )
            if (not Reserved?):
                return false
            set ClassReserved = true

        Pending := aeonfall_pending_activation{
            RequestId := RequestId, OwnerKey := OwnerKey,
            AbilityId := Definition.AbilityId, TimeoutRemainingSeconds := 5.0
        }
        if (set PendingActivations[RequestId] = Pending):
            Requested := GetAEONFALLAbilityRuntime().RequestActivation(
                RequestId, OwnerKey, Definition, Context,
                TargetKey, RuntimeContextId, Magnitude
            )
            if (Requested?):
                return true
            Removed := RemovePendingRecord(RequestId)

        if (ClassReserved?):
            Released := GetAEONFALLClassRuntime().ReleaseReservation(RequestId)
        false

    IsMatchingPending(
        Definition:aeonfall_ability_definition,
        Result:aeonfall_adapter_result
    )<transacts>:logic=
        if:
            Result.RequestId <> ""
            Result.AbilityId = Definition.AbilityId
            Result.AdapterId = Definition.AdapterId
            Pending := PendingActivations[Result.RequestId]
            Pending.OwnerKey = Result.OwnerKey
            Pending.AbilityId = Result.AbilityId
            State := GetAEONFALLAbilityRuntime().GetState[Result.OwnerKey, Result.AbilityId]
            State.Pending?
            State.PendingRequestId = Result.RequestId
        then:
            return true
        false

    ResolveAdapterResult(
        Definition:aeonfall_ability_definition,
        Result:aeonfall_adapter_result
    )<transacts>:logic=
        # Ignore stale/duplicate/mismatched callbacks before releasing either
        # timeout ownership or class resources belonging to another request.
        if (not IsMatchingPending(Definition, Result)?):
            return false
        RemovedPending := RemovePendingRecord(Result.RequestId)

        if (not Result.Succeeded?):
            if (Definition.ClassResourceMode <> aeonfall_class_resource_mode.None):
                Released := GetAEONFALLClassRuntime().ReleaseReservation(Result.RequestId)

            return GetAEONFALLAbilityRuntime().ResolveActivation(
                Definition,
                Result
            )

        if (Definition.ClassResourceMode = aeonfall_class_resource_mode.SpendOnSuccess):
            CommittedClass := GetAEONFALLClassRuntime().CommitReservation(
                Result.RequestId
            )

            if (not CommittedClass?):
                FailedResult := aeonfall_adapter_result:
                    RequestId := Result.RequestId
                    OwnerKey := Result.OwnerKey
                    AbilityId := Result.AbilityId
                    AdapterId := Result.AdapterId
                    Succeeded := false
                    ResultCode := "class_resource_commit_failed"

                Released := GetAEONFALLClassRuntime().ReleaseReservation(
                    Result.RequestId
                )

                return GetAEONFALLAbilityRuntime().ResolveActivation(
                    Definition,
                    FailedResult
                )

            Resolved := GetAEONFALLAbilityRuntime().ResolveActivation(
                Definition,
                Result
            )

            if (not Resolved?):
                # Reservation guaranteed this spend. Restore it if the
                # canonical ability state unexpectedly fails to commit.
                Restored := GetAEONFALLClassRuntime().AddResource(
                    Result.OwnerKey,
                    Definition.ClassResourceCost
                )

            return Resolved

        if (Definition.ClassResourceMode = aeonfall_class_resource_mode.ReserveWhileActive):
            Held := GetAEONFALLClassRuntime().HoldReservation(Result.RequestId)
            if (not Held?):
                FailedResult := aeonfall_adapter_result:
                    RequestId := Result.RequestId
                    OwnerKey := Result.OwnerKey
                    AbilityId := Result.AbilityId
                    AdapterId := Result.AdapterId
                    Succeeded := false
                    ResultCode := "class_resource_hold_failed"

                Released := GetAEONFALLClassRuntime().ReleaseReservation(
                    Result.RequestId
                )

                return GetAEONFALLAbilityRuntime().ResolveActivation(
                    Definition,
                    FailedResult
                )

            Resolved := GetAEONFALLAbilityRuntime().ResolveActivation(
                Definition,
                Result
            )

            if (not Resolved?):
                Released := GetAEONFALLClassRuntime().ReleaseReservation(
                    Result.RequestId
                )

            return Resolved

        GetAEONFALLAbilityRuntime().ResolveActivation(
            Definition,
            Result
        )

    EndActivation(
        OwnerKey:string,
        AbilityId:string
    )<transacts>:logic=
        if:
            Definition := GetAEONFALLAbilityRegistry().Get[AbilityId]
            State := GetAEONFALLAbilityRuntime().GetState[OwnerKey, AbilityId]
        then:
            ActiveRequestId:string = State.ActiveRequestId
            Ended := GetAEONFALLAbilityRuntime().EndActivation(
                OwnerKey,
                AbilityId
            )

            if:
                Ended?
                Definition.ClassResourceMode = aeonfall_class_resource_mode.ReserveWhileActive
                ActiveRequestId <> ""
            then:
                Released := GetAEONFALLClassRuntime().ReleaseReservation(
                    ActiveRequestId
                )
                if (not Released?):
                    AEONFALLRuntimeBus.Emit(
                        aeonfall_runtime_event{
                            EventType := "class.resource_release_failed",
                            SourceId := OwnerKey,
                            TargetId := Definition.RequiredClassId,
                            ContextId := ActiveRequestId
                        }
                    )

            return Ended

        false

    CancelPending(
        OwnerKey:string,
        AbilityId:string,
        RequestId:string
    )<transacts>:logic=
        if:
            Pending := PendingActivations[RequestId]
            Pending.OwnerKey = OwnerKey
            Pending.AbilityId = AbilityId
            Definition := GetAEONFALLAbilityRegistry().Get[AbilityId]
            State := GetAEONFALLAbilityRuntime().GetState[OwnerKey, AbilityId]
            State.Pending?
            State.PendingRequestId = RequestId
        then:
            Cancelled := GetAEONFALLAbilityRuntime().CancelPending(OwnerKey, AbilityId, RequestId)
            if (Cancelled?):
                Removed := RemovePendingRecord(RequestId)
                if (Definition.ClassResourceMode <> aeonfall_class_resource_mode.None):
                    Released := GetAEONFALLClassRuntime().ReleaseReservation(RequestId)
                return true
        false

    TickPendingActivations(DeltaSeconds:float)<transacts>:void=
        if (DeltaSeconds <= 0.0):
            return

        var Updated:[string]aeonfall_pending_activation = map{}
        var Expired:[]aeonfall_pending_activation = array{}

        for (RequestId -> Pending : PendingActivations):
            Remaining:float = Pending.TimeoutRemainingSeconds - DeltaSeconds

            if (Remaining > 0.0):
                Next := aeonfall_pending_activation:
                    RequestId := Pending.RequestId
                    OwnerKey := Pending.OwnerKey
                    AbilityId := Pending.AbilityId
                    TimeoutRemainingSeconds := Remaining

                if:
                    set Updated[RequestId] = Next
                then:
                    set Updated = Updated
            else:
                set Expired = Expired + array{Pending}

        set PendingActivations = Updated

        for (Pending : Expired):
            if:
                Definition := GetAEONFALLAbilityRegistry().Get[Pending.AbilityId]
            then:
                if (Definition.ClassResourceMode <> aeonfall_class_resource_mode.None):
                    Released := GetAEONFALLClassRuntime().ReleaseReservation(
                        Pending.RequestId
                    )

            Cancelled := GetAEONFALLAbilityRuntime().CancelPending(
                Pending.OwnerKey,
                Pending.AbilityId,
                Pending.RequestId
            )

            if (Cancelled?):
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "ability.adapter_timeout",
                        SourceId := Pending.OwnerKey,
                        TargetId := Pending.AbilityId,
                        ContextId := Pending.RequestId
                    }
                )

    ClearOwnerPending(OwnerKey:string)<transacts>:void=
        var PendingIds:[]string = array{}

        for (RequestId -> Pending : PendingActivations):
            if (Pending.OwnerKey = OwnerKey):
                set PendingIds = PendingIds + array{RequestId}

        for (RequestId : PendingIds):
            if:
                Pending := PendingActivations[RequestId]
            then:
                Cancelled := CancelPending(
                    Pending.OwnerKey,
                    Pending.AbilityId,
                    Pending.RequestId
                )

        AEONFALLRuntimeBus.Emit(
            aeonfall_runtime_event{
                EventType := "ability.pending_owner_cleared",
                SourceId := OwnerKey
            }
        )

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLActivationCoordinatorSessions:weak_map(session, aeonfall_activation_coordinator) = map{}

GetAEONFALLActivationCoordinator()<transacts>:aeonfall_activation_coordinator=
    CurrentSession := GetSession()
    if (Existing := AEONFALLActivationCoordinatorSessions[CurrentSession]):
        return Existing
    Created := aeonfall_activation_coordinator{}
    if (set AEONFALLActivationCoordinatorSessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLActivationCoordinator in its session")
