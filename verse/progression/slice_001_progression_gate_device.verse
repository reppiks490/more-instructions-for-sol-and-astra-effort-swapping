using { /Fortnite.com/Characters }
using { /Fortnite.com/Devices }
using { /Fortnite.com/Playspaces }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

aeonfall_slice_gate_listener := class:
    Owner:aeonfall_slice_001_progression_gate_device
    Index:int

    OnEntered(Agent:agent):void=
        Owner.OnEntered(Index, Agent)

    OnExited(Agent:agent):void=
        Owner.OnExited(Index, Agent)

var AEONFALLSliceGateOwners:weak_map(session, ?aeonfall_slice_001_progression_gate_device) = map{}

# Editor-placeable, per-player progression passage. These are one-way physical
# TELEPORT requests; actual collision/landing/navigation require Launch Session.
# Do not bind a global barrier that would unlock for unrelated players.
aeonfall_slice_001_progression_gate_device := class(creative_device):
    @editable
    GateVolumes:[]volume_device = array{}
    @editable
    GateTeleporters:[]teleporter_device = array{}
    @editable
    Feedback:hud_message_device = hud_message_device{}

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}
    GateIds:[]string = array{
        "SLICE-001:GATE-RED-MASON",
        "SLICE-001:GATE-SAINTLESS",
        "SLICE-001:GATE-GRAVE-MARKET",
        "SLICE-001:GATE-BLACK-THRONE",
        "SLICE-001:GATE-EXIT"
    }
    var Running:logic = false
    var OwnsLease:logic = false
    var Subscriptions:[]cancelable = array{}
    # A latch is transient, per player AND per gate; exiting rearms that gate.
    var Latched:[player][]int = map{}

    Message<localizes>(Text:string):message = "{Text}"

    OnBegin<override>()<suspends>:void=
        if (not ValidatePhysicalBindings()?):
            Print("AEONFALL: SLICE-001 progression gate bindings invalid; disabled.")
            return
        if:
            Existing := AEONFALLSliceGateOwners[GetSession()]
            Owner := Existing?
            Owner <> Self
        then:
            Print("AEONFALL: duplicate SLICE-001 progression gate owner rejected.")
            return
        if (set AEONFALLSliceGateOwners[GetSession()] = option{Self}):
            set OwnsLease = true
        if (not OwnsLease?):
            return
        set Running = true
        set Subscriptions = array{
            GetPlayspace().PlayerRemovedEvent().Subscribe(OnPlayerRemoved)
        }
        for (Index -> Volume : GateVolumes):
            Listener := aeonfall_slice_gate_listener{Owner := Self, Index := Index}
            set Subscriptions += array{
                Volume.AgentEntersEvent.Subscribe(Listener.OnEntered),
                Volume.AgentExitsEvent.Subscribe(Listener.OnExited)
            }

    ValidatePhysicalBindings()<transacts>:logic=
        if (GateVolumes.Length <> 5 or GateTeleporters.Length <> 5):
            return false
        if (Devices := GetPhysicalDevices[]):
            return true
        false

    GetPhysicalDevices()<decides><transacts>:[]creative_object=
        var Devices:[]creative_object = array{}
        for (Volume : GateVolumes):
            set Devices = AddPhysicalDevice[Devices, Volume]
        for (Teleporter : GateTeleporters):
            set Devices = AddPhysicalDevice[Devices, Teleporter]
        set Devices = AddPhysicalDevice[Devices, Feedback]
        Devices

    AddPhysicalDevice(Devices:[]creative_object, Device:creative_object)<decides><transacts>:[]creative_object=
        Device.IsValid[]
        not Devices.Find[Device]
        Devices + array{Device}

    OnEntered(Index:int, Agent:agent):void=
        if:
            Running?
            Index >= 0
            Index < 5
            Player := player[Agent]
            Player.IsActive[]
            Character := Player.GetFortCharacter[]
            Character.IsActive[]
        then:
            if (Existing := Latched[Player]):
                if (Existing.Find[Index]):
                    return
            # Fail closed on unavailable profile. The Verse director has its
            # own identical gate on encounter start, so direct triggers cannot
            # bypass this physical passage.
            if (Profile := ProfileService.GetProfile[Player]):
                if (AEONFALLSlice001GateAllowed(Profile, Index)?):
                    if (Destination := GateTeleporters[Index]):
                        var Used:[]int = array{}
                        if (Old := Latched[Player]):
                            set Used = Old
                        if (set Latched[Player] = Used + array{Index}):
                            Destination.Teleport(Player)
                            if (GateId := GateIds[Index]):
                                AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                                    EventType := "progression.gate_teleport_requested",
                                    SourceId := GateId
                                })
                        return
            Feedback.Show(Player, Message("Path sealed: complete earlier Ossuary milestones."))

    OnExited(Index:int, Agent:agent):void=
        if (Player := player[Agent], Existing := Latched[Player]):
            var Remaining:[]int = array{}
            for (Stored : Existing, Stored <> Index):
                set Remaining += array{Stored}
            if (set Latched[Player] = Remaining) {}

    OnPlayerRemoved(Player:player):void=
        var Kept:[player][]int = map{}
        for (Other -> Indices : Latched, Other <> Player):
            if (set Kept[Other] = Indices) {}
        set Latched = Kept

    OnEnd<override>():void=
        set Running = false
        for (Subscription : Subscriptions):
            Subscription.Cancel()
        set Subscriptions = array{}
        set Latched = map{}
        if:
            OwnsLease?
            Existing := AEONFALLSliceGateOwners[GetSession()]
            Owner := Existing?
            Owner = Self
        then:
            if (set AEONFALLSliceGateOwners[GetSession()] = false) {}
        set OwnsLease = false
