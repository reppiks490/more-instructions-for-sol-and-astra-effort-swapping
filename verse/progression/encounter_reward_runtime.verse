using { /Verse.org/Simulation }

# First-clear reward service for registered bosses and world events.
# Durable completion + XP + derived level + mastery + unlocks + materials commit
# through one immutable persistent profile replacement per participant.

aeonfall_encounter_reward_service := class():

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}

    AwardRegistered(EncounterId:string)<transacts>:int=
        if:
            Definition := GetAEONFALLEncounterRewardRegistry().Get[EncounterId]
        then:
            ParticipantKeys := GetAEONFALLEncounterParticipation().GetParticipants(
                EncounterId
            )

            var Awarded:int = 0

            if (not Definition.FirstClearOnly?):
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "encounter_reward.non_first_clear_definition_rejected",
                        SourceId := EncounterId
                    }
                )
                GetAEONFALLEncounterParticipation().ClearEncounter(
                    EncounterId
                )
                return 0

            for (RuntimeKey : ParticipantKeys):
                if:
                    Agent := GetAEONFALLActorRegistry().GetAgent[RuntimeKey]
                    Player := player[Agent]
                    BeforeReward := ProfileService.GetProfile[Player]
                then:
                    IsBoss:logic = logic{
                        Definition.Kind = aeonfall_encounter_reward_kind.Boss
                    }

                    Committed := ProfileService.CommitEncounterFirstClearReward(
                        Player,
                        Definition.EncounterId,
                        IsBoss,
                        Definition.XP,
                        Definition.MasteryPoints,
                        Definition.UnlockEntityIds,
                        Definition.MaterialRewards
                    )

                    if (Committed?):
                        set Awarded += 1
                        # Only the successful immutable first-clear commit can
                        # request physical unlock delivery; repeated clears skip.
                        for (EntityId : Definition.UnlockEntityIds):
                            if (not BeforeReward.UnlockedEntityIds.Find[EntityId]):
                                DeliveryStarted := GetAEONFALLUnlockDeliveryService().QueueAfterCommit(
                                    Player, EntityId, EncounterId
                                )
                                if (not DeliveryStarted?):
                                    AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                                        EventType := "encounter_reward.delivery_backlog_full",
                                        SourceId := EncounterId,
                                        TargetId := EntityId,
                                        ContextId := RuntimeKey
                                    })

                        AEONFALLRuntimeBus.Emit(
                            aeonfall_runtime_event{
                                EventType := "encounter_reward.awarded",
                                SourceId := EncounterId,
                                TargetId := RuntimeKey,
                                Amount := Definition.XP
                            }
                        )
                    else:
                        AEONFALLRuntimeBus.Emit(
                            aeonfall_runtime_event{
                                EventType := "encounter_reward.first_clear_skipped",
                                SourceId := EncounterId,
                                TargetId := RuntimeKey
                            }
                        )

            GetAEONFALLEncounterParticipation().ClearEncounter(
                EncounterId
            )

            Awarded
        else:
            0

AEONFALLEncounterRewardService:aeonfall_encounter_reward_service =
    aeonfall_encounter_reward_service{}
