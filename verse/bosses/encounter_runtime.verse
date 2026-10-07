using { /Verse.org/Verse }

# Session-only boss encounter state service.
# Project-bound controllers own spawning, damage, devices, navigation, VFX, and
# cinematics; this service owns canonical phase/objective state transitions.
aeonfall_boss_encounter_service := class():

    var States:[string]aeonfall_boss_runtime_state = map{}

    StartEncounter(BossId:string)<transacts>:logic=
        if:
            Existing := States[BossId]
            Existing.EncounterActive?
        then:
            return false

        Initial := aeonfall_boss_runtime_state:
            BossId := BossId
            CurrentPhaseIndex := 0
            CompletedObjectiveIds := array{}
            BrokenWeakPointIds := array{}
            EncounterActive := true
            EncounterFailed := false
            EncounterCompleted := false

        if:
            set States[BossId] = Initial
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "boss.started",
                    SourceId := BossId
                }
            )
            return true

        false

    GetState(BossId:string)<decides><transacts>:aeonfall_boss_runtime_state=
        States[BossId]

    MarkObjectiveComplete(BossId:string, ObjectiveId:string)<transacts>:logic=
        if:
            Old := States[BossId]
            Old.EncounterActive?
        then:
            if:
                Old.CompletedObjectiveIds.Find[ObjectiveId]
            then:
                return false

            Updated := aeonfall_boss_runtime_state:
                BossId := Old.BossId
                CurrentPhaseIndex := Old.CurrentPhaseIndex
                CompletedObjectiveIds := Old.CompletedObjectiveIds + array{ObjectiveId}
                BrokenWeakPointIds := Old.BrokenWeakPointIds
                EncounterActive := Old.EncounterActive
                EncounterFailed := Old.EncounterFailed
                EncounterCompleted := Old.EncounterCompleted

            if:
                set States[BossId] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "boss.objective_completed",
                        SourceId := BossId,
                        TargetId := ObjectiveId
                    }
                )
                return true

        false

    MarkWeakPointBroken(BossId:string, WeakPointId:string)<transacts>:logic=
        if:
            Old := States[BossId]
            Old.EncounterActive?
        then:
            if:
                Old.BrokenWeakPointIds.Find[WeakPointId]
            then:
                return false

            Updated := aeonfall_boss_runtime_state:
                BossId := Old.BossId
                CurrentPhaseIndex := Old.CurrentPhaseIndex
                CompletedObjectiveIds := Old.CompletedObjectiveIds
                BrokenWeakPointIds := Old.BrokenWeakPointIds + array{WeakPointId}
                EncounterActive := Old.EncounterActive
                EncounterFailed := Old.EncounterFailed
                EncounterCompleted := Old.EncounterCompleted

            if:
                set States[BossId] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "boss.weakpoint_broken",
                        SourceId := BossId,
                        TargetId := WeakPointId
                    }
                )
                return true

        false

    AdvancePhase(BossId:string, NextPhaseIndex:int)<transacts>:logic=
        if:
            NextPhaseIndex >= 0
            Old := States[BossId]
            Old.EncounterActive?
            NextPhaseIndex > Old.CurrentPhaseIndex
        then:
            Updated := aeonfall_boss_runtime_state:
                BossId := Old.BossId
                CurrentPhaseIndex := NextPhaseIndex
                CompletedObjectiveIds := Old.CompletedObjectiveIds
                BrokenWeakPointIds := Old.BrokenWeakPointIds
                EncounterActive := true
                EncounterFailed := false
                EncounterCompleted := false

            if:
                set States[BossId] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "boss.phase_advanced",
                        SourceId := BossId,
                        Amount := NextPhaseIndex
                    }
                )
                return true

        false

    CompleteEncounter(BossId:string)<transacts>:logic=
        if:
            Old := States[BossId]
            Old.EncounterActive?
        then:
            Updated := aeonfall_boss_runtime_state:
                BossId := Old.BossId
                CurrentPhaseIndex := Old.CurrentPhaseIndex
                CompletedObjectiveIds := Old.CompletedObjectiveIds
                BrokenWeakPointIds := Old.BrokenWeakPointIds
                EncounterActive := false
                EncounterFailed := false
                EncounterCompleted := true

            if:
                set States[BossId] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "boss.completed",
                        SourceId := BossId
                    }
                )
                return true

        false

    FailEncounter(BossId:string)<transacts>:logic=
        if:
            Old := States[BossId]
            Old.EncounterActive?
        then:
            Updated := aeonfall_boss_runtime_state:
                BossId := Old.BossId
                CurrentPhaseIndex := Old.CurrentPhaseIndex
                CompletedObjectiveIds := Old.CompletedObjectiveIds
                BrokenWeakPointIds := Old.BrokenWeakPointIds
                EncounterActive := false
                EncounterFailed := true
                EncounterCompleted := false

            if:
                set States[BossId] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "boss.failed",
                        SourceId := BossId
                    }
                )
                return true

        false
