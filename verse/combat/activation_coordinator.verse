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
        var ClassReserved:logic = false

        if (Definition.ClassResourceMode <> aeonfall_class_resource_mode.None):
            HoldWhileActive:logic =
                Definition.ClassResourceMode = aeonfall_class_resource_mode.ReserveWhileActive

            Reserved := AEONFALLClassRuntime.ReserveResource(
                RequestId,
                OwnerKey,
                Definition.RequiredClassId,
                Definition.ClassResourceCost,
                HoldWhileActive
            )

            if (not Reserved?):
                return false

            set ClassReserved = true

        Requested := AEONFALLAbilityRuntime.RequestActivation(
            RequestId,
            OwnerKey,
            Definition,
            Context,
            TargetKey,
            RuntimeContextId,
            Magnitude
        )

        if (not Requested?):
            if (ClassReserved?):
                Released := AEONFALLClassRuntime.ReleaseReservation(RequestId)
                if (Released?):
                    set ClassReserved = false
            return false

        Pending := aeonfall_pending_activation:
            RequestId := RequestId
            OwnerKey := OwnerKey
            AbilityId := Definition.AbilityId
            TimeoutRemainingSeconds := 5.0

        if:
            set PendingActivations[RequestId] = Pending
        then:
            return true

        # Roll back both reservations if timeout tracking itself cannot be stored.
        Cancelled := AEONFALLAbilityRuntime.CancelPending(
            OwnerKey,
            Definition.AbilityId,
            RequestId
        )
        if (Cancelled?):
            if (ClassReserved?):
                Released := AEONFALLClassRuntime.ReleaseReservation(RequestId)
                if (Released?):
                    set ClassReserved = false

        false

    ResolveAdapterResult(
        Definition:aeonfall_ability_definition,
        Result:aeonfall_adapter_result
    )<transacts>:logic=
        RemovedPending := RemovePendingRecord(Result.RequestId)
        if (RemovedPending?):
            RemovedPending = true

        if (not Result.Succeeded?):
            if (Definition.ClassResourceMode <> aeonfall_class_resource_mode.None):
                Released := AEONFALLClassRuntime.ReleaseReservation(Result.RequestId)
                if (Released?):
                    Released = true

            return AEONFALLAbilityRuntime.ResolveActivation(
                Definition,
                Result
            )

        if (Definition.ClassResourceMode = aeonfall_class_resource_mode.SpendOnSuccess):
            CommittedClass := AEONFALLClassRuntime.CommitReservation(
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

                Released := AEONFALLClassRuntime.ReleaseReservation(
                    Result.RequestId
                )
                if (Released?):
                    Released = true

                return AEONFALLAbilityRuntime.ResolveActivation(
                    Definition,
                    FailedResult
                )

            Resolved := AEONFALLAbilityRuntime.ResolveActivation(
                Definition,
                Result
            )

            if (not Resolved?):
                # Reservation guaranteed this spend. Restore it if the
                # canonical ability state unexpectedly fails to commit.
                Restored := AEONFALLClassRuntime.AddResource(
                    Result.OwnerKey,
                    Definition.ClassResourceCost
                )
                if (Restored?):
                    Restored = true

            return Resolved

        if (Definition.ClassResourceMode = aeonfall_class_resource_mode.ReserveWhileActive):
            Held := AEONFALLClassRuntime.HoldReservation(Result.RequestId)
            if (not Held?):
                FailedResult := aeonfall_adapter_result:
                    RequestId := Result.RequestId
                    OwnerKey := Result.OwnerKey
                    AbilityId := Result.AbilityId
                    AdapterId := Result.AdapterId
                    Succeeded := false
                    ResultCode := "class_resource_hold_failed"

                Released := AEONFALLClassRuntime.ReleaseReservation(
                    Result.RequestId
                )
                if (Released?):
                    Released = true

                return AEONFALLAbilityRuntime.ResolveActivation(
                    Definition,
                    FailedResult
                )

            Resolved := AEONFALLAbilityRuntime.ResolveActivation(
                Definition,
                Result
            )

            if (not Resolved?):
                Released := AEONFALLClassRuntime.ReleaseReservation(
                    Result.RequestId
                )
                if (Released?):
                    Released = true

            return Resolved

        AEONFALLAbilityRuntime.ResolveActivation(
            Definition,
            Result
        )

    EndActivation(
        OwnerKey:string,
        AbilityId:string
    )<transacts>:logic=
        if:
            Definition := AEONFALLAbilityRegistry.Get[AbilityId]
            State := AEONFALLAbilityRuntime.GetState[OwnerKey, AbilityId]
        then:
            ActiveRequestId:string = State.ActiveRequestId
            Ended := AEONFALLAbilityRuntime.EndActivation(
                OwnerKey,
                AbilityId
            )

            if:
                Ended?
                Definition.ClassResourceMode = aeonfall_class_resource_mode.ReserveWhileActive
                ActiveRequestId <> ""
            then:
                Released := AEONFALLClassRuntime.ReleaseReservation(
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
        RemovedPending := RemovePendingRecord(RequestId)
        if (RemovedPending?):
            RemovedPending = true

        if:
            Definition := AEONFALLAbilityRegistry.Get[AbilityId]
        then:
            if (Definition.ClassResourceMode <> aeonfall_class_resource_mode.None):
                Released := AEONFALLClassRuntime.ReleaseReservation(RequestId)
                if (Released?):
                    Released = true

            AEONFALLAbilityRuntime.CancelPending(
                OwnerKey,
                AbilityId,
                RequestId
            )
        else:
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
                Definition := AEONFALLAbilityRegistry.Get[Pending.AbilityId]
            then:
                if (Definition.ClassResourceMode <> aeonfall_class_resource_mode.None):
                    Released := AEONFALLClassRuntime.ReleaseReservation(
                        Pending.RequestId
                    )
                    if (Released?):
                        Released = true

            Cancelled := AEONFALLAbilityRuntime.CancelPending(
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
                if (Cancelled?):
                    Cancelled = true

        AEONFALLRuntimeBus.Emit(
            aeonfall_runtime_event{
                EventType := "ability.pending_owner_cleared",
                SourceId := OwnerKey
            }
        )

AEONFALLActivationCoordinator:aeonfall_activation_coordinator = aeonfall_activation_coordinator{}
