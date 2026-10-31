using { /Verse.org/Verse }
using { /Verse.org/Simulation }
aeonfall_faction_conflict_registry := class():

    var Definitions:[string]aeonfall_faction_conflict_definition = map{}

    Register(Definition:aeonfall_faction_conflict_definition)<transacts>:logic=
        if:
            Definition.ConflictId <> ""
            Definition.RegionId <> ""
            Definition.FactionAId <> ""
            Definition.FactionBId <> ""
            Definition.FactionAId <> Definition.FactionBId
            Definition.VictoryScore > 0
            Definition.MinHostilityTier >= 0
            Definition.MinHostilityTier <= 5
            GetAEONFALLRegionRegistry().IsRegistered[Definition.RegionId]
        then:
            if:
                Existing := Definitions[Definition.ConflictId]
            then:
                return false

            if:
                set Definitions[Definition.ConflictId] = Definition
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "faction_conflict.definition_registered",
                        SourceId := Definition.ConflictId,
                        TargetId := Definition.RegionId,
                        ContextId := Definition.FactionAId + "::" + Definition.FactionBId
                    }
                )
                return true

        false

    Get(ConflictId:string)<decides><transacts>:aeonfall_faction_conflict_definition=
        Definitions[ConflictId]

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLFactionConflictRegistrySessions:weak_map(session, aeonfall_faction_conflict_registry) = map{}

GetAEONFALLFactionConflictRegistry()<transacts>:aeonfall_faction_conflict_registry=
    CurrentSession := GetSession()
    if (Existing := AEONFALLFactionConflictRegistrySessions[CurrentSession]):
        return Existing
    Created := aeonfall_faction_conflict_registry{}
    if (set AEONFALLFactionConflictRegistrySessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLFactionConflictRegistry in its session")
