using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# GENERATED FILE — do not hand edit.
# Source: content/world/region_001_faction_conflicts.json

Region001FactionConflictDefinitions:[]aeonfall_faction_conflict_definition = array{
    aeonfall_faction_conflict_definition{
        ConflictId := "CON-R001-001",
        RegionId := "REG-001",
        FactionAId := "FAC-002",
        FactionBId := "FAC-004",
        VictoryScore := 100,
        MinHostilityTier := 1,
        ObjectiveIds := array{"OBJ-CON001-HOLD-TOLLHOUSE", "OBJ-CON001-SECURE-RELIQUARY", "OBJ-CON001-ESCORT-LEDGER"},
        HazardIds := array{"HZ-CON001-BLACK-MARKET-RIFTS"}
    },
    aeonfall_faction_conflict_definition{
        ConflictId := "CON-R001-002",
        RegionId := "REG-001",
        FactionAId := "FAC-004",
        FactionBId := "FAC-007",
        VictoryScore := 120,
        MinHostilityTier := 2,
        ObjectiveIds := array{"OBJ-CON002-PURIFY-DIGSITE", "OBJ-CON002-STEAL-RESEARCH", "OBJ-CON002-HOLD-OSSUARY-WELL"},
        HazardIds := array{"HZ-CON002-VOID-RESEARCH-FIELD", "HZ-CON002-SANCTIFIED-FIRE"}
    },
    aeonfall_faction_conflict_definition{
        ConflictId := "CON-R001-003",
        RegionId := "REG-001",
        FactionAId := "FAC-002",
        FactionBId := "FAC-007",
        VictoryScore := 150,
        MinHostilityTier := 3,
        ObjectiveIds := array{"OBJ-CON003-CAPTURE-COURIER", "OBJ-CON003-DECODE-GRAVEGLASS", "OBJ-CON003-SEAL-SMUGGLER-GATE"},
        HazardIds := array{"HZ-CON003-MIRROR-RIFT", "HZ-CON003-NULL-SURVEILLANCE"}
    },
}

aeonfall_region_001_faction_conflict_bootstrap_device := class(creative_device):

    OnBegin<override>()<suspends>:void=
        var Ready:logic = false

        for (Attempt := 1..20):
            if (AEONFALLRegionRegistry.IsRegistered["REG-001"]):
                set Ready = true
                break
            Sleep(0.25)

        if (not Ready?):
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "bootstrap.region_001_conflict_world_not_ready",
                    SourceId := "REG-001"
                }
            )
            return

        for (Definition : Region001FactionConflictDefinitions):
            Registered := AEONFALLFactionConflictRegistry.Register(Definition)
            if (not Registered?):
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "bootstrap.faction_conflict_registration_failed",
                        SourceId := Definition.ConflictId,
                        TargetId := Definition.RegionId
                    }
                )
