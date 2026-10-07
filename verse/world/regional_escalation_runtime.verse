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

            if (Band >= 1):
                Added1 := AEONFALLRegionRuntime.AddMutation(
                    RegionId,
                    "MUT-CORRUPTION-I"
                )
                if (Added1?):
                    Added1 = true

            if (Band >= 2):
                Added2 := AEONFALLRegionRuntime.AddMutation(
                    RegionId,
                    "MUT-CORRUPTION-II"
                )
                if (Added2?):
                    Added2 = true

            if (Band >= 3):
                Added3 := AEONFALLRegionRuntime.AddMutation(
                    RegionId,
                    "MUT-CORRUPTION-III"
                )
                if (Added3?):
                    Added3 = true

            if (Band >= 4):
                Added4 := AEONFALLRegionRuntime.AddMutation(
                    RegionId,
                    "MUT-CORRUPTION-IV"
                )
                if (Added4?):
                    Added4 = true

            if (Band >= 5):
                Added5 := AEONFALLRegionRuntime.AddMutation(
                    RegionId,
                    "MUT-CORRUPTION-V"
                )
                if (Added5?):
                    Added5 = true

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
