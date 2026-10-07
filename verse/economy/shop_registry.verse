# Canonical in-session registry for validated shop offers.
aeonfall_shop_registry := class():

    var Offers:[string]aeonfall_shop_offer = map{}

    Register(Offer:aeonfall_shop_offer)<transacts>:logic=
        if:
            Offer.OfferId <> ""
            Offer.OutputEntityId <> ""
            set Offers[Offer.OfferId] = Offer
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "shop.offer_registered",
                    SourceId := Offer.OfferId,
                    TargetId := Offer.OutputEntityId
                }
            )
            return true

        false

    Get(OfferId:string)<decides><transacts>:aeonfall_shop_offer=
        Offers[OfferId]

    IsRegistered(OfferId:string)<decides><transacts>:void=
        Offer := Offers[OfferId]
        Offer.OfferId <> ""

AEONFALLShopRegistry:aeonfall_shop_registry = aeonfall_shop_registry{}
