using { /Verse.org/Simulation }

# Runtime progression policy.
# Exact balance values stay centralized here instead of leaking into encounters.
AEONFALLMaxLevel:int = 1000

aeonfall_level_service := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}

    # Initial curve scaffold. Production values will be tuned from playtest telemetry.
    # Level 1000 is intentionally reachable only after very large cumulative XP.
    XPForLevel(Level:int):int=
        if (Level <= 1):
            0
        else if (Level >= AEONFALLMaxLevel):
            500 * AEONFALLMaxLevel * AEONFALLMaxLevel
        else:
            # Quadratic-style growth without relying on hidden per-entity constants.
            500 * Level * Level

    # Finite bounded scan: no scheduler loop and no possibility of a runaway
    # progression task. This is called on progression reads, not every runtime tick.
    GetLevelForXP(XP:int)<transacts>:int=
        var Level:int = 1

        for (CandidateLevel := 2..AEONFALLMaxLevel):
            if (XP >= XPForLevel(CandidateLevel)):
                set Level = CandidateLevel

        Level

    GrantXP(Agent:agent, Amount:int)<transacts>:void=
        ProfileService.GrantXP(Agent, Amount)

    GetCurrentLevel(Agent:agent)<decides><transacts>:int=
        Profile := ProfileService.GetProfile[Agent]
        GetLevelForXP(Profile.XP)
