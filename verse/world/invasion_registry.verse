using { /Verse.org/Verse }
using { /Verse.org/Simulation }
aeonfall_invasion_registry := class():

    var Definitions:[string]aeonfall_invasion_definition = map{}

    Register(Definition:aeonfall_invasion_definition)<transacts>:logic=
        if:
            Definition.InvasionId <> ""
            Definition.RegionId <> ""
            Definition.WaveSpawnGroupIds.Length > 0
            Definition.DurationSeconds > 0.0
            Definition.MaxConcurrentAi > 0
            GetAEONFALLRegionRegistry().IsRegistered[Definition.RegionId]
        then:
            if:
                Existing := Definitions[Definition.InvasionId]
            then:
                return false

            if:
                set Definitions[Definition.InvasionId] = Definition
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "invasion.definition_registered",
                        SourceId := Definition.InvasionId,
                        TargetId := Definition.RegionId,
                        ContextId := Definition.AggressorId
                    }
                )
                return true

        false

    Get(InvasionId:string)<decides><transacts>:aeonfall_invasion_definition=
        Definitions[InvasionId]

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLInvasionRegistrySessions:weak_map(session, aeonfall_invasion_registry) = map{}

GetAEONFALLInvasionRegistry()<transacts>:aeonfall_invasion_registry=
    CurrentSession := GetSession()
    if (Existing := AEONFALLInvasionRegistrySessions[CurrentSession]):
        return Existing
    Created := aeonfall_invasion_registry{}
    if (set AEONFALLInvasionRegistrySessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLInvasionRegistry in its session")
