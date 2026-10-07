using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Central persistent profile update service.
# Variable-sized updates are checked with FitsInPlayerMap before replacement.
# Canonical completion arrays are de-duplicated with array.Find[] so progression
# counts represent unique accomplishments rather than repeated writes.
aeonfall_profile_service := class():

    GetProfile(Agent:agent)<decides><transacts>:aeonfall_player_profile=
        var Result:aeonfall_player_profile = aeonfall_player_profile{}
        if:
            Player := player[Agent]
            Saved := AEONFALLPlayerProfiles[Player]
            set Result = MakeAEONFALLPlayerProfile(Saved)
        Result

    SaveProfile(Player:player, Candidate:aeonfall_player_profile)<transacts>:void=
        if:
            FitsInPlayerMap(Candidate)
        then:
            set AEONFALLPlayerProfiles[Player] = Candidate

    GrantXP(Agent:agent, Amount:int)<transacts>:void=
        if:
            Amount > 0
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            NewXP:int = Old.XP + Amount
            NewLevel:int = AEONFALLGetLevelForXP(NewXP)

            Candidate := aeonfall_player_profile:
                MakeAEONFALLPlayerProfile<constructor>(Old)
                XP := NewXP
                Level := NewLevel
            SaveProfile(Player, Candidate)

            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "progression.xp_granted",
                    SourceId := "player",
                    Amount := Amount,
                    ContextId := "{NewLevel}"
                }
            )

    GrantMasteryPoints(Agent:agent, Amount:int)<transacts>:void=
        if:
            Amount > 0
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            Candidate := aeonfall_player_profile:
                MakeAEONFALLPlayerProfile<constructor>(Old)
                MasteryPoints := Old.MasteryPoints + Amount
            SaveProfile(Player, Candidate)

    UnlockEntity(Agent:agent, EntityId:string)<transacts>:void=
        if:
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            if:
                Old.UnlockedEntityIds.Find[EntityId]
            then:
                return
            else:
                Candidate := aeonfall_player_profile:
                    MakeAEONFALLPlayerProfile<constructor>(Old)
                    UnlockedEntityIds := Old.UnlockedEntityIds + array{EntityId}
                SaveProfile(Player, Candidate)

    MasterClass(Agent:agent, ClassId:string)<transacts>:void=
        if:
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            if:
                Old.MasteredClassIds.Find[ClassId]
            then:
                return
            else:
                Candidate := aeonfall_player_profile:
                    MakeAEONFALLPlayerProfile<constructor>(Old)
                    MasteredClassIds := Old.MasteredClassIds + array{ClassId}
                SaveProfile(Player, Candidate)

    CompleteBoss(Agent:agent, BossId:string)<transacts>:void=
        if:
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            if:
                Old.CompletedBossIds.Find[BossId]
            then:
                return
            else:
                Candidate := aeonfall_player_profile:
                    MakeAEONFALLPlayerProfile<constructor>(Old)
                    CompletedBossIds := Old.CompletedBossIds + array{BossId}
                SaveProfile(Player, Candidate)

    CompleteWorldEvent(Agent:agent, EventId:string)<transacts>:void=
        if:
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            if:
                Old.CompletedWorldEventIds.Find[EventId]
            then:
                return
            else:
                Candidate := aeonfall_player_profile:
                    MakeAEONFALLPlayerProfile<constructor>(Old)
                    CompletedWorldEventIds := Old.CompletedWorldEventIds + array{EventId}
                SaveProfile(Player, Candidate)

    CompleteTrial(Agent:agent, TrialId:string)<transacts>:void=
        if:
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            if:
                Old.CompletedTrialIds.Find[TrialId]
            then:
                return
            else:
                Candidate := aeonfall_player_profile:
                    MakeAEONFALLPlayerProfile<constructor>(Old)
                    CompletedTrialIds := Old.CompletedTrialIds + array{TrialId}
                SaveProfile(Player, Candidate)

    DiscoverPoi(Agent:agent, PoiId:string)<transacts>:void=
        if:
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            if:
                Old.DiscoveredPoiIds.Find[PoiId]
            then:
                return
            else:
                Candidate := aeonfall_player_profile:
                    MakeAEONFALLPlayerProfile<constructor>(Old)
                    DiscoveredPoiIds := Old.DiscoveredPoiIds + array{PoiId}
                SaveProfile(Player, Candidate)

    UnlockHireable(Agent:agent, NpcId:string)<transacts>:void=
        if:
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            if:
                Old.HireableUnlockIds.Find[NpcId]
            then:
                return
            else:
                Candidate := aeonfall_player_profile:
                    MakeAEONFALLPlayerProfile<constructor>(Old)
                    HireableUnlockIds := Old.HireableUnlockIds + array{NpcId}
                SaveProfile(Player, Candidate)

    RecordTamedSpecies(Agent:agent, SpeciesId:string)<transacts>:void=
        if:
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            if:
                Old.TamedSpeciesIds.Find[SpeciesId]
            then:
                return
            else:
                Candidate := aeonfall_player_profile:
                    MakeAEONFALLPlayerProfile<constructor>(Old)
                    TamedSpeciesIds := Old.TamedSpeciesIds + array{SpeciesId}
                SaveProfile(Player, Candidate)

    SetMaterialCount(Agent:agent, MaterialId:string, NewCount:int)<transacts>:void=
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
                SaveProfile(Player, Candidate)

    SetFactionReputation(Agent:agent, FactionId:string, Reputation:int)<transacts>:void=
        if:
            Reputation >= 0
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            var UpdatedReputation:[string]int = Old.FactionReputation
            if:
                set UpdatedReputation[FactionId] = Reputation
            then:
                Candidate := aeonfall_player_profile:
                    MakeAEONFALLPlayerProfile<constructor>(Old)
                    FactionReputation := UpdatedReputation
                SaveProfile(Player, Candidate)

    SetEquipment(
        Agent:agent,
        ArmorIds:[]string,
        WeaponIds:[]string,
        RelicIds:[]string
    )<transacts>:void=
        if:
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            Candidate := aeonfall_player_profile:
                MakeAEONFALLPlayerProfile<constructor>(Old)
                EquippedArmorIds := ArmorIds
                EquippedWeaponIds := WeaponIds
                EquippedRelicIds := RelicIds
            SaveProfile(Player, Candidate)

    SetAscensionRank(Agent:agent, NewRank:int)<transacts>:void=
        if:
            NewRank >= 0
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            Candidate := aeonfall_player_profile:
                MakeAEONFALLPlayerProfile<constructor>(Old)
                AscensionRank := NewRank
            SaveProfile(Player, Candidate)

    SetAxiomHeartCrafted(Agent:agent, IsCrafted:logic)<transacts>:void=
        if:
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            Candidate := aeonfall_player_profile:
                MakeAEONFALLPlayerProfile<constructor>(Old)
                AxiomHeartCrafted := IsCrafted
            SaveProfile(Player, Candidate)

    SetZeroCandidate(Agent:agent, IsCandidate:logic)<transacts>:void=
        if:
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            Candidate := aeonfall_player_profile:
                MakeAEONFALLPlayerProfile<constructor>(Old)
                IsZeroCandidate := IsCandidate
            SaveProfile(Player, Candidate)


    # Replaces the complete sparse material ledger in one profile write.
    # Multi-cost crafting/shop transactions build and validate a candidate map
    # first, then call this once to avoid partial per-material persistence.
    SetMaterialLedger(Agent:agent, NewLedger:[string]int)<transacts>:void=
        if:
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            Candidate := aeonfall_player_profile:
                MakeAEONFALLPlayerProfile<constructor>(Old)
                MaterialLedger := NewLedger
            SaveProfile(Player, Candidate)

    # Commits a material-ledger mutation and one canonical unlock together.
    # Inventory delivery remains a separate project-bound adapter, but durable
    # progression sees one candidate profile rather than partially applied costs.
    CommitMaterialAndUnlock(
        Agent:agent,
        NewLedger:[string]int,
        UnlockEntityId:string
    )<transacts>:void=
        if:
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            var UpdatedUnlocks:[]string = Old.UnlockedEntityIds
            if:
                Old.UnlockedEntityIds.Find[UnlockEntityId]
            then:
                set UpdatedUnlocks = Old.UnlockedEntityIds
            else:
                set UpdatedUnlocks = Old.UnlockedEntityIds + array{UnlockEntityId}

            Candidate := aeonfall_player_profile:
                MakeAEONFALLPlayerProfile<constructor>(Old)
                MaterialLedger := NewLedger
                UnlockedEntityIds := UpdatedUnlocks
            SaveProfile(Player, Candidate)


    SetEquippedClass(Agent:agent, ClassId:string)<transacts>:void=
        if:
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            Candidate := aeonfall_player_profile:
                MakeAEONFALLPlayerProfile<constructor>(Old)
                EquippedClassId := ClassId
            SaveProfile(Player, Candidate)


    # Atomically commits the durable portion of one first-clear encounter reward.
    # This is deliberately self-idempotent: even if two completion signals race,
    # a profile that already contains the boss/event completion is rejected before
    # any XP, mastery, unlock, or material mutation is constructed.
    CommitEncounterFirstClearReward(
        Agent:agent,
        EncounterId:string,
        IsBoss:logic,
        XPReward:int,
        MasteryReward:int,
        UnlockIds:[]string,
        MaterialRewards:[]aeonfall_material_cost
    )<transacts>:logic=
        if:
            EncounterId <> ""
            XPReward >= 0
            MasteryReward >= 0
            Player := player[Agent]
            Old := AEONFALLPlayerProfiles[Player]
        then:
            if (IsBoss?):
                if:
                    Old.CompletedBossIds.Find[EncounterId]
                then:
                    return false
            else:
                if:
                    Old.CompletedWorldEventIds.Find[EncounterId]
                then:
                    return false

            var UpdatedBossIds:[]string = Old.CompletedBossIds
            var UpdatedEventIds:[]string = Old.CompletedWorldEventIds

            if (IsBoss?):
                set UpdatedBossIds = Old.CompletedBossIds + array{EncounterId}
            else:
                set UpdatedEventIds = Old.CompletedWorldEventIds + array{EncounterId}

            var UpdatedUnlocks:[]string = Old.UnlockedEntityIds
            for (UnlockId : UnlockIds):
                if:
                    UpdatedUnlocks.Find[UnlockId]
                then:
                    UnlockId = UnlockId
                else:
                    set UpdatedUnlocks = UpdatedUnlocks + array{UnlockId}

            var UpdatedLedger:[string]int = Old.MaterialLedger
            var Valid:logic = true

            for (Reward : MaterialRewards):
                if:
                    Reward.MaterialId <> ""
                    Reward.Amount > 0
                then:
                    var Current:int = 0
                    if:
                        Stored := UpdatedLedger[Reward.MaterialId]
                    then:
                        set Current = Stored

                    if:
                        set UpdatedLedger[Reward.MaterialId] =
                            Current + Reward.Amount
                    then:
                        set Valid = Valid
                    else:
                        set Valid = false
                else:
                    set Valid = false

            if (not Valid?):
                return false

            NewXP:int = Old.XP + XPReward
            NewLevel:int = AEONFALLGetLevelForXP(NewXP)

            Candidate := aeonfall_player_profile:
                MakeAEONFALLPlayerProfile<constructor>(Old)
                Level := NewLevel
                XP := NewXP
                MasteryPoints := Old.MasteryPoints + MasteryReward
                UnlockedEntityIds := UpdatedUnlocks
                CompletedBossIds := UpdatedBossIds
                CompletedWorldEventIds := UpdatedEventIds
                MaterialLedger := UpdatedLedger

            if:
                FitsInPlayerMap(Candidate)
                set AEONFALLPlayerProfiles[Player] = Candidate
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "progression.encounter_first_clear_committed",
                        SourceId := EncounterId,
                        Amount := XPReward,
                        ContextId := "{NewLevel}"
                    }
                )
                return true

            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "progression.encounter_first_clear_rejected",
                    SourceId := EncounterId,
                    ContextId := "profile_commit_failed"
                }
            )

        false
