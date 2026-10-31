using { /Verse.org/Verse }
using { /Verse.org/Simulation }
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

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLEncounterRewardRegistrySessions:weak_map(session, aeonfall_encounter_reward_registry) = map{}

GetAEONFALLEncounterRewardRegistry()<transacts>:aeonfall_encounter_reward_registry=
    CurrentSession := GetSession()
    if (Existing := AEONFALLEncounterRewardRegistrySessions[CurrentSession]):
        return Existing
    Created := aeonfall_encounter_reward_registry{}
    if (set AEONFALLEncounterRewardRegistrySessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLEncounterRewardRegistry in its session")
