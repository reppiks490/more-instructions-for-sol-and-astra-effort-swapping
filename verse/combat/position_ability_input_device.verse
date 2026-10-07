using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Input bridge for position-targeted abilities. The adapter resolves the
# position snapshot through AEONFALLPositionTargetingRuntime using ContextId.
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

    OnBegin<override>()<suspends>:void=
        Input.PressedEvent.Subscribe(OnPressed)

    OnPressed(Agent:agent)<transacts>:void=
        if:
            OwnerKey := AEONFALLActorRegistry.GetRuntimeKey[Agent]
            ContextId := AEONFALLPositionTargetingRuntime.CreateFromView[
                Agent,
                AbilityId,
                DistanceWorldUnits,
                ContextLifetimeSeconds
            ]
        then:
            Flags := AEONFALLActorContextRuntime.GetFlags(OwnerKey)

            Activated := AEONFALLAbilityActivationService.TryActivate(
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

            Removed := AEONFALLPositionTargetingRuntime.Remove(ContextId)
            if (Removed?):
                Removed = true

        if:
            OwnerKey := AEONFALLActorRegistry.GetRuntimeKey[Agent]
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "ability.position_input_rejected",
                    SourceId := OwnerKey,
                    TargetId := AbilityId
                }
            )
