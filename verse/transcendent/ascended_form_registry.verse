using { /Verse.org/Verse }
using { /Verse.org/Simulation }
# Canonical God/Absolute form registry.

aeonfall_ascended_form_registry := class():

    var Definitions:[string]aeonfall_ascended_form_definition = map{}

    Register(Definition:aeonfall_ascended_form_definition)<transacts>:logic=
        if:
            Definition.FormId <> ""
            Definition.TransformationId <> ""
            Definition.RequiredAscensionRank > 0
            Definition.ActiveSeconds > 0.0
            Definition.ExhaustionSeconds > 0.0
            Definition.AbilityIds.Length > 0
            set Definitions[Definition.FormId] = Definition
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "ascended_form.definition_registered",
                    SourceId := Definition.FormId,
                    TargetId := Definition.TransformationId
                }
            )
            return true

        false

    Get(FormId:string)<decides><transacts>:aeonfall_ascended_form_definition=
        Definitions[FormId]

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLAscendedFormRegistrySessions:weak_map(session, aeonfall_ascended_form_registry) = map{}

GetAEONFALLAscendedFormRegistry()<transacts>:aeonfall_ascended_form_registry=
    CurrentSession := GetSession()
    if (Existing := AEONFALLAscendedFormRegistrySessions[CurrentSession]):
        return Existing
    Created := aeonfall_ascended_form_registry{}
    if (set AEONFALLAscendedFormRegistrySessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLAscendedFormRegistry in its session")
