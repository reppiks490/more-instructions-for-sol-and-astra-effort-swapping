using { /Verse.org/Verse }
using { /Verse.org/Simulation }
using { /Fortnite.com/Characters }

aeonfall_unlock_delivery_state := class:
    RequestId:string = ""
    OwnerKey:string = ""
    EntityId:string = ""
    SourceId:string = ""
    RemainingSeconds:float = 0.0
    AttemptsRemaining:int = 0
    PhysicalClaimed:logic = false

# Post-commit delivery coordinator.
# Durable profile state is authoritative. Physical inventory/device delivery is
# retryable session state and never rolls back a successful purchase/craft.
aeonfall_unlock_delivery_service := class():

    var NextRequestNumber:int = 0
    var Pending:[string]aeonfall_unlock_delivery_state = map{}
    var Deferred:[string]aeonfall_unlock_delivery_state = map{}
    DeferredCapacity:int = 256
    PendingCapacity:int = 1024

    Request(
        Agent:agent,
        EntityId:string,
        SourceId:string
    )<transacts>:logic=
        if (CommitRequest[Agent, EntityId, SourceId]):
            return true
        false

    # Pending state and queue admission commit together. A saturated queue
    # never leaves a phantom request that prevents the caller from retrying.
    CommitRequest(Agent:agent, EntityId:string, SourceId:string)<decides><transacts>:void=
        EntityId <> ""
        Pending.Length < PendingCapacity
        Player := player[Agent]
        Player.IsActive[]
        Profile := AEONFALLPlayerProfiles[Player]
        Profile.UnlockedEntityIds.Find[EntityId]
        OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
        for (RequestId -> State : Pending):
            not (State.OwnerKey = OwnerKey and State.EntityId = EntityId)
        set NextRequestNumber += 1
        RequestId:string = "DELIVERY::" + OwnerKey + "::" + EntityId + "::{NextRequestNumber}"
        set Pending[RequestId] = aeonfall_unlock_delivery_state{
            RequestId := RequestId,
            OwnerKey := OwnerKey,
            EntityId := EntityId,
            SourceId := SourceId,
            RemainingSeconds := 2.0,
            AttemptsRemaining := 3,
            PhysicalClaimed := false
        }
        Admitted := AEONFALLRuntimeBus.TryRequestUnlockDelivery(aeonfall_unlock_delivery_request{
            RequestId := RequestId,
            OwnerKey := OwnerKey,
            EntityId := EntityId,
            SourceId := SourceId
        })
        Admitted?

    HasPendingDelivery(OwnerKey:string, EntityId:string)<transacts>:logic=
        for (RequestId -> State : Pending):
            if (State.OwnerKey = OwnerKey, State.EntityId = EntityId):
                return true
        false

    # Saved unlocks are retained for later queue admission. Existing pending
    # work satisfies the same owner/entity delivery without starting another.
    QueueAfterCommit(Agent:agent, EntityId:string, SourceId:string)<transacts>:logic=
        if:
            EntityId <> ""
            Player := player[Agent]
            Player.IsActive[]
            Profile := AEONFALLPlayerProfiles[Player]
            Profile.UnlockedEntityIds.Find[EntityId]
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
        then:
            Existing := HasPendingDelivery(OwnerKey, EntityId)
            if (Existing?):
                return true
            Key:string = OwnerKey + "::" + EntityId
            if (Deferred[Key]):
                return true
            Started := Request(Agent, EntityId, SourceId)
            if (Started?):
                return true
            if (Deferred.Length >= DeferredCapacity):
                return false
            if (set Deferred[Key] = aeonfall_unlock_delivery_state{
                OwnerKey := OwnerKey,
                EntityId := EntityId,
                SourceId := SourceId
            }):
                return true
        false

    TickDeferred()<transacts>:void=
        var Remaining:[string]aeonfall_unlock_delivery_state = map{}
        for (Key -> State : Deferred):
            var Started:logic = false
            if (Agent := GetAEONFALLActorRegistry().GetAgent[State.OwnerKey]):
                set Started = HasPendingDelivery(State.OwnerKey, State.EntityId)
                if (not Started?):
                    set Started = Request(Agent, State.EntityId, State.SourceId)
                if (not Started?):
                    if (set Remaining[Key] = State) {}
            # An unregistered owner is dropped without touching persistence.
        set Deferred = Remaining

    RequestEquipmentRestore(Player:player, EntityIds:[]string, SourceId:string)<transacts>:logic=
        if (CommitEquipmentRestore[Player, EntityIds, SourceId]):
            return true
        false

    CommitEquipmentRestore(Player:player, EntityIds:[]string, SourceId:string)<decides><transacts>:void=
        var Requested:[]string = array{}
        for (EntityId : EntityIds):
            if (not Requested.Find[EntityId]):
                Started := QueueAfterCommit(Player, EntityId, SourceId)
                Started?
                set Requested += array{EntityId}

    # Irreversible adapters claim synchronously outside a failure context.
    # Native item/trigger APIs acknowledge dispatch, not inventory possession.
    # Duplicate adapters, duplicate events and retries cannot dispatch twice.
    ClaimDelivery(Request:aeonfall_unlock_delivery_request)<transacts>:logic=
        if:
            State := Pending[Request.RequestId]
            State.OwnerKey = Request.OwnerKey
            State.EntityId = Request.EntityId
            State.SourceId = Request.SourceId
            not State.PhysicalClaimed?
            Agent := GetAEONFALLActorRegistry().GetAgent[Request.OwnerKey]
            Player := player[Agent]
            Player.IsActive[]
            Profile := AEONFALLPlayerProfiles[Player]
            Profile.UnlockedEntityIds.Find[Request.EntityId]
            Character := Agent.GetFortCharacter[]
            Character.IsActive[]
            set Pending[Request.RequestId] = aeonfall_unlock_delivery_state{
                RequestId := State.RequestId,
                OwnerKey := State.OwnerKey,
                EntityId := State.EntityId,
                SourceId := State.SourceId,
                RemainingSeconds := State.RemainingSeconds,
                AttemptsRemaining := State.AttemptsRemaining,
                PhysicalClaimed := true
            }
        then:
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
        var KeptDeferred:[string]aeonfall_unlock_delivery_state = map{}
        for (Key -> State : Deferred):
            if (State.OwnerKey <> OwnerKey, set KeptDeferred[Key] = State) {}
        set Deferred = KeptDeferred

    TickAll(DeltaSeconds:float)<transacts>:void=
        if (DeltaSeconds <= 0.0):
            return
        TickDeferred()

        var Updated:[string]aeonfall_unlock_delivery_state = map{}
        var Retries:[]aeonfall_unlock_delivery_state = array{}
        var Expired:[]aeonfall_unlock_delivery_state = array{}

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
                    PhysicalClaimed := State.PhysicalClaimed

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
                        PhysicalClaimed := State.PhysicalClaimed

                    if:
                        set Updated[RequestId] = Retry
                    then:
                        set Retries += array{Retry}

                else:
                    set Expired += array{State}

        # Commit retry state before callbacks can resolve it. Never overwrite
        # callback removals with a pre-dispatch snapshot of Pending.
        set Pending = Updated
        for (Retry : Retries):
            Admitted := AEONFALLRuntimeBus.TryRequestUnlockDelivery(aeonfall_unlock_delivery_request{
                RequestId := Retry.RequestId, OwnerKey := Retry.OwnerKey,
                EntityId := Retry.EntityId, SourceId := Retry.SourceId
            })
            AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                EventType := "unlock.delivery_retried", SourceId := Retry.OwnerKey,
                TargetId := Retry.EntityId, ContextId := Retry.RequestId,
                Amount := Retry.AttemptsRemaining
            })
        for (State : Expired):
            AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                EventType := "unlock.delivery_timed_out", SourceId := State.OwnerKey,
                TargetId := State.EntityId, ContextId := State.RequestId
            })

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLUnlockDeliveryServiceSessions:weak_map(session, aeonfall_unlock_delivery_service) = map{}

GetAEONFALLUnlockDeliveryService()<transacts>:aeonfall_unlock_delivery_service=
    CurrentSession := GetSession()
    if (Existing := AEONFALLUnlockDeliveryServiceSessions[CurrentSession]):
        return Existing
    Created := aeonfall_unlock_delivery_service{}
    if (set AEONFALLUnlockDeliveryServiceSessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLUnlockDeliveryService in its session")
