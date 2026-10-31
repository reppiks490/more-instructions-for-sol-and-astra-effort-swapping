using { /Verse.org/Verse }
using { /Verse.org/Simulation }
# Canonical ability-definition registry.
# Project/bootstrap registration is generated from validated content data.

aeonfall_ability_registry := class():

    var Definitions:[string]aeonfall_ability_definition = map{}

    Register(Definition:aeonfall_ability_definition)<transacts>:logic=
        if:
            Definition.AbilityId <> ""
            Definition.AdapterId <> ""
            set Definitions[Definition.AbilityId] = Definition
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "ability.definition_registered",
                    SourceId := Definition.OwnerEntityId,
                    TargetId := Definition.AbilityId,
                    ContextId := Definition.AdapterId
                }
            )
            return true

        false

    Get(AbilityId:string)<decides><transacts>:aeonfall_ability_definition=
        Definitions[AbilityId]

    IsRegistered(AbilityId:string)<decides><transacts>:void=
        Definition := Definitions[AbilityId]
        Definition.AbilityId <> ""
        Definition.AdapterId <> ""

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLAbilityRegistrySessions:weak_map(session, aeonfall_ability_registry) = map{}

GetAEONFALLAbilityRegistry()<transacts>:aeonfall_ability_registry=
    CurrentSession := GetSession()
    if (Existing := AEONFALLAbilityRegistrySessions[CurrentSession]):
        return Existing
    Created := aeonfall_ability_registry{}
    if (set AEONFALLAbilityRegistrySessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLAbilityRegistry in its session")
