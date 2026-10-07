using { /Fortnite.com/Devices }
using { /Fortnite.com/Playspaces }
using { /Verse.org/Simulation }

# Initializes AEONFALL persistent player records for players already present
# and for players who join later.
aeonfall_profile_bootstrap_device := class(creative_device):

    OnBegin<override>()<suspends>:void=
        for (Player : GetPlayspace().GetPlayers()):
            EnsureProfile(Player)

        GetPlayspace().PlayerAddedEvent().Subscribe(OnPlayerAdded)

    OnPlayerAdded(Player:player)<transacts>:void=
        EnsureProfile(Player)

    EnsureProfile(Player:player)<transacts>:void=
        if:
            not AEONFALLPlayerProfiles[Player]
            set AEONFALLPlayerProfiles[Player] = aeonfall_player_profile{}

        Refreshed := AEONFALLHallOfAscendants.RefreshIfReady(Player)
        if (Refreshed?):
            Refreshed = true
