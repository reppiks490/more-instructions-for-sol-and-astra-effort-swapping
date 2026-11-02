using { /Verse.org/Verse }
using { /Verse.org/Simulation }
# Session logical spawn-budget runtime.
# Physical props/entities/NPCs are created by project-bound adapters only after
# this runtime accepts the request. This service owns caps, lifetimes, and cleanup.

aeonfall_spawn_record := class:
    SpawnHandleId:string = ""
    OwnerKey:string = ""
    SpawnId:string = ""
    AbilityId:string = ""
    ContextId:string = ""
    RemainingSeconds:float = 0.0
    Active:logic = true

aeonfall_spawn_runtime := class():

    var NextSpawnNumber:int = 0
    var Records:[string]aeonfall_spawn_record = map{}

    CountActive(
        OwnerKey:string,
        SpawnId:string
    )<transacts>:int=
        var Count:int = 0

        for (HandleId -> Record : Records):
            if:
                Record.OwnerKey = OwnerKey
                Record.SpawnId = SpawnId
                Record.Active?
            then:
                set Count += 1

        Count

    Reserve(
        OwnerKey:string,
        AbilityId:string,
        SpawnId:string,
        ContextId:string,
        LifetimeSeconds:float,
        MaxPerOwner:int
    )<transacts>:?string=
        if:
            OwnerKey <> ""
            AbilityId <> ""
            SpawnId <> ""
            LifetimeSeconds > 0.0
            MaxPerOwner > 0
            CountActive(OwnerKey, SpawnId) < MaxPerOwner
        then:
            set NextSpawnNumber += 1
            HandleId:string =
                "SPAWN-HANDLE::" + OwnerKey + "::" + SpawnId + "::" + "{NextSpawnNumber}"

            Record := aeonfall_spawn_record:
                SpawnHandleId := HandleId
                OwnerKey := OwnerKey
                SpawnId := SpawnId
                AbilityId := AbilityId
                ContextId := ContextId
                RemainingSeconds := LifetimeSeconds
                Active := true

            if:
                set Records[HandleId] = Record
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "spawn.reserved",
                        SourceId := OwnerKey,
                        TargetId := SpawnId,
                        ContextId := HandleId,
                        Amount := CountActive(OwnerKey, SpawnId)
                    }
                )
                option{HandleId}
            else:
                false
        else:
            false

    Release(
        HandleId:string,
        Reason:string
    )<transacts>:logic=
        if:
            Existing := Records[HandleId]
        then:
            var Updated:[string]aeonfall_spawn_record = map{}
            var Valid:logic = true

            for (StoredId -> Record : Records):
                if (StoredId <> HandleId):
                    if (set Updated[StoredId] = Record):
                        set Valid = Valid
                    else:
                        set Valid = false

            if (not Valid?):
                AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                    EventType := "spawn.release_rebuild_failed",
                    ContextId := HandleId
                })
                return false
            set Records = Updated

            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "spawn.released",
                    SourceId := Existing.OwnerKey,
                    TargetId := Existing.SpawnId,
                    ContextId := Reason
                }
            )
            return true

        false

    ClearOwner(
        OwnerKey:string,
        Reason:string
    )<transacts>:void=
        var Updated:[string]aeonfall_spawn_record = map{}
        var Released:[]aeonfall_spawn_record = array{}
        var Valid:logic = true

        for (HandleId -> Record : Records):
            if (Record.OwnerKey <> OwnerKey):
                if (set Updated[HandleId] = Record):
                    set Valid = Valid
                else:
                    set Valid = false
            else:
                set Released += array{Record}

        if (not Valid?):
            AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                EventType := "spawn.owner_clear_rebuild_failed",
                SourceId := OwnerKey
            })
            return
        set Records = Updated
        for (Record : Released):
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "spawn.released",
                    SourceId := OwnerKey,
                    TargetId := Record.SpawnId,
                    ContextId := Reason
                }
            )

    TickAll(DeltaSeconds:float)<transacts>:void=
        if (DeltaSeconds <= 0.0):
            return

        var Updated:[string]aeonfall_spawn_record = map{}
        var Expired:[]aeonfall_spawn_record = array{}
        var Valid:logic = true

        for (HandleId -> Record : Records):
            Remaining:float = Record.RemainingSeconds - DeltaSeconds

            if (Remaining > 0.0):
                Next := aeonfall_spawn_record:
                    SpawnHandleId := Record.SpawnHandleId
                    OwnerKey := Record.OwnerKey
                    SpawnId := Record.SpawnId
                    AbilityId := Record.AbilityId
                    ContextId := Record.ContextId
                    RemainingSeconds := Remaining
                    Active := Record.Active

                if (set Updated[HandleId] = Next):
                    set Valid = Valid
                else:
                    set Valid = false
            else:
                set Expired += array{Record}

        if (not Valid?):
            AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                EventType := "spawn.tick_rebuild_failed"
            })
            return
        set Records = Updated
        for (Record : Expired):
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "spawn.expired",
                    SourceId := Record.OwnerKey,
                    TargetId := Record.SpawnId,
                    ContextId := Record.SpawnHandleId
                }
            )

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLSpawnRuntimeSessions:weak_map(session, aeonfall_spawn_runtime) = map{}

GetAEONFALLSpawnRuntime()<transacts>:aeonfall_spawn_runtime=
    CurrentSession := GetSession()
    if (Existing := AEONFALLSpawnRuntimeSessions[CurrentSession]):
        return Existing
    Created := aeonfall_spawn_runtime{}
    if (set AEONFALLSpawnRuntimeSessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLSpawnRuntime in its session")
