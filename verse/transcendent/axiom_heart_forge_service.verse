using { /Verse.org/Simulation }

# Server-owned final craft for canonical RCP-013. Refined inputs are earned
# through the separate RCP-001..012/014 graph; this service does not mint them.
# No suspension occurs between eligibility, ledger debit, and checked save.
aeonfall_axiom_heart_forge_service := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}
    CandidateManager:aeonfall_zero_candidate_manager = aeonfall_zero_candidate_manager{}

    TryForge(Agent:agent)<transacts>:logic=
        if:
            Player := player[Agent]
            Player.IsActive[]
            CandidateManager.CanForgeAxiomHeart[Agent]
            Profile := ProfileService.GetProfile[Agent]
        then:
            # Trial X / Choosing cannot be used to re-enter this transaction.
            if (Profile.AxiomHeartCrafted?):
                return false
            if (Profile.TranscendentState <> 0):
                return false

            # A pre-existing apex output is not proof of a valid forge.
            if (ExistingHeart := Profile.MaterialLedger[AxiomHeartFinalOutputMaterialId]):
                if (ExistingHeart <> 0):
                    return false

            var UpdatedLedger:[string]int = Profile.MaterialLedger
            var CostsValid:logic = true
            for (Cost : AxiomHeartFinalCosts):
                if:
                    Cost.MaterialId <> ""
                    Cost.MaterialId <> AxiomHeartFinalOutputMaterialId
                    Cost.Amount > 0
                    Balance := UpdatedLedger[Cost.MaterialId]
                    Balance >= Cost.Amount
                    set UpdatedLedger[Cost.MaterialId] = Balance - Cost.Amount
                then:
                    set CostsValid = CostsValid
                else:
                    set CostsValid = false

            if (not CostsValid?):
                return false

            if:
                set UpdatedLedger[AxiomHeartFinalOutputMaterialId] = 1
            then:
                # A single acknowledged profile replacement binds the material
                # debits, apex output, and permanent ascension eligibility.
                Candidate := aeonfall_player_profile:
                    MakeAEONFALLPlayerProfile<constructor>(Profile)
                    MaterialLedger := UpdatedLedger
                    AxiomHeartCrafted := true

                Saved := ProfileService.TrySaveProfile(Player, Candidate)
                if (Saved?):
                    AEONFALLRuntimeBus.Emit(
                        aeonfall_runtime_event{
                            EventType := "transcendent.axiom_heart_forged",
                            SourceId := AxiomHeartFinalRecipeId,
                            TargetId := AxiomHeartFinalOutputMaterialId
                        }
                    )
                    return true

        false
