using { /Verse.org/Simulation }

# Intermediate refinements are material transactions, not permanent unlocks.
# RCP-013 / MAT-030 must ONLY pass through the specialized final forge.
aeonfall_refinement_recipe_definition := class:
    RecipeId:string = ""
    StationId:string = ""
    OutputMaterialId:string = ""
    OutputQuantity:int = 0
    Costs:[]aeonfall_material_cost = array{}
    MinimumAscensionRank:int = 0
    RequiredTrialIds:[]string = array{}
    GateBound:logic = false

aeonfall_axiom_refinement_service := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}

    TryRefine(Agent:agent, RecipeId:string, StationId:string)<transacts>:logic=
        for (Recipe : AxiomRefinementRecipes):
            if (Recipe.RecipeId = RecipeId):
                return TryRefineDefinition(Agent, Recipe, StationId)
        false

    TryRefineDefinition(
        Agent:agent,
        Recipe:aeonfall_refinement_recipe_definition,
        StationId:string
    )<transacts>:logic=
        # Unbound narrative prerequisites are NOT silently treated as optional.
        if (not Recipe.GateBound?):
            return false
        if:
            Player := player[Agent]
            Player.IsActive[]
            Recipe.RecipeId <> "RCP-013"
            Recipe.OutputMaterialId <> "MAT-030"
            Recipe.OutputMaterialId <> ""
            Recipe.OutputQuantity > 0
            Recipe.Costs.Length > 0
            Recipe.StationId <> ""
            Recipe.StationId = StationId
            Profile := ProfileService.GetProfile[Agent]
            Profile.AscensionRank >= Recipe.MinimumAscensionRank
        then:
            var Valid:logic = true
            for (TrialId : Recipe.RequiredTrialIds):
                if:
                    Profile.CompletedTrialIds.Find[TrialId]
                then:
                    set Valid = Valid
                else:
                    set Valid = false

            # Candidate-only ledger. No writes until every gate and debit passes.
            var UpdatedLedger:[string]int = Profile.MaterialLedger
            for (Cost : Recipe.Costs):
                if:
                    Cost.MaterialId <> ""
                    Cost.MaterialId <> Recipe.OutputMaterialId
                    Cost.MaterialId <> "MAT-030"
                    Cost.Amount > 0
                    Balance := UpdatedLedger[Cost.MaterialId]
                    Balance >= Cost.Amount
                    set UpdatedLedger[Cost.MaterialId] = Balance - Cost.Amount
                then:
                    set Valid = Valid
                else:
                    set Valid = false

            if (not Valid?):
                return false

            var CurrentOutput:int = 0
            if (StoredOutput := UpdatedLedger[Recipe.OutputMaterialId]):
                set CurrentOutput = StoredOutput
            if (CurrentOutput < 0):
                return false

            if:
                set UpdatedLedger[Recipe.OutputMaterialId] = CurrentOutput + Recipe.OutputQuantity
            then:
                Candidate := aeonfall_player_profile:
                    MakeAEONFALLPlayerProfile<constructor>(Profile)
                    MaterialLedger := UpdatedLedger

                Saved := ProfileService.TrySaveProfile(Player, Candidate)
                if (not Saved?):
                    return false

                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "crafting.refinement_committed",
                        SourceId := Recipe.RecipeId,
                        TargetId := Recipe.OutputMaterialId,
                        Amount := Recipe.OutputQuantity
                    }
                )
                return true

        false
