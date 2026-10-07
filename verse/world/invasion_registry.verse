aeonfall_invasion_registry := class():

    var Definitions:[string]aeonfall_invasion_definition = map{}

    Register(Definition:aeonfall_invasion_definition)<transacts>:logic=
        if:
            Definition.InvasionId <> ""
            Definition.RegionId <> ""
            Definition.WaveSpawnGroupIds.Length > 0
            Definition.DurationSeconds > 0.0
            Definition.MaxConcurrentAi > 0
            AEONFALLRegionRegistry.IsRegistered[Definition.RegionId]
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

AEONFALLInvasionRegistry:aeonfall_invasion_registry = aeonfall_invasion_registry{}
