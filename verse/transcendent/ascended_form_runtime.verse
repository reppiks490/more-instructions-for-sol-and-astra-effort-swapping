using { /Verse.org/Verse }
using { /Verse.org/Simulation }

# Session-only God / Absolute transformation runtime.
# Permanent eligibility is read from AscensionRank. Active/cooldown state is
# never persisted, and actor context provides the global transformation mutex.

aeonfall_ascended_form_runtime := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}

    var StatesByOwner:[string]aeonfall_ascended_form_runtime_state = map{}

    GetState(OwnerKey:string)<transacts>:aeonfall_ascended_form_runtime_state=
        if (State := StatesByOwner[OwnerKey]):
            State
        else:
            aeonfall_ascended_form_runtime_state{
                OwnerKey := OwnerKey
            }

    CanActivate(
        Agent:agent,
        FormId:string
    )<decides><transacts>:void=
        OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
        Definition := GetAEONFALLAscendedFormRegistry().Get[FormId]
        Profile := ProfileService.GetProfile[Agent]
        State := GetState(OwnerKey)
        Flags := GetAEONFALLActorContextRuntime().GetFlags(OwnerKey)

        Profile.AscensionRank >= Definition.RequiredAscensionRank
        not Flags.TransformationActive?
        State.Phase = aeonfall_ascended_form_phase.Dormant
        State.ActiveRemainingSeconds <= 0.0
        State.ExhaustionRemainingSeconds <= 0.0

    Activate(
        Agent:agent,
        FormId:string
    )<transacts>:logic=
        if:
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
            Definition := GetAEONFALLAscendedFormRegistry().Get[FormId]
            CanActivate[Agent, FormId]
        then:
            Old := GetState(OwnerKey)

            ContextSet := GetAEONFALLActorContextRuntime().SetTransformation(
                OwnerKey,
                true,
                Definition.TransformationId
            )

            if (not ContextSet?):
                return false

            ActiveState := aeonfall_ascended_form_runtime_state:
                OwnerKey := OwnerKey
                FormId := Definition.FormId
                TransformationId := Definition.TransformationId
                Phase := aeonfall_ascended_form_phase.Active
                ActiveRemainingSeconds := Definition.ActiveSeconds
                ExhaustionRemainingSeconds := 0.0
                SessionActivationCount := Old.SessionActivationCount + 1

            if:
                set StatesByOwner[OwnerKey] = ActiveState
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "ascended_form.activated",
                        SourceId := OwnerKey,
                        TargetId := Definition.FormId,
                        ContextId := Definition.TransformationId,
                        Amount := ActiveState.SessionActivationCount
                    }
                )
                return true

            RolledBack := GetAEONFALLActorContextRuntime().SetTransformation(
                OwnerKey,
                false,
                Definition.TransformationId
            )

        false

    StopFormAbilities(
        OwnerKey:string,
        Definition:aeonfall_ascended_form_definition
    )<transacts>:void=
        for (AbilityId : Definition.AbilityIds):
            if:
                State := GetAEONFALLAbilityRuntime().GetState[OwnerKey, AbilityId]
            then:
                if:
                    State.Pending?
                    State.PendingRequestId <> ""
                then:
                    Cancelled := GetAEONFALLActivationCoordinator().CancelPending(
                        OwnerKey,
                        AbilityId,
                        State.PendingRequestId
                    )

                if (State.Active?):
                    Ended := GetAEONFALLActivationCoordinator().EndActivation(
                        OwnerKey,
                        AbilityId
                    )

    EndActive(
        OwnerKey:string,
        Reason:string
    )<transacts>:logic=
        if:
            Old := StatesByOwner[OwnerKey]
            Old.Phase = aeonfall_ascended_form_phase.Active
            Definition := GetAEONFALLAscendedFormRegistry().Get[Old.FormId]
        then:
            StopFormAbilities(
                OwnerKey,
                Definition
            )

            ContextCleared := GetAEONFALLActorContextRuntime().SetTransformation(
                OwnerKey,
                false,
                Definition.TransformationId
            )

            if (not ContextCleared?):
                return false

            Exhausted := aeonfall_ascended_form_runtime_state:
                OwnerKey := OwnerKey
                FormId := Old.FormId
                TransformationId := Definition.TransformationId
                Phase := aeonfall_ascended_form_phase.Exhausted
                ActiveRemainingSeconds := 0.0
                ExhaustionRemainingSeconds := Definition.ExhaustionSeconds
                SessionActivationCount := Old.SessionActivationCount

            if:
                set StatesByOwner[OwnerKey] = Exhausted
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "ascended_form.ended",
                        SourceId := OwnerKey,
                        TargetId := Old.FormId,
                        ContextId := Reason
                    }
                )
                return true

        false

    EndForAgent(
        Agent:agent,
        Reason:string
    )<transacts>:logic=
        if:
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
        then:
            EndActive(
                OwnerKey,
                Reason
            )
        else:
            false

    ClearOwner(OwnerKey:string)<transacts>:void=
        if:
            Existing := StatesByOwner[OwnerKey]
        then:
            if:
                Existing.Phase = aeonfall_ascended_form_phase.Active
                Definition := GetAEONFALLAscendedFormRegistry().Get[Existing.FormId]
            then:
                StopFormAbilities(
                    OwnerKey,
                    Definition
                )

                Cleared := GetAEONFALLActorContextRuntime().SetTransformation(
                    OwnerKey,
                    false,
                    Existing.TransformationId
                )

        var Updated:[string]aeonfall_ascended_form_runtime_state = map{}

        for (StoredOwner -> State : StatesByOwner):
            if (StoredOwner <> OwnerKey):
                if:
                    set Updated[StoredOwner] = State
                then:
                    set Updated = Updated

        set StatesByOwner = Updated

        AEONFALLRuntimeBus.Emit(
            aeonfall_runtime_event{
                EventType := "ascended_form.owner_cleared",
                SourceId := OwnerKey
            }
        )

    TickAll(DeltaSeconds:float)<transacts>:void=
        if (DeltaSeconds <= 0.0):
            return

        var Updated:[string]aeonfall_ascended_form_runtime_state = map{}
        var ExpiredOwners:[]string = array{}

        for (OwnerKey -> State : StatesByOwner):
            if (State.Phase = aeonfall_ascended_form_phase.Active):
                Remaining:float = State.ActiveRemainingSeconds - DeltaSeconds

                if (Remaining > 0.0):
                    Next := aeonfall_ascended_form_runtime_state:
                        OwnerKey := State.OwnerKey
                        FormId := State.FormId
                        TransformationId := State.TransformationId
                        Phase := aeonfall_ascended_form_phase.Active
                        ActiveRemainingSeconds := Remaining
                        ExhaustionRemainingSeconds := 0.0
                        SessionActivationCount := State.SessionActivationCount

                    if:
                        set Updated[OwnerKey] = Next
                    then:
                        set Updated = Updated
                else:
                    Expired := aeonfall_ascended_form_runtime_state:
                        OwnerKey := State.OwnerKey
                        FormId := State.FormId
                        TransformationId := State.TransformationId
                        Phase := aeonfall_ascended_form_phase.Active
                        ActiveRemainingSeconds := 0.0
                        ExhaustionRemainingSeconds := 0.0
                        SessionActivationCount := State.SessionActivationCount

                    if:
                        set Updated[OwnerKey] = Expired
                    then:
                        set Updated = Updated

                    set ExpiredOwners = ExpiredOwners + array{OwnerKey}

            else:
                if (State.Phase = aeonfall_ascended_form_phase.Exhausted):
                    Remaining:float =
                        State.ExhaustionRemainingSeconds - DeltaSeconds

                    if (Remaining > 0.0):
                        Next := aeonfall_ascended_form_runtime_state:
                            OwnerKey := State.OwnerKey
                            FormId := State.FormId
                            TransformationId := State.TransformationId
                            Phase := aeonfall_ascended_form_phase.Exhausted
                            ActiveRemainingSeconds := 0.0
                            ExhaustionRemainingSeconds := Remaining
                            SessionActivationCount := State.SessionActivationCount

                        if:
                            set Updated[OwnerKey] = Next
                        then:
                            set Updated = Updated
                    else:
                        Ready := aeonfall_ascended_form_runtime_state:
                            OwnerKey := State.OwnerKey
                            FormId := ""
                            TransformationId := ""
                            Phase := aeonfall_ascended_form_phase.Dormant
                            ActiveRemainingSeconds := 0.0
                            ExhaustionRemainingSeconds := 0.0
                            SessionActivationCount := State.SessionActivationCount

                        if:
                            set Updated[OwnerKey] = Ready
                        then:
                            set Updated = Updated

                        AEONFALLRuntimeBus.Emit(
                            aeonfall_runtime_event{
                                EventType := "ascended_form.exhaustion_ended",
                                SourceId := OwnerKey,
                                TargetId := State.FormId
                            }
                        )

                else:
                    if:
                        set Updated[OwnerKey] = State
                    then:
                        set Updated = Updated

        set StatesByOwner = Updated

        for (OwnerKey : ExpiredOwners):
            Ended := EndActive(
                OwnerKey,
                "duration_expired"
            )

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLAscendedFormRuntimeSessions:weak_map(session, aeonfall_ascended_form_runtime) = map{}

GetAEONFALLAscendedFormRuntime()<transacts>:aeonfall_ascended_form_runtime=
    CurrentSession := GetSession()
    if (Existing := AEONFALLAscendedFormRuntimeSessions[CurrentSession]):
        return Existing
    Created := aeonfall_ascended_form_runtime{}
    if (set AEONFALLAscendedFormRuntimeSessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLAscendedFormRuntime in its session")
