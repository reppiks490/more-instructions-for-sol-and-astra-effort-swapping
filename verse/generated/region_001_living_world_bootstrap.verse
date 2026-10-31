using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# GENERATED FILE — do not hand edit.
# Source: content/world/region_001_living_world.json

Region001InvasionDefinitions:[]aeonfall_invasion_definition = array{
    aeonfall_invasion_definition{
        InvasionId := "INV-R001-001",
        RegionId := "REG-001",
        AggressorId := "ECOL-NECROTIC",
        MinHostilityTier := 1,
        WaveSpawnGroupIds := array{array{"SG-R001-GRAVE-SCAVENGERS"}, array{"SG-R001-GRAVE-SCAVENGERS", "SG-R001-NECRO-SUPPORT"}},
        ObjectiveIds := array{"OBJ-INV001-DENY-CORPSES", "OBJ-INV001-CLEAR-NEST"},
        HazardIds := array{"HZ-INV001-CORPSE-LOTS"},
        DurationSeconds := 180.0,
        MaxConcurrentAi := 10,
        TimeoutIsFailure := true
    },
    aeonfall_invasion_definition{
        InvasionId := "INV-R001-002",
        RegionId := "REG-001",
        AggressorId := "FAC-002",
        MinHostilityTier := 2,
        WaveSpawnGroupIds := array{array{"SG-R001-NULL-ESCORT"}, array{"SG-R001-NULL-ESCORT", "SG-R001-GRAVE-SCAVENGERS"}, array{"SG-R001-NECRO-SUPPORT"}},
        ObjectiveIds := array{"OBJ-INV002-INTERCEPT-RELIC", "OBJ-INV002-SEAL-RIFT"},
        HazardIds := array{"HZ-INV002-SMUGGLER-GATES"},
        DurationSeconds := 240.0,
        MaxConcurrentAi := 12,
        TimeoutIsFailure := true
    },
    aeonfall_invasion_definition{
        InvasionId := "INV-R001-003",
        RegionId := "REG-001",
        AggressorId := "FAC-004",
        MinHostilityTier := 2,
        WaveSpawnGroupIds := array{array{"SG-R001-GRAVE-SCAVENGERS"}, array{"SG-R001-NECRO-SUPPORT", "SG-R001-BROOD-PRESSURE"}},
        ObjectiveIds := array{"OBJ-INV003-DEFEND-SANCTIFIERS", "OBJ-INV003-BURN-CORPSE-LOTS"},
        HazardIds := array{"HZ-INV003-SANCTIFIED-FIRE"},
        DurationSeconds := 240.0,
        MaxConcurrentAi := 14,
        TimeoutIsFailure := false
    },
    aeonfall_invasion_definition{
        InvasionId := "INV-R001-004",
        RegionId := "REG-001",
        AggressorId := "FAC-007",
        MinHostilityTier := 3,
        WaveSpawnGroupIds := array{array{"SG-R001-BROOD-PRESSURE"}, array{"SG-R001-NULL-ESCORT", "SG-R001-NECRO-SUPPORT"}, array{"SG-R001-OSSUARY-SIEGE"}},
        ObjectiveIds := array{"OBJ-INV004-BREAK-RESEARCH-NODES", "OBJ-INV004-KILL-ANCHOR"},
        HazardIds := array{"HZ-INV004-VOID-GRAVE-FIELD", "HZ-INV004-EXPERIMENTAL-RIFT"},
        DurationSeconds := 300.0,
        MaxConcurrentAi := 16,
        TimeoutIsFailure := true
    },
    aeonfall_invasion_definition{
        InvasionId := "INV-R001-005",
        RegionId := "REG-001",
        AggressorId := "ECOL-GRAVEFEEDING",
        MinHostilityTier := 4,
        WaveSpawnGroupIds := array{array{"SG-R001-DEVOURING-PRECURSOR"}, array{"SG-R001-DEVOURING-PRECURSOR", "SG-R001-NECRO-SUPPORT"}, array{"SG-R001-OSSUARY-SIEGE", "SG-R001-BROOD-PRESSURE"}},
        ObjectiveIds := array{"OBJ-INV005-STOP-FEEDING", "OBJ-INV005-DESTROY-EVOLUTION-NODES", "OBJ-INV005-SEAL-MOON-RIFT"},
        HazardIds := array{"HZ-INV005-RED-ASH", "HZ-INV005-HUNGER-ZONES"},
        DurationSeconds := 360.0,
        MaxConcurrentAi := 20,
        TimeoutIsFailure := true
    },
}

aeonfall_region_001_living_world_bootstrap_device := class(creative_device):

    OnBegin<override>()<suspends>:void=
        var Ready:logic = false

        for (Attempt := 1..20):
            if (GetAEONFALLRegionRegistry().IsRegistered["REG-001"]):
                set Ready = true
                break
            Sleep(0.25)

        if (not Ready?):
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "bootstrap.region_001_world_not_ready",
                    SourceId := "REG-001"
                }
            )
            return

        Seeded0 := GetAEONFALLRegionRuntime().SetFactionInfluence(
            "REG-001",
            "FAC-002",
            35
        )
        if (not Seeded0?):
            AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                EventType := "bootstrap.region_001_faction_seed_failed",
                SourceId := "REG-001",
                TargetId := "FAC-002"
            })
            return
        Seeded1 := GetAEONFALLRegionRuntime().SetFactionInfluence(
            "REG-001",
            "FAC-004",
            25
        )
        if (not Seeded1?):
            AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                EventType := "bootstrap.region_001_faction_seed_failed",
                SourceId := "REG-001",
                TargetId := "FAC-004"
            })
            return
        Seeded2 := GetAEONFALLRegionRuntime().SetFactionInfluence(
            "REG-001",
            "FAC-007",
            15
        )
        if (not Seeded2?):
            AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                EventType := "bootstrap.region_001_faction_seed_failed",
                SourceId := "REG-001",
                TargetId := "FAC-007"
            })
            return

        for (Definition : Region001InvasionDefinitions):
            Registered := GetAEONFALLInvasionRegistry().Register(Definition)
            if (not Registered?):
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "bootstrap.invasion_registration_failed",
                        SourceId := Definition.InvasionId,
                        TargetId := Definition.RegionId
                    }
                )

        AEONFALLRegionalEscalation.ReconcileRegion("REG-001")
