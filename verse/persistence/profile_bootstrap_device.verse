using { /Fortnite.com/Devices }
using { /Fortnite.com/Playspaces }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Exactly one placed bootstrap initializes the existing persistent player
# root per session. Duplicate instances cannot race initial writes or refreshes.
var AEONFALLProfileBootstrapOwners:weak_map(session, ?aeonfall_profile_bootstrap_device) = map{}

# Initializes the single persistent root, retaining native subscription ownership.
aeonfall_profile_bootstrap_device := class(creative_device):
    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}
    var Subscriptions:[]cancelable = array{}
    var Running:logic = false
    var OwnsLease:logic = false

    OnBegin<override>()<suspends>:void=
        # Acquire before subscribing or touching persistent profile state.
        if:
            Lease := AEONFALLProfileBootstrapOwners[GetSession()]
            Owner := Lease?
            Owner <> Self
        then:
            Print("AEONFALL: duplicate profile bootstrap rejected.")
            return
        if (set AEONFALLProfileBootstrapOwners[GetSession()] = option{Self}):
            set OwnsLease = true
        if (not OwnsLease?):
            return
        set Running = true
        Added := GetPlayspace().PlayerAddedEvent().Subscribe(OnPlayerAdded)
        set Subscriptions += array{Added}
        for (Player : GetPlayspace().GetPlayers()):
            EnsureProfile(Player)

    OnEnd<override>():void=
        set Running = false
        # A canceled listener cannot act after its lease is transferred.
        for (Subscription : Subscriptions):
            Subscription.Cancel()
        set Subscriptions = array{}
        if:
            OwnsLease?
            Lease := AEONFALLProfileBootstrapOwners[GetSession()]
            Owner := Lease?
            Owner = Self
        then:
            if (set AEONFALLProfileBootstrapOwners[GetSession()] = false) {}
        set OwnsLease = false

    OnPlayerAdded(Player:player)<transacts>:void=
        if (Running?):
            EnsureProfile(Player)

    EnsureProfile(Player:player)<transacts>:void=
        if (not Running?):
            return
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
