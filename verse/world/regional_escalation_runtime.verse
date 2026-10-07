# Derives living-world pressure from canonical region state.
# Project-bound directors translate pressure bands into concrete spawn groups,
# weather, VFX, loot, encounter tables, and music.

aeonfall_region_pressure := class:
    RegionId:string = ""
    HostilityTier:int = 0
    SpawnPressure:int = 0
    ElitePressure:int = 0
    HazardPressure:int = 0
    CorruptionBand:int = 0

aeonfall_regional_escalation_service := class():

    CorruptionBand(Value:int):int=
        if (Value >= 95):
            5
        else if (Value >= 80):
            4
        else if (Value >= 60):
            3
        else if (Value >= 40):
            2
        else if (Value >= 20):
            1
        else:
            0

    ComputeHostility(State:aeonfall_region_runtime_state):int=
        var Tier:int = CorruptionBand(State.Corruption)

        if (State.ActiveEventIds.Length >= 1):
            set Tier += 1

        if (State.ActiveEventIds.Length >= 2):
            set Tier += 1

        if (Tier > 5):
            5
        else:
            Tier

    GetPressure(RegionId:string)<decides><transacts>:aeonfall_region_pressure=
        State := AEONFALLRegionRuntime.GetState[RegionId]
        Tier:int = ComputeHostility(State)
        Band:int = CorruptionBand(State.Corruption)

        aeonfall_region_pressure:
            RegionId := RegionId
            HostilityTier := Tier
            SpawnPressure := Tier
            ElitePressure := Band
            HazardPressure :=
                if (Tier + Band > 5):
                    5
                else:
                    Tier + Band
            CorruptionBand := Band

    ReconcileMutation(
        RegionId:string,
        MutationId:string,
        ShouldBeActive:logic
    )<transacts>:void=
        if (ShouldBeActive?):
            Added := AEONFALLRegionRuntime.AddMutation(
                RegionId,
                MutationId
            )
            if (Added?):
                Added = true
        else:
            Removed := AEONFALLRegionRuntime.RemoveMutation(
                RegionId,
                MutationId
            )
            if (Removed?):
                Removed = true

    ReconcileRegion(RegionId:string)<transacts>:logic=
        if:
            State := AEONFALLRegionRuntime.GetState[RegionId]
        then:
            NewTier:int = ComputeHostility(State)
            Changed := AEONFALLRegionRuntime.SetHostilityTier(
                RegionId,
                NewTier
            )

            Band:int = CorruptionBand(State.Corruption)

            # Mutation flags are exact state, not an append-only history.
            # Cleansing corruption must remove tiers no longer justified.
            ReconcileMutation(
                RegionId,
                "MUT-CORRUPTION-I",
                Band >= 1
            )
            ReconcileMutation(
                RegionId,
                "MUT-CORRUPTION-II",
                Band >= 2
            )
            ReconcileMutation(
                RegionId,
                "MUT-CORRUPTION-III",
                Band >= 3
            )
            ReconcileMutation(
                RegionId,
                "MUT-CORRUPTION-IV",
                Band >= 4
            )
            ReconcileMutation(
                RegionId,
                "MUT-CORRUPTION-V",
                Band >= 5
            )

            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "region.pressure_reconciled",
                    SourceId := RegionId,
                    Amount := NewTier,
                    ContextId := "corruption_band::{Band}"
                }
            )
            return Changed

        false

AEONFALLRegionalEscalation:aeonfall_regional_escalation_service =
    aeonfall_regional_escalation_service{}
