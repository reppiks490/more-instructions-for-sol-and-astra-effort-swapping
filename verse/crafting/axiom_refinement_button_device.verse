using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Place one device per physical refinement station/button in the UEFN editor.
# StationId MUST match the canonical recipe station; a wrong editor binding
# fails closed. Editor placement and native Verse compilation remain required.
aeonfall_axiom_refinement_button_device := class(creative_device):

    @editable
    RefinementButton:button_device = button_device{}

    @editable
    RecipeId:string = ""

    @editable
    StationId:string = ""

    @editable
    SuccessMessage:hud_message_device = hud_message_device{}

    @editable
    RejectedMessage:hud_message_device = hud_message_device{}

    RefinementService:aeonfall_axiom_refinement_service = aeonfall_axiom_refinement_service{}
    var ButtonSubscription:?cancelable = false

    OnBegin<override>()<suspends>:void=
        Subscription := RefinementButton.InteractedWithEvent.Subscribe(OnInteracted)
        set ButtonSubscription = option{Subscription}

    OnEnd<override>():void=
        if (Subscription := ButtonSubscription?):
            Subscription.Cancel()
        set ButtonSubscription = false

    OnInteracted(Agent:agent)<transacts>:void=
        Crafted := RefinementService.TryRefine(Agent, RecipeId, StationId)
        if (Crafted?):
            SuccessMessage.Show(Agent)
            return
        RejectedMessage.Show(Agent)
