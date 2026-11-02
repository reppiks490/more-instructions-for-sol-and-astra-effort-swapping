using { /Verse.org/Verse }
using { /Verse.org/Simulation }

# Session-only world-event state service.
# Event-specific directors use this shared state machine and bind spawn groups,
# objectives, streaming regions, hazards, weather, and presentation externally.
# Only local, materialized regions claim event slots; distant world effects
# remain abstract with an empty regional footprint.
AEONFALLWorldEventMaxActiveRegions:int = 4

aeonfall_world_event_service := class():

    var States:[string]aeonfall_world_event_runtime_state = map{}

    # A regional shell is logical admission, not permission to spawn NPCs.
    HasActiveInRegion(RegionId:string)<transacts>:logic=
        for (OtherEventId -> State : States):
            if (State.Active?, State.ActiveRegionIds.Find[RegionId]):
                return true
        false

    # One active world-event owner per region. Both initial and subsequent
    # stage footprints must be distinct, canonical, initialized and bounded.
    # A zero-region abstract stage is allowed and owns no physical region.
    CanClaimRegions(EventId:string, RegionIds:[]string)<transacts>:logic=
        if (RegionIds.Length > AEONFALLWorldEventMaxActiveRegions):
            return false
        var Seen:[]string = array{}
        for (RegionId : RegionIds):
            if (RegionId = ""):
                return false
            if (not GetAEONFALLRegionRegistry().IsRegistered[RegionId]):
                return false
            if (not GetAEONFALLRegionRuntime().GetState[RegionId]):
                return false
            if (Seen.Find[RegionId]):
                return false
            # No event shell may take materialized space from an existing
            # invasion, faction battle or another active world-event shell.
            if (GetAEONFALLInvasionRuntime().HasActiveInRegion(RegionId)?):
                return false
            if (GetAEONFALLFactionConflictRuntime().HasActiveInRegion(RegionId)?):
                return false
            for (OtherEventId -> State : States):
                if (OtherEventId <> EventId, State.Active?, State.ActiveRegionIds.Find[RegionId]):
                    return false
            set Seen = Seen + array{RegionId}
        true

    StartEvent(EventId:string, InitialRegionIds:[]string)<transacts>:logic=
        # An empty identifier aliases unrelated events and defeats cleanup/rewards.
        if (EventId = ""):
            return false
        if:
            Existing := States[EventId]
            Existing.Active?
        then:
            return false
        if (not CanClaimRegions(EventId, InitialRegionIds)?):
            return false

        Initial := aeonfall_world_event_runtime_state:
            EventId := EventId
            CurrentStageIndex := 0
            CompletedObjectiveIds := array{}
            ActiveRegionIds := InitialRegionIds
            Active := true
            Failed := false
            Completed := false

        if:
            set States[EventId] = Initial
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "world_event.started",
                    SourceId := EventId
                }
            )
            return true

        false

    GetState(EventId:string)<decides><transacts>:aeonfall_world_event_runtime_state=
        States[EventId]

    MarkObjectiveComplete(EventId:string, ObjectiveId:string)<transacts>:logic=
        # Empty objective IDs cannot count as valid phase progress.
        if (EventId = "" or ObjectiveId = ""):
            return false
        if:
            Old := States[EventId]
            Old.Active?
        then:
            if:
                Old.CompletedObjectiveIds.Find[ObjectiveId]
            then:
                return false

            Updated := aeonfall_world_event_runtime_state:
                EventId := Old.EventId
                CurrentStageIndex := Old.CurrentStageIndex
                CompletedObjectiveIds := Old.CompletedObjectiveIds + array{ObjectiveId}
                ActiveRegionIds := Old.ActiveRegionIds
                Active := true
                Failed := false
                Completed := false

            if:
                set States[EventId] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "world_event.objective_completed",
                        SourceId := EventId,
                        TargetId := ObjectiveId
                    }
                )
                return true

        false

    AdvanceStage(
        EventId:string,
        NextStageIndex:int,
        ActiveRegionIds:[]string
    )<transacts>:logic=
        if:
            EventId <> ""
            NextStageIndex >= 0
            Old := States[EventId]
            Old.Active?
            # No phase jumps, retries of the same phase, or rewinds.
            NextStageIndex = Old.CurrentStageIndex + 1
            CanClaimRegions(EventId, ActiveRegionIds)?
        then:
            Updated := aeonfall_world_event_runtime_state:
                EventId := Old.EventId
                CurrentStageIndex := NextStageIndex
                CompletedObjectiveIds := Old.CompletedObjectiveIds
                ActiveRegionIds := ActiveRegionIds
                Active := true
                Failed := false
                Completed := false

            if:
                set States[EventId] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "world_event.stage_advanced",
                        SourceId := EventId,
                        Amount := NextStageIndex
                    }
                )
                return true

        false

    CompleteEvent(EventId:string)<transacts>:logic=
        if:
            Old := States[EventId]
            Old.Active?
        then:
            Updated := aeonfall_world_event_runtime_state:
                EventId := Old.EventId
                CurrentStageIndex := Old.CurrentStageIndex
                CompletedObjectiveIds := Old.CompletedObjectiveIds
                ActiveRegionIds := array{}
                Active := false
                Failed := false
                Completed := true

            if:
                set States[EventId] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "world_event.completed",
                        SourceId := EventId
                    }
                )

                Awarded:int = AEONFALLEncounterRewardService.AwardRegistered(
                    EventId
                )

                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "world_event.rewards_resolved",
                        SourceId := EventId,
                        Amount := Awarded
                    }
                )
                return true

        false

    FailEvent(EventId:string)<transacts>:logic=
        if:
            Old := States[EventId]
            Old.Active?
        then:
            Updated := aeonfall_world_event_runtime_state:
                EventId := Old.EventId
                CurrentStageIndex := Old.CurrentStageIndex
                CompletedObjectiveIds := Old.CompletedObjectiveIds
                ActiveRegionIds := array{}
                Active := false
                Failed := true
                Completed := false

            if:
                set States[EventId] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "world_event.failed",
                        SourceId := EventId
                    }
                )

                GetAEONFALLEncounterParticipation().ClearEncounter(
                    EventId
                )
                return true

        false

# One shared service for regional admission with invasions and faction wars.
# This does not add an NPC director, actor budget, or persistent world state.
var AEONFALLWorldEventRuntimeSessions:weak_map(session, aeonfall_world_event_service) = map{}

GetAEONFALLWorldEventRuntime()<transacts>:aeonfall_world_event_service=
    CurrentSession := GetSession()
    if (Existing := AEONFALLWorldEventRuntimeSessions[CurrentSession]):
        return Existing
    Created := aeonfall_world_event_service{}
    if (set AEONFALLWorldEventRuntimeSessions[CurrentSession] = Created):
        return Created
    Err("AEONFALL could not retain world-event runtime in its session")
