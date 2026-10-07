aeonfall_encounter_reward_registry := class():

    var Definitions:[string]aeonfall_encounter_reward_definition = map{}

    Register(
        Definition:aeonfall_encounter_reward_definition
    )<transacts>:logic=
        if:
            Definition.EncounterId <> ""
            Definition.XP >= 0
            Definition.MasteryPoints >= 0
        then:
            if:
                Existing := Definitions[Definition.EncounterId]
            then:
                return false

            if:
                set Definitions[Definition.EncounterId] = Definition
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "encounter_reward.definition_registered",
                        SourceId := Definition.EncounterId
                    }
                )
                return true

        false

    Get(
        EncounterId:string
    )<decides><transacts>:aeonfall_encounter_reward_definition=
        Definitions[EncounterId]

AEONFALLEncounterRewardRegistry:aeonfall_encounter_reward_registry =
    aeonfall_encounter_reward_registry{}
