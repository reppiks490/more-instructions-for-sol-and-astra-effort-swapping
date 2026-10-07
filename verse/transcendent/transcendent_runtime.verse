using { /Verse.org/Simulation }

# Session-only Transcendent Zero transformation runtime.
#
# Persistent profile state only proves that the Choosing was passed.
# Active Authority, remaining transformation time, and exhaustion are never
# written as persistent profile values.

aeonfall_transcendent_runtime := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}
    GateService:aeonfall_ascension_gate_service = aeonfall_ascension_gate_service{}

    var StatesByOwner:[string]aeonfall_transcendent_runtime_state = map{}

    GetState(OwnerKey:string)<transacts>:aeonfall_transcendent_runtime_state=
        if (State := StatesByOwner[OwnerKey]):
            State
        else:
            aeonfall_transcendent_runtime_state{
                OwnerKey := OwnerKey
            }

    CanActivate(
        Agent:agent,
        AuthorityId:string
    )<decides><transacts>:void=
        OwnerKey := AEONFALLActorRegistry.GetRuntimeKey[Agent]
        Definition := AEONFALLTranscendentAuthorityRegistry.Get[AuthorityId]
        Profile := ProfileService.GetProfile[Agent]
        State := GetState(OwnerKey)

        GateService.CanActivateTranscendentState[Agent]
        Profile.TranscendentHistoryCount >= Definition.MinHistoryActivations
        State.Phase = aeonfall_transcendent_phase.Dormant
        State.ActiveRemainingSeconds <= 0.0
        State.ExhaustionRemainingSeconds <= 0.0

    Activate(
        Agent:agent,
        AuthorityId:string
    )<transacts>:logic=
        if:
            OwnerKey := AEONFALLActorRegistry.GetRuntimeKey[Agent]
            Definition := AEONFALLTranscendentAuthorityRegistry.Get[AuthorityId]
            CanActivate[Agent, AuthorityId]
        then:
            Old := GetState(OwnerKey)

            TransformationSet := AEONFALLActorContextRuntime.SetTransformation(
                OwnerKey,
                true,
                "TRANSCENDENT_ZERO::" + AuthorityId
            )

            if (not TransformationSet?):
                return false

            HistoryCommitted := ProfileService.IncrementTranscendentHistory(Agent)

            if (not HistoryCommitted?):
                RolledBack := AEONFALLActorContextRuntime.SetTransformation(
                    OwnerKey,
                    false,
                    "TRANSCENDENT_ZERO::" + AuthorityId
                )
                if (RolledBack?):
                    RolledBack = true
                return false

            ActiveState := aeonfall_transcendent_runtime_state:
                OwnerKey := OwnerKey
                AuthorityId := AuthorityId
                Phase := aeonfall_transcendent_phase.Active
                ActiveRemainingSeconds := Definition.ActiveSeconds
                ExhaustionRemainingSeconds := 0.0
                SessionActivationCount := Old.SessionActivationCount + 1

            if:
                set StatesByOwner[OwnerKey] = ActiveState
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "transcendent.authority_activated",
                        SourceId := OwnerKey,
                        TargetId := AuthorityId,
                        ContextId := Definition.DisplayName,
                        Amount := ActiveState.SessionActivationCount
                    }
                )
                return true

            RolledBack := AEONFALLActorContextRuntime.SetTransformation(
                OwnerKey,
                false,
                "TRANSCENDENT_ZERO::" + AuthorityId
            )
            if (RolledBack?):
                RolledBack = true

        false

    StopAuthorityAbilities(
        OwnerKey:string,
        Definition:aeonfall_transcendent_authority_definition
    )<transacts>:void=
        for (AbilityId : Definition.AbilityIds):
            if:
                State := AEONFALLAbilityRuntime.GetState[OwnerKey, AbilityId]
            then:
                if:
                    State.Pending?
                    State.PendingRequestId <> ""
                then:
                    Cancelled := AEONFALLActivationCoordinator.CancelPending(
                        OwnerKey,
                        AbilityId,
                        State.PendingRequestId
                    )
                    if (Cancelled?):
                        Cancelled = true

                if (State.Active?):
                    Ended := AEONFALLActivationCoordinator.EndActivation(
                        OwnerKey,
                        AbilityId
                    )
                    if (Ended?):
                        Ended = true

    EndActive(
        OwnerKey:string,
        Reason:string
    )<transacts>:logic=
        if:
            Old := StatesByOwner[OwnerKey]
            Old.Phase = aeonfall_transcendent_phase.Active
            Definition := AEONFALLTranscendentAuthorityRegistry.Get[Old.AuthorityId]
        then:
            StopAuthorityAbilities(
                OwnerKey,
                Definition
            )

            TransformationCleared := AEONFALLActorContextRuntime.SetTransformation(
                OwnerKey,
                false,
                "TRANSCENDENT_ZERO::" + Old.AuthorityId
            )

            if (not TransformationCleared?):
                return false

            Exhausted := aeonfall_transcendent_runtime_state:
                OwnerKey := OwnerKey
                AuthorityId := Old.AuthorityId
                Phase := aeonfall_transcendent_phase.Exhausted
                ActiveRemainingSeconds := 0.0
                ExhaustionRemainingSeconds := Definition.ExhaustionSeconds
                SessionActivationCount := Old.SessionActivationCount

            if:
                set StatesByOwner[OwnerKey] = Exhausted
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "transcendent.authority_ended",
                        SourceId := OwnerKey,
                        TargetId := Old.AuthorityId,
                        ContextId := Reason
                    }
                )
                return true

        false

    ClearOwner(OwnerKey:string)<transacts>:void=
        if:
            Existing := StatesByOwner[OwnerKey]
        then:
            if:
                Existing.Phase = aeonfall_transcendent_phase.Active
                Definition := AEONFALLTranscendentAuthorityRegistry.Get[Existing.AuthorityId]
            then:
                StopAuthorityAbilities(
                    OwnerKey,
                    Definition
                )

                Cleared := AEONFALLActorContextRuntime.SetTransformation(
                    OwnerKey,
                    false,
                    "TRANSCENDENT_ZERO::" + Existing.AuthorityId
                )
                if (Cleared?):
                    Cleared = true

        var Updated:[string]aeonfall_transcendent_runtime_state = map{}

        for (StoredOwner -> State : StatesByOwner):
            if (StoredOwner <> OwnerKey):
                if:
                    set Updated[StoredOwner] = State
                then:
                    set Updated = Updated

        set StatesByOwner = Updated

        AEONFALLRuntimeBus.Emit(
            aeonfall_runtime_event{
                EventType := "transcendent.owner_cleared",
                SourceId := OwnerKey
            }
        )

    TickAll(DeltaSeconds:float)<transacts>:void=
        if (DeltaSeconds <= 0.0):
            return

        var Updated:[string]aeonfall_transcendent_runtime_state = map{}
        var ExpiredActiveOwners:[]string = array{}

        for (OwnerKey -> State : StatesByOwner):
            if (State.Phase = aeonfall_transcendent_phase.Active):
                Remaining:float = State.ActiveRemainingSeconds - DeltaSeconds

                if (Remaining > 0.0):
                    Next := aeonfall_transcendent_runtime_state:
                        OwnerKey := State.OwnerKey
                        AuthorityId := State.AuthorityId
                        Phase := aeonfall_transcendent_phase.Active
                        ActiveRemainingSeconds := Remaining
                        ExhaustionRemainingSeconds := 0.0
                        SessionActivationCount := State.SessionActivationCount

                    if:
                        set Updated[OwnerKey] = Next
                    then:
                        set Updated = Updated
                else:
                    # Keep the active state present until EndActive performs
                    # adapter cancellation, context teardown, and exhaustion.
                    Expired := aeonfall_transcendent_runtime_state:
                        OwnerKey := State.OwnerKey
                        AuthorityId := State.AuthorityId
                        Phase := aeonfall_transcendent_phase.Active
                        ActiveRemainingSeconds := 0.0
                        ExhaustionRemainingSeconds := 0.0
                        SessionActivationCount := State.SessionActivationCount

                    if:
                        set Updated[OwnerKey] = Expired
                    then:
                        set Updated = Updated

                    set ExpiredActiveOwners =
                        ExpiredActiveOwners + array{OwnerKey}

            else:
                if (State.Phase = aeonfall_transcendent_phase.Exhausted):
                    Remaining:float =
                        State.ExhaustionRemainingSeconds - DeltaSeconds

                    if (Remaining > 0.0):
                        Next := aeonfall_transcendent_runtime_state:
                            OwnerKey := State.OwnerKey
                            AuthorityId := State.AuthorityId
                            Phase := aeonfall_transcendent_phase.Exhausted
                            ActiveRemainingSeconds := 0.0
                            ExhaustionRemainingSeconds := Remaining
                            SessionActivationCount := State.SessionActivationCount

                        if:
                            set Updated[OwnerKey] = Next
                        then:
                            set Updated = Updated
                    else:
                        Ready := aeonfall_transcendent_runtime_state:
                            OwnerKey := State.OwnerKey
                            AuthorityId := ""
                            Phase := aeonfall_transcendent_phase.Dormant
                            ActiveRemainingSeconds := 0.0
                            ExhaustionRemainingSeconds := 0.0
                            SessionActivationCount := State.SessionActivationCount

                        if:
                            set Updated[OwnerKey] = Ready
                        then:
                            set Updated = Updated

                        AEONFALLRuntimeBus.Emit(
                            aeonfall_runtime_event{
                                EventType := "transcendent.exhaustion_ended",
                                SourceId := OwnerKey,
                                TargetId := State.AuthorityId
                            }
                        )

                else:
                    if:
                        set Updated[OwnerKey] = State
                    then:
                        set Updated = Updated

        set StatesByOwner = Updated

        for (OwnerKey : ExpiredActiveOwners):
            Ended := EndActive(
                OwnerKey,
                "duration_expired"
            )
            if (Ended?):
                Ended = true

AEONFALLTranscendentRuntime:aeonfall_transcendent_runtime =
    aeonfall_transcendent_runtime{}
