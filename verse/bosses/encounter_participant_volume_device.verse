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
            RuntimeKey := AEONFALLActorRegistry.GetRuntimeKey[Player]
        then:
            Added := AEONFALLEncounterParticipation.Add(
                EncounterId,
                RuntimeKey
            )
            if (Added?):
                Added = true

    OnExited(Agent:agent)<transacts>:void=
        if:
            Player := player[Agent]
            RuntimeKey := AEONFALLActorRegistry.GetRuntimeKey[Player]
        then:
            Removed := AEONFALLEncounterParticipation.Remove(
                EncounterId,
                RuntimeKey
            )
            if (Removed?):
                Removed = true
