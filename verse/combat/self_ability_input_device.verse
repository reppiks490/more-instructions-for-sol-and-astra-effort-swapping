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
        Activated := GetAEONFALLAbilityActivationService().TryActivateSelf(
            Agent,
            AbilityId,
            RuntimeContextId,
            Magnitude
        )

        if (not Activated?):
            if:
                OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "ability.input_rejected",
                        SourceId := OwnerKey,
                        TargetId := AbilityId,
                        ContextId := RuntimeContextId
                    }
                )
