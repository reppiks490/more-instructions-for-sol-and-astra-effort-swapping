using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Fortnite.com/Playspaces }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

TitanProxyDenied<localizes>:message = "Titan proxy unavailable: FUS-001 owner or binding rejected."
TitanProxyReady<localizes>:message = "Experimental Titan proxy summoned. Player movement stays native."
TitanProxyReleased<localizes>:message = "Titan proxy released."

# Disabled-by-default, research-only physical harness. This is NOT a native
# FUS-002 transformation, NPC possession or custom player skeletal mesh.
aeonfall_titan_proxy_device := class(creative_device):
    @editable
    Enabled:logic = false
    @editable
    AvatarController:aeonfall_sovereign_fusion_device = aeonfall_sovereign_fusion_device{}
    @editable
    TitanSpawner:npc_spawner_device = npc_spawner_device{}
    @editable
    SummonInput:input_trigger_device = input_trigger_device{}
    @editable
    AdvanceInput:input_trigger_device = input_trigger_device{}
    @editable
    AttackCueInput:input_trigger_device = input_trigger_device{}
    @editable
    DismissInput:input_trigger_device = input_trigger_device{}
    @editable
    AttackCueOutput:trigger_device = trigger_device{}
    @editable
    Waypoints:[]creative_prop = array{}
    @editable
    Feedback:hud_message_device = hud_message_device{}

    var Running:logic = false
    var Service:?aeonfall_titan_proxy_command_runtime = false
    var ProxyOwner:?player = false
    var ProxyCharacter:?fort_character = false
    var Epoch:int = 0
    var WaypointIndex:int = 0
    var Subscriptions:[]cancelable = array{}
    StopEvent:event() = event(){}

    ValidBindings()<transacts>:logic=
        if:
            Waypoints.Length >= 1
            Waypoints.Length <= 8
            SummonInput <> AdvanceInput
            SummonInput <> AttackCueInput
            SummonInput <> DismissInput
            AdvanceInput <> AttackCueInput
            AdvanceInput <> DismissInput
            AttackCueInput <> DismissInput
        then:
            if (Devices := GetPhysicalDevices[]):
                return true
        false

    GetPhysicalDevices()<decides><transacts>:[]creative_object=
        var Devices:[]creative_object = array{}
        set Devices = AddPhysicalDevice[Devices, TitanSpawner]
        set Devices = AddPhysicalDevice[Devices, SummonInput]
        set Devices = AddPhysicalDevice[Devices, AdvanceInput]
        set Devices = AddPhysicalDevice[Devices, AttackCueInput]
        set Devices = AddPhysicalDevice[Devices, DismissInput]
        set Devices = AddPhysicalDevice[Devices, AttackCueOutput]
        set Devices = AddPhysicalDevice[Devices, Feedback]
        for (Waypoint : Waypoints):
            set Devices = AddPhysicalDevice[Devices, Waypoint]
        Devices

    AddPhysicalDevice(Devices:[]creative_object, Device:creative_object)<decides><transacts>:[]creative_object=
        Device.IsValid[]
        not Devices.Find[Device]
        Devices + array{Device}

    OnBegin<override>()<suspends>:void=
        if (not Enabled? or not ValidBindings()?):
            return
        Runtime := GetAEONFALLTitanProxyCommands()
        Acquired := Runtime.Acquire(Self)
        if (not Acquired?):
            Print("Titan proxy lease already held; duplicate harness rejected.")
            return
        set Service = option{Runtime}
        # This spawner must be Titan-owned, initially disabled and never
        # shared with world monsters, boss arenas or other fusion devices.
        TitanSpawner.Disable()
        TitanSpawner.DespawnAll(false)
        set Running = true
        set Subscriptions = array{
            SummonInput.PressedEvent.Subscribe(OnSummon),
            AdvanceInput.PressedEvent.Subscribe(OnAdvance),
            AttackCueInput.PressedEvent.Subscribe(OnAttackCue),
            DismissInput.PressedEvent.Subscribe(OnDismiss),
            GetPlayspace().PlayerRemovedEvent().Subscribe(OnPlayerLeft)
        }
        race:
            Monitor()
            StopEvent.Await()

    # Only a current and active Armor Fusion owner can operate the proxy.
    ValidOwner(Agent:agent)<decides><transacts>:player=
        Running?
        Player := player[Agent]
        Player.IsActive[]
        CurrentOwner := ProxyOwner?
        CurrentOwner = Player
        Original := ProxyCharacter?
        Character := Player.GetFortCharacter[]
        Character = Original
        Character.IsActive[]
        Runtime := Service?
        Runtime.IsAuthorized()?
        Player

    OnSummon(Agent:agent):void=
        if:
            Running?
            not ProxyOwner?
            Player := player[Agent]
            Player.IsActive[]
            Character := Player.GetFortCharacter[]
            Character.IsActive[]
            ControllerOwner := AvatarController.VisualOwner?
            ControllerOwner = Player
            ControllerCharacter := AvatarController.VisualCharacter?
            ControllerCharacter = Character
            Runtime := Service?
        then:
            Attempt := Runtime.Begin(
                Self, AvatarController, Player, Character, AvatarController.Token
            )
            if (StartedEpoch := Attempt?):
                set Epoch = StartedEpoch
                set ProxyOwner = option{Player}
                set ProxyCharacter = option{Character}
                set WaypointIndex = 0
                TitanSpawner.Reset()
                TitanSpawner.Enable()
                spawn{SpawnProxy(StartedEpoch)}
                spawn{AwaitSpawn(StartedEpoch)}
                Feedback.Show(Player, TitanProxyReady, 3.0)
                return
        Feedback.Show(Agent, TitanProxyDenied, 3.0)

    AwaitSpawn(ExpectedEpoch:int)<suspends>:void=
        Sleep(5.0)
        if:
            Running?
            Runtime := Service?
            Runtime.IsCurrentEpoch(ExpectedEpoch)?
            not Runtime.HasNpc()?
        then:
            # Timeout invalidates the generation and disables late spawns.
            FinishProxy()

    SpawnProxy(ExpectedEpoch:int)<suspends>:void=
        # SpawnAt returns the actual spawned agent, unlike SpawnedEvent, so
        # the session can associate one in-flight request with one epoch.
        if (TitanSpawner.IsValid[]):
            Position := TitanSpawner.GetTransform().Translation
            Spawned := TitanSpawner.SpawnAt(Position, false)
            if (Runtime := Service?):
                if (Runtime.CompleteSpawn(ExpectedEpoch, Spawned)?):
                    return
        # An invalid/late/failed result must not survive teardown or attach
        # to a new generation. Begin refuses new requests while in flight.
        TitanSpawner.Disable()
        TitanSpawner.DespawnAll(false)
        if (Runtime := Service?, Runtime.IsCurrentEpoch(ExpectedEpoch)?):
            FinishProxy()

    OnAdvance(Agent:agent):void=
        if (Player := ValidOwner[Agent], Runtime := Service?):
            if (WaypointIndex >= Waypoints.Length):
                set WaypointIndex = 0
            if (Waypoint := Waypoints[WaypointIndex], Waypoint.IsValid[]):
                Destination := Waypoint.GetTransform().Translation
                if (Runtime.RequestMove(Player, Destination)?):
                    set WaypointIndex += 1

    OnAttackCue(Agent:agent):void=
        if (Player := ValidOwner[Agent], Runtime := Service?):
            if (Runtime.RequestAttackCue(Player)?):
                # This signal is owner-tagged animation/audio ONLY. It must
                # never directly drive Damage, a grant or shared global VFX.
                AttackCueOutput.Trigger(Player)

    OnDismiss(Agent:agent):void=
        if (Player := ValidOwner[Agent]):
            FinishProxy()
            Feedback.Show(Player, TitanProxyReleased, 2.0)

    OnPlayerLeft(Player:player):void=
        if (Owner := ProxyOwner?, Owner = Player):
            FinishProxy()

    Monitor()<suspends>:void=
        loop:
            Sleep(0.25)
            if (not Running?):
                return
            if (Owner := ProxyOwner?, Runtime := Service?):
                if (not Runtime.IsAuthorized()?):
                    FinishProxy()

    FinishProxy():void=
        # Invalidate all mailbox commands FIRST, then remove only NPCs
        # spawned by the bound dedicated Titan spawner.
        if (Runtime := Service?):
            Stopped := Runtime.End(Self)
        if (ProxyOwner?):
            TitanSpawner.Disable()
            TitanSpawner.DespawnAll(false)
        set ProxyOwner = false
        set ProxyCharacter = false
        set Epoch = 0
        set WaypointIndex = 0

    OnEnd<override>():void=
        set Running = false
        StopEvent.Signal()
        for (Subscription : Subscriptions):
            Subscription.Cancel()
        set Subscriptions = array{}
        if (Runtime := Service?, Runtime.Owns(Self)?):
            FinishProxy()
            Runtime.Release(Self)
        set Service = false
