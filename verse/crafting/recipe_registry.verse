# Canonical in-session registry for validated crafting recipes.
aeonfall_recipe_registry := class():

    var Recipes:[string]aeonfall_recipe_definition = map{}

    Register(Recipe:aeonfall_recipe_definition)<transacts>:logic=
        if:
            Recipe.RecipeId <> ""
            Recipe.OutputEntityId <> ""
            Recipe.Costs.Length > 0
            set Recipes[Recipe.RecipeId] = Recipe
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "crafting.recipe_registered",
                    SourceId := Recipe.RecipeId,
                    TargetId := Recipe.OutputEntityId
                }
            )
            return true

        false

    Get(RecipeId:string)<decides><transacts>:aeonfall_recipe_definition=
        Recipes[RecipeId]

    IsRegistered(RecipeId:string)<decides><transacts>:void=
        Recipe := Recipes[RecipeId]
        Recipe.RecipeId <> ""

AEONFALLRecipeRegistry:aeonfall_recipe_registry = aeonfall_recipe_registry{}
