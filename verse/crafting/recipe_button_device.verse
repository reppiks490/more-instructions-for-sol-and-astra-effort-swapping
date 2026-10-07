using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# One editor-bound crafting interaction.
# Recipe costs/prerequisites stay in the generated registry so stations do not
# duplicate balance data in editor properties.
aeonfall_recipe_button_device := class(creative_device):

    @editable
    Button:button_device = button_device{}

    @editable
    RecipeId:string = ""

    @editable
    SuccessMessage:hud_message_device = hud_message_device{}

    @editable
    RejectedMessage:hud_message_device = hud_message_device{}

    OnBegin<override>()<suspends>:void=
        Button.InteractedWithEvent.Subscribe(OnInteracted)

    OnInteracted(Agent:agent)<transacts>:void=
        if:
            Recipe := AEONFALLRecipeRegistry.Get[RecipeId]
        then:
            Crafted := AEONFALLRecipeService.TryCraftUnlock(
                Agent,
                Recipe
            )

            if (Crafted?):
                SuccessMessage.Show(Agent)

                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "crafting.interaction_succeeded",
                        SourceId := RecipeId,
                        TargetId := Recipe.OutputEntityId
                    }
                )
                return

        RejectedMessage.Show(Agent)

        AEONFALLRuntimeBus.Emit(
            aeonfall_runtime_event{
                EventType := "crafting.interaction_rejected",
                SourceId := RecipeId
            }
        )
