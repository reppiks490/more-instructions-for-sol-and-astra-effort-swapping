using { /Fortnite.com/Devices }
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
    ReconciliationStopped:event() = event(){}

    OnBegin<override>()<suspends>:void=
        Subscription := AEONFALLRuntimeBus.RuntimeEvent.Subscribe(OnRuntimeEvent)
        set BusSubscription = option{Subscription}
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

    OnRuntimeEvent(Event:aeonfall_runtime_event):void=
        if:
            Event.EventType = "status.applied"
            Event.ContextId = StatusId
            AEONFALLStatusRuntime.HasStatus(Event.TargetId, StatusId)?
            TargetAgent := AEONFALLActorRegistry.GetAgent[Event.TargetId]
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

        # Admission to tracking precedes every physical effect. A failed map
        # write leaves no new effect that reconciliation would be unable to find.
        if (set AppliedAgents[TargetKey] = TargetAgent):
            if (TrackedAgent := PreviousAgent?, TrackedAgent <> TargetAgent):
                Cleanup(TrackedAgent)

            # Every valid applied command, including a duration refresh or a
            # stack-cap reapplication, retriggers the authored devices.
            if (UseApplyTrigger?):
                ApplyTrigger.Trigger(TargetAgent)
            if (UseVfx?):
                Effect.Begin(TargetAgent)

    CleanupIfStale(TargetKey:string):void=
        if (TrackedAgent := AppliedAgents[TargetKey]):
            if:
                AEONFALLStatusRuntime.HasStatus(TargetKey, StatusId)?
                CurrentAgent := AEONFALLActorRegistry.GetAgent[TargetKey]
                CurrentAgent = TrackedAgent
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
        set AppliedAgents = Remaining

    CleanupAll():void=
        Tracked := AppliedAgents
        set AppliedAgents = map{}
        for (TargetKey -> TrackedAgent : Tracked):
            Cleanup(TrackedAgent)

    Cleanup(TargetAgent:agent):void=
        if (UseRemoveTrigger?):
            RemoveTrigger.Trigger(TargetAgent)

        if (UseVfx?):
            Effect.End(TargetAgent)
