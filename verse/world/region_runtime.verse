# Session living-world state.
# Physical streaming, weather, NPC spawning, terrain presentation, and devices
# are project-bound adapters; this runtime owns canonical region state only.

aeonfall_region_runtime := class():

    var States:[string]aeonfall_region_runtime_state = map{}

    ClampPercent(Value:int):int=
        if (Value < 0):
            0
        else if (Value > 100):
            100
        else:
            Value

    ClampHostility(Value:int):int=
        if (Value < 0):
            0
        else if (Value > 5):
            5
        else:
            Value

    InitializeRegion(RegionId:string)<transacts>:logic=
        if:
            AEONFALLRegionRegistry.IsRegistered[RegionId]
        then:
            if:
                Existing := States[RegionId]
            then:
                return true

            Initial := aeonfall_region_runtime_state:
                RegionId := RegionId
                ControllingFactionId := ""
                FactionInfluence := map{}
                Corruption := 0
                HostilityTier := 0
                ActiveEventIds := array{}
                MutationIds := array{}

            if:
                set States[RegionId] = Initial
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "region.initialized",
                        SourceId := RegionId
                    }
                )
                return true

        false

    GetState(RegionId:string)<decides><transacts>:aeonfall_region_runtime_state=
        States[RegionId]

    ResolveController(Influence:[string]int):string=
        var BestFaction:string = ""
        var BestValue:int = 0
        var Tied:logic = false

        for (FactionId -> Value : Influence):
            if (Value > BestValue):
                set BestFaction = FactionId
                set BestValue = Value
                set Tied = false
            else if:
                Value = BestValue
                Value > 0
            then:
                set Tied = true

        if (Tied?):
            ""
        else:
            BestFaction

    SetFactionInfluence(
        RegionId:string,
        FactionId:string,
        Value:int
    )<transacts>:logic=
        if:
            FactionId <> ""
            Old := States[RegionId]
        then:
            var UpdatedInfluence:[string]int = Old.FactionInfluence
            SafeValue:int = ClampPercent(Value)

            if:
                set UpdatedInfluence[FactionId] = SafeValue
            then:
                NewController:string = ResolveController(UpdatedInfluence)

                Updated := aeonfall_region_runtime_state:
                    RegionId := Old.RegionId
                    ControllingFactionId := NewController
                    FactionInfluence := UpdatedInfluence
                    Corruption := Old.Corruption
                    HostilityTier := Old.HostilityTier
                    ActiveEventIds := Old.ActiveEventIds
                    MutationIds := Old.MutationIds

                if:
                    set States[RegionId] = Updated
                then:
                    AEONFALLRuntimeBus.Emit(
                        aeonfall_runtime_event{
                            EventType := "region.influence_changed",
                            SourceId := RegionId,
                            TargetId := FactionId,
                            ContextId := NewController,
                            Amount := SafeValue
                        }
                    )
                    return true

        false

    AddFactionInfluence(
        RegionId:string,
        FactionId:string,
        Delta:int
    )<transacts>:logic=
        if:
            Old := States[RegionId]
        then:
            var Current:int = 0
            if:
                Existing := Old.FactionInfluence[FactionId]
            then:
                set Current = Existing

            SetFactionInfluence(
                RegionId,
                FactionId,
                Current + Delta
            )
        else:
            false

    SetCorruption(
        RegionId:string,
        Value:int
    )<transacts>:logic=
        if:
            Old := States[RegionId]
        then:
            SafeValue:int = ClampPercent(Value)

            Updated := aeonfall_region_runtime_state:
                RegionId := Old.RegionId
                ControllingFactionId := Old.ControllingFactionId
                FactionInfluence := Old.FactionInfluence
                Corruption := SafeValue
                HostilityTier := Old.HostilityTier
                ActiveEventIds := Old.ActiveEventIds
                MutationIds := Old.MutationIds

            if:
                set States[RegionId] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "region.corruption_changed",
                        SourceId := RegionId,
                        Amount := SafeValue
                    }
                )
                return true

        false

    SetHostilityTier(
        RegionId:string,
        Value:int
    )<transacts>:logic=
        if:
            Old := States[RegionId]
        then:
            SafeValue:int = ClampHostility(Value)

            Updated := aeonfall_region_runtime_state:
                RegionId := Old.RegionId
                ControllingFactionId := Old.ControllingFactionId
                FactionInfluence := Old.FactionInfluence
                Corruption := Old.Corruption
                HostilityTier := SafeValue
                ActiveEventIds := Old.ActiveEventIds
                MutationIds := Old.MutationIds

            if:
                set States[RegionId] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "region.hostility_changed",
                        SourceId := RegionId,
                        Amount := SafeValue
                    }
                )
                return true

        false

    AddEvent(
        RegionId:string,
        EventId:string
    )<transacts>:logic=
        if:
            EventId <> ""
            Old := States[RegionId]
        then:
            if:
                Old.ActiveEventIds.Find[EventId]
            then:
                return false

            Updated := aeonfall_region_runtime_state:
                RegionId := Old.RegionId
                ControllingFactionId := Old.ControllingFactionId
                FactionInfluence := Old.FactionInfluence
                Corruption := Old.Corruption
                HostilityTier := Old.HostilityTier
                ActiveEventIds := Old.ActiveEventIds + array{EventId}
                MutationIds := Old.MutationIds

            if:
                set States[RegionId] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "region.event_added",
                        SourceId := RegionId,
                        TargetId := EventId
                    }
                )
                return true

        false

    RemoveEvent(
        RegionId:string,
        EventId:string
    )<transacts>:logic=
        if:
            Old := States[RegionId]
        then:
            var UpdatedEvents:[]string = array{}
            var Removed:logic = false

            for (ExistingId : Old.ActiveEventIds):
                if (ExistingId = EventId):
                    set Removed = true
                else:
                    set UpdatedEvents = UpdatedEvents + array{ExistingId}

            if (Removed?):
                Updated := aeonfall_region_runtime_state:
                    RegionId := Old.RegionId
                    ControllingFactionId := Old.ControllingFactionId
                    FactionInfluence := Old.FactionInfluence
                    Corruption := Old.Corruption
                    HostilityTier := Old.HostilityTier
                    ActiveEventIds := UpdatedEvents
                    MutationIds := Old.MutationIds

                if:
                    set States[RegionId] = Updated
                then:
                    AEONFALLRuntimeBus.Emit(
                        aeonfall_runtime_event{
                            EventType := "region.event_removed",
                            SourceId := RegionId,
                            TargetId := EventId
                        }
                    )
                    return true

        false

    AddMutation(
        RegionId:string,
        MutationId:string
    )<transacts>:logic=
        if:
            MutationId <> ""
            Old := States[RegionId]
        then:
            if:
                Old.MutationIds.Find[MutationId]
            then:
                return false

            Updated := aeonfall_region_runtime_state:
                RegionId := Old.RegionId
                ControllingFactionId := Old.ControllingFactionId
                FactionInfluence := Old.FactionInfluence
                Corruption := Old.Corruption
                HostilityTier := Old.HostilityTier
                ActiveEventIds := Old.ActiveEventIds
                MutationIds := Old.MutationIds + array{MutationId}

            if:
                set States[RegionId] = Updated
            then:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "region.mutation_added",
                        SourceId := RegionId,
                        TargetId := MutationId
                    }
                )
                return true

        false

    RemoveMutation(
        RegionId:string,
        MutationId:string
    )<transacts>:logic=
        if:
            Old := States[RegionId]
        then:
            var UpdatedMutations:[]string = array{}
            var Removed:logic = false

            for (ExistingId : Old.MutationIds):
                if (ExistingId = MutationId):
                    set Removed = true
                else:
                    set UpdatedMutations = UpdatedMutations + array{ExistingId}

            if (Removed?):
                Updated := aeonfall_region_runtime_state:
                    RegionId := Old.RegionId
                    ControllingFactionId := Old.ControllingFactionId
                    FactionInfluence := Old.FactionInfluence
                    Corruption := Old.Corruption
                    HostilityTier := Old.HostilityTier
                    ActiveEventIds := Old.ActiveEventIds
                    MutationIds := UpdatedMutations

                if:
                    set States[RegionId] = Updated
                then:
                    AEONFALLRuntimeBus.Emit(
                        aeonfall_runtime_event{
                            EventType := "region.mutation_removed",
                            SourceId := RegionId,
                            TargetId := MutationId
                        }
                    )
                    return true

        false

AEONFALLRegionRuntime:aeonfall_region_runtime = aeonfall_region_runtime{}
