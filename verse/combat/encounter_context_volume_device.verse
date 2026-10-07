using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Binds a UEFN volume to AEONFALL encounter context.
aeonfall_encounter_context_volume_device := class(creative_device):

    @editable
    Volume:volume_device = volume_device{}

    @editable
    EncounterId:string = ""

    OnBegin<override>()<suspends>:void=
        Volume.AgentEntersEvent.Subscribe(OnEnter)
        Volume.AgentExitsEvent.Subscribe(OnExit)

    OnEnter(Agent:agent)<transacts>:void=
        Entered := AEONFALLActorContextRuntime.EnterEncounter(
            Agent,
            EncounterId
        )
        if (Entered?):
            Entered = true

    OnExit(Agent:agent)<transacts>:void=
        Exited := AEONFALLActorContextRuntime.ExitEncounter(
            Agent,
            EncounterId
        )
        if (Exited?):
            Exited = true
