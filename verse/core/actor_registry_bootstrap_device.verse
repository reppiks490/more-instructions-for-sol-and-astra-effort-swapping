using { /Fortnite.com/Devices }
using { /Fortnite.com/Playspaces }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Registers human players into the same session identity system used by NPCs.
aeonfall_actor_registry_bootstrap_device := class(creative_device):
    var Subscriptions:[]cancelable = array{}

    OnBegin<override>()<suspends>:void=
        Added := GetPlayspace().PlayerAddedEvent().Subscribe(RegisterPlayer)
        Removed := GetPlayspace().PlayerRemovedEvent().Subscribe(UnregisterPlayer)
        set Subscriptions += array{Added, Removed}
        for (Player : GetPlayspace().GetPlayers()):
            RegisterPlayer(Player)

    OnEnd<override>():void=
        for (Subscription : Subscriptions):
            Subscription.Cancel()
        set Subscriptions = array{}

    RegisterPlayer(Player:player)<transacts>:void=
        if:
            Player.IsActive[]
            RuntimeKey := GetAEONFALLActorRegistry().Register["PLAYER", Player]
        then:
            AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                EventType := "player.runtime_identity_ready",
                SourceId := RuntimeKey
            })
            Refreshed := GetAEONFALLHallOfAscendants().RefreshIfReady(Player)

    UnregisterPlayer(Player:player)<transacts>:void=
        if (RuntimeKey := GetAEONFALLActorRegistry().GetRuntimeKey[Player]):
            Removed := GetAEONFALLActorRegistry().Unregister(RuntimeKey)
            if (not Removed?):
                AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                    EventType := "player.runtime_identity_cleanup_failed",
                    SourceId := RuntimeKey
                })
