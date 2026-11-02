using { /Fortnite.com/Devices }
using { /Fortnite.com/Playspaces }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Exactly one bootstrap owns player identity events for this Verse session.
# Duplicate placed devices cannot repeat ready events or unregister players.
var AEONFALLActorBootstrapOwners:weak_map(session, ?aeonfall_actor_registry_bootstrap_device) = map{}

# Registers human players into the same session identity system used by NPCs.
aeonfall_actor_registry_bootstrap_device := class(creative_device):
    var Subscriptions:[]cancelable = array{}
    var Running:logic = false
    var OwnsLease:logic = false

    OnBegin<override>()<suspends>:void=
        # Acquire before subscribing or enumerating players. No duplicate may
        # touch the actor registry, and only the owner may release this lease.
        if:
            Lease := AEONFALLActorBootstrapOwners[GetSession()]
            Owner := Lease?
            Owner <> Self
        then:
            Print("AEONFALL: duplicate actor registry bootstrap rejected.")
            return
        if (set AEONFALLActorBootstrapOwners[GetSession()] = option{Self}):
            set OwnsLease = true
        if (not OwnsLease?):
            return
        set Running = true
        Added := GetPlayspace().PlayerAddedEvent().Subscribe(RegisterPlayer)
        Removed := GetPlayspace().PlayerRemovedEvent().Subscribe(UnregisterPlayer)
        set Subscriptions += array{Added, Removed}
        for (Player : GetPlayspace().GetPlayers()):
            RegisterPlayer(Player)

    OnEnd<override>():void=
        set Running = false
        # Cancel callbacks before allowing another device to acquire ownership.
        for (Subscription : Subscriptions):
            Subscription.Cancel()
        set Subscriptions = array{}
        if:
            OwnsLease?
            Lease := AEONFALLActorBootstrapOwners[GetSession()]
            Owner := Lease?
            Owner = Self
        then:
            if (set AEONFALLActorBootstrapOwners[GetSession()] = false) {}
        set OwnsLease = false

    RegisterPlayer(Player:player)<transacts>:void=
        if:
            Running?
            Player.IsActive[]
            RuntimeKey := GetAEONFALLActorRegistry().Register["PLAYER", Player]
        then:
            AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                EventType := "player.runtime_identity_ready",
                SourceId := RuntimeKey
            })
            Refreshed := GetAEONFALLHallOfAscendants().RefreshIfReady(Player)

    UnregisterPlayer(Player:player)<transacts>:void=
        if (not Running?):
            return
        if (RuntimeKey := GetAEONFALLActorRegistry().GetRuntimeKey[Player]):
            Removed := GetAEONFALLActorRegistry().Unregister(RuntimeKey)
            if (not Removed?):
                AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                    EventType := "player.runtime_identity_cleanup_failed",
                    SourceId := RuntimeKey
                })
