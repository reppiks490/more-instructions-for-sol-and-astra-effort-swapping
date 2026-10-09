# Structured progression for the first-slice encounter device bridge.
# Objective/weak-point/hazard/spawn identity still comes from the canonical
# boss/world-event contracts; these gates make their prose transitions executable.

aeonfall_encounter_kind := enum:
    Boss
    WorldEvent

aeonfall_encounter_input_kind := enum:
    Objective
    WeakPoint
    Progression

# Native destruction reports a real destroyed prop and its destroying agent.
# TriggerGraph remains available for authored mechanics that have their own
# authenticated producers; it must never impersonate boss health or defeat.
aeonfall_encounter_input_source := enum:
    TriggerGraph
    PropDestroyed

aeonfall_encounter_counter_contract := class:
    Id:string = ""
    RequiredCount:int = 1
    BossHealthPercent:int = 0
    BossDefeat:logic = false

# A phase resolves when ANY alternative has ALL of its requirements satisfied.
aeonfall_encounter_transition_gate := class:
    ObjectiveIds:[]string = array{}
    WeakPointIds:[]string = array{}
    SignalIds:[]string = array{}

aeonfall_encounter_progression_phase := class:
    PhaseId:string = ""
    ObjectiveTargets:[]aeonfall_encounter_counter_contract = array{}
    WeakPointIds:[]string = array{}
    SignalTargets:[]aeonfall_encounter_counter_contract = array{}
    TransitionAlternatives:[]aeonfall_encounter_transition_gate = array{}

aeonfall_encounter_director_contract := class:
    EncounterId:string = ""
    Kind:aeonfall_encounter_kind = aeonfall_encounter_kind.Boss
    BossContract:aeonfall_boss_encounter_contract = aeonfall_boss_encounter_contract{}
    EventContract:aeonfall_world_event_contract = aeonfall_world_event_contract{}
    ProgressionPhases:[]aeonfall_encounter_progression_phase = array{}

    GetObjectiveIds(Index:int)<transacts>:[]string=
        if (Kind = aeonfall_encounter_kind.Boss, Phase := BossContract.PhaseContracts[Index]):
            return Phase.ObjectiveIds
        if (Kind = aeonfall_encounter_kind.WorldEvent, Stage := EventContract.StageContracts[Index]):
            return Stage.ObjectiveIds
        array{}

    GetHazardIds(Index:int)<transacts>:[]string=
        if (Kind = aeonfall_encounter_kind.Boss, Phase := BossContract.PhaseContracts[Index]):
            return Phase.ActiveHazardIds
        if (Kind = aeonfall_encounter_kind.WorldEvent, Stage := EventContract.StageContracts[Index]):
            return Stage.HazardIds
        array{}

    GetSpawnGroupIds(Index:int)<transacts>:[]string=
        if (Kind = aeonfall_encounter_kind.Boss, Phase := BossContract.PhaseContracts[Index]):
            return Phase.ActiveSpawnGroupIds
        if (Kind = aeonfall_encounter_kind.WorldEvent, Stage := EventContract.StageContracts[Index]):
            return Stage.SpawnGroupIds
        array{}

    GetRegionIds(Index:int)<transacts>:[]string=
        if (Kind = aeonfall_encounter_kind.WorldEvent, Stage := EventContract.StageContracts[Index]):
            return Stage.RegionIds
        array{}
