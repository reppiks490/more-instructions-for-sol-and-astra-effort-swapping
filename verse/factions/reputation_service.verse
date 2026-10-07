using { /Verse.org/Simulation }

# Persistent faction reputation facade.
# Canonical faction IDs use FAC-### and are stored in the player profile map.
aeonfall_reputation_service := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}

    GetReputation(Agent:agent, FactionId:string)<transacts>:int=
        var Result:int = 0
        if:
            Profile := ProfileService.GetProfile[Agent]
            Stored := Profile.FactionReputation[FactionId]
        then:
            set Result = Stored
        Result

    SetReputation(Agent:agent, FactionId:string, Reputation:int)<transacts>:void=
        if:
            Reputation >= 0
        then:
            ProfileService.SetFactionReputation(Agent, FactionId, Reputation)

    AddReputation(Agent:agent, FactionId:string, Amount:int)<transacts>:void=
        if:
            Amount > 0
        then:
            Current := GetReputation(Agent, FactionId)
            SetReputation(Agent, FactionId, Current + Amount)

    MeetsReputation(
        Agent:agent,
        FactionId:string,
        RequiredReputation:int
    )<decides><transacts>:void=
        RequiredReputation >= 0
        GetReputation(Agent, FactionId) >= RequiredReputation

    # Reputation is deliberately not allowed to go negative. Hostility and
    # temporary faction disposition belong in session runtime, not persistent
    # long-term reputation.
    SpendReputation(
        Agent:agent,
        FactionId:string,
        Amount:int
    )<decides><transacts>:void=
        Amount > 0
        Current := GetReputation(Agent, FactionId)
        Current >= Amount
        SetReputation(Agent, FactionId, Current - Amount)
