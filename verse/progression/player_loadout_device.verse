using { /Fortnite.com/Characters }
using { /Fortnite.com/Devices }
using { /Fortnite.com/Playspaces }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

var AEONFALLPlayerLoadoutOwners:weak_map(session, ?aeonfall_player_loadout_device) = map{}

# One player-loop owner per map. Subscribe before enumerating existing players.
# Configure spawn pads and selection buttons; normal startup ordering is awaited.
aeonfall_player_loadout_device := class(creative_device):
    @editable
    PlayerSpawners:[]player_spawner_device = array{}
    @editable
    DefaultClassId:string = "CLS-006"
    @editable
    SelectSepulchral:button_device = button_device{}
    @editable
    SelectBeastCrown:button_device = button_device{}
    @editable
    SelectStarterWeapon:button_device = button_device{}
    @editable
    SelectAshcoil:button_device = button_device{}
    @editable
    SelectCorpseRoute:button_device = button_device{}
    @editable
    Feedback:hud_message_device = hud_message_device{}
    # Enable only when Island Settings remove equipment on the corresponding
    # spawn. Durable unlocks are not proof that inventory needs another item.
    @editable
    RestoreEquipmentOnFirstSpawn:logic = false
    @editable
    RestoreEquipmentOnRespawn:logic = false

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}
    var Running:logic = false
    var OwnsLease:logic = false
    var Subscriptions:[]cancelable = array{}
    var PendingPlayers:[player]logic = map{}
    var SeenCharacters:[player]fort_character = map{}
    var StarterDeliveryNeeded:[player]logic = map{}

    Message<localizes>(Text:string):message = "{Text}"

    OnBegin<override>()<suspends>:void=
        if:
            Lease := AEONFALLPlayerLoadoutOwners[GetSession()]
            Owner := Lease?
            Owner <> Self
        then:
            Print("AEONFALL: duplicate player loadout device rejected before subscriptions.")
            return
        if (set AEONFALLPlayerLoadoutOwners[GetSession()] = option{Self}):
            set OwnsLease = true
        if (not OwnsLease?):
            return
        set Running = true
        Added := GetPlayspace().PlayerAddedEvent().Subscribe(OnPlayerAdded)
        Removed := GetPlayspace().PlayerRemovedEvent().Subscribe(OnPlayerRemoved)
        Sepulchral := SelectSepulchral.InteractedWithEvent.Subscribe(OnSepulchral)
        Crown := SelectBeastCrown.InteractedWithEvent.Subscribe(OnCrown)
        Starter := SelectStarterWeapon.InteractedWithEvent.Subscribe(OnStarterWeapon)
        Ashcoil := SelectAshcoil.InteractedWithEvent.Subscribe(OnAshcoil)
        Route := SelectCorpseRoute.InteractedWithEvent.Subscribe(OnCorpseRoute)
        set Subscriptions = array{Added, Removed, Sepulchral, Crown, Starter, Ashcoil, Route}
        for (Spawner : PlayerSpawners):
            Spawned := Spawner.SpawnedEvent.Subscribe(OnSpawned)
            set Subscriptions += array{Spawned}
        for (Player : GetPlayspace().GetPlayers()):
            QueuePlayer(Player)

    OnEnd<override>():void=
        set Running = false
        if:
            OwnsLease?
            Lease := AEONFALLPlayerLoadoutOwners[GetSession()]
            Owner := Lease?
            Owner = Self
        then:
            if (set AEONFALLPlayerLoadoutOwners[GetSession()] = false) {}
        set OwnsLease = false
        for (Subscription : Subscriptions):
            Subscription.Cancel()
        set Subscriptions = array{}
        set PendingPlayers = map{}
        set SeenCharacters = map{}
        set StarterDeliveryNeeded = map{}

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

    OnPlayerRemoved(Player:player):void=
        # Remove inactive players without accessing their persistent weak map.
        var Pending:[player]logic = map{}
        var Seen:[player]fort_character = map{}
        var Starters:[player]logic = map{}
        for (StoredPlayer -> Value : PendingPlayers):
            if (StoredPlayer <> Player, set Pending[StoredPlayer] = Value) {}
        for (StoredPlayer -> Character : SeenCharacters):
            if (StoredPlayer <> Player, set Seen[StoredPlayer] = Character) {}
        for (StoredPlayer -> Value : StarterDeliveryNeeded):
            if (StoredPlayer <> Player, set Starters[StoredPlayer] = Value) {}
        set PendingPlayers = Pending
        set SeenCharacters = Seen
        set StarterDeliveryNeeded = Starters

    RegistriesReady(Player:player)<transacts>:logic=
        if:
            Player.IsActive[]
            Profile := ProfileService.GetProfile[Player]
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Player]
            Character := Player.GetFortCharacter[]
            Character.IsActive[]
            DefaultDefinition := GetAEONFALLClassRegistry().Get[DefaultClassId]
        then:
            # Wait for all authored class abilities, not just the first registry.
            for (Definition : Slice001ClassDefinitions):
                if (not GetAEONFALLClassRegistry().Get[Definition.ClassId]):
                    return false
                for (AbilityId : Definition.AbilityIds):
                    if (not GetAEONFALLAbilityRegistry().Get[AbilityId]):
                        return false
            for (AbilityDefinition : Slice001AbilityDefinitions):
                if (not GetAEONFALLAbilityRegistry().Get[AbilityDefinition.AbilityId]):
                    return false
            return true
        false

    RestoreWhenReady(Player:player)<suspends>:void=
        # Startup and respawn races have a bounded wait and visible diagnostics.
        var Attempt:int = 0
        loop:
            if (not Running?):
                return
            if (not Player.IsActive[]):
                return
            Ready := RegistriesReady(Player)
            if (Ready?):
                Restored := RestorePlayer(Player)
                if (Restored?):
                    if (set PendingPlayers[Player] = false) {}
                    return
            set Attempt += 1
            if (Attempt >= 100):
                if (set PendingPlayers[Player] = false) {}
                Feedback.Show(Player, Message("AEONFALL loadout is unavailable. Check bootstrap and delivery bindings."))
                AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                    EventType := "player.loadout_startup_failed",
                    SourceId := "player",
                    ContextId := "readiness_or_checked_save_timeout"
                })
                return
            Sleep(0.1)

    RestorePlayer(Player:player):logic=
        if:
            Player.IsActive[]
            Profile := ProfileService.GetProfile[Player]
            Character := Player.GetFortCharacter[]
            Character.IsActive[]
        then:
            if (Seen := SeenCharacters[Player], Seen = Character):
                return true
            var FirstSpawn:logic = true
            if (SeenCharacters[Player]):
                set FirstSpawn = false
            if (not Profile.UnlockedEntityIds.Find["WPN-001"]):
                if (set StarterDeliveryNeeded[Player] = true) {}
            StarterSaved := AEONFALLPlayerLoadoutService.EnsureStarter(Player, "WPN-001")
            if (not StarterSaved?):
                return false
            ClassId:string = if (Profile.EquippedClassId <> "") then Profile.EquippedClassId else DefaultClassId
            Activated := AEONFALLPlayerLoadoutService.TrySelectClass(Player, ClassId)
            if (not Activated?):
                return false
            Initialized := AEONFALLPlayerLoadoutService.InitializeEquippedAbilities(Player)
            if (not Initialized?):
                return false
            if (Needed := StarterDeliveryNeeded[Player], Needed?):
                Started := GetAEONFALLUnlockDeliveryService().QueueAfterCommit(Player, "WPN-001", "starter.loadout")
                if (not Started?):
                    return false
                if (set StarterDeliveryNeeded[Player] = false) {}
            else:
                if ((FirstSpawn? and RestoreEquipmentOnFirstSpawn?) or (not FirstSpawn? and RestoreEquipmentOnRespawn?)):
                    if (Current := ProfileService.GetProfile[Player]):
                        Started := GetAEONFALLUnlockDeliveryService().RequestEquipmentRestore(
                            Player, Current.EquippedWeaponIds, "loadout.spawn_restore"
                        )
                        if (not Started?):
                            return false
            if (set SeenCharacters[Player] = Character):
                AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                    EventType := "player.loadout_ready",
                    SourceId := ClassId
                })
                return true
        false

    OnSepulchral(Agent:agent):void=
        SelectClass(Agent, "CLS-006")
    OnCrown(Agent:agent):void=
        SelectClass(Agent, "CLS-007")
    OnStarterWeapon(Agent:agent):void=
        SelectWeapon(Agent, "WPN-001")
    OnAshcoil(Agent:agent):void=
        SelectWeapon(Agent, "WPN-007")
    OnCorpseRoute(Agent:agent):void=
        SelectWeapon(Agent, "WPN-124")

    SelectClass(Agent:agent, ClassId:string):void=
        if (Player := player[Agent]):
            Selected := AEONFALLPlayerLoadoutService.TrySelectClass(Player, ClassId)
            if (Selected?):
                Feedback.Show(Player, Message("Class selected: " + ClassId))
            else:
                Feedback.Show(Player, Message("Class selection denied: locked, pending ability, or save unavailable."))

    SelectWeapon(Agent:agent, WeaponId:string):void=
        if (Player := player[Agent]):
            Selected := AEONFALLPlayerLoadoutService.TrySelectWeapon(Player, WeaponId)
            if (Selected?):
                Feedback.Show(Player, Message("Weapon selected: " + WeaponId))
            else:
                Feedback.Show(Player, Message("Unlock this weapon before selecting it."))
