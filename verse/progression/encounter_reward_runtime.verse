using { /Verse.org/Simulation }

# First-clear reward service for registered bosses and world events.
# Repeatable/farmable reward tables belong in a separate loot service; this
# service intentionally protects durable progression rewards from duplicate
# completion signals.

aeonfall_encounter_reward_service := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}
    MaterialLedger:aeonfall_material_ledger = aeonfall_material_ledger{}

    IsAlreadyCompleted(
        Profile:aeonfall_player_profile,
        Definition:aeonfall_encounter_reward_definition
    )<transacts>:logic=
        if (Definition.Kind = aeonfall_encounter_reward_kind.Boss):
            if:
                Profile.CompletedBossIds.Find[Definition.EncounterId]
            then:
                return true
            return false

        if:
            Profile.CompletedWorldEventIds.Find[Definition.EncounterId]
        then:
            true
        else:
            false

    MarkCompleted(
        Agent:agent,
        Definition:aeonfall_encounter_reward_definition
    )<transacts>:void=
        if (Definition.Kind = aeonfall_encounter_reward_kind.Boss):
            ProfileService.CompleteBoss(
                Agent,
                Definition.EncounterId
            )
        else:
            ProfileService.CompleteWorldEvent(
                Agent,
                Definition.EncounterId
            )

    AwardRegistered(EncounterId:string)<transacts>:int=
        if:
            Definition := AEONFALLEncounterRewardRegistry.Get[EncounterId]
        then:
            ParticipantKeys := AEONFALLEncounterParticipation.GetParticipants(
                EncounterId
            )

            var Awarded:int = 0

            for (RuntimeKey : ParticipantKeys):
                if:
                    Agent := AEONFALLActorRegistry.GetAgent[RuntimeKey]
                    Player := player[Agent]
                    Profile := ProfileService.GetProfile[Player]
                then:
                    AlreadyCompleted:logic =
                        IsAlreadyCompleted(Profile, Definition)

                    if:
                        Definition.FirstClearOnly?
                        AlreadyCompleted?
                    then:
                        AEONFALLRuntimeBus.Emit(
                            aeonfall_runtime_event{
                                EventType := "encounter_reward.first_clear_skipped",
                                SourceId := EncounterId,
                                TargetId := RuntimeKey
                            }
                        )
                    else:
                        MarkCompleted(Player, Definition)

                        if (Definition.XP > 0):
                            ProfileService.GrantXP(
                                Player,
                                Definition.XP
                            )

                        if (Definition.MasteryPoints > 0):
                            ProfileService.GrantMasteryPoints(
                                Player,
                                Definition.MasteryPoints
                            )

                        for (UnlockId : Definition.UnlockEntityIds):
                            ProfileService.UnlockEntity(
                                Player,
                                UnlockId
                            )

                        for (Reward : Definition.MaterialRewards):
                            MaterialLedger.Add(
                                Player,
                                Reward.MaterialId,
                                Reward.Amount
                            )

                        set Awarded += 1

                        AEONFALLRuntimeBus.Emit(
                            aeonfall_runtime_event{
                                EventType := "encounter_reward.awarded",
                                SourceId := EncounterId,
                                TargetId := RuntimeKey,
                                Amount := Definition.XP
                            }
                        )

            AEONFALLEncounterParticipation.ClearEncounter(
                EncounterId
            )

            Awarded
        else:
            0

AEONFALLEncounterRewardService:aeonfall_encounter_reward_service =
    aeonfall_encounter_reward_service{}
