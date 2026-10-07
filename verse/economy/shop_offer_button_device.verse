using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# One editor-bound Grave Market purchase interaction.
# Offer content and costs stay in the generated registry; the placed device
# only selects which canonical offer this button represents.
aeonfall_shop_offer_button_device := class(creative_device):

    @editable
    Button:button_device = button_device{}

    @editable
    OfferId:string = ""

    @editable
    SuccessMessage:hud_message_device = hud_message_device{}

    @editable
    RejectedMessage:hud_message_device = hud_message_device{}

    OnBegin<override>()<suspends>:void=
        Button.InteractedWithEvent.Subscribe(OnInteracted)

    OnInteracted(Agent:agent)<transacts>:void=
        if:
            Offer := AEONFALLShopRegistry.Get[OfferId]
        then:
            Purchased := AEONFALLShopService.TryPurchaseUnlock(
                Agent,
                Offer
            )

            if (Purchased?):
                SuccessMessage.Show(Agent)

                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "shop.interaction_succeeded",
                        SourceId := OfferId,
                        TargetId := Offer.OutputEntityId
                    }
                )
                return

        RejectedMessage.Show(Agent)

        AEONFALLRuntimeBus.Emit(
            aeonfall_runtime_event{
                EventType := "shop.interaction_rejected",
                SourceId := OfferId
            }
        )
