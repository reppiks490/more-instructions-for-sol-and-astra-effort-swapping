using { /Verse.org/Simulation }

# Runtime progression facade.
aeonfall_level_service := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}

    XPForLevel(Level:int):int=
        AEONFALLXPForLevel(Level)

    GetLevelForXP(XP:int)<transacts>:int=
        AEONFALLGetLevelForXP(XP)

    GrantXP(Agent:agent, Amount:int)<transacts>:void=
        ProfileService.GrantXP(Agent, Amount)

    GetCurrentLevel(Agent:agent)<decides><transacts>:int=
        Profile := ProfileService.GetProfile[Agent]
        AEONFALLGetLevelForXP(Profile.XP)
