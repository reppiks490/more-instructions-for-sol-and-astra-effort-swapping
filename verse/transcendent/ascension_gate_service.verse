using { /Verse.org/Simulation }

# Enforces the final progression gates around Transcendent Zero.
#
# IMPORTANT:
# - Becoming a Zero Candidate never grants the final tier.
# - Crafting the Axiom Heart never grants the final tier.
# - The Choosing remains a separate encounter/system.
# - No purchase flag can satisfy any of these checks.
aeonfall_ascension_gate_service := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}
    CandidateManager:aeonfall_zero_candidate_manager = aeonfall_zero_candidate_manager{}

    RequiredTrials:int = 10
    RequiredAbsoluteRank:int = 2

    CanEnterChoosing(Agent:agent)<decides><transacts>:void=
        Profile := ProfileService.GetProfile[Agent]

        CandidateManager.MeetsRequirements[Agent]
        Profile.IsZeroCandidate?
        Profile.AxiomHeartCrafted?
        Profile.AscensionRank >= RequiredAbsoluteRank
        Profile.CompletedTrialIds.Length >= RequiredTrials

    # TranscendentState is intentionally an integer state machine rather than
    # a permanent boolean. Runtime mapping is owned by the transformation
    # controller once the UEFN project is bound.
    #
    # 0 = none/dormant
    # 1 = Choosing passed, ascension available
    # 2 = active transformation
    # 3 = cooldown/exhaustion
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
