using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Input bridge for abilities that consume the owner's current actor target.
# Project-bound targeting logic must set AEONFALLTargetingRuntime first.
aeonfall_targeted_ability_input_device := class(creative_device):

    @editable
    Input:input_trigger_device = input_trigger_device{}

    @editable
    AbilityId:string = ""

    @editable
    Magnitude:int = 0

    OnBegin<override>()<suspends>:void=
        Input.PressedEvent.Subscribe(OnPressed)

    OnPressed(Agent:agent)<transacts>:void=
        if:
            OwnerKey := AEONFALLActorRegistry.GetRuntimeKey[Agent]
            Selection := AEONFALLTargetingRuntime.GetSelection[OwnerKey]
        then:
            Flags := AEONFALLActorContextRuntime.GetFlags(OwnerKey)

            Activated := AEONFALLAbilityActivationService.TryActivate(
                Agent,
                AbilityId,
                Selection.TargetKey,
                Selection.ContextId,
                Magnitude,
                Flags.EncounterActive,
                Flags.TransformationActive
            )

            if (Activated?):
                return

        if:
            OwnerKey := AEONFALLActorRegistry.GetRuntimeKey[Agent]
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "ability.targeted_input_rejected",
                    SourceId := OwnerKey,
                    TargetId := AbilityId
                }
            )
