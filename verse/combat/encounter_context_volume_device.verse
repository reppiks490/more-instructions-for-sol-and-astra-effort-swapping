using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Each bound encounter volume owns exactly one depth contribution per agent.
# Duplicate native enter events cannot manufacture extra encounter context,
# and teardown releases this device's own contributions before replacement.
aeonfall_encounter_context_volume_device := class(creative_device):

    @editable
    Volume:volume_device = volume_device{}

    @editable
    EncounterId:string = ""

    var Running:logic = false
    var Subscriptions:[]cancelable = array{}
    var TrackedAgents:[agent]logic = map{}

    OnBegin<override>()<suspends>:void=
        if (EncounterId = ""):
            Print("AEONFALL encounter context volume requires an encounter ID.")
            return
        set Running = true
        set Subscriptions = array{
            Volume.AgentEntersEvent.Subscribe(OnEnter),
            Volume.AgentExitsEvent.Subscribe(OnExit)
        }
        # Native begin ordering does not imply that the volume was empty.
        for (Agent : Volume.GetAgentsInVolume()):
            OnEnter(Agent)

    OnEnd<override>():void=
        set Running = false
        for (Subscription : Subscriptions):
            Subscription.Cancel()
        set Subscriptions = array{}
        # Release only context contributions admitted by this device.
        for (TrackedAgent -> Admitted : TrackedAgents):
            if (Admitted?):
                Released := GetAEONFALLActorContextRuntime().ExitEncounter(
                    TrackedAgent, EncounterId
                )
                if (not Released?):
                    Print("AEONFALL context volume could not release an inactive actor.")
        set TrackedAgents = map{}

    # Both the canonical context increment and our ownership record share a
    # failable transaction. A failed tracking write cannot leave a phantom
    # encounter entitlement or a partially committed entry.
    CommitEnter(Agent:agent)<decides><transacts>:void=
        not TrackedAgents[Agent]
        GetAEONFALLActorContextRuntime().EnterEncounter(Agent, EncounterId)?
        set TrackedAgents[Agent] = true

    OnEnter(Agent:agent)<transacts>:void=
        if (not Running?):
            return
        if (CommitEnter[Agent]):
            return

    CommitExit(Agent:agent)<decides><transacts>:void=
        TrackedAgents[Agent]?
        GetAEONFALLActorContextRuntime().ExitEncounter(Agent, EncounterId)?
        var Remaining:[agent]logic = map{}
        for (Stored -> Admitted : TrackedAgents):
            if (Stored <> Agent):
                set Remaining[Stored] = Admitted
        set TrackedAgents = Remaining

    OnExit(Agent:agent)<transacts>:void=
        if (not Running?):
            return
        if (CommitExit[Agent]):
            return
