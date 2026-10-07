using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Central persistent profile update service.
# Variable-sized updates are checked with FitsInPlayerMap before replacement.
aeonfall_profile_service := class():

    GetProfile(Agent:agent)<decides><transacts>:aeonfall_player_profile=
        var Result:aeonfall_player_profile = aeonfall_player_profile{}
        if:
            Player := player[Agent]
            Saved := AEONFALLPlayerProfiles[Player]
            set Result = MakeAEONFALLPlayerProfile(Saved)
        Result

    GrantXP(Agent:agent, Amount:int):void=
        if:
            Amount > 0
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            Candidate := aeonfall_player_profile:
                MakeAEONFALLPlayerProfile<constructor>(Old)
                XP := Old.XP + Amount

            if:
                FitsInPlayerMap(Candidate)
            then:
                set AEONFALLPlayerProfiles[Player] = Candidate

    GrantMasteryPoints(Agent:agent, Amount:int):void=
        if:
            Amount > 0
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            Candidate := aeonfall_player_profile:
                MakeAEONFALLPlayerProfile<constructor>(Old)
                MasteryPoints := Old.MasteryPoints + Amount

            if:
                FitsInPlayerMap(Candidate)
            then:
                set AEONFALLPlayerProfiles[Player] = Candidate

    SetMaterialCount(Agent:agent, MaterialId:string, NewCount:int):void=
        if:
            NewCount >= 0
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            var UpdatedLedger:[string]int = Old.MaterialLedger

            if:
                set UpdatedLedger[MaterialId] = NewCount
            then:
                Candidate := aeonfall_player_profile:
                    MakeAEONFALLPlayerProfile<constructor>(Old)
                    MaterialLedger := UpdatedLedger

                if:
                    FitsInPlayerMap(Candidate)
                then:
                    set AEONFALLPlayerProfiles[Player] = Candidate

    SetEquipment(
        Agent:agent,
        ArmorIds:[]string,
        WeaponIds:[]string,
        RelicIds:[]string
    ):void=
        if:
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            Candidate := aeonfall_player_profile:
                MakeAEONFALLPlayerProfile<constructor>(Old)
                EquippedArmorIds := ArmorIds
                EquippedWeaponIds := WeaponIds
                EquippedRelicIds := RelicIds

            if:
                FitsInPlayerMap(Candidate)
            then:
                set AEONFALLPlayerProfiles[Player] = Candidate

    SetAxiomHeartCrafted(Agent:agent, IsCrafted:logic):void=
        if:
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            set AEONFALLPlayerProfiles[Player] = aeonfall_player_profile:
                MakeAEONFALLPlayerProfile<constructor>(Old)
                AxiomHeartCrafted := IsCrafted

    SetZeroCandidate(Agent:agent, IsCandidate:logic):void=
        if:
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            set AEONFALLPlayerProfiles[Player] = aeonfall_player_profile:
                MakeAEONFALLPlayerProfile<constructor>(Old)
                IsZeroCandidate := IsCandidate
