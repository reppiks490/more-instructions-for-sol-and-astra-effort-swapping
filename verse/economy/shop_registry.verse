using { /Verse.org/Verse }
using { /Verse.org/Simulation }
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

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLShopRegistrySessions:weak_map(session, aeonfall_shop_registry) = map{}

GetAEONFALLShopRegistry()<transacts>:aeonfall_shop_registry=
    CurrentSession := GetSession()
    if (Existing := AEONFALLShopRegistrySessions[CurrentSession]):
        return Existing
    Created := aeonfall_shop_registry{}
    if (set AEONFALLShopRegistrySessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLShopRegistry in its session")
