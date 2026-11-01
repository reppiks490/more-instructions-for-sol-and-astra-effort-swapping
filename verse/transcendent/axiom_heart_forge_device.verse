using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Bind this device's Button to the actual Throne of Zero forge interaction
# in UEFN. A placed device is not proof that the physical binding is correct.
aeonfall_axiom_heart_forge_device := class(creative_device):

    @editable
    ForgeButton:button_device = button_device{}

    @editable
    SuccessMessage:hud_message_device = hud_message_device{}

    @editable
    RejectedMessage:hud_message_device = hud_message_device{}

    ForgeService:aeonfall_axiom_heart_forge_service = aeonfall_axiom_heart_forge_service{}
    var ButtonSubscription:?cancelable = false

    OnBegin<override>()<suspends>:void=
        Subscription := ForgeButton.InteractedWithEvent.Subscribe(OnInteracted)
        set ButtonSubscription = option{Subscription}

    OnEnd<override>():void=
        if (Subscription := ButtonSubscription?):
            Subscription.Cancel()
        set ButtonSubscription = false

    OnInteracted(Agent:agent)<transacts>:void=
        Forged := ForgeService.TryForge(Agent)
        if (Forged?):
            SuccessMessage.Show(Agent)
            return
        RejectedMessage.Show(Agent)
