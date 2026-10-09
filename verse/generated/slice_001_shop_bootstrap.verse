using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# GENERATED FILE — do not hand edit.
# Source: content/vertical_slice/slice_001_shop.json

Slice001ShopOffers:[]aeonfall_shop_offer = array{
    aeonfall_shop_offer{
        ShopId := "SHOP-001",
        OfferId := "OFFER-001",
        OutputEntityId := "WPN-001",
        Costs := array{aeonfall_material_cost{MaterialId := "MAT-008", Amount := 45}},
        RequiredFactionId := "FAC-002",
        RequiredReputation := 0,
        RequiredUnlockIds := array{}
    },
    aeonfall_shop_offer{
        ShopId := "SHOP-001",
        OfferId := "OFFER-002",
        OutputEntityId := "WPN-007",
        Costs := array{aeonfall_material_cost{MaterialId := "MAT-008", Amount := 75}, aeonfall_material_cost{MaterialId := "MAT-003", Amount := 15}},
        RequiredFactionId := "FAC-002",
        RequiredReputation := 50,
        RequiredUnlockIds := array{}
    },
    aeonfall_shop_offer{
        ShopId := "SHOP-001",
        OfferId := "OFFER-003",
        OutputEntityId := "WPN-122",
        Costs := array{aeonfall_material_cost{MaterialId := "MAT-008", Amount := 140}, aeonfall_material_cost{MaterialId := "MAT-003", Amount := 35}},
        RequiredFactionId := "FAC-002",
        RequiredReputation := 100,
        RequiredUnlockIds := array{"WPN-001"}
    },
    aeonfall_shop_offer{
        ShopId := "SHOP-001",
        OfferId := "OFFER-004",
        OutputEntityId := "ARM-002",
        Costs := array{aeonfall_material_cost{MaterialId := "MAT-008", Amount := 225}, aeonfall_material_cost{MaterialId := "MAT-003", Amount := 120}, aeonfall_material_cost{MaterialId := "MAT-011", Amount := 1}},
        RequiredFactionId := "FAC-002",
        RequiredReputation := 200,
        RequiredUnlockIds := array{"WPN-122"}
    },
    aeonfall_shop_offer{
        ShopId := "SHOP-001",
        OfferId := "OFFER-005",
        OutputEntityId := "VEH-010",
        Costs := array{aeonfall_material_cost{MaterialId := "MAT-003", Amount := 350}, aeonfall_material_cost{MaterialId := "MAT-008", Amount := 250}, aeonfall_material_cost{MaterialId := "MAT-011", Amount := 2}},
        RequiredFactionId := "FAC-002",
        RequiredReputation := 300,
        RequiredUnlockIds := array{"ARM-002"}
    },
}

aeonfall_slice_001_shop_bootstrap_device := class(creative_device):

    OnBegin<override>()<suspends>:void=
        for (Offer : Slice001ShopOffers):
            Registered := GetAEONFALLShopRegistry().Register(Offer)
            if (not Registered?):
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "bootstrap.shop_offer_registration_failed",
                        SourceId := Offer.OfferId,
                        TargetId := Offer.OutputEntityId
                    }
                )
