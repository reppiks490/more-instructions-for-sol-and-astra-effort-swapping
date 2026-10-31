using { /Verse.org/Verse }
using { /Verse.org/Simulation }
# Dynamic invasion state machine.
# Physical spawning is requested through runtime events and remains the job of
# project-bound spawn adapters / NPC Spawners.

aeonfall_invasion_runtime := class():

    var States:[string]aeonfall_invasion_runtime_state = map{}

    RequestWave(
        Definition:aeonfall_invasion_definition,
        WaveIndex:int
    )<transacts>:void=
        if:
            Wave := Definition.WaveSpawnGroupIds[WaveIndex]
        then:
            for (SpawnGroupId : Wave):
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "invasion.spawn_group_requested",
                        SourceId := Definition.InvasionId,
                        TargetId := SpawnGroupId,
                        ContextId := Definition.RegionId,
                        Amount := WaveIndex
                    }
                )

    ReleaseSpawnGroup(
        InvasionId:string,
        RegionId:string,
        SpawnGroupId:string,
        WaveIndex:int
    )<transacts>:void=
        AEONFALLRuntimeBus.Emit(
            aeonfall_runtime_event{
                EventType := "invasion.spawn_group_released",
                SourceId := InvasionId,
                TargetId := SpawnGroupId,
                ContextId := RegionId,
                Amount := WaveIndex
            }
        )

    TransitionWave(
        Definition:aeonfall_invasion_definition,
        OldWaveIndex:int,
        NewWaveIndex:int
    )<transacts>:void=
        if:
            OldWave := Definition.WaveSpawnGroupIds[OldWaveIndex]
            NewWave := Definition.WaveSpawnGroupIds[NewWaveIndex]
        then:
            for (OldGroupId : OldWave):
                if (not NewWave.Find[OldGroupId]):
                    ReleaseSpawnGroup(
                        Definition.InvasionId,
                        Definition.RegionId,
                        OldGroupId,
                        OldWaveIndex
                    )

            for (NewGroupId : NewWave):
                if (not OldWave.Find[NewGroupId]):
                    AEONFALLRuntimeBus.Emit(
                        aeonfall_runtime_event{
                            EventType := "invasion.spawn_group_requested",
                            SourceId := Definition.InvasionId,
                            TargetId := NewGroupId,
                            ContextId := Definition.RegionId,
                            Amount := NewWaveIndex
                        }
                    )

    Start(InvasionId:string)<transacts>:logic=
        if:
            Definition := GetAEONFALLInvasionRegistry().Get[InvasionId]
            RegionState := GetAEONFALLRegionRuntime().GetState[Definition.RegionId]
            RegionState.HostilityTier >= Definition.MinHostilityTier
        then:
            if:
                Existing := States[InvasionId]
                Existing.Active?
            then:
                return false

            Initial := aeonfall_invasion_runtime_state:
                InvasionId := InvasionId
                RegionId := Definition.RegionId
                CurrentWaveIndex := 0
                CompletedObjectiveIds := array{}
                RemainingSeconds := Definition.DurationSeconds
                Active := true
                Completed := false
                Failed := false

            if:
                set States[InvasionId] = Initial
            then:
                Added := GetAEONFALLRegionRuntime().AddEvent(
                    Definition.RegionId,
                    InvasionId
                )

                AEONFALLRegionalEscalation.ReconcileRegion(
                    Definition.RegionId
                )

                RequestWave(Definition, 0)

                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "invasion.started",
                        SourceId := InvasionId,
                        TargetId := Definition.RegionId,
                        ContextId := Definition.AggressorId,
                        Amount := Definition.MaxConcurrentAi
                    }
                )
                return true

        false

    GetState(InvasionId:string)<decides><transacts>:aeonfall_invasion_runtime_state=
        States[InvasionId]

    MarkObjectiveComplete(
        InvasionId:string,
        ObjectiveId:string
    )<transacts>:logic=
        if:
            Old := States[InvasionId]
            Old.Active?
        then:
            if:
                Old.CompletedObjectiveIds.Find[ObjectiveId]
            then:
                return false

            Updated := aeonfall_invasion_runtime_state:
                InvasionId := Old.InvasionId
                RegionId := Old.RegionId
                CurrentWaveIndex := Old.CurrentWaveIndex
                CompletedObjectiveIds := Old.CompletedObjectiveIds + array{ObjectiveId}
                RemainingSeconds := Old.RemainingSeconds
                Active := true
                Completed := false
                Failed := false

            if:
                set States[InvasionId] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "invasion.objective_completed",
                        SourceId := InvasionId,
                        TargetId := ObjectiveId,
                        ContextId := Old.RegionId
                    }
                )
                return true

        false

    AdvanceWave(InvasionId:string)<transacts>:logic=
        if:
            Definition := GetAEONFALLInvasionRegistry().Get[InvasionId]
            Old := States[InvasionId]
            Old.Active?
        then:
            NextIndex:int = Old.CurrentWaveIndex + 1

            if (NextIndex >= Definition.WaveSpawnGroupIds.Length):
                return Complete(InvasionId)

            Updated := aeonfall_invasion_runtime_state:
                InvasionId := Old.InvasionId
                RegionId := Old.RegionId
                CurrentWaveIndex := NextIndex
                CompletedObjectiveIds := Old.CompletedObjectiveIds
                RemainingSeconds := Old.RemainingSeconds
                Active := true
                Completed := false
                Failed := false

            if:
                set States[InvasionId] = Updated
            then:
                TransitionWave(
                    Definition,
                    Old.CurrentWaveIndex,
                    NextIndex
                )

                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "invasion.wave_advanced",
                        SourceId := InvasionId,
                        TargetId := Old.RegionId,
                        Amount := NextIndex
                    }
                )
                return true

        false

    Complete(InvasionId:string)<transacts>:logic=
        if:
            Definition := GetAEONFALLInvasionRegistry().Get[InvasionId]
            Old := States[InvasionId]
            Old.Active?
        then:
            Finished := aeonfall_invasion_runtime_state:
                InvasionId := Old.InvasionId
                RegionId := Old.RegionId
                CurrentWaveIndex := Old.CurrentWaveIndex
                CompletedObjectiveIds := Old.CompletedObjectiveIds
                RemainingSeconds := Old.RemainingSeconds
                Active := false
                Completed := true
                Failed := false

            if:
                set States[InvasionId] = Finished
            then:
                Removed := GetAEONFALLRegionRuntime().RemoveEvent(
                    Definition.RegionId,
                    InvasionId
                )

                AEONFALLRegionalEscalation.ReconcileRegion(
                    Definition.RegionId
                )

                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "invasion.completed",
                        SourceId := InvasionId,
                        TargetId := Definition.RegionId
                    }
                )
                return true

        false

    Fail(InvasionId:string)<transacts>:logic=
        if:
            Definition := GetAEONFALLInvasionRegistry().Get[InvasionId]
            Old := States[InvasionId]
            Old.Active?
        then:
            Finished := aeonfall_invasion_runtime_state:
                InvasionId := Old.InvasionId
                RegionId := Old.RegionId
                CurrentWaveIndex := Old.CurrentWaveIndex
                CompletedObjectiveIds := Old.CompletedObjectiveIds
                RemainingSeconds := 0.0
                Active := false
                Completed := false
                Failed := true

            if:
                set States[InvasionId] = Finished
            then:
                Removed := GetAEONFALLRegionRuntime().RemoveEvent(
                    Definition.RegionId,
                    InvasionId
                )

                if:
                    RegionState := GetAEONFALLRegionRuntime().GetState[Definition.RegionId]
                then:
                    Corrupted := GetAEONFALLRegionRuntime().SetCorruption(
                        Definition.RegionId,
                        RegionState.Corruption + Old.CurrentWaveIndex * 10 + 10
                    )

                AEONFALLRegionalEscalation.ReconcileRegion(
                    Definition.RegionId
                )

                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "invasion.failed",
                        SourceId := InvasionId,
                        TargetId := Definition.RegionId
                    }
                )
                return true

        false

    TickAll(DeltaSeconds:float)<transacts>:void=
        if (DeltaSeconds <= 0.0):
            return

        var Updated:[string]aeonfall_invasion_runtime_state = map{}
        var ExpiredIds:[]string = array{}

        for (InvasionId -> State : States):
            if (State.Active?):
                Remaining:float = State.RemainingSeconds - DeltaSeconds

                if (Remaining > 0.0):
                    Next := aeonfall_invasion_runtime_state:
                        InvasionId := State.InvasionId
                        RegionId := State.RegionId
                        CurrentWaveIndex := State.CurrentWaveIndex
                        CompletedObjectiveIds := State.CompletedObjectiveIds
                        RemainingSeconds := Remaining
                        Active := true
                        Completed := false
                        Failed := false

                    if:
                        set Updated[InvasionId] = Next
                    then:
                        set Updated = Updated
                else:
                    Expired := aeonfall_invasion_runtime_state:
                        InvasionId := State.InvasionId
                        RegionId := State.RegionId
                        CurrentWaveIndex := State.CurrentWaveIndex
                        CompletedObjectiveIds := State.CompletedObjectiveIds
                        RemainingSeconds := 0.0
                        Active := true
                        Completed := false
                        Failed := false

                    if:
                        set Updated[InvasionId] = Expired
                    then:
                        set Updated = Updated

                    set ExpiredIds = ExpiredIds + array{InvasionId}
            else:
                if:
                    set Updated[InvasionId] = State
                then:
                    set Updated = Updated

        set States = Updated

        for (InvasionId : ExpiredIds):
            if:
                Definition := GetAEONFALLInvasionRegistry().Get[InvasionId]
            then:
                if (Definition.TimeoutIsFailure?):
                    Failed := Fail(InvasionId)
                else:
                    Completed := Complete(InvasionId)

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLInvasionRuntimeSessions:weak_map(session, aeonfall_invasion_runtime) = map{}

GetAEONFALLInvasionRuntime()<transacts>:aeonfall_invasion_runtime=
    CurrentSession := GetSession()
    if (Existing := AEONFALLInvasionRuntimeSessions[CurrentSession]):
        return Existing
    Created := aeonfall_invasion_runtime{}
    if (set AEONFALLInvasionRuntimeSessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLInvasionRuntime in its session")
