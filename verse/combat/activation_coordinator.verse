# Coordinates AEONFALL ability resources with class resources.
# This is the public activation path for abilities. It keeps the canonical
# ability reservation and class-resource reservation synchronized.

aeonfall_activation_coordinator := class():

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

        true

    ResolveAdapterResult(
        Definition:aeonfall_ability_definition,
        Result:aeonfall_adapter_result
    )<transacts>:logic=
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

AEONFALLActivationCoordinator:aeonfall_activation_coordinator = aeonfall_activation_coordinator{}
