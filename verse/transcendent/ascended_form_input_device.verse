using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Editor-facing God / Absolute transformation bridge.
aeonfall_ascended_form_input_device := class(creative_device):

    @editable
    ActivateInput:input_trigger_device = input_trigger_device{}

    @editable
    CancelInput:input_trigger_device = input_trigger_device{}

    @editable
    FormId:string = ""

    OnBegin<override>()<suspends>:void=
        ActivateInput.PressedEvent.Subscribe(OnActivatePressed)
        CancelInput.PressedEvent.Subscribe(OnCancelPressed)

    OnActivatePressed(Agent:agent)<transacts>:void=
        Activated := AEONFALLAscendedFormRuntime.Activate(
            Agent,
            FormId
        )

        if (not Activated?):
            if:
                OwnerKey := AEONFALLActorRegistry.GetRuntimeKey[Agent]
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "ascended_form.activation_rejected",
                        SourceId := OwnerKey,
                        TargetId := FormId
                    }
                )

    OnCancelPressed(Agent:agent)<transacts>:void=
        Ended := AEONFALLAscendedFormRuntime.EndForAgent(
            Agent,
            "manual_cancel"
        )

        if (not Ended?):
            if:
                OwnerKey := AEONFALLActorRegistry.GetRuntimeKey[Agent]
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "ascended_form.cancel_rejected",
                        SourceId := OwnerKey,
                        TargetId := FormId
                    }
                )
