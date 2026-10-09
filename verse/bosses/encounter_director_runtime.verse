using { /Verse.org/Verse }

# Pure, phase-scoped progression. No physical device operations or rewards here.
# The editor harness exercises this actual Verse logic, not a Python substitute.
aeonfall_encounter_director_runtime := class():
    Definition:aeonfall_encounter_director_contract = aeonfall_encounter_director_contract{}
    var Active:logic = false
    var PhaseIndex:int = 0
    var ObjectiveCounts:[string]int = map{}
    var SignalCounts:[string]int = map{}
    var BrokenWeakPointIds:[]string = array{}

    Start()<transacts>:logic=
        if (Active? or Definition.EncounterId = "" or Definition.ProgressionPhases.Length = 0):
            return false
        set Active = true
        set PhaseIndex = 0
        ResetPhase()
        true

    Stop()<transacts>:void=
        set Active = false
        ResetPhase()

    ResetPhase()<transacts>:void=
        set ObjectiveCounts = map{}
        set SignalCounts = map{}
        set BrokenWeakPointIds = array{}

    AcceptsInput(ExpectedPhaseIndex:int)<transacts>:logic=
        logic{Active?, ExpectedPhaseIndex = PhaseIndex}

    RecordObjective(ExpectedPhaseIndex:int, ObjectiveId:string)<transacts>:logic=
        Accepted := AcceptsInput(ExpectedPhaseIndex)
        if (not Accepted?):
            return false
        Allowed := Definition.GetObjectiveIds(PhaseIndex)
        if (not Allowed.Find[ObjectiveId]):
            return false
        if (Phase := Definition.ProgressionPhases[PhaseIndex]):
            for (Target : Phase.ObjectiveTargets, Target.Id = ObjectiveId):
                var OldCount:int = 0
                if (Stored := ObjectiveCounts[ObjectiveId]):
                    set OldCount = Stored
                if (OldCount >= Target.RequiredCount):
                    return false
                if (set ObjectiveCounts[ObjectiveId] = OldCount + 1):
                    return true
        false

    IsObjectiveComplete(ObjectiveId:string)<transacts>:logic=
        if (Phase := Definition.ProgressionPhases[PhaseIndex]):
            for (Target : Phase.ObjectiveTargets, Target.Id = ObjectiveId):
                if (Count := ObjectiveCounts[ObjectiveId], Count >= Target.RequiredCount):
                    return true
        false

    RecordWeakPoint(ExpectedPhaseIndex:int, WeakPointId:string)<transacts>:logic=
        Accepted := AcceptsInput(ExpectedPhaseIndex)
        if (not Accepted?):
            return false
        if:
            Phase := Definition.ProgressionPhases[PhaseIndex]
            Phase.WeakPointIds.Find[WeakPointId]
            not BrokenWeakPointIds.Find[WeakPointId]
        then:
            set BrokenWeakPointIds = BrokenWeakPointIds + array{WeakPointId}
            return true
        false

    RecordSignal(ExpectedPhaseIndex:int, SignalId:string)<transacts>:logic=
        Accepted := AcceptsInput(ExpectedPhaseIndex)
        if (not Accepted?):
            return false
        if (Phase := Definition.ProgressionPhases[PhaseIndex]):
            for (Target : Phase.SignalTargets, Target.Id = SignalId):
                var OldCount:int = 0
                if (Stored := SignalCounts[SignalId]):
                    set OldCount = Stored
                if (OldCount >= Target.RequiredCount):
                    return false
                if (set SignalCounts[SignalId] = OldCount + 1):
                    return true
        false

    IsSignalComplete(SignalId:string)<transacts>:logic=
        if (Phase := Definition.ProgressionPhases[PhaseIndex]):
            for (Target : Phase.SignalTargets, Target.Id = SignalId):
                if (Count := SignalCounts[SignalId], Count >= Target.RequiredCount):
                    return true
        false

    IsGateSatisfied(Gate:aeonfall_encounter_transition_gate)<transacts>:logic=
        if (Gate.ObjectiveIds.Length + Gate.WeakPointIds.Length + Gate.SignalIds.Length = 0):
            return false
        for (Id : Gate.ObjectiveIds):
            Complete := IsObjectiveComplete(Id)
            if (not Complete?):
                return false
        for (Id : Gate.WeakPointIds):
            if (not BrokenWeakPointIds.Find[Id]):
                return false
        for (Id : Gate.SignalIds):
            Complete := IsSignalComplete(Id)
            if (not Complete?):
                return false
        true

    CanResolvePhase()<transacts>:logic=
        if (not Active?):
            return false
        if (Phase := Definition.ProgressionPhases[PhaseIndex]):
            for (Gate : Phase.TransitionAlternatives):
                Satisfied := IsGateSatisfied(Gate)
                if (Satisfied?):
                    return true
        false

    IsFinalPhase()<transacts>:logic=
        logic{PhaseIndex = Definition.ProgressionPhases.Length - 1}

    Advance()<transacts>:logic=
        Ready := CanResolvePhase()
        Final := IsFinalPhase()
        if (not Ready? or Final?):
            return false
        set PhaseIndex += 1
        ResetPhase()
        true

    CanComplete()<transacts>:logic=
        Ready := CanResolvePhase()
        Final := IsFinalPhase()
        logic{Ready?, Final?}
