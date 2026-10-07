using { /Verse.org/Simulation }

# Transcendent Zero qualification gates.
#
# Canonical order:
# 1. Complete max-level/broad-mastery/Absolute prerequisites.
# 2. Complete Ascension Trials I-IX.
# 3. Craft the Axiom Heart.
# 4. Complete Ascension Trial X.
# 5. Become a Zero Candidate.
# 6. Pass the Choosing.
# 7. Transcendent Zero becomes activation-eligible.
aeonfall_zero_candidate_manager := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}
    LevelService:aeonfall_level_service = aeonfall_level_service{}

    RequiredLevel:int = AEONFALLMaxLevel
    RequiredMasteredClasses:int = 10
    RequiredBossClears:int = 40
    RequiredWorldEvents:int = 20
    RequiredFactionTracks:int = 8

    # AscensionRank 1 = God progression complete.
    # AscensionRank 2 = Absolute progression complete.
    RequiredAscensionRank:int = 2

    HasTrialsThroughNine(
        Profile:aeonfall_player_profile
    )<decides><transacts>:void=
        Profile.CompletedTrialIds.Find["ASC-TRIAL-001"]
        Profile.CompletedTrialIds.Find["ASC-TRIAL-002"]
        Profile.CompletedTrialIds.Find["ASC-TRIAL-003"]
        Profile.CompletedTrialIds.Find["ASC-TRIAL-004"]
        Profile.CompletedTrialIds.Find["ASC-TRIAL-005"]
        Profile.CompletedTrialIds.Find["ASC-TRIAL-006"]
        Profile.CompletedTrialIds.Find["ASC-TRIAL-007"]
        Profile.CompletedTrialIds.Find["ASC-TRIAL-008"]
        Profile.CompletedTrialIds.Find["ASC-TRIAL-009"]

    HasAllAscensionTrials(
        Profile:aeonfall_player_profile
    )<decides><transacts>:void=
        HasTrialsThroughNine[Profile]
        Profile.CompletedTrialIds.Find["ASC-TRIAL-010"]

    MeetsPreCandidateRequirements(
        Agent:agent
    )<decides><transacts>:void=
        Profile := ProfileService.GetProfile[Agent]
        CurrentLevel := LevelService.GetCurrentLevel[Agent]

        CurrentLevel >= RequiredLevel
        Profile.MasteredClassIds.Length >= RequiredMasteredClasses
        Profile.CompletedBossIds.Length >= RequiredBossClears
        Profile.CompletedWorldEventIds.Length >= RequiredWorldEvents
        Profile.FactionReputation.Length >= RequiredFactionTracks
        Profile.AscensionRank >= RequiredAscensionRank

    CanForgeAxiomHeart(
        Agent:agent
    )<decides><transacts>:void=
        Profile := ProfileService.GetProfile[Agent]

        MeetsPreCandidateRequirements[Agent]
        HasTrialsThroughNine[Profile]
        not Profile.AxiomHeartCrafted?

    MeetsRequirements(Agent:agent)<decides><transacts>:void=
        Profile := ProfileService.GetProfile[Agent]

        MeetsPreCandidateRequirements[Agent]
        HasAllAscensionTrials[Profile]
        Profile.AxiomHeartCrafted?

    EvaluateCandidate(Agent:agent)<transacts>:void=
        if:
            MeetsRequirements[Agent]
        then:
            ProfileService.SetZeroCandidate(Agent, true)

            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "transcendent.zero_candidate_granted",
                    SourceId := "player"
                }
            )
        else:
            ProfileService.SetZeroCandidate(Agent, false)
