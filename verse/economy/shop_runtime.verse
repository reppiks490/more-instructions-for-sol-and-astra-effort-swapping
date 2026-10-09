using { /Verse.org/Simulation }

# Durable unlock shop transaction.
# The first vertical slice uses in-world persistent materials/reputation only.
# Real-money purchase delivery is intentionally not part of this runtime.

aeonfall_shop_offer := class:
    ShopId:string = ""
    OfferId:string = ""
    OutputEntityId:string = ""
    Costs:[]aeonfall_material_cost = array{}
    RequiredFactionId:string = ""
    RequiredReputation:int = 0
    RequiredUnlockIds:[]string = array{}

aeonfall_shop_service := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}
    ReputationService:aeonfall_reputation_service = aeonfall_reputation_service{}

    TryPurchaseUnlock(
        Agent:agent,
        Offer:aeonfall_shop_offer
    )<transacts>:logic=
        if:
            Profile := ProfileService.GetProfile[Agent]
        then:
            if:
                Profile.UnlockedEntityIds.Find[Offer.OutputEntityId]
            then:
                return false

            var Eligible:logic = true

            if:
                Offer.RequiredFactionId <> ""
                Offer.RequiredReputation > 0
            then:
                if:
                    ReputationService.MeetsReputation[
                        Agent,
                        Offer.RequiredFactionId,
                        Offer.RequiredReputation
                    ]
                then:
                    set Eligible = Eligible
                else:
                    set Eligible = false

            for (UnlockId : Offer.RequiredUnlockIds):
                if:
                    Profile.UnlockedEntityIds.Find[UnlockId]
                then:
                    set Eligible = Eligible
                else:
                    set Eligible = false

            var RequiredTotals:[string]int = map{}
            for (Cost : Offer.Costs):
                if:
                    Cost.Amount > 0
                then:
                    if:
                        Existing := RequiredTotals[Cost.MaterialId]
                    then:
                        if:
                            set RequiredTotals[Cost.MaterialId] = Existing + Cost.Amount
                        then:
                            set Eligible = Eligible
                        else:
                            set Eligible = false
                    else:
                        if:
                            set RequiredTotals[Cost.MaterialId] = Cost.Amount
                        then:
                            set Eligible = Eligible
                        else:
                            set Eligible = false
                else:
                    set Eligible = false

            var UpdatedLedger:[string]int = Profile.MaterialLedger
            if (Eligible?):
                for (MaterialId -> RequiredAmount : RequiredTotals):
                    var Current:int = 0
                    if:
                        Stored := UpdatedLedger[MaterialId]
                    then:
                        set Current = Stored

                    if:
                        Current >= RequiredAmount
                    then:
                        if:
                            set UpdatedLedger[MaterialId] = Current - RequiredAmount
                        then:
                            set Eligible = Eligible
                        else:
                            set Eligible = false
                    else:
                        set Eligible = false

            if (Eligible?):
                Committed := ProfileService.CommitMaterialAndUnlock(
                    Agent,
                    UpdatedLedger,
                    Offer.OutputEntityId
                )
                if (not Committed?):
                    return false

                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "shop.unlock_committed",
                        SourceId := Offer.OfferId,
                        TargetId := Offer.OutputEntityId
                    }
                )

                DeliveryStarted := GetAEONFALLUnlockDeliveryService().QueueAfterCommit(
                    Agent,
                    Offer.OutputEntityId,
                    Offer.OfferId
                )
                if (not DeliveryStarted?):
                    AEONFALLRuntimeBus.Emit(
                        aeonfall_runtime_event{
                            EventType := "shop.delivery_deferred",
                            SourceId := Offer.OfferId,
                            TargetId := Offer.OutputEntityId
                        }
                    )

                return true

        false


AEONFALLShopService:aeonfall_shop_service = aeonfall_shop_service{}
