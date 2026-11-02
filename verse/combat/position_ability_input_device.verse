using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Input bridge for position-targeted abilities. The adapter resolves the
# position snapshot through GetAEONFALLPositionTargetingRuntime() using ContextId.
aeonfall_position_ability_input_device := class(creative_device):

    @editable
    Input:input_trigger_device = input_trigger_device{}

    @editable
    AbilityId:string = ""

    @editable
    DistanceWorldUnits:float = 600.0

    @editable
    ContextLifetimeSeconds:float = 3.0

    @editable
    Magnitude:int = 0

    var Running:logic = false
    var InputSubscription:?cancelable = false

    OnBegin<override>()<suspends>:void=
        # An unconfigured input device must not observe player actions.
        if (AbilityId = ""):
            Print("AEONFALL ability input rejected empty canonical ability ID.")
            return
        set Running = true
        Bound := Input.PressedEvent.Subscribe(OnPressed)
        set InputSubscription = option{Bound}

    OnEnd<override>():void=
        set Running = false
        if (Bound := InputSubscription?):
            Bound.Cancel()
        set InputSubscription = false

    OnPressed(Agent:agent)<transacts>:void=
        if (not Running?):
            return
        if:
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
            ContextId := GetAEONFALLPositionTargetingRuntime().CreateFromView[
                Agent,
                AbilityId,
                DistanceWorldUnits,
                ContextLifetimeSeconds
            ]
        then:
            Flags := GetAEONFALLActorContextRuntime().GetFlags(OwnerKey)

            Activated := GetAEONFALLAbilityActivationService().TryActivate(
                Agent,
                AbilityId,
                OwnerKey,
                ContextId,
                Magnitude,
                Flags.EncounterActive,
                Flags.TransformationActive
            )

            if (Activated?):
                return

            Removed := GetAEONFALLPositionTargetingRuntime().Remove(ContextId)

        if:
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "ability.position_input_rejected",
                    SourceId := OwnerKey,
                    TargetId := AbilityId
                }
            )
