using { /Verse.org/Simulation }

# Transcendent Zero qualification gate.
# Qualification only grants candidacy; it never grants the final tier directly.
aeonfall_zero_candidate_manager := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}
    LevelService:aeonfall_level_service = aeonfall_level_service{}

    RequiredLevel:int = 100
    RequiredMasteredClasses:int = 8
    RequiredBossClears:int = 20
    RequiredWorldEvents:int = 15
    RequiredTrials:int = 10
    RequiredFactionTracks:int = 8

    MeetsRequirements(Agent:agent)<decides><transacts>:void=
        Profile := ProfileService.GetProfile[Agent]
        CurrentLevel := LevelService.GetCurrentLevel[Agent]

        CurrentLevel >= RequiredLevel
        Profile.MasteredClassIds.Length >= RequiredMasteredClasses
        Profile.CompletedBossIds.Length >= RequiredBossClears
        Profile.CompletedWorldEventIds.Length >= RequiredWorldEvents
        Profile.CompletedTrialIds.Length >= RequiredTrials
        Profile.FactionReputation.Length >= RequiredFactionTracks
        Profile.AxiomHeartCrafted?

    EvaluateCandidate(Agent:agent):void=
        if:
            MeetsRequirements[Agent]
        then:
            ProfileService.SetZeroCandidate(Agent, true)
        else:
            ProfileService.SetZeroCandidate(Agent, false)
