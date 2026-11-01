using { /Fortnite.com/Characters }
using { /Fortnite.com/Devices }
using { /Fortnite.com/Playspaces }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# A placed, source-authored checkpoint is not a respawn until its volume,
# teleporter and player spawner are bound in UEFN and tested in Launch Session.
aeonfall_slice_checkpoint_listener := class:
    Owner:aeonfall_slice_001_checkpoint_device
    Index:int

    OnEntered(Agent:agent):void=
        Owner.OnCheckpointEntered(Index, Agent)

var AEONFALLSliceCheckpointOwners:weak_map(session, ?aeonfall_slice_001_checkpoint_device) = map{}

# CHECKPOINT-1..4 use the canonical Ossuary geometry marker order.
# Discovery persists in the existing single player profile; transient character
# identity and pending restoration never persist. No new weak_map(player, ...) root.
aeonfall_slice_001_checkpoint_device := class(creative_device):
    @editable
    CheckpointVolumes:[]volume_device = array{}
    @editable
    CheckpointTeleporters:[]teleporter_device = array{}
    @editable
    PlayerSpawners:[]player_spawner_device = array{}
    @editable
    Feedback:hud_message_device = hud_message_device{}

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}
    CheckpointIds:[]string = array{
        "SLICE-001:CHECKPOINT-1",
        "SLICE-001:CHECKPOINT-2",
        "SLICE-001:CHECKPOINT-3",
        "SLICE-001:CHECKPOINT-4"
    }
    var Running:logic = false
    var OwnsLease:logic = false
    var Subscriptions:[]cancelable = array{}
    var PendingPlayers:[player]logic = map{}
    var SeenCharacters:[player]fort_character = map{}

    Message<localizes>(Text:string):message = "{Text}"

    OnBegin<override>()<suspends>:void=
        # Fail before any subscriptions, teleports or persistent writes.
        if (not ValidatePhysicalBindings()?):
            Print("AEONFALL: SLICE-001 checkpoint bindings invalid; device disabled.")
            return
        if:
            Lease := AEONFALLSliceCheckpointOwners[GetSession()]
            Owner := Lease?
            Owner <> Self
        then:
            Print("AEONFALL: duplicate checkpoint owner rejected.")
            return
        if (set AEONFALLSliceCheckpointOwners[GetSession()] = option{Self}):
            set OwnsLease = true
        if (not OwnsLease?):
            return

        set Running = true
        set Subscriptions = array{
            GetPlayspace().PlayerAddedEvent().Subscribe(OnPlayerAdded),
            GetPlayspace().PlayerRemovedEvent().Subscribe(OnPlayerRemoved)
        }
        for (Index -> Volume : CheckpointVolumes):
            Listener := aeonfall_slice_checkpoint_listener{Owner := Self, Index := Index}
            set Subscriptions += array{Volume.AgentEntersEvent.Subscribe(Listener.OnEntered)}
        for (Spawner : PlayerSpawners):
            set Subscriptions += array{Spawner.SpawnedEvent.Subscribe(OnSpawned)}
        for (Player : GetPlayspace().GetPlayers()):
            QueuePlayer(Player)

    OnEnd<override>():void=
        set Running = false
        for (Subscription : Subscriptions):
            Subscription.Cancel()
        set Subscriptions = array{}
        set PendingPlayers = map{}
        set SeenCharacters = map{}
        if:
            OwnsLease?
            Lease := AEONFALLSliceCheckpointOwners[GetSession()]
            Owner := Lease?
            Owner = Self
        then:
            if (set AEONFALLSliceCheckpointOwners[GetSession()] = false) {}
        set OwnsLease = false

    ValidatePhysicalBindings()<transacts>:logic=
        if (CheckpointVolumes.Length <> 4 or CheckpointTeleporters.Length <> 4 or PlayerSpawners.Length = 0):
            return false
        if (Devices := GetPhysicalDevices[]):
            return true
        false

    GetPhysicalDevices()<decides><transacts>:[]creative_object=
        var Devices:[]creative_object = array{}
        for (Volume : CheckpointVolumes):
            set Devices = AddPhysicalDevice[Devices, Volume]
        for (Teleporter : CheckpointTeleporters):
            set Devices = AddPhysicalDevice[Devices, Teleporter]
        for (Spawner : PlayerSpawners):
            set Devices = AddPhysicalDevice[Devices, Spawner]
        Devices

    AddPhysicalDevice(Devices:[]creative_object, Device:creative_object)<decides><transacts>:[]creative_object=
        Device.IsValid[]
        not Devices.Find[Device]
        Devices + array{Device}

    OnCheckpointEntered(Index:int, Agent:agent):void=
        if:
            Running?
            Index >= 0
            Index < 4
            Player := player[Agent]
            Player.IsActive[]
            Character := Player.GetFortCharacter[]
            Character.IsActive[]
        then:
            if (Profile := ProfileService.GetProfile[Player]):
                if (Id := CheckpointIds[Index]):
                    if (Profile.DiscoveredPoiIds.Find[Id]):
                        return
            Saved := TryCommitCheckpoint(Player, Index)
            if (Saved?):
                Feedback.Show(Player, Message("Ossuary checkpoint secured."))
                if (Id := CheckpointIds[Index]):
                    AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                        EventType := "progression.checkpoint_saved",
                        SourceId := Id
                    })
            else:
                Feedback.Show(Player, Message("Checkpoint locked or save unavailable."))

    # Only the next contiguous checkpoint may be committed. Repeated entry is
    # idempotent, but does not generate a second save or reward.
    TryCommitCheckpoint(Player:player, Index:int)<transacts>:logic=
        if (Index < 0 or Index >= 4):
            return false
        if:
            Player.IsActive[]
            Old := ProfileService.GetProfile[Player]
            Id := CheckpointIds[Index]
        then:
            if (Old.DiscoveredPoiIds.Find[Id]):
                return true
            if (Index > 0):
                if (PreviousId := CheckpointIds[Index - 1]):
                    if (not Old.DiscoveredPoiIds.Find[PreviousId]):
                        return false
                else:
                    return false
            Candidate := aeonfall_player_profile:
                MakeAEONFALLPlayerProfile<constructor>(Old)
                DiscoveredPoiIds := Old.DiscoveredPoiIds + array{Id}
            return ProfileService.TrySaveProfile(Player, Candidate)
        false

    OnPlayerAdded(Player:player):void=
        QueuePlayer(Player)

    OnSpawned(Agent:agent):void=
        if (Player := player[Agent]):
            QueuePlayer(Player)

    QueuePlayer(Player:player):void=
        if (Existing := PendingPlayers[Player], Existing?):
            return
        if (Running?, Player.IsActive[], set PendingPlayers[Player] = true):
            spawn{RestoreWhenReady(Player)}

    RestoreWhenReady(Player:player)<suspends>:void=
        var Attempt:int = 0
        loop:
            if (not Running? or not Player.IsActive[]):
                return
            if:
                Profile := ProfileService.GetProfile[Player]
                Character := Player.GetFortCharacter[]
                Character.IsActive[]
            then:
                if (Seen := SeenCharacters[Player], Seen = Character):
                    if (set PendingPlayers[Player] = false) {}
                    return
                Latest := LatestContiguousCheckpoint(Profile)
                if (Latest >= 0):
                    if (Destination := CheckpointTeleporters[Latest]):
                        # Native Teleport is a request, not evidence of successful
                        # arrival. Validate actual location in Launch Session.
                        Destination.Teleport(Player)
                        if (Id := CheckpointIds[Latest]):
                            AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                                EventType := "player.checkpoint_restore_requested",
                                SourceId := Id
                            })
                    else:
                        return
                if (set SeenCharacters[Player] = Character):
                    if (set PendingPlayers[Player] = false) {}
                    return
            set Attempt += 1
            if (Attempt >= 100):
                if (set PendingPlayers[Player] = false) {}
                Print("AEONFALL: checkpoint restore timed out waiting for active profile/character.")
                return
            Sleep(0.1)

    LatestContiguousCheckpoint(Profile:aeonfall_player_profile)<transacts>:int=
        var Latest:int = -1
        for (Index -> Id : CheckpointIds):
            if (Profile.DiscoveredPoiIds.Find[Id]):
                set Latest = Index
            else:
                return Latest
        Latest

    OnPlayerRemoved(Player:player):void=
        var Pending:[player]logic = map{}
        var Seen:[player]fort_character = map{}
        for (Stored -> Value : PendingPlayers, Stored <> Player):
            if (set Pending[Stored] = Value) {}
        for (Stored -> Character : SeenCharacters, Stored <> Player):
            if (set Seen[Stored] = Character) {}
        set PendingPlayers = Pending
        set SeenCharacters = Seen
