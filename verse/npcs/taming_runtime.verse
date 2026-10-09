using { /Verse.org/Verse }
using { /Verse.org/Simulation }

# Species-specific taming challenge runtime.
# Project-bound NPC behaviors/devices report challenge actions; this service
# verifies the authored sequence and owns the Crown Bond handoff.

aeonfall_taming_registry := class():

    var Definitions:[string]aeonfall_taming_definition = map{}

    Register(Definition:aeonfall_taming_definition)<transacts>:logic=
        if:
            Definition.SpeciesId <> ""
            Definition.Steps.Length > 0
            Definition.MaxChallengeSeconds > 0.0
            set Definitions[Definition.SpeciesId] = Definition
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "taming.definition_registered",
                    SourceId := Definition.SpeciesId
                }
            )
            return true

        false

    Get(SpeciesId:string)<decides><transacts>:aeonfall_taming_definition=
        Definitions[SpeciesId]

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLTamingRegistrySessions:weak_map(session, aeonfall_taming_registry) = map{}

GetAEONFALLTamingRegistry()<transacts>:aeonfall_taming_registry=
    CurrentSession := GetSession()
    if (Existing := AEONFALLTamingRegistrySessions[CurrentSession]):
        return Existing
    Created := aeonfall_taming_registry{}
    if (set AEONFALLTamingRegistrySessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLTamingRegistry in its session")

aeonfall_taming_runtime := class():

    var Challenges:[string]aeonfall_taming_challenge_state = map{}

    GetChallenge(TargetKey:string)<decides><transacts>:aeonfall_taming_challenge_state=
        Challenges[TargetKey]

    StartChallenge(
        RequestId:string,
        OwnerKey:string,
        TargetKey:string,
        SpeciesId:string
    )<transacts>:logic=
        if:
            RequestId <> ""
            OwnerKey <> ""
            TargetKey <> ""
            Definition := GetAEONFALLTamingRegistry().Get[SpeciesId]
            CanonicalId := GetAEONFALLActorRegistry().GetCanonicalId[TargetKey]
            CanonicalId = SpeciesId
            GetAEONFALLCompanionRuntime().CanBind(OwnerKey, TargetKey)?
        then:
            if:
                Existing := Challenges[TargetKey]
                Existing.Active?
            then:
                return false
            else:
                Challenge := aeonfall_taming_challenge_state:
                    RequestId := RequestId
                    OwnerKey := OwnerKey
                    TargetKey := TargetKey
                    SpeciesId := SpeciesId
                    AbilityId := Definition.AbilityId
                    CurrentStepIndex := 0
                    Active := true
                    Completed := false
                    Failed := false

                if:
                    set Challenges[TargetKey] = Challenge
                then:
                    AEONFALLRuntimeBus.Emit(
                        aeonfall_runtime_event{
                            EventType := "taming.challenge_started",
                            SourceId := OwnerKey,
                            TargetId := TargetKey,
                            ContextId := SpeciesId,
                            Amount := Definition.Steps.Length
                        }
                    )
                    return true

        false

    WatchTimeout(
        TargetKey:string,
        RequestId:string,
        DurationSeconds:float
    )<suspends>:void=
        if (DurationSeconds <= 0.0):
            return

        Sleep(DurationSeconds)

        if:
            Challenge := Challenges[TargetKey]
            Challenge.Active?
            Challenge.RequestId = RequestId
        then:
            TimedOut := FailChallenge(
                TargetKey,
                "challenge_timeout"
            )

    CompleteStep(
        OwnerKey:string,
        TargetKey:string,
        Step:aeonfall_taming_step_kind
    )<transacts>:logic=
        if:
            Old := Challenges[TargetKey]
            Old.Active?
            Old.OwnerKey = OwnerKey
            Definition := GetAEONFALLTamingRegistry().Get[Old.SpeciesId]
            ExpectedStep := Definition.Steps[Old.CurrentStepIndex]
            ExpectedStep = Step
        then:
            NextIndex:int = Old.CurrentStepIndex + 1

            if (NextIndex >= Definition.Steps.Length):
                return CompleteChallenge(TargetKey)

            Updated := aeonfall_taming_challenge_state:
                RequestId := Old.RequestId
                OwnerKey := Old.OwnerKey
                TargetKey := Old.TargetKey
                SpeciesId := Old.SpeciesId
                AbilityId := Old.AbilityId
                CurrentStepIndex := NextIndex
                Active := true
                Completed := false
                Failed := false

            if:
                set Challenges[TargetKey] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "taming.step_completed",
                        SourceId := OwnerKey,
                        TargetId := TargetKey,
                        ContextId := Old.SpeciesId,
                        Amount := NextIndex
                    }
                )
                return true

        false

    CompleteChallenge(TargetKey:string)<transacts>:logic=
        if:
            Old := Challenges[TargetKey]
            Old.Active?
            Definition := GetAEONFALLTamingRegistry().Get[Old.SpeciesId]
            GetAEONFALLCompanionRuntime().CanBind(Old.OwnerKey, TargetKey)?
        then:
            BondReservationId:string = "BOND::" + TargetKey
            Transferred := GetAEONFALLClassRuntime().TransferReservation(
                Old.RequestId,
                BondReservationId
            )

            if (Transferred?):
                Bound := GetAEONFALLCompanionRuntime().BindTamed(
                    Old.OwnerKey,
                    TargetKey,
                    Old.SpeciesId,
                    BondReservationId,
                    Old.AbilityId
                )

                if (Bound?):
                    # The challenge ability can close while its class-resource
                    # reservation survives under the companion bond ID.
                    Ended := GetAEONFALLAbilityRuntime().EndActivation(
                        Old.OwnerKey,
                        Old.AbilityId
                    )

                    Removed := RemoveChallenge(TargetKey)
                    if (Removed?):
                        AEONFALLRuntimeBus.Emit(
                            aeonfall_runtime_event{
                                EventType := Definition.SuccessEventId,
                                SourceId := Old.OwnerKey,
                                TargetId := TargetKey,
                                ContextId := Old.SpeciesId
                            }
                        )
                        return true

                RolledBack := GetAEONFALLClassRuntime().TransferReservation(
                    BondReservationId,
                    Old.RequestId
                )

            return FailChallenge(
                TargetKey,
                "bond_transfer_or_companion_bind_failed"
            )

        false

    FailChallenge(
        TargetKey:string,
        Reason:string
    )<transacts>:logic=
        if:
            Old := Challenges[TargetKey]
            Old.Active?
            Definition := GetAEONFALLTamingRegistry().Get[Old.SpeciesId]
        then:
            Ended := GetAEONFALLActivationCoordinator().EndActivation(
                Old.OwnerKey,
                Old.AbilityId
            )

            RemovedMark := GetAEONFALLStatusRuntime().RemoveStatus(
                TargetKey,
                "STS-005"
            )

            Removed := RemoveChallenge(TargetKey)
            if (Removed?):
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := Definition.FailureEventId,
                        SourceId := Old.OwnerKey,
                        TargetId := TargetKey,
                        ContextId := Reason
                    }
                )
                return true

        false

    RemoveChallenge(TargetKey:string)<transacts>:logic=
        if:
            Existing := Challenges[TargetKey]
        then:
            var Updated:[string]aeonfall_taming_challenge_state = map{}
            var Valid:logic = true

            for (StoredTargetKey -> Challenge : Challenges):
                if (StoredTargetKey <> TargetKey):
                    if:
                        set Updated[StoredTargetKey] = Challenge
                    then:
                        set Valid = Valid
                    else:
                        set Valid = false

            if (Valid?):
                set Challenges = Updated
                return true

        false

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLTamingRuntimeSessions:weak_map(session, aeonfall_taming_runtime) = map{}

GetAEONFALLTamingRuntime()<transacts>:aeonfall_taming_runtime=
    CurrentSession := GetSession()
    if (Existing := AEONFALLTamingRuntimeSessions[CurrentSession]):
        return Existing
    Created := aeonfall_taming_runtime{}
    if (set AEONFALLTamingRuntimeSessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLTamingRuntime in its session")
