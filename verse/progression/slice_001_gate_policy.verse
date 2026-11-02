# Source-only admission policy for SLICE-001. No separate persistence root.
# A missing or noncontiguous player profile never grants access.
# The gate index is tied to source-pinned editor handoff bindings.
AEONFALLSlice001GateAllowed(Profile:aeonfall_player_profile, GateIndex:int)<transacts>:logic=
    if (GateIndex < 0 or GateIndex > 4):
        return false
    CheckpointIds:[]string = array{
        "SLICE-001:CHECKPOINT-1", "SLICE-001:CHECKPOINT-2",
        "SLICE-001:CHECKPOINT-3", "SLICE-001:CHECKPOINT-4"
    }
    RequiredLastCheckpoint := if (GateIndex >= 4) then 3 else GateIndex
    # Require the FULL checkpoint prefix, not just the final identifier.
    for (Index -> Id : CheckpointIds):
        if (Index <= RequiredLastCheckpoint):
            if (not Profile.DiscoveredPoiIds.Find[Id]):
                return false
    if (GateIndex >= 1 and not Profile.CompletedBossIds.Find["BOS-005"]):
        return false
    if (GateIndex >= 2 and not Profile.CompletedBossIds.Find["BOS-006"]):
        return false
    if (GateIndex >= 3 and not Profile.CompletedWorldEventIds.Find["EVT-011"]):
        return false
    if (GateIndex >= 4 and not Profile.CompletedBossIds.Find["BOS-011"]):
        return false
    true

# Director ingress uses the same policy as physical passage. A direct UEFN
# trigger graph cannot bypass the checkpoint and prior encounter requirements.
AEONFALLSlice001CanStart(Profile:aeonfall_player_profile, EncounterId:string)<transacts>:logic=
    if (EncounterId = "BOS-005"):
        return AEONFALLSlice001GateAllowed(Profile, 0)
    if (EncounterId = "BOS-006"):
        return AEONFALLSlice001GateAllowed(Profile, 1)
    if (EncounterId = "EVT-011"):
        return AEONFALLSlice001GateAllowed(Profile, 2)
    if (EncounterId = "BOS-011"):
        return AEONFALLSlice001GateAllowed(Profile, 3)
    false
