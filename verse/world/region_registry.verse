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

AEONFALLRegionRegistry:aeonfall_region_registry = aeonfall_region_registry{}
