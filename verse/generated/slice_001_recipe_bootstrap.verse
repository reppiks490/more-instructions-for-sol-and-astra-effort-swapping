using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# GENERATED FILE — do not hand edit.
# Source: content/vertical_slice/slice_001_recipes.json

Slice001RecipeDefinitions:[]aeonfall_recipe_definition = array{
    aeonfall_recipe_definition{
        RecipeId := "SLR-001",
        StationId := "STATION::GRAVE-MARKET-FORGE",
        OutputEntityId := "WPN-001",
        Costs := array{aeonfall_material_cost{MaterialId := "MAT-008", Amount := 60}, aeonfall_material_cost{MaterialId := "MAT-003", Amount := 20}},
        RequiredUnlockIds := array{}
    },
    aeonfall_recipe_definition{
        RecipeId := "SLR-002",
        StationId := "STATION::GRAVE-MARKET-FORGE",
        OutputEntityId := "WPN-007",
        Costs := array{aeonfall_material_cost{MaterialId := "MAT-008", Amount := 30}, aeonfall_material_cost{MaterialId := "MAT-003", Amount := 20}},
        RequiredUnlockIds := array{}
    },
    aeonfall_recipe_definition{
        RecipeId := "SLR-003",
        StationId := "STATION::OSSUARY-WORKBENCH",
        OutputEntityId := "WPN-122",
        Costs := array{aeonfall_material_cost{MaterialId := "MAT-008", Amount := 80}, aeonfall_material_cost{MaterialId := "MAT-003", Amount := 40}},
        RequiredUnlockIds := array{"WPN-001"}
    },
    aeonfall_recipe_definition{
        RecipeId := "SLR-004",
        StationId := "STATION::OSSUARY-WORKBENCH",
        OutputEntityId := "WPN-124",
        Costs := array{aeonfall_material_cost{MaterialId := "MAT-008", Amount := 120}, aeonfall_material_cost{MaterialId := "MAT-003", Amount := 60}, aeonfall_material_cost{MaterialId := "MAT-011", Amount := 1}},
        RequiredUnlockIds := array{"WPN-001"}
    },
    aeonfall_recipe_definition{
        RecipeId := "SLR-005",
        StationId := "STATION::SAINTLESS-RELIQUARY",
        OutputEntityId := "ARM-002",
        Costs := array{aeonfall_material_cost{MaterialId := "MAT-008", Amount := 150}, aeonfall_material_cost{MaterialId := "MAT-003", Amount := 100}, aeonfall_material_cost{MaterialId := "MAT-011", Amount := 2}},
        RequiredUnlockIds := array{"WPN-124"}
    },
    aeonfall_recipe_definition{
        RecipeId := "SLR-006",
        StationId := "STATION::BONE-HAULER-YARD",
        OutputEntityId := "VEH-010",
        Costs := array{aeonfall_material_cost{MaterialId := "MAT-003", Amount := 300}, aeonfall_material_cost{MaterialId := "MAT-008", Amount := 200}, aeonfall_material_cost{MaterialId := "MAT-011", Amount := 3}},
        RequiredUnlockIds := array{"ARM-002"}
    },
}

aeonfall_slice_001_recipe_bootstrap_device := class(creative_device):

    OnBegin<override>()<suspends>:void=
        for (Recipe : Slice001RecipeDefinitions):
            Registered := AEONFALLRecipeRegistry.Register(Recipe)
            if (not Registered?):
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "bootstrap.recipe_registration_failed",
                        SourceId := Recipe.RecipeId,
                        TargetId := Recipe.OutputEntityId
                    }
                )
