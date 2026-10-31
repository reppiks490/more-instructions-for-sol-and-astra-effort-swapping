using { /Verse.org/Verse }
using { /Verse.org/Simulation }

aeonfall_choosing_service := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}
    GateService:aeonfall_ascension_gate_service = aeonfall_ascension_gate_service{}

    Definition:aeonfall_choosing_definition = aeonfall_choosing_definition{
        ChoosingId := "CHOOSING-001",
        ObjectiveIds := array{
            "OBJ-CHOOSING-RESTRAINT",
            "OBJ-CHOOSING-PRESERVATION",
            "OBJ-CHOOSING-CONSEQUENCE",
            "OBJ-CHOOSING-TRUTH",
            "OBJ-CHOOSING-FINAL-ANSWER"
        },
        TimeLimitSeconds := 3600.0
    }

    var StatesByOwner:[string]aeonfall_choosing_runtime_state = map{}

    Start(Agent:agent)<transacts>:logic=
        if:
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
            GateService.CanEnterChoosing[Agent]
        then:
            if:
                Existing := StatesByOwner[OwnerKey]
                Existing.Active?
            then:
                return false

            State := aeonfall_choosing_runtime_state:
                OwnerKey := OwnerKey
                ChoosingId := Definition.ChoosingId
                CompletedObjectiveIds := array{}
                RemainingSeconds := Definition.TimeLimitSeconds
                Active := true
                Failed := false

            if:
                set StatesByOwner[OwnerKey] = State
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "choosing.started",
                        SourceId := OwnerKey,
                        TargetId := Definition.ChoosingId
                    }
                )
                return true

        false

    MarkObjectiveComplete(
        Agent:agent,
        ObjectiveId:string
    )<transacts>:logic=
        if:
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
            Old := StatesByOwner[OwnerKey]
            Old.Active?
            Definition.ObjectiveIds.Find[ObjectiveId]
        then:
            if:
                Old.CompletedObjectiveIds.Find[ObjectiveId]
            then:
                return false

            UpdatedObjectives:[]string =
                Old.CompletedObjectiveIds + array{ObjectiveId}

            Updated := aeonfall_choosing_runtime_state:
                OwnerKey := Old.OwnerKey
                ChoosingId := Old.ChoosingId
                CompletedObjectiveIds := UpdatedObjectives
                RemainingSeconds := Old.RemainingSeconds
                Active := true
                Failed := false

            if:
                set StatesByOwner[OwnerKey] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "choosing.objective_completed",
                        SourceId := OwnerKey,
                        TargetId := ObjectiveId,
                        Amount := UpdatedObjectives.Length
                    }
                )

                if:
                    UpdatedObjectives.Length >= Definition.ObjectiveIds.Length
                then:
                    Completed := Complete(Agent)

                return true

        false

    Complete(Agent:agent)<transacts>:logic=
        if:
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
            Old := StatesByOwner[OwnerKey]
            Old.Active?
            Old.CompletedObjectiveIds.Length >= Definition.ObjectiveIds.Length
        then:
            Committed := ProfileService.CommitChoosingSuccess(Agent)

            if (not Committed?):
                return false

            Finished := aeonfall_choosing_runtime_state:
                OwnerKey := Old.OwnerKey
                ChoosingId := Old.ChoosingId
                CompletedObjectiveIds := Old.CompletedObjectiveIds
                RemainingSeconds := Old.RemainingSeconds
                Active := false
                Failed := false

            if:
                set StatesByOwner[OwnerKey] = Finished
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "choosing.completed",
                        SourceId := OwnerKey,
                        TargetId := Definition.ChoosingId
                    }
                )
                return true

        false

    FailOwner(
        OwnerKey:string,
        Reason:string
    )<transacts>:logic=
        if:
            Old := StatesByOwner[OwnerKey]
            Old.Active?
        then:
            FailedState := aeonfall_choosing_runtime_state:
                OwnerKey := Old.OwnerKey
                ChoosingId := Old.ChoosingId
                CompletedObjectiveIds := Old.CompletedObjectiveIds
                RemainingSeconds := 0.0
                Active := false
                Failed := true

            if:
                set StatesByOwner[OwnerKey] = FailedState
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "choosing.failed",
                        SourceId := OwnerKey,
                        TargetId := Old.ChoosingId,
                        ContextId := Reason
                    }
                )
                return true

        false

    ClearOwner(OwnerKey:string)<transacts>:void=
        Failed := FailOwner(
            OwnerKey,
            "owner_unregistered"
        )

        var Updated:[string]aeonfall_choosing_runtime_state = map{}
        for (StoredOwner -> State : StatesByOwner):
            if (StoredOwner <> OwnerKey):
                if:
                    set Updated[StoredOwner] = State
                then:
                    set Updated = Updated
        set StatesByOwner = Updated

    TickAll(DeltaSeconds:float)<transacts>:void=
        if (DeltaSeconds <= 0.0):
            return

        var Updated:[string]aeonfall_choosing_runtime_state = map{}
        var ExpiredOwners:[]string = array{}

        for (OwnerKey -> State : StatesByOwner):
            if (State.Active?):
                Remaining:float = State.RemainingSeconds - DeltaSeconds

                if (Remaining > 0.0):
                    Next := aeonfall_choosing_runtime_state:
                        OwnerKey := State.OwnerKey
                        ChoosingId := State.ChoosingId
                        CompletedObjectiveIds := State.CompletedObjectiveIds
                        RemainingSeconds := Remaining
                        Active := true
                        Failed := false
                    if:
                        set Updated[OwnerKey] = Next
                    then:
                        set Updated = Updated
                else:
                    Expired := aeonfall_choosing_runtime_state:
                        OwnerKey := State.OwnerKey
                        ChoosingId := State.ChoosingId
                        CompletedObjectiveIds := State.CompletedObjectiveIds
                        RemainingSeconds := 0.0
                        Active := true
                        Failed := false
                    if:
                        set Updated[OwnerKey] = Expired
                    then:
                        set Updated = Updated
                    set ExpiredOwners = ExpiredOwners + array{OwnerKey}
            else:
                if:
                    set Updated[OwnerKey] = State
                then:
                    set Updated = Updated

        set StatesByOwner = Updated

        for (OwnerKey : ExpiredOwners):
            Failed := FailOwner(
                OwnerKey,
                "time_limit"
            )

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLChoosingRuntimeSessions:weak_map(session, aeonfall_choosing_service) = map{}

GetAEONFALLChoosingRuntime()<transacts>:aeonfall_choosing_service=
    CurrentSession := GetSession()
    if (Existing := AEONFALLChoosingRuntimeSessions[CurrentSession]):
        return Existing
    Created := aeonfall_choosing_service{}
    if (set AEONFALLChoosingRuntimeSessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLChoosingRuntime in its session")
