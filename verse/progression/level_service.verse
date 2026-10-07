using { /Verse.org/Simulation }

# Runtime progression policy.
# Exact balance values stay centralized here instead of leaking into encounters.
aeonfall_level_service := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}

    # Initial curve scaffold. Production values will be tuned from playtest telemetry.
    XPForLevel(Level:int):int=
        if (Level <= 1):
            0
        else:
            # Quadratic-style growth without relying on hidden per-entity constants.
            500 * Level * Level

    GetLevelForXP(XP:int):int=
        var Level:int = 1
        var Continue:logic = true

        loop:
            if:
                Continue?
                XP >= XPForLevel(Level + 1)
                Level < 100
            then:
                set Level += 1
            else:
                set Continue = false
                break

        Level

    GrantXP(Agent:agent, Amount:int):void=
        ProfileService.GrantXP(Agent, Amount)

    GetCurrentLevel(Agent:agent)<decides><transacts>:int=
        Profile := ProfileService.GetProfile[Agent]
        GetLevelForXP(Profile.XP)
