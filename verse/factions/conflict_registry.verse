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
            AEONFALLRegionRegistry.IsRegistered[Definition.RegionId]
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

AEONFALLFactionConflictRegistry:aeonfall_faction_conflict_registry =
    aeonfall_faction_conflict_registry{}
