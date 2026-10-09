using { /Verse.org/Verse }
using { /Verse.org/Simulation }
# Session faction-war runtime.
# Physical NPC armies, territory props, objectives, and presentation are
# project-bound directors. This service owns conflict score/escalation/results.

aeonfall_faction_conflict_state := class:
    ConflictId:string = ""
    RegionId:string = ""
    FactionAId:string = ""
    FactionBId:string = ""
    ScoreA:int = 0
    ScoreB:int = 0
    EscalationTier:int = 0
    Active:logic = false
    WinnerFactionId:string = ""

aeonfall_faction_conflict_service := class():

    var Conflicts:[string]aeonfall_faction_conflict_state = map{}

    ClampScore(Value:int):int=
        if (Value < 0):
            0
        else:
            Value

    EscalationForTotal(Total:int):int=
        if (Total >= 400):
            5
        else if (Total >= 250):
            4
        else if (Total >= 150):
            3
        else if (Total >= 75):
            2
        else if (Total >= 25):
            1
        else:
            0

    StartConflict(
        ConflictId:string,
        RegionId:string,
        FactionAId:string,
        FactionBId:string
    )<transacts>:logic=
        if:
            ConflictId <> ""
            RegionId <> ""
            FactionAId <> ""
            FactionBId <> ""
            FactionAId <> FactionBId
            GetAEONFALLRegionRegistry().IsRegistered[RegionId]
        then:
            if:
                Existing := Conflicts[ConflictId]
            then:
                return false

            Initial := aeonfall_faction_conflict_state:
                ConflictId := ConflictId
                RegionId := RegionId
                FactionAId := FactionAId
                FactionBId := FactionBId
                ScoreA := 0
                ScoreB := 0
                EscalationTier := 0
                Active := true
                WinnerFactionId := ""

            if:
                set Conflicts[ConflictId] = Initial
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "faction_conflict.started",
                        SourceId := ConflictId,
                        TargetId := RegionId,
                        ContextId := FactionAId + "::" + FactionBId
                    }
                )
                return true

        false

    StartRegistered(ConflictId:string)<transacts>:logic=
        if:
            Definition := GetAEONFALLFactionConflictRegistry().Get[ConflictId]
            RegionState := GetAEONFALLRegionRuntime().GetState[Definition.RegionId]
            RegionState.HostilityTier >= Definition.MinHostilityTier
        then:
            StartConflict(
                Definition.ConflictId,
                Definition.RegionId,
                Definition.FactionAId,
                Definition.FactionBId
            )
        else:
            false

    GetState(ConflictId:string)<decides><transacts>:aeonfall_faction_conflict_state=
        Conflicts[ConflictId]

    AddScore(
        ConflictId:string,
        FactionId:string,
        Amount:int
    )<transacts>:logic=
        if:
            Amount > 0
            Old := Conflicts[ConflictId]
            Old.Active?
        then:
            var ScoreA:int = Old.ScoreA
            var ScoreB:int = Old.ScoreB

            if (FactionId = Old.FactionAId):
                set ScoreA = ClampScore(ScoreA + Amount)
            else if (FactionId = Old.FactionBId):
                set ScoreB = ClampScore(ScoreB + Amount)
            else:
                return false

            NewTier:int = EscalationForTotal(ScoreA + ScoreB)

            Updated := aeonfall_faction_conflict_state:
                ConflictId := Old.ConflictId
                RegionId := Old.RegionId
                FactionAId := Old.FactionAId
                FactionBId := Old.FactionBId
                ScoreA := ScoreA
                ScoreB := ScoreB
                EscalationTier := NewTier
                Active := true
                WinnerFactionId := ""

            if:
                set Conflicts[ConflictId] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "faction_conflict.score_changed",
                        SourceId := ConflictId,
                        TargetId := FactionId,
                        Amount := Amount,
                        ContextId := "tier::{NewTier}"
                    }
                )

                if:
                    Definition := GetAEONFALLFactionConflictRegistry().Get[ConflictId]
                    (
                        ScoreA >= Definition.VictoryScore
                        or ScoreB >= Definition.VictoryScore
                    )
                    ScoreA <> ScoreB
                then:
                    Completed := CompleteConflict(ConflictId)

                return true

        false

    CompleteConflict(ConflictId:string)<transacts>:logic=
        if:
            Old := Conflicts[ConflictId]
            Old.Active?
        then:
            Winner:string =
                if (Old.ScoreA > Old.ScoreB):
                    Old.FactionAId
                else if (Old.ScoreB > Old.ScoreA):
                    Old.FactionBId
                else:
                    ""

            Completed := aeonfall_faction_conflict_state:
                ConflictId := Old.ConflictId
                RegionId := Old.RegionId
                FactionAId := Old.FactionAId
                FactionBId := Old.FactionBId
                ScoreA := Old.ScoreA
                ScoreB := Old.ScoreB
                EscalationTier := Old.EscalationTier
                Active := false
                WinnerFactionId := Winner

            if:
                set Conflicts[ConflictId] = Completed
            then:
                if (Winner <> ""):
                    InfluenceAdded := GetAEONFALLRegionRuntime().AddFactionInfluence(
                        Old.RegionId,
                        Winner,
                        20
                    )

                    Loser:string =
                        if (Winner = Old.FactionAId):
                            Old.FactionBId
                        else:
                            Old.FactionAId

                    InfluenceRemoved := GetAEONFALLRegionRuntime().AddFactionInfluence(
                        Old.RegionId,
                        Loser,
                        -10
                    )

                AEONFALLRegionalEscalation.ReconcileRegion(Old.RegionId)

                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "faction_conflict.completed",
                        SourceId := ConflictId,
                        TargetId := Winner,
                        ContextId := Old.RegionId,
                        Amount := Old.EscalationTier
                    }
                )
                return true

        false

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLFactionConflictRuntimeSessions:weak_map(session, aeonfall_faction_conflict_service) = map{}

GetAEONFALLFactionConflictRuntime()<transacts>:aeonfall_faction_conflict_service=
    CurrentSession := GetSession()
    if (Existing := AEONFALLFactionConflictRuntimeSessions[CurrentSession]):
        return Existing
    Created := aeonfall_faction_conflict_service{}
    if (set AEONFALLFactionConflictRuntimeSessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLFactionConflictRuntime in its session")
