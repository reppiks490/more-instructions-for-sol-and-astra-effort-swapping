using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Fortnite.com/Game }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Nested editable classes need concrete defaults for UEFN's Details panel.
aeonfall_encounter_input_binding := class<concrete>:
    @editable
    Kind:aeonfall_encounter_input_kind = aeonfall_encounter_input_kind.Objective
    @editable
    CanonicalId:string = ""
    @editable
    Input:trigger_device = trigger_device{}

aeonfall_encounter_hazard_binding := class<concrete>:
    @editable
    HazardId:string = ""
    @editable
    DamageVolumes:[]damage_volume_device = array{}
    @editable
    EnableOutput:trigger_device = trigger_device{}
    @editable
    DisableOutput:trigger_device = trigger_device{}

aeonfall_encounter_spawn_binding := class<concrete>:
    @editable
    SpawnGroupId:string = ""
    @editable
    Spawners:[]npc_spawner_device = array{}

aeonfall_encounter_phase_binding := class<concrete>:
    @editable
    PhaseId:string = ""
    @editable
    Inputs:[]aeonfall_encounter_input_binding = array{}
    @editable
    Hazards:[]aeonfall_encounter_hazard_binding = array{}
    @editable
    SpawnGroups:[]aeonfall_encounter_spawn_binding = array{}
    @editable
    EnterOutput:trigger_device = trigger_device{}
    @editable
    CleanupOutput:trigger_device = trigger_device{}

aeonfall_encounter_input_listener := class:
    Director:aeonfall_encounter_director_device
    PhaseIndex:int
    Kind:aeonfall_encounter_input_kind
    CanonicalId:string

    OnTriggered(Instigator:?agent):void=
        Director.OnPhaseInput(PhaseIndex, Kind, CanonicalId)

aeonfall_encounter_boss_listener := class:
    Director:aeonfall_encounter_director_device
    Generation:int

    OnDamaged(Result:damage_result):void=
        Director.OnBossDamaged(Generation)

    OnEliminated(Result:elimination_result):void=
        Director.OnBossEliminated(Generation)

# One placed director per canonical encounter ID. All referenced physical
# devices must be encounter-owned, never shared with ambient/invasion spawners.
# Boss health/defeat signals come only from the owned live fort_character.
aeonfall_encounter_director_device := class(creative_device):
    @editable
    EncounterId:string = "BOS-005"
    @editable
    StartInput:trigger_device = trigger_device{}
    @editable
    FailInput:trigger_device = trigger_device{}
    @editable
    ParticipantVolume:volume_device = volume_device{}
    @editable
    BossSpawners:[]npc_spawner_device = array{}
    @editable
    BossSpawnTimeoutSeconds:float = 5.0
    @editable
    Phases:[]aeonfall_encounter_phase_binding = array{}
    @editable
    CompletedOutput:trigger_device = trigger_device{}
    @editable
    FailedOutput:trigger_device = trigger_device{}

    BossService:aeonfall_boss_encounter_service = aeonfall_boss_encounter_service{}
    EventService:aeonfall_world_event_service = aeonfall_world_event_service{}
    var Progress:?aeonfall_encounter_director_runtime = false
    var Subscriptions:[]cancelable = array{}
    var BossSubscriptions:[]cancelable = array{}
    var BossCharacter:?fort_character = false
    var BossAgent:?agent = false
    var Ready:logic = false
    var Busy:logic = false
    var Ending:logic = false
    var Generation:int = 0
    var PendingBossElimination:?int = false
    var PendingFailure:logic = false
    RunStopped:event() = event(){}

    OnBegin<override>()<suspends>:void=
        # Initial cleanup clears hazards without firing phase cleanup graphs.
        DisableAll(false)
        if (Definition := GetSlice001EncounterDirector[EncounterId]):
            Valid := ValidateBindings(Definition)
            if (not Valid?):
                Report("encounter.director_invalid_bindings")
                return
            set Progress = option{aeonfall_encounter_director_runtime{Definition := Definition}}
        else:
            Report("encounter.director_unknown_id")
            return

        set Subscriptions = array{
            StartInput.TriggeredEvent.Subscribe(OnStart),
            FailInput.TriggeredEvent.Subscribe(OnFail),
            ParticipantVolume.AgentEntersEvent.Subscribe(OnParticipantEntered),
            ParticipantVolume.AgentExitsEvent.Subscribe(OnParticipantExited)
        }
        for (Index -> Binding : Phases):
            for (Input : Binding.Inputs):
                Listener := aeonfall_encounter_input_listener{
                    Director := Self, PhaseIndex := Index,
                    Kind := Input.Kind, CanonicalId := Input.CanonicalId
                }
                Subscription := Input.Input.TriggeredEvent.Subscribe(Listener.OnTriggered)
                set Subscriptions += array{Subscription}
        for (Spawner : BossSpawners):
            set Subscriptions += array{Spawner.SpawnedEvent.Subscribe(OnBossSpawned)}
        set Ready = true
        Report("encounter.director_ready")

    Report(EventType:string):void=
        AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{EventType := EventType, SourceId := EncounterId})

    ValidateBindings(Definition:aeonfall_encounter_director_contract)<transacts>:logic=
        if (Phases.Length <> Definition.ProgressionPhases.Length):
            return false
        if (Definition.Kind = aeonfall_encounter_kind.Boss, BossSpawners.Length <> 1):
            return false
        if (Definition.Kind = aeonfall_encounter_kind.WorldEvent, BossSpawners.Length <> 0):
            return false
        for (Index -> Binding : Phases):
            if (Phase := Definition.ProgressionPhases[Index], Binding.PhaseId = Phase.PhaseId):
                var Objectives:[]string = array{}
                var WeakPoints:[]string = array{}
                var Signals:[]string = array{}
                var ExpectedSignals:[]string = array{}
                for (Target : Phase.SignalTargets):
                    if (Target.BossHealthPercent = 0, not Target.BossDefeat?):
                        set ExpectedSignals += array{Target.Id}
                for (Input : Binding.Inputs):
                    if (Input.Kind = aeonfall_encounter_input_kind.Objective):
                        if (Objectives.Find[Input.CanonicalId]):
                            return false
                        set Objectives += array{Input.CanonicalId}
                    else if (Input.Kind = aeonfall_encounter_input_kind.WeakPoint):
                        if (WeakPoints.Find[Input.CanonicalId]):
                            return false
                        set WeakPoints += array{Input.CanonicalId}
                    else:
                        if (Signals.Find[Input.CanonicalId]):
                            return false
                        set Signals += array{Input.CanonicalId}
                ObjectivesMatch := SameIds(Objectives, Definition.GetObjectiveIds(Index))
                WeakPointsMatch := SameIds(WeakPoints, Phase.WeakPointIds)
                SignalsMatch := SameIds(Signals, ExpectedSignals)
                if (not ObjectivesMatch? or not WeakPointsMatch? or not SignalsMatch?):
                    return false
                var Hazards:[]string = array{}
                for (Hazard : Binding.Hazards):
                    if (Hazards.Find[Hazard.HazardId]):
                        return false
                    set Hazards += array{Hazard.HazardId}
                var Groups:[]string = array{}
                for (Group : Binding.SpawnGroups):
                    if (Groups.Find[Group.SpawnGroupId] or Group.Spawners.Length = 0):
                        return false
                    set Groups += array{Group.SpawnGroupId}
                HazardsMatch := SameIds(Hazards, Definition.GetHazardIds(Index))
                GroupsMatch := SameIds(Groups, Definition.GetSpawnGroupIds(Index))
                if (not HazardsMatch? or not GroupsMatch?):
                    return false
            else:
                return false
        true

    SameIds(Actual:[]string, Expected:[]string)<transacts>:logic=
        if (Actual.Length <> Expected.Length):
            return false
        for (Id : Expected):
            if (not Actual.Find[Id]):
                return false
        true

    RewardReady(Definition:aeonfall_encounter_director_contract)<transacts>:logic=
        if (Reward := AEONFALLEncounterRewardRegistry.Get[EncounterId], Reward.FirstClearOnly?):
            if (Definition.Kind = aeonfall_encounter_kind.Boss, Reward.Kind = aeonfall_encounter_reward_kind.Boss):
                return true
            if (Definition.Kind = aeonfall_encounter_kind.WorldEvent, Reward.Kind = aeonfall_encounter_reward_kind.WorldEvent):
                return true
        false

    OnStart(Instigator:?agent):void=
        if (not Ready? or Busy? or Ending?):
            return
        if (Runtime := Progress?, not Runtime.Active?):
            RewardAvailable := RewardReady(Runtime.Definition)
            if (not RewardAvailable?):
                Report("encounter.director_reward_not_ready")
                return
            set Busy = true
            set PendingFailure = false
            set Generation += 1
            var Started:logic = false
            if (Runtime.Definition.Kind = aeonfall_encounter_kind.Boss):
                set Started = BossService.StartEncounter(EncounterId)
            else:
                set Started = EventService.StartEvent(EncounterId, Runtime.Definition.GetRegionIds(0))
            if (Started?):
                ProgressStarted := Runtime.Start()
                if (ProgressStarted?):
                    RefreshParticipants()
                    EnterPhase(Runtime)
                    for (Spawner : BossSpawners):
                        Spawner.Reset()
                        Spawner.Enable()
                        Spawner.Spawn()
                    if (Runtime.Definition.Kind = aeonfall_encounter_kind.Boss):
                        spawn{AwaitBossReady(Generation)}
            ReleaseBusy()
            EvaluateBossHealth()

    OnFail(Instigator:?agent):void=
        if (not Ready? or Ending?):
            return
        if (Runtime := Progress?, Runtime.Active?):
            if (Busy?):
                set PendingFailure = true
                return
            set Busy = true
            Finish(Runtime, false)
            ReleaseBusy()

    OnPhaseInput(Index:int, Kind:aeonfall_encounter_input_kind, Id:string):void=
        if (Busy? or Ending?):
            return
        if (Runtime := Progress?):
            Current := Runtime.AcceptsInput(Index)
            if (not Current?):
                return
            if (Runtime.Definition.Kind = aeonfall_encounter_kind.Boss):
                Alive := BossIsAlive()
                if (not Alive?):
                    return
            set Busy = true
            var Accepted:logic = false
            if (Kind = aeonfall_encounter_input_kind.Objective):
                set Accepted = Runtime.RecordObjective(Index, Id)
                Complete := Runtime.IsObjectiveComplete(Id)
                if (Accepted? and Complete?):
                    if (Runtime.Definition.Kind = aeonfall_encounter_kind.Boss):
                        Marked := BossService.MarkObjectiveComplete(EncounterId, Id)
                    else:
                        Marked := EventService.MarkObjectiveComplete(EncounterId, Id)
            else if (Kind = aeonfall_encounter_input_kind.WeakPoint):
                set Accepted = Runtime.RecordWeakPoint(Index, Id)
                if (Accepted?, Runtime.Definition.Kind = aeonfall_encounter_kind.Boss):
                    # Service-level weak-point IDs are cumulative across phases.
                    # Its deduplication must not discard valid phase-local credit.
                    Marked := BossService.MarkWeakPointBroken(EncounterId, Id)
            else:
                if (Phase := Runtime.Definition.ProgressionPhases[Index]):
                    for (Target : Phase.SignalTargets, Target.Id = Id):
                        if (Target.BossHealthPercent = 0, not Target.BossDefeat?):
                            set Accepted = Runtime.RecordSignal(Index, Id)
            if (Accepted?):
                ResolvePhase(Runtime)
            ReleaseBusy()
            EvaluateBossHealth()

    ResolvePhase(Runtime:aeonfall_encounter_director_runtime):void=
        if (PendingFailure?):
            Finish(Runtime, false)
            return
        Resolved := Runtime.CanResolvePhase()
        if (not Resolved?):
            return
        Final := Runtime.IsFinalPhase()
        if (Final?):
            Finish(Runtime, true)
            return
        NextIndex := Runtime.PhaseIndex + 1
        var Advanced:logic = false
        if (Runtime.Definition.Kind = aeonfall_encounter_kind.Boss):
            set Advanced = BossService.AdvancePhase(EncounterId, NextIndex)
        else:
            set Advanced = EventService.AdvanceStage(EncounterId, NextIndex, Runtime.Definition.GetRegionIds(NextIndex))
        if (Advanced?):
            ExitPhase(Runtime.PhaseIndex, true)
            ProgressAdvanced := Runtime.Advance()
            if (ProgressAdvanced?):
                EnterPhase(Runtime)

    EnterPhase(Runtime:aeonfall_encounter_director_runtime):void=
        if (Binding := Phases[Runtime.PhaseIndex]):
            for (Input : Binding.Inputs):
                Input.Input.Reset()
                Input.Input.Enable()
            if (Character := BossCharacter?, Phase := Runtime.Definition.BossContract.PhaseContracts[Runtime.PhaseIndex]):
                Character.SetVulnerability(Phase.AllowsDirectBossDamage)
            for (Hazard : Binding.Hazards):
                for (Volume : Hazard.DamageVolumes):
                    Volume.Enable()
                Hazard.EnableOutput.Trigger()
            for (Group : Binding.SpawnGroups):
                for (Spawner : Group.Spawners):
                    Spawner.Reset()
                    Spawner.Enable()
            Binding.EnterOutput.Trigger()

    ExitPhase(Index:int, FireCleanup:logic):void=
        if (Binding := Phases[Index]):
            for (Input : Binding.Inputs):
                Input.Input.Disable()
            for (Hazard : Binding.Hazards):
                for (Volume : Hazard.DamageVolumes):
                    Volume.Disable()
                # Disable graphs must be idempotent: initial/terminal sweeps
                # also release hazards outside the currently active phase.
                Hazard.DisableOutput.Trigger()
            for (Group : Binding.SpawnGroups):
                for (Spawner : Group.Spawners):
                    Spawner.Disable()
                    Spawner.DespawnAll(false)
            if (FireCleanup?):
                Binding.CleanupOutput.Trigger()

    DisableAll(FireCleanup:logic):void=
        for (Index -> Binding : Phases):
            ExitPhase(Index, FireCleanup)
        for (Spawner : BossSpawners):
            Spawner.Disable()
            Spawner.DespawnAll(false)

    CancelBossSubscriptions():void=
        for (Subscription : BossSubscriptions):
            Subscription.Cancel()
        set BossSubscriptions = array{}
        set BossCharacter = false
        set BossAgent = false

    OnBossSpawned(Agent:agent):void=
        if (Ending?):
            return
        if (Runtime := Progress?, Runtime.Active?):
            if (ExistingAgent := BossAgent?, ExistingAgent = Agent):
                return
            if (BossCharacter?):
                # An accidental second body is a configuration failure.
                set Busy = true
                Report("encounter.director_multiple_bosses")
                Finish(Runtime, false)
                ReleaseBusy()
                return
            if (Character := Agent.GetFortCharacter[], Character.IsActive[]):
                set BossAgent = option{Agent}
                set BossCharacter = option{Character}
                Listener := aeonfall_encounter_boss_listener{Director := Self, Generation := Generation}
                set BossSubscriptions = array{
                    Character.DamagedEvent().Subscribe(Listener.OnDamaged),
                    Character.EliminatedEvent().Subscribe(Listener.OnEliminated)
                }
                if (Phase := Runtime.Definition.BossContract.PhaseContracts[Runtime.PhaseIndex]):
                    Character.SetVulnerability(Phase.AllowsDirectBossDamage)
                EvaluateBossHealth()
            else:
                set Busy = true
                Report("encounter.director_boss_character_unavailable")
                Finish(Runtime, false)
                ReleaseBusy()

    AwaitBossReady(ExpectedGeneration:int)<suspends>:void=
        if (Ending? or ExpectedGeneration <> Generation):
            return
        Timeout := if (BossSpawnTimeoutSeconds > 0.0) then BossSpawnTimeoutSeconds else 5.0
        race:
            block:
                Sleep(Timeout)
                if:
                    not Ending?
                    ExpectedGeneration = Generation
                    Runtime := Progress?
                    Runtime.Active?
                    not BossCharacter?
                then:
                    set Busy = true
                    Report("encounter.director_boss_spawn_timeout")
                    Finish(Runtime, false)
                    ReleaseBusy()
            RunStopped.Await()

    OnBossDamaged(ExpectedGeneration:int):void=
        if (ExpectedGeneration = Generation):
            EvaluateBossHealth()

    BossIsAlive()<transacts>:logic=
        if (Character := BossCharacter?, Character.IsActive[], Character.GetHealth() > 0.0):
            return true
        false

    EvaluateBossHealth():void=
        if (Busy? or Ending?):
            return
        if:
            Runtime := Progress?
            Runtime.Active?
            Character := BossCharacter?
            Character.IsActive[]
            Character.GetHealth() > 0.0
            Character.GetMaxHealth() > 0.0
            Phase := Runtime.Definition.ProgressionPhases[Runtime.PhaseIndex]
        then:
            set Busy = true
            CurrentIndex := Runtime.PhaseIndex
            HealthPercent := Character.GetHealth() * 100.0 / Character.GetMaxHealth()
            for (Target : Phase.SignalTargets, Target.BossHealthPercent > 0):
                if (HealthPercent <= Target.BossHealthPercent * 1.0):
                    Accepted := Runtime.RecordSignal(CurrentIndex, Target.Id)
                    if (Accepted?):
                        ResolvePhase(Runtime)
            ReleaseBusy()

    OnBossEliminated(ExpectedGeneration:int):void=
        if (Ending? or ExpectedGeneration <> Generation):
            return
        if (Runtime := Progress?, Runtime.Active?):
            # Device output graphs can synchronously eliminate the body while
            # Busy. Preserve the phase at death instead of losing that callback.
            if (not PendingBossElimination?):
                set PendingBossElimination = option{Runtime.PhaseIndex}
            ProcessBossElimination()

    ReleaseBusy():void=
        set Busy = false
        if (PendingFailure?):
            set PendingFailure = false
            if (Runtime := Progress?, Runtime.Active?):
                set Busy = true
                Finish(Runtime, false)
                set Busy = false
        ProcessBossElimination()

    ProcessBossElimination():void=
        if (Busy? or Ending?):
            return
        if (DeathPhase := PendingBossElimination?):
            set PendingBossElimination = false
            if (Runtime := Progress?, Runtime.Active?):
                ResolveBossElimination(Runtime, DeathPhase)

    ResolveBossElimination(Runtime:aeonfall_encounter_director_runtime, DeathPhase:int):void=
        set Busy = true
        Final := Runtime.IsFinalPhase()
        if (not Final? or DeathPhase <> Runtime.PhaseIndex):
            Report("encounter.director_boss_defeated_before_final_phase")
            Finish(Runtime, false)
        else if (Phase := Runtime.Definition.ProgressionPhases[Runtime.PhaseIndex]):
            for (Target : Phase.SignalTargets, Target.BossDefeat?):
                Accepted := Runtime.RecordSignal(Runtime.PhaseIndex, Target.Id)
                if (Accepted?):
                    ResolvePhase(Runtime)
        set Busy = false

    OnParticipantEntered(Agent:agent):void=
        if (Runtime := Progress?, Runtime.Active?):
            AddParticipant(Agent)

    AddParticipant(Agent:agent):void=
        if:
            Player := player[Agent]
            Player.IsActive[]
            Character := Agent.GetFortCharacter[]
            Character.IsActive[]
            Key := AEONFALLActorRegistry.GetRuntimeKey[Player]
        then:
            Added := AEONFALLEncounterParticipation.Add(EncounterId, Key)

    OnParticipantExited(Agent:agent):void=
        if (Player := player[Agent], Key := AEONFALLActorRegistry.GetRuntimeKey[Player]):
            Removed := AEONFALLEncounterParticipation.Remove(EncounterId, Key)

    RefreshParticipants():void=
        AEONFALLEncounterParticipation.ClearEncounter(EncounterId)
        for (Agent : ParticipantVolume.GetAgentsInVolume()):
            AddParticipant(Agent)

    Finish(Runtime:aeonfall_encounter_director_runtime, Success:logic):void=
        # Stop ingress before cleanup/despawn outputs can synchronously reenter.
        CurrentIndex := Runtime.PhaseIndex
        Runtime.Stop()
        RunStopped.Signal()
        set PendingBossElimination = false
        set PendingFailure = false
        CancelBossSubscriptions()
        if (Success?):
            RefreshParticipants()
            if (Runtime.Definition.Kind = aeonfall_encounter_kind.Boss):
                Completed := BossService.CompleteEncounter(EncounterId)
            else:
                Completed := EventService.CompleteEvent(EncounterId)
        else:
            if (Runtime.Definition.Kind = aeonfall_encounter_kind.Boss):
                Failed := BossService.FailEncounter(EncounterId)
            else:
                Failed := EventService.FailEvent(EncounterId)
        # Reward resolution happens above, while participant keys are populated.
        AEONFALLEncounterParticipation.ClearEncounter(EncounterId)
        ExitPhase(CurrentIndex, true)
        DisableAll(false)
        if (Success?):
            CompletedOutput.Trigger()
        else:
            FailedOutput.Trigger()

    OnEnd<override>():void=
        set Ending = true
        set Ready = false
        set Busy = true
        RunStopped.Signal()
        for (Subscription : Subscriptions):
            Subscription.Cancel()
        set Subscriptions = array{}
        if (Runtime := Progress?, Runtime.Active?):
            Finish(Runtime, false)
        else:
            CancelBossSubscriptions()
            DisableAll(false)
            AEONFALLEncounterParticipation.ClearEncounter(EncounterId)
