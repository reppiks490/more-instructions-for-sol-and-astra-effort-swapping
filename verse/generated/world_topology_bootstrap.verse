using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# GENERATED FILE — do not hand edit.
# Source: content/world/world_topology.json

AEONFALLWorldRegionDefinitions:[]aeonfall_region_definition = array{
    aeonfall_region_definition{
        RegionId := "REG-001",
        DisplayName := "The Ossuary March",
        NeighborRegionIds := array{"REG-002", "REG-004", "REG-007"},
        StreamingBand := aeonfall_region_streaming_band.Medium,
        VerticalSlice := true
    },
    aeonfall_region_definition{
        RegionId := "REG-002",
        DisplayName := "Black Sun Meridian",
        NeighborRegionIds := array{"REG-001", "REG-003", "REG-009"},
        StreamingBand := aeonfall_region_streaming_band.High,
        VerticalSlice := false
    },
    aeonfall_region_definition{
        RegionId := "REG-003",
        DisplayName := "Crownless Tempest",
        NeighborRegionIds := array{"REG-002", "REG-004", "REG-010"},
        StreamingBand := aeonfall_region_streaming_band.High,
        VerticalSlice := false
    },
    aeonfall_region_definition{
        RegionId := "REG-004",
        DisplayName := "Leviathan Red Coast",
        NeighborRegionIds := array{"REG-001", "REG-003", "REG-005"},
        StreamingBand := aeonfall_region_streaming_band.High,
        VerticalSlice := false
    },
    aeonfall_region_definition{
        RegionId := "REG-005",
        DisplayName := "Worldroot Cathedral",
        NeighborRegionIds := array{"REG-004", "REG-006", "REG-011"},
        StreamingBand := aeonfall_region_streaming_band.Medium,
        VerticalSlice := false
    },
    aeonfall_region_definition{
        RegionId := "REG-006",
        DisplayName := "Court of Broken Hours",
        NeighborRegionIds := array{"REG-005", "REG-007", "REG-012"},
        StreamingBand := aeonfall_region_streaming_band.High,
        VerticalSlice := false
    },
    aeonfall_region_definition{
        RegionId := "REG-007",
        DisplayName := "Infernal Ledgerlands",
        NeighborRegionIds := array{"REG-001", "REG-006", "REG-008"},
        StreamingBand := aeonfall_region_streaming_band.High,
        VerticalSlice := false
    },
    aeonfall_region_definition{
        RegionId := "REG-008",
        DisplayName := "Glass Wyrm Expanse",
        NeighborRegionIds := array{"REG-007", "REG-009", "REG-011"},
        StreamingBand := aeonfall_region_streaming_band.Medium,
        VerticalSlice := false
    },
    aeonfall_region_definition{
        RegionId := "REG-009",
        DisplayName := "Hollow Astral Synod",
        NeighborRegionIds := array{"REG-002", "REG-008", "REG-010"},
        StreamingBand := aeonfall_region_streaming_band.High,
        VerticalSlice := false
    },
    aeonfall_region_definition{
        RegionId := "REG-010",
        DisplayName := "Null Cartography",
        NeighborRegionIds := array{"REG-003", "REG-009", "REG-012"},
        StreamingBand := aeonfall_region_streaming_band.High,
        VerticalSlice := false
    },
    aeonfall_region_definition{
        RegionId := "REG-011",
        DisplayName := "Titan's Last Orchard",
        NeighborRegionIds := array{"REG-005", "REG-008", "REG-012"},
        StreamingBand := aeonfall_region_streaming_band.High,
        VerticalSlice := false
    },
    aeonfall_region_definition{
        RegionId := "REG-012",
        DisplayName := "The Axiom Scar",
        NeighborRegionIds := array{"REG-006", "REG-010", "REG-011", "REG-013"},
        StreamingBand := aeonfall_region_streaming_band.Cinematic,
        VerticalSlice := false
    },
    aeonfall_region_definition{
        RegionId := "REG-013",
        DisplayName := "Threshold of Zero",
        NeighborRegionIds := array{"REG-012"},
        StreamingBand := aeonfall_region_streaming_band.Cinematic,
        VerticalSlice := false
    },
}

aeonfall_world_topology_bootstrap_device := class(creative_device):

    OnBegin<override>()<suspends>:void=
        for (Definition : AEONFALLWorldRegionDefinitions):
            Registered := AEONFALLRegionRegistry.Register(Definition)
            if (Registered?):
                Initialized := AEONFALLRegionRuntime.InitializeRegion(Definition.RegionId)
                if (not Initialized?):
                    AEONFALLRuntimeBus.Emit(
                        aeonfall_runtime_event{
                            EventType := "bootstrap.region_initialization_failed",
                            SourceId := Definition.RegionId
                        }
                    )
            else:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "bootstrap.region_registration_failed",
                        SourceId := Definition.RegionId
                    }
                )
