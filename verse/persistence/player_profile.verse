using { /Verse.org/Simulation }

# AEONFALL persistent player state.
# IMPORTANT: after first production publication this class becomes append-only:
# new fields must have defaults and existing field types/names must remain compatible.
aeonfall_player_profile := class<final><persistable>:
    Version:int = 3

    Level:int = 1
    XP:int = 0
    MasteryPoints:int = 0

    # Canonical IDs decouple save data from transient actors/assets.
    UnlockedEntityIds:[]string = array{}
    MasteredClassIds:[]string = array{}
    CompletedBossIds:[]string = array{}
    CompletedWorldEventIds:[]string = array{}
    CompletedTrialIds:[]string = array{}
    DiscoveredPoiIds:[]string = array{}
    TamedSpeciesIds:[]string = array{}
    HireableUnlockIds:[]string = array{}

    # Gameplay equipment selections. Visual asset state is reconstructed at runtime.
    EquippedClassId:string = ""
    EquippedArmorIds:[]string = array{}
    EquippedWeaponIds:[]string = array{}
    EquippedRelicIds:[]string = array{}

    # Sparse ledgers use canonical IDs such as MAT-001 / FAC-001 as keys.
    MaterialLedger:[string]int = map{}
    FactionReputation:[string]int = map{}

    IsZeroCandidate:logic = false
    AscensionRank:int = 0
    AxiomHeartCrafted:logic = false
    TranscendentState:int = 0
    TranscendentHistoryCount:int = 0

# Copy constructor used for partial persistent updates.
# This follows Epic's recommended pattern: build a new immutable persistable
# class value, override selected fields, then replace the weak_map value.
MakeAEONFALLPlayerProfile<constructor>(Src:aeonfall_player_profile)<transacts> := aeonfall_player_profile:
    Version := Src.Version

    Level := Src.Level
    XP := Src.XP
    MasteryPoints := Src.MasteryPoints

    UnlockedEntityIds := Src.UnlockedEntityIds
    MasteredClassIds := Src.MasteredClassIds
    CompletedBossIds := Src.CompletedBossIds
    CompletedWorldEventIds := Src.CompletedWorldEventIds
    CompletedTrialIds := Src.CompletedTrialIds
    DiscoveredPoiIds := Src.DiscoveredPoiIds
    TamedSpeciesIds := Src.TamedSpeciesIds
    HireableUnlockIds := Src.HireableUnlockIds

    EquippedClassId := Src.EquippedClassId
    EquippedArmorIds := Src.EquippedArmorIds
    EquippedWeaponIds := Src.EquippedWeaponIds
    EquippedRelicIds := Src.EquippedRelicIds

    MaterialLedger := Src.MaterialLedger
    FactionReputation := Src.FactionReputation

    IsZeroCandidate := Src.IsZeroCandidate
    AscensionRank := Src.AscensionRank
    AxiomHeartCrafted := Src.AxiomHeartCrafted
    TranscendentState := Src.TranscendentState
    TranscendentHistoryCount := Src.TranscendentHistoryCount

# One primary persistent root keeps schema evolution manageable and stays well
# below the island limit on persistent player weak maps.
var AEONFALLPlayerProfiles:weak_map(player, aeonfall_player_profile) = map{}
