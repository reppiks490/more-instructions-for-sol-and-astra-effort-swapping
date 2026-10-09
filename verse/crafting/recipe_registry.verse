using { /Verse.org/Verse }
using { /Verse.org/Simulation }
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

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLRecipeRegistrySessions:weak_map(session, aeonfall_recipe_registry) = map{}

GetAEONFALLRecipeRegistry()<transacts>:aeonfall_recipe_registry=
    CurrentSession := GetSession()
    if (Existing := AEONFALLRecipeRegistrySessions[CurrentSession]):
        return Existing
    Created := aeonfall_recipe_registry{}
    if (set AEONFALLRecipeRegistrySessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLRecipeRegistry in its session")
