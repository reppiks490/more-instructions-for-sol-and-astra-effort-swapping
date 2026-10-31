using { /Verse.org/Verse }
using { /Verse.org/Simulation }

aeonfall_actor_context_state := class:
    OwnerKey:string = ""
    EncounterDepth:int = 0
    TransformationActive:logic = false
    EncounterId:string = ""
    TransformationId:string = ""

# Session context gates used by the ability runtime.
# EncounterDepth handles nested/overlapping encounter volumes safely.
aeonfall_actor_context_runtime := class():

    var States:[string]aeonfall_actor_context_state = map{}

    GetState(OwnerKey:string)<transacts>:aeonfall_actor_context_state=
        if (State := States[OwnerKey]):
            State
        else:
            aeonfall_actor_context_state{
                OwnerKey := OwnerKey
            }

    GetFlags(OwnerKey:string)<transacts>:aeonfall_ability_context_flags=
        State := GetState(OwnerKey)

        aeonfall_ability_context_flags:
            EncounterActive := State.EncounterDepth > 0
            TransformationActive := State.TransformationActive
            TransformationId := State.TransformationId

    EnterEncounter(
        Agent:agent,
        EncounterId:string
    )<transacts>:logic=
        if:
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
        then:
            Old := GetState(OwnerKey)
            Updated := aeonfall_actor_context_state:
                OwnerKey := OwnerKey
                EncounterDepth := Old.EncounterDepth + 1
                TransformationActive := Old.TransformationActive
                EncounterId := EncounterId
                TransformationId := Old.TransformationId

            if:
                set States[OwnerKey] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "context.encounter_entered",
                        SourceId := OwnerKey,
                        ContextId := EncounterId,
                        Amount := Updated.EncounterDepth
                    }
                )
                return true

        false

    ExitEncounter(
        Agent:agent,
        EncounterId:string
    )<transacts>:logic=
        if:
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
        then:
            Old := GetState(OwnerKey)
            NextDepth:int =
                if (Old.EncounterDepth > 0):
                    Old.EncounterDepth - 1
                else:
                    0

            Updated := aeonfall_actor_context_state:
                OwnerKey := OwnerKey
                EncounterDepth := NextDepth
                TransformationActive := Old.TransformationActive
                EncounterId :=
                    if (NextDepth > 0):
                        Old.EncounterId
                    else:
                        ""
                TransformationId := Old.TransformationId

            if:
                set States[OwnerKey] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "context.encounter_exited",
                        SourceId := OwnerKey,
                        ContextId := EncounterId,
                        Amount := NextDepth
                    }
                )
                return true

        false

    SetTransformation(
        OwnerKey:string,
        Active:logic,
        TransformationId:string
    )<transacts>:logic=
        if:
            GetAEONFALLActorRegistry().IsRegistered[OwnerKey]
        then:
            Old := GetState(OwnerKey)

            Updated := aeonfall_actor_context_state:
                OwnerKey := OwnerKey
                EncounterDepth := Old.EncounterDepth
                TransformationActive := Active
                EncounterId := Old.EncounterId
                TransformationId :=
                    if (Active?):
                        TransformationId
                    else:
                        ""

            if:
                set States[OwnerKey] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType :=
                            if (Active?):
                                "context.transformation_started"
                            else:
                                "context.transformation_ended",
                        SourceId := OwnerKey,
                        ContextId := TransformationId
                    }
                )
                return true

        false

    Clear(OwnerKey:string)<transacts>:void=
        var Updated:[string]aeonfall_actor_context_state = map{}

        for (StoredOwnerKey -> State : States):
            if (StoredOwnerKey <> OwnerKey):
                if:
                    set Updated[StoredOwnerKey] = State
                then:
                    set Updated = Updated

        set States = Updated

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLActorContextRuntimeSessions:weak_map(session, aeonfall_actor_context_runtime) = map{}

GetAEONFALLActorContextRuntime()<transacts>:aeonfall_actor_context_runtime=
    CurrentSession := GetSession()
    if (Existing := AEONFALLActorContextRuntimeSessions[CurrentSession]):
        return Existing
    Created := aeonfall_actor_context_runtime{}
    if (set AEONFALLActorContextRuntimeSessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLActorContextRuntime in its session")
