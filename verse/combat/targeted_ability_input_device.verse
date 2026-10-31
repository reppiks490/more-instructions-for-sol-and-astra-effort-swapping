using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Input bridge for abilities that consume the owner's current actor target.
# Project-bound targeting logic must set GetAEONFALLTargetingRuntime() first.
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
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
            Selection := GetAEONFALLTargetingRuntime().GetSelection[OwnerKey]
        then:
            Flags := GetAEONFALLActorContextRuntime().GetFlags(OwnerKey)

            Activated := GetAEONFALLAbilityActivationService().TryActivate(
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
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "ability.targeted_input_rejected",
                    SourceId := OwnerKey,
                    TargetId := AbilityId
                }
            )
