using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Editor-configurable input bridge for self-targeting abilities such as
# Ashcoil Vent and Chronoclast Reprise. Targeted/position abilities use the
# activation service from their targeting adapters instead.
aeonfall_self_ability_input_device := class(creative_device):

    @editable
    Input:input_trigger_device = input_trigger_device{}

    @editable
    AbilityId:string = ""

    @editable
    RuntimeContextId:string = "player_input"

    @editable
    Magnitude:int = 0

    OnBegin<override>()<suspends>:void=
        Input.PressedEvent.Subscribe(OnPressed)

    OnPressed(Agent:agent)<transacts>:void=
        Activated := AEONFALLAbilityActivationService.TryActivateSelf(
            Agent,
            AbilityId,
            RuntimeContextId,
            Magnitude
        )

        if (not Activated?):
            if:
                OwnerKey := AEONFALLActorRegistry.GetRuntimeKey[Agent]
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "ability.input_rejected",
                        SourceId := OwnerKey,
                        TargetId := AbilityId,
                        ContextId := RuntimeContextId
                    }
                )
