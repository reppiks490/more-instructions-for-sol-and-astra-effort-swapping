using { /Verse.org/Simulation }

# Runtime recipe definition for persistent unlock crafting.
aeonfall_recipe_definition := class:
    RecipeId:string = ""
    StationId:string = ""
    OutputEntityId:string = ""
    Costs:[]aeonfall_material_cost = array{}
    RequiredUnlockIds:[]string = array{}

aeonfall_recipe_service := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}

    # Builds the entire candidate ledger in memory and commits material costs
    # plus the durable entity unlock in one profile replacement.
    TryCraftUnlock(
        Agent:agent,
        Recipe:aeonfall_recipe_definition
    )<transacts>:logic=
        if:
            Profile := ProfileService.GetProfile[Agent]
        then:
            if:
                Profile.UnlockedEntityIds.Find[Recipe.OutputEntityId]
            then:
                return false

            var RequirementsMet:logic = true
            for (UnlockId : Recipe.RequiredUnlockIds):
                if:
                    Profile.UnlockedEntityIds.Find[UnlockId]
                then:
                    set RequirementsMet = RequirementsMet
                else:
                    set RequirementsMet = false

            var RequiredTotals:[string]int = map{}
            for (Cost : Recipe.Costs):
                if:
                    Cost.Amount > 0
                then:
                    if:
                        Existing := RequiredTotals[Cost.MaterialId]
                    then:
                        if:
                            set RequiredTotals[Cost.MaterialId] = Existing + Cost.Amount
                        then:
                            set RequirementsMet = RequirementsMet
                        else:
                            set RequirementsMet = false
                    else:
                        if:
                            set RequiredTotals[Cost.MaterialId] = Cost.Amount
                        then:
                            set RequirementsMet = RequirementsMet
                        else:
                            set RequirementsMet = false
                else:
                    set RequirementsMet = false

            var UpdatedLedger:[string]int = Profile.MaterialLedger
            if (RequirementsMet?):
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
                            set RequirementsMet = RequirementsMet
                        else:
                            set RequirementsMet = false
                    else:
                        set RequirementsMet = false

            if (RequirementsMet?):
                Committed := ProfileService.CommitMaterialAndUnlock(
                    Agent,
                    UpdatedLedger,
                    Recipe.OutputEntityId
                )
                if (not Committed?):
                    return false
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "crafting.unlock_committed",
                        SourceId := Recipe.RecipeId,
                        TargetId := Recipe.OutputEntityId
                    }
                )

                DeliveryStarted := GetAEONFALLUnlockDeliveryService().QueueAfterCommit(
                    Agent,
                    Recipe.OutputEntityId,
                    Recipe.RecipeId
                )
                if (not DeliveryStarted?):
                    AEONFALLRuntimeBus.Emit(
                        aeonfall_runtime_event{
                            EventType := "crafting.delivery_deferred",
                            SourceId := Recipe.RecipeId,
                            TargetId := Recipe.OutputEntityId
                        }
                    )

                return true

        false


AEONFALLRecipeService:aeonfall_recipe_service = aeonfall_recipe_service{}
