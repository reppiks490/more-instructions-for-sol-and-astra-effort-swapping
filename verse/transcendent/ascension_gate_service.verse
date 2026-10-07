using { /Verse.org/Simulation }

# Final gate around the Choosing and Transcendent Zero activation.
aeonfall_ascension_gate_service := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}
    CandidateManager:aeonfall_zero_candidate_manager = aeonfall_zero_candidate_manager{}

    RequiredAbsoluteRank:int = 2

    CanEnterChoosing(Agent:agent)<decides><transacts>:void=
        Profile := ProfileService.GetProfile[Agent]

        CandidateManager.MeetsRequirements[Agent]
        Profile.IsZeroCandidate?
        Profile.AxiomHeartCrafted?
        Profile.AscensionRank >= RequiredAbsoluteRank
        Profile.TranscendentState = 0

    # Persistent TranscendentState:
    # 0 = Choosing not yet completed
    # 1 = Choosing passed / activation permanently unlocked
    # Active transformation and cooldown/exhaustion are session-only runtime
    # state and must never be persisted as profile values 2/3.
    CanActivateTranscendentState(Agent:agent)<decides><transacts>:void=
        Profile := ProfileService.GetProfile[Agent]
        Profile.IsZeroCandidate?
        Profile.AxiomHeartCrafted?
        Profile.AscensionRank >= RequiredAbsoluteRank
        Profile.TranscendentState = 1

    IsDormantTranscendent(Agent:agent)<decides><transacts>:void=
        Profile := ProfileService.GetProfile[Agent]
        Profile.TranscendentHistoryCount > 0
        Profile.TranscendentState = 0
