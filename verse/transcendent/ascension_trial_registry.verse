using { /Verse.org/Verse }
using { /Verse.org/Simulation }
aeonfall_ascension_trial_registry := class():

    var Definitions:[string]aeonfall_ascension_trial_definition = map{}

    Register(
        Definition:aeonfall_ascension_trial_definition
    )<transacts>:logic=
        if:
            Definition.TrialId <> ""
            Definition.Index >= 1
            Definition.Index <= 10
            Definition.ObjectiveIds.Length > 0
            Definition.TimeLimitSeconds > 0.0
        then:
            if:
                Existing := Definitions[Definition.TrialId]
            then:
                return false

            if:
                set Definitions[Definition.TrialId] = Definition
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "ascension_trial.definition_registered",
                        SourceId := Definition.TrialId,
                        Amount := Definition.Index
                    }
                )
                return true

        false

    Get(
        TrialId:string
    )<decides><transacts>:aeonfall_ascension_trial_definition=
        Definitions[TrialId]

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLAscensionTrialRegistrySessions:weak_map(session, aeonfall_ascension_trial_registry) = map{}

GetAEONFALLAscensionTrialRegistry()<transacts>:aeonfall_ascension_trial_registry=
    CurrentSession := GetSession()
    if (Existing := AEONFALLAscensionTrialRegistrySessions[CurrentSession]):
        return Existing
    Created := aeonfall_ascension_trial_registry{}
    if (set AEONFALLAscensionTrialRegistrySessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLAscensionTrialRegistry in its session")
