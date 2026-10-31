using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Project-bound bridge from canonical AEONFALL status events into UEFN devices.
# Configure one instance per visual/gameplay status binding.
#
# - ApplyTrigger may drive supported device logic for the affected agent.
# - RemoveTrigger reverses or cleans up that logic.
# - Effect is optional presentation when UseVfx is enabled and configured with
#   Stick to Player in UEFN.
aeonfall_status_device_bridge := class(creative_device):

    @editable
    StatusId:string = ""

    @editable
    ApplyTrigger:trigger_device = trigger_device{}

    @editable
    RemoveTrigger:trigger_device = trigger_device{}

    @editable
    Effect:vfx_creator_device = vfx_creator_device{}

    @editable
    UseApplyTrigger:logic = true

    @editable
    UseRemoveTrigger:logic = true

    @editable
    UseVfx:logic = false

    var BusSubscription:?cancelable = false
    var AppliedAgents:[string]agent = map{}
    var AppliedCharacters:[string]fort_character = map{}
    ReconciliationStopped:event() = event(){}

    OnBegin<override>()<suspends>:void=
        if (StatusId = ""):
            Print("AEONFALL status bridge requires a canonical status ID.")
            return
        Subscription := AEONFALLRuntimeBus.RuntimeEvent.Subscribe(OnRuntimeEvent)
        set BusSubscription = option{Subscription}
        # Bootstrap order is not a native-device guarantee. Recover statuses
        # committed before this bridge subscribed to the event channel.
        Reconcile()
        race:
            ReconciliationStopped.Await()
            ReconcileLoop()

    OnEnd<override>():void=
        if (Subscription := BusSubscription?):
            Subscription.Cancel()
        set BusSubscription = false
        ReconciliationStopped.Signal()
        CleanupAll()

    ReconcileLoop()<suspends>:void=
        loop:
            Sleep(0.1)
            Reconcile()

    # Removal events are best-effort presentation hints. Poll canonical state
    # as well so queue saturation or registry removal cannot strand an effect.
    Reconcile():void=
        Tracked := AppliedAgents
        for (TargetKey -> TrackedAgent : Tracked):
            CleanupIfStale(TargetKey)

        # The player agent survives respawn, while its fort_character changes.
        # Rebind only missing generations; polling must not refresh authored
        # effects every tenth of a second while the same character is active.
        for (TargetKey -> Instances : GetAEONFALLStatusRuntime().StatusesByTarget):
            if:
                GetAEONFALLStatusRuntime().HasStatus(TargetKey, StatusId)?
                TargetAgent := GetAEONFALLActorRegistry().GetAgent[TargetKey]
                Character := TargetAgent.GetFortCharacter[]
                Character.IsActive[]
                not AppliedCharacters[TargetKey]
            then:
                ApplyTracked(TargetKey, TargetAgent)

    OnRuntimeEvent(Event:aeonfall_runtime_event):void=
        if:
            Event.EventType = "status.applied"
            Event.ContextId = StatusId
            GetAEONFALLStatusRuntime().HasStatus(Event.TargetId, StatusId)?
            TargetAgent := GetAEONFALLActorRegistry().GetAgent[Event.TargetId]
            Character := TargetAgent.GetFortCharacter[]
            Character.IsActive[]
        then:
            ApplyTracked(Event.TargetId, TargetAgent)
            return

        if:
            Event.EventType = "status.removed"
            Event.ContextId = StatusId
        then:
            CleanupIfStale(Event.TargetId)
            return

        if:
            Event.EventType = "status.expired"
            Event.ContextId = StatusId
        then:
            CleanupIfStale(Event.TargetId)
            return

        if:
            Event.EventType = "status.target_cleared"
        then:
            CleanupIfStale(Event.TargetId)
            return

        if (Event.EventType = "actor.unregistered"):
            CleanupIfStale(Event.SourceId)

    ApplyTracked(TargetKey:string, TargetAgent:agent):void=
        PreviousAgent:?agent =
            if (TrackedAgent := AppliedAgents[TargetKey]):
                option{TrackedAgent}
            else:
                false

        # Both tracking maps commit atomically before any physical effect.
        # Failed admission creates no untracked native effect.
        if (CommitTracking[TargetKey, TargetAgent]):
            if (TrackedAgent := PreviousAgent?, TrackedAgent <> TargetAgent):
                Cleanup(TrackedAgent)

            # Every valid applied command, including a duration refresh or a
            # stack-cap reapplication, retriggers the authored devices.
            if (UseApplyTrigger?):
                ApplyTrigger.Trigger(TargetAgent)
            if (UseVfx?):
                Effect.Begin(TargetAgent)

    CommitTracking(TargetKey:string, TargetAgent:agent)<decides><transacts>:void=
        Character := TargetAgent.GetFortCharacter[]
        Character.IsActive[]
        set AppliedAgents[TargetKey] = TargetAgent
        set AppliedCharacters[TargetKey] = Character

    CleanupIfStale(TargetKey:string):void=
        if (TrackedAgent := AppliedAgents[TargetKey]):
            if:
                GetAEONFALLStatusRuntime().HasStatus(TargetKey, StatusId)?
                CurrentAgent := GetAEONFALLActorRegistry().GetAgent[TargetKey]
                CurrentAgent = TrackedAgent
                TrackedCharacter := AppliedCharacters[TargetKey]
                CurrentCharacter := CurrentAgent.GetFortCharacter[]
                CurrentCharacter.IsActive[]
                CurrentCharacter = TrackedCharacter
            then:
                # A queued removal can refer to an older status lifetime. Keep
                # the current physical effect while canonical status is active.
                return

            if (ForgetTarget[TargetKey]):
                Cleanup(TrackedAgent)

    ForgetTarget(TargetKey:string)<decides><transacts>:void=
        var Remaining:[string]agent = map{}
        for (StoredKey -> StoredAgent : AppliedAgents):
            if (StoredKey <> TargetKey):
                set Remaining[StoredKey] = StoredAgent
        var RemainingCharacters:[string]fort_character = map{}
        for (StoredKey -> StoredCharacter : AppliedCharacters):
            if (StoredKey <> TargetKey):
                set RemainingCharacters[StoredKey] = StoredCharacter
        set AppliedAgents = Remaining
        set AppliedCharacters = RemainingCharacters

    CleanupAll():void=
        Tracked := AppliedAgents
        set AppliedAgents = map{}
        set AppliedCharacters = map{}
        for (TargetKey -> TrackedAgent : Tracked):
            Cleanup(TrackedAgent)

    Cleanup(TargetAgent:agent):void=
        if (UseRemoveTrigger?):
            RemoveTrigger.Trigger(TargetAgent)

        if (UseVfx?):
            Effect.End(TargetAgent)
