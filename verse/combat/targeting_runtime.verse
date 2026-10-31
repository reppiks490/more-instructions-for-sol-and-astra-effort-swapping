using { /Verse.org/Verse }
using { /Verse.org/Simulation }

aeonfall_target_selection := class:
    OwnerKey:string = ""
    TargetKey:string = ""
    ContextId:string = ""
    RemainingSeconds:float = 0.0

# Session target registry for dynamic actor targets.
# Project-bound selectors decide WHAT may be selected. This service only stores
# the resulting canonical runtime target and expires it safely.
aeonfall_targeting_runtime := class():

    var Selections:[string]aeonfall_target_selection = map{}

    SetActorTarget(
        Owner:agent,
        Target:agent,
        ContextId:string,
        DurationSeconds:float
    )<transacts>:logic=
        if:
            DurationSeconds > 0.0
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Owner]
            TargetKey := GetAEONFALLActorRegistry().GetRuntimeKey[Target]
            OwnerKey <> TargetKey
        then:
            Selection := aeonfall_target_selection:
                OwnerKey := OwnerKey
                TargetKey := TargetKey
                ContextId := ContextId
                RemainingSeconds := DurationSeconds

            if:
                set Selections[OwnerKey] = Selection
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "target.selected",
                        SourceId := OwnerKey,
                        TargetId := TargetKey,
                        ContextId := ContextId
                    }
                )
                return true

        false

    SetRuntimeTarget(
        OwnerKey:string,
        TargetKey:string,
        ContextId:string,
        DurationSeconds:float
    )<transacts>:logic=
        if:
            DurationSeconds > 0.0
            OwnerKey <> TargetKey
            GetAEONFALLActorRegistry().IsRegistered[OwnerKey]
            GetAEONFALLActorRegistry().IsRegistered[TargetKey]
        then:
            Selection := aeonfall_target_selection:
                OwnerKey := OwnerKey
                TargetKey := TargetKey
                ContextId := ContextId
                RemainingSeconds := DurationSeconds

            if:
                set Selections[OwnerKey] = Selection
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "target.selected",
                        SourceId := OwnerKey,
                        TargetId := TargetKey,
                        ContextId := ContextId
                    }
                )
                return true

        false

    GetSelection(OwnerKey:string)<decides><transacts>:aeonfall_target_selection=
        Selection := Selections[OwnerKey]
        Selection.RemainingSeconds > 0.0
        GetAEONFALLActorRegistry().IsRegistered[Selection.TargetKey]
        Selection

    Clear(OwnerKey:string)<transacts>:logic=
        if:
            Existing := Selections[OwnerKey]
        then:
            var Updated:[string]aeonfall_target_selection = map{}
            var Valid:logic = true

            for (StoredOwnerKey -> Selection : Selections):
                if (StoredOwnerKey <> OwnerKey):
                    if:
                        set Updated[StoredOwnerKey] = Selection
                    then:
                        set Valid = Valid
                    else:
                        set Valid = false

            if (Valid?):
                set Selections = Updated
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "target.cleared",
                        SourceId := OwnerKey,
                        TargetId := Existing.TargetKey,
                        ContextId := Existing.ContextId
                    }
                )
                return true

        false

    TickAll(DeltaSeconds:float)<transacts>:void=
        if (DeltaSeconds <= 0.0):
            return

        var Updated:[string]aeonfall_target_selection = map{}

        for (OwnerKey -> Selection : Selections):
            Remaining:float = Selection.RemainingSeconds - DeltaSeconds

            if:
                Remaining > 0.0
                GetAEONFALLActorRegistry().IsRegistered[Selection.TargetKey]
            then:
                Next := aeonfall_target_selection:
                    OwnerKey := Selection.OwnerKey
                    TargetKey := Selection.TargetKey
                    ContextId := Selection.ContextId
                    RemainingSeconds := Remaining

                if:
                    set Updated[OwnerKey] = Next
                then:
                    set Updated = Updated
            else:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "target.expired",
                        SourceId := OwnerKey,
                        TargetId := Selection.TargetKey,
                        ContextId := Selection.ContextId
                    }
                )

        set Selections = Updated

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLTargetingRuntimeSessions:weak_map(session, aeonfall_targeting_runtime) = map{}

GetAEONFALLTargetingRuntime()<transacts>:aeonfall_targeting_runtime=
    CurrentSession := GetSession()
    if (Existing := AEONFALLTargetingRuntimeSessions[CurrentSession]):
        return Existing
    Created := aeonfall_targeting_runtime{}
    if (set AEONFALLTargetingRuntimeSessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLTargetingRuntime in its session")
