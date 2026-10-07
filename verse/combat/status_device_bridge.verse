using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

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

    OnBegin<override>()<suspends>:void=
        AEONFALLRuntimeBus.RuntimeEvent.Subscribe(OnRuntimeEvent)

    OnRuntimeEvent(Event:aeonfall_runtime_event)<transacts>:void=
        if:
            Event.EventType = "status.applied"
            Event.ContextId = StatusId
            TargetAgent := AEONFALLActorRegistry.GetAgent[Event.TargetId]
        then:
            if (UseApplyTrigger?):
                ApplyTrigger.Trigger(TargetAgent)

            if (UseVfx?):
                Effect.Begin(TargetAgent)

            return

        if:
            Event.EventType = "status.removed"
            Event.ContextId = StatusId
            TargetAgent := AEONFALLActorRegistry.GetAgent[Event.TargetId]
        then:
            Cleanup(TargetAgent)
            return

        if:
            Event.EventType = "status.expired"
            Event.ContextId = StatusId
            TargetAgent := AEONFALLActorRegistry.GetAgent[Event.TargetId]
        then:
            Cleanup(TargetAgent)
            return

        if:
            Event.EventType = "status.target_cleared"
            TargetAgent := AEONFALLActorRegistry.GetAgent[Event.TargetId]
        then:
            Cleanup(TargetAgent)

    Cleanup(TargetAgent:agent)<transacts>:void=
        if (UseRemoveTrigger?):
            RemoveTrigger.Trigger(TargetAgent)

        if (UseVfx?):
            Effect.End(TargetAgent)
