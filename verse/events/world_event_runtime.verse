using { /Verse.org/Verse }

# Session-only world-event state service.
# Event-specific directors use this shared state machine and bind spawn groups,
# objectives, streaming regions, hazards, weather, and presentation externally.
aeonfall_world_event_service := class():

    var States:[string]aeonfall_world_event_runtime_state = map{}

    StartEvent(EventId:string, InitialRegionIds:[]string)<transacts>:logic=
        if:
            Existing := States[EventId]
            Existing.Active?
        then:
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
            NextStageIndex >= 0
            Old := States[EventId]
            Old.Active?
            NextStageIndex > Old.CurrentStageIndex
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
