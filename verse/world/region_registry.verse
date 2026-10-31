using { /Verse.org/Verse }
using { /Verse.org/Simulation }
# Canonical region registry generated from content/world/world_topology.json.

aeonfall_region_registry := class():

    var Definitions:[string]aeonfall_region_definition = map{}

    Register(Definition:aeonfall_region_definition)<transacts>:logic=
        if:
            Definition.RegionId <> ""
            Definition.DisplayName <> ""
        then:
            if:
                Existing := Definitions[Definition.RegionId]
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "region.definition_duplicate_rejected",
                        SourceId := Definition.RegionId
                    }
                )
                return false

            if:
                set Definitions[Definition.RegionId] = Definition
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "region.definition_registered",
                        SourceId := Definition.RegionId
                    }
                )
                return true

        false

    Get(RegionId:string)<decides><transacts>:aeonfall_region_definition=
        Definitions[RegionId]

    IsRegistered(RegionId:string)<decides><transacts>:void=
        Definition := Definitions[RegionId]
        Definition.RegionId <> ""

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLRegionRegistrySessions:weak_map(session, aeonfall_region_registry) = map{}

GetAEONFALLRegionRegistry()<transacts>:aeonfall_region_registry=
    CurrentSession := GetSession()
    if (Existing := AEONFALLRegionRegistrySessions[CurrentSession]):
        return Existing
    Created := aeonfall_region_registry{}
    if (set AEONFALLRegionRegistrySessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLRegionRegistry in its session")
