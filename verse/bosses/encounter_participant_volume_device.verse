using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Project-bound human-participation volume. A stopped device must not process
# stale enter/exit callbacks; ownership of the encounter participant registry
# itself remains with the canonical encounter director / actor lifecycle.
aeonfall_encounter_participant_volume_device := class(creative_device):

    @editable
    EncounterId:string = ""

    @editable
    Volume:volume_device = volume_device{}

    var Running:logic = false
    var Subscriptions:[]cancelable = array{}

    OnBegin<override>()<suspends>:void=
        if (EncounterId = ""):
            Print("AEONFALL participant volume requires an encounter ID.")
            return
        set Running = true
        set Subscriptions = array{
            Volume.AgentEntersEvent.Subscribe(OnEntered),
            Volume.AgentExitsEvent.Subscribe(OnExited)
        }
        # Register players already inside on startup.
        for (Agent : Volume.GetAgentsInVolume()):
            OnEntered(Agent)

    OnEnd<override>():void=
        set Running = false
        for (Subscription : Subscriptions):
            Subscription.Cancel()
        set Subscriptions = array{}
        # Do not ClearEncounter here: the director or another bound participant
        # source may still own the same canonical encounter.

    OnEntered(Agent:agent)<transacts>:void=
        if (not Running?):
            return
        if:
            Player := player[Agent]
            RuntimeKey := GetAEONFALLActorRegistry().GetRuntimeKey[Player]
        then:
            Added := GetAEONFALLEncounterParticipation().Add(
                EncounterId,
                RuntimeKey
            )

    OnExited(Agent:agent)<transacts>:void=
        if (not Running?):
            return
        if:
            Player := player[Agent]
            RuntimeKey := GetAEONFALLActorRegistry().GetRuntimeKey[Player]
        then:
            Removed := GetAEONFALLEncounterParticipation().Remove(
                EncounterId,
                RuntimeKey
            )
