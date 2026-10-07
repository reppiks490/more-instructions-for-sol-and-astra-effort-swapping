using { /Verse.org/Simulation }

# AEONFALL persistent player state.
# Keep this class append-only after first publication: new fields require defaults.
aeonfall_player_profile := class<final><persistable>:
    Version:int = 1
    Level:int = 1
    XP:int = 0
    MasteryPoints:int = 0

    # Canonical IDs are stored as strings so content definitions can evolve
    # without making the persistence schema depend on transient actors.
    UnlockedEntityIds:[]string = array{}
    CompletedBossIds:[]string = array{}
    CompletedTrialIds:[]string = array{}
    DiscoveredPoiIds:[]string = array{}

    # Ledgers use canonical IDs (for example MAT-001) as keys.
    MaterialLedger:[string]int = map{}
    FactionReputation:[string]int = map{}

    IsZeroCandidate:logic = false
    AscensionRank:int = 0
    TranscendentState:int = 0

# One versioned profile map is intentionally used as the primary persistent root.
var AEONFALLPlayerProfiles:weak_map(player, aeonfall_player_profile) = map{}
