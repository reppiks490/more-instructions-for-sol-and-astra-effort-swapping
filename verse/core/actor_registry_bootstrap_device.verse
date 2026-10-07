using { /Fortnite.com/Devices }
using { /Fortnite.com/Playspaces }
using { /Verse.org/Simulation }

# Registers human players into the same session identity system used by NPCs.
aeonfall_actor_registry_bootstrap_device := class(creative_device):

    OnBegin<override>()<suspends>:void=
        for (Player : GetPlayspace().GetPlayers()):
            RegisterPlayer(Player)

        GetPlayspace().PlayerAddedEvent().Subscribe(RegisterPlayer)
        GetPlayspace().PlayerRemovedEvent().Subscribe(UnregisterPlayer)

    RegisterPlayer(Player:player)<transacts>:void=
        if:
            RuntimeKey := AEONFALLActorRegistry.Register["PLAYER", Player]
        then:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "player.runtime_identity_ready",
                    SourceId := RuntimeKey
                }
            )

            Refreshed := AEONFALLHallOfAscendants.RefreshIfReady(Player)
            if (Refreshed?):
                Refreshed = true

    UnregisterPlayer(Player:player)<transacts>:void=
        if:
            RuntimeKey := AEONFALLActorRegistry.GetRuntimeKey[Player]
        then:
            Removed := AEONFALLActorRegistry.Unregister(RuntimeKey)
            if (not Removed?):
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "player.runtime_identity_cleanup_failed",
                        SourceId := RuntimeKey
                    }
                )
