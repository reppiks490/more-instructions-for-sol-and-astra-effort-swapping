using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Editor-facing bridge for one Transcendent Zero Authority.
# Place/configure one instance per Authority selection surface.
aeonfall_transcendent_authority_input_device := class(creative_device):

    @editable
    ActivateInput:input_trigger_device = input_trigger_device{}

    @editable
    CancelInput:input_trigger_device = input_trigger_device{}

    @editable
    AuthorityId:string = ""

    OnBegin<override>()<suspends>:void=
        ActivateInput.PressedEvent.Subscribe(OnActivatePressed)
        CancelInput.PressedEvent.Subscribe(OnCancelPressed)

    OnActivatePressed(Agent:agent)<transacts>:void=
        Activated := AEONFALLTranscendentRuntime.Activate(
            Agent,
            AuthorityId
        )

        if (not Activated?):
            if:
                OwnerKey := AEONFALLActorRegistry.GetRuntimeKey[Agent]
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "transcendent.activation_rejected",
                        SourceId := OwnerKey,
                        TargetId := AuthorityId
                    }
                )

    OnCancelPressed(Agent:agent)<transacts>:void=
        Ended := AEONFALLTranscendentRuntime.EndForAgent(
            Agent,
            "manual_cancel"
        )

        if (not Ended?):
            if:
                OwnerKey := AEONFALLActorRegistry.GetRuntimeKey[Agent]
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "transcendent.cancel_rejected",
                        SourceId := OwnerKey,
                        TargetId := AuthorityId
                    }
                )
