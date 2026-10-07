using { /Verse.org/Simulation }

# Sequential trial state machine.
# Physical arenas, hazards, bosses, item restrictions, and objective devices are
# project-bound; this runtime owns eligibility, ordering, timeout, completion,
# failure, persistence, and the Trial-X Zero Candidate evaluation handoff.

aeonfall_ascension_trial_service := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}
    CandidateManager:aeonfall_zero_candidate_manager = aeonfall_zero_candidate_manager{}

    var StatesByOwner:[string]aeonfall_ascension_trial_runtime_state = map{}

    CanStart(
        Agent:agent,
        Definition:aeonfall_ascension_trial_definition
    )<decides><transacts>:void=
        Profile := ProfileService.GetProfile[Agent]

        not Profile.CompletedTrialIds.Find[Definition.TrialId]

        if (Definition.Index = 1):
            CandidateManager.MeetsPreCandidateRequirements[Agent]
        else:
            Definition.RequiredPreviousTrialId <> ""
            Profile.CompletedTrialIds.Find[Definition.RequiredPreviousTrialId]

        if (Definition.RequiresAxiomHeart?):
            Profile.AxiomHeartCrafted?

    Start(
        Agent:agent,
        TrialId:string
    )<transacts>:logic=
        if:
            OwnerKey := AEONFALLActorRegistry.GetRuntimeKey[Agent]
            Definition := AEONFALLAscensionTrialRegistry.Get[TrialId]
            CanStart[Agent, Definition]
        then:
            if:
                Existing := StatesByOwner[OwnerKey]
                Existing.Active?
            then:
                return false

            State := aeonfall_ascension_trial_runtime_state:
                OwnerKey := OwnerKey
                TrialId := TrialId
                CompletedObjectiveIds := array{}
                RemainingSeconds := Definition.TimeLimitSeconds
                Active := true
                Failed := false

            if:
                set StatesByOwner[OwnerKey] = State
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "ascension_trial.started",
                        SourceId := OwnerKey,
                        TargetId := TrialId,
                        Amount := Definition.Index
                    }
                )
                return true

        false

    GetState(
        OwnerKey:string
    )<decides><transacts>:aeonfall_ascension_trial_runtime_state=
        StatesByOwner[OwnerKey]

    MarkObjectiveComplete(
        Agent:agent,
        ObjectiveId:string
    )<transacts>:logic=
        if:
            OwnerKey := AEONFALLActorRegistry.GetRuntimeKey[Agent]
            Old := StatesByOwner[OwnerKey]
            Old.Active?
            Definition := AEONFALLAscensionTrialRegistry.Get[Old.TrialId]
        then:
            if:
                not Definition.ObjectiveIds.Find[ObjectiveId]
            then:
                return false

            if:
                Old.CompletedObjectiveIds.Find[ObjectiveId]
            then:
                return false

            UpdatedObjectives:[]string =
                Old.CompletedObjectiveIds + array{ObjectiveId}

            Updated := aeonfall_ascension_trial_runtime_state:
                OwnerKey := Old.OwnerKey
                TrialId := Old.TrialId
                CompletedObjectiveIds := UpdatedObjectives
                RemainingSeconds := Old.RemainingSeconds
                Active := true
                Failed := false

            if:
                set StatesByOwner[OwnerKey] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "ascension_trial.objective_completed",
                        SourceId := OwnerKey,
                        TargetId := ObjectiveId,
                        ContextId := Old.TrialId,
                        Amount := UpdatedObjectives.Length
                    }
                )

                if:
                    UpdatedObjectives.Length >= Definition.ObjectiveIds.Length
                then:
                    Completed := Complete(Agent)
                    if (Completed?):
                        Completed = true

                return true

        false

    Complete(Agent:agent)<transacts>:logic=
        if:
            OwnerKey := AEONFALLActorRegistry.GetRuntimeKey[Agent]
            Old := StatesByOwner[OwnerKey]
            Old.Active?
            Definition := AEONFALLAscensionTrialRegistry.Get[Old.TrialId]
            Old.CompletedObjectiveIds.Length >= Definition.ObjectiveIds.Length
        then:
            ProfileService.CompleteTrial(
                Agent,
                Definition.TrialId
            )

            Finished := aeonfall_ascension_trial_runtime_state:
                OwnerKey := OwnerKey
                TrialId := Definition.TrialId
                CompletedObjectiveIds := Old.CompletedObjectiveIds
                RemainingSeconds := Old.RemainingSeconds
                Active := false
                Failed := false

            if:
                set StatesByOwner[OwnerKey] = Finished
            then:
                if (Definition.UnlocksAxiomForge?):
                    AEONFALLRuntimeBus.Emit(
                        aeonfall_runtime_event{
                            EventType := "ascension_trial.axiom_forge_unlocked",
                            SourceId := OwnerKey,
                            TargetId := Definition.TrialId
                        }
                    )

                if (Definition.Index = 10):
                    CandidateManager.EvaluateCandidate(Agent)

                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "ascension_trial.completed",
                        SourceId := OwnerKey,
                        TargetId := Definition.TrialId,
                        Amount := Definition.Index
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
            FailedState := aeonfall_ascension_trial_runtime_state:
                OwnerKey := Old.OwnerKey
                TrialId := Old.TrialId
                CompletedObjectiveIds := Old.CompletedObjectiveIds
                RemainingSeconds := 0.0
                Active := false
                Failed := true

            if:
                set StatesByOwner[OwnerKey] = FailedState
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "ascension_trial.failed",
                        SourceId := OwnerKey,
                        TargetId := Old.TrialId,
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
        if (Failed?):
            Failed = true

        var Updated:[string]aeonfall_ascension_trial_runtime_state = map{}

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

        var Updated:[string]aeonfall_ascension_trial_runtime_state = map{}
        var ExpiredOwners:[]string = array{}

        for (OwnerKey -> State : StatesByOwner):
            if (State.Active?):
                Remaining:float = State.RemainingSeconds - DeltaSeconds

                if (Remaining > 0.0):
                    Next := aeonfall_ascension_trial_runtime_state:
                        OwnerKey := State.OwnerKey
                        TrialId := State.TrialId
                        CompletedObjectiveIds := State.CompletedObjectiveIds
                        RemainingSeconds := Remaining
                        Active := true
                        Failed := false

                    if:
                        set Updated[OwnerKey] = Next
                    then:
                        set Updated = Updated
                else:
                    Expired := aeonfall_ascension_trial_runtime_state:
                        OwnerKey := State.OwnerKey
                        TrialId := State.TrialId
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
            if (Failed?):
                Failed = true

AEONFALLAscensionTrialRuntime:aeonfall_ascension_trial_service =
    aeonfall_ascension_trial_service{}
