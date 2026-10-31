using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Project-bound participant volume.
# Bind this to a UEFN volume_device surrounding a boss arena, dungeon chamber,
# or world-event participation zone.
aeonfall_encounter_participant_volume_device := class(creative_device):

    @editable
    EncounterId:string = ""

    @editable
    Volume:volume_device = volume_device{}

    OnBegin<override>()<suspends>:void=
        Volume.AgentEntersEvent.Subscribe(OnEntered)
        Volume.AgentExitsEvent.Subscribe(OnExited)

        # Register players already in the volume when the device begins.
        for (Agent : Volume.GetAgentsInVolume()):
            OnEntered(Agent)

    OnEntered(Agent:agent)<transacts>:void=
        if:
            Player := player[Agent]
            RuntimeKey := GetAEONFALLActorRegistry().GetRuntimeKey[Player]
        then:
            Added := GetAEONFALLEncounterParticipation().Add(
                EncounterId,
                RuntimeKey
            )

    OnExited(Agent:agent)<transacts>:void=
        if:
            Player := player[Agent]
            RuntimeKey := GetAEONFALLActorRegistry().GetRuntimeKey[Player]
        then:
            Removed := GetAEONFALLEncounterParticipation().Remove(
                EncounterId,
                RuntimeKey
            )
