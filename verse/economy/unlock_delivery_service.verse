using { /Verse.org/Simulation }

aeonfall_unlock_delivery_state := class:
    RequestId:string = ""
    OwnerKey:string = ""
    EntityId:string = ""
    SourceId:string = ""
    RemainingSeconds:float = 0.0
    AttemptsRemaining:int = 0

# Post-commit delivery coordinator.
# Durable profile state is authoritative. Physical inventory/device delivery is
# retryable session state and never rolls back a successful purchase/craft.
aeonfall_unlock_delivery_service := class():

    var NextRequestNumber:int = 0
    var Pending:[string]aeonfall_unlock_delivery_state = map{}

    Request(
        Agent:agent,
        EntityId:string,
        SourceId:string
    )<transacts>:logic=
        if:
            EntityId <> ""
            OwnerKey := AEONFALLActorRegistry.GetRuntimeKey[Agent]
        then:
            # Do not create a second outstanding delivery for the same
            # owner/entity pair.
            for (RequestId -> State : Pending):
                if:
                    State.OwnerKey = OwnerKey
                    State.EntityId = EntityId
                then:
                    return false

            set NextRequestNumber += 1
            RequestId:string =
                "DELIVERY::" + OwnerKey + "::" + EntityId + "::" + "{NextRequestNumber}"

            State := aeonfall_unlock_delivery_state:
                RequestId := RequestId
                OwnerKey := OwnerKey
                EntityId := EntityId
                SourceId := SourceId
                RemainingSeconds := 2.0
                AttemptsRemaining := 3

            if:
                set Pending[RequestId] = State
            then:
                AEONFALLRuntimeBus.RequestUnlockDelivery(
                    aeonfall_unlock_delivery_request{
                        RequestId := RequestId,
                        OwnerKey := OwnerKey,
                        EntityId := EntityId,
                        SourceId := SourceId
                    }
                )

                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "unlock.delivery_requested",
                        SourceId := OwnerKey,
                        TargetId := EntityId,
                        ContextId := RequestId
                    }
                )
                return true

        false

    Resolve(Result:aeonfall_unlock_delivery_result)<transacts>:logic=
        if:
            State := Pending[Result.RequestId]
            State.OwnerKey = Result.OwnerKey
            State.EntityId = Result.EntityId
        then:
            Removed := Remove(Result.RequestId)
            if (Removed?):
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType :=
                            if (Result.Succeeded?):
                                "unlock.delivery_succeeded"
                            else:
                                "unlock.delivery_failed",
                        SourceId := Result.OwnerKey,
                        TargetId := Result.EntityId,
                        ContextId := Result.ResultCode
                    }
                )
                return true

        false

    Remove(RequestId:string)<transacts>:logic=
        if:
            Existing := Pending[RequestId]
        then:
            var Updated:[string]aeonfall_unlock_delivery_state = map{}

            for (StoredId -> State : Pending):
                if (StoredId <> RequestId):
                    if:
                        set Updated[StoredId] = State
                    then:
                        set Updated = Updated

            set Pending = Updated
            return true

        false

    ClearOwner(OwnerKey:string)<transacts>:void=
        var Updated:[string]aeonfall_unlock_delivery_state = map{}

        for (RequestId -> State : Pending):
            if (State.OwnerKey <> OwnerKey):
                if:
                    set Updated[RequestId] = State
                then:
                    set Updated = Updated

        set Pending = Updated

    TickAll(DeltaSeconds:float)<transacts>:void=
        if (DeltaSeconds <= 0.0):
            return

        var Updated:[string]aeonfall_unlock_delivery_state = map{}

        for (RequestId -> State : Pending):
            Remaining:float = State.RemainingSeconds - DeltaSeconds

            if (Remaining > 0.0):
                Next := aeonfall_unlock_delivery_state:
                    RequestId := State.RequestId
                    OwnerKey := State.OwnerKey
                    EntityId := State.EntityId
                    SourceId := State.SourceId
                    RemainingSeconds := Remaining
                    AttemptsRemaining := State.AttemptsRemaining

                if:
                    set Updated[RequestId] = Next
                then:
                    set Updated = Updated
            else:
                if (State.AttemptsRemaining > 0):
                    Retry := aeonfall_unlock_delivery_state:
                        RequestId := State.RequestId
                        OwnerKey := State.OwnerKey
                        EntityId := State.EntityId
                        SourceId := State.SourceId
                        RemainingSeconds := 2.0
                        AttemptsRemaining := State.AttemptsRemaining - 1

                    if:
                        set Updated[RequestId] = Retry
                    then:
                        AEONFALLRuntimeBus.RequestUnlockDelivery(
                            aeonfall_unlock_delivery_request{
                                RequestId := Retry.RequestId,
                                OwnerKey := Retry.OwnerKey,
                                EntityId := Retry.EntityId,
                                SourceId := Retry.SourceId
                            }
                        )

                        AEONFALLRuntimeBus.Emit(
                            aeonfall_runtime_event{
                                EventType := "unlock.delivery_retried",
                                SourceId := Retry.OwnerKey,
                                TargetId := Retry.EntityId,
                                ContextId := Retry.RequestId,
                                Amount := Retry.AttemptsRemaining
                            }
                        )
                else:
                    AEONFALLRuntimeBus.Emit(
                        aeonfall_runtime_event{
                            EventType := "unlock.delivery_timed_out",
                            SourceId := State.OwnerKey,
                            TargetId := State.EntityId,
                            ContextId := State.RequestId
                        }
                    )

        set Pending = Updated

AEONFALLUnlockDeliveryService:aeonfall_unlock_delivery_service =
    aeonfall_unlock_delivery_service{}
