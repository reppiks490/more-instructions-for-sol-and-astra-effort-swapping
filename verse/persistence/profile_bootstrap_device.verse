using { /Fortnite.com/Devices }
using { /Fortnite.com/Playspaces }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Initializes the single persistent root, retaining native subscription ownership.
aeonfall_profile_bootstrap_device := class(creative_device):
    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}
    var Subscriptions:[]cancelable = array{}

    OnBegin<override>()<suspends>:void=
        Added := GetPlayspace().PlayerAddedEvent().Subscribe(OnPlayerAdded)
        set Subscriptions += array{Added}
        for (Player : GetPlayspace().GetPlayers()):
            EnsureProfile(Player)

    OnEnd<override>():void=
        for (Subscription : Subscriptions):
            Subscription.Cancel()
        set Subscriptions = array{}

    OnPlayerAdded(Player:player)<transacts>:void=
        EnsureProfile(Player)

    EnsureProfile(Player:player)<transacts>:void=
        if (not Player.IsActive[]):
            return
        if (not AEONFALLPlayerProfiles[Player]):
            Saved := ProfileService.TrySaveProfile(Player, aeonfall_player_profile{})
            if (not Saved?):
                AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                    EventType := "profile.initialization_rejected",
                    SourceId := "player"
                })
                return
        Refreshed := GetAEONFALLHallOfAscendants().RefreshIfReady(Player)
