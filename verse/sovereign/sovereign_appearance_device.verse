using { /Fortnite.com/Characters }
using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Native disguise access shares the same verified identity as UNI-001.
# This lease prevents two appearance controllers from mutating aliased rigs.
var AEONFALLSovereignAppearanceLease:weak_map(session, ?aeonfall_sovereign_appearance_device) = map{}

aeonfall_sovereign_appearance_target := class:
    Player:player
    Character:fort_character

aeonfall_sovereign_appearance_device := class(creative_device):
    @editable
    Enabled:logic = false
    @editable
    Authority:aeonfall_sovereign_authority_device = aeonfall_sovereign_authority_device{}
    @editable
    Disguise:disguise_device = disguise_device{}

    var Running<private>:logic = false
    var NativeOwned<private>:logic = false
    var OwnedPlayer<private>:?player = false
    var OwnedCharacter<private>:?fort_character = false
    var Attempts<private>:int = 0
    var Confirmed<private>:logic = false
    StopEvent<private>:event() = event(){}

    AcquireLease<private>()<decides><transacts>:void=
        Session := GetSession()
        if (Existing := AEONFALLSovereignAppearanceLease[Session]?):
            Existing = Self
        else:
            set AEONFALLSovereignAppearanceLease[Session] = option{Self}

    SpawnConfigurationSafe<private>()<transacts>:logic=
        # An absent option is unknown, not evidence that automatic granting is off.
        if (Automatic := Disguise.ShouldApplyDisguiseOnPlayerSpawn?, not Automatic?):
            return true
        false

    OnBegin<override>()<suspends>:void=
        if (not Enabled?):
            return
        Safe := SpawnConfigurationSafe()
        # All configuration gates precede the lease and every native mutation.
        if (Safe?, not Disguise.IsEnabled[], AcquireLease[]):
            set NativeOwned = true
            Disguise.Enable()
            set Running = true
        else:
            Print("AEONFALL appearance rejected unsafe native settings or a duplicate controller.")
            return
        race:
            MaintenanceLoop()
            StopEvent.Await()

    FindAuthorizedTarget<private>()<transacts>:?aeonfall_sovereign_appearance_target=
        if (GetPlayspace().GetPlayers().Length <= 512):
            for (Player : GetPlayspace().GetPlayers()):
                if:
                    Player.IsActive[]
                    Character := Player.GetFortCharacter[]
                    Character.IsActive[]
                    Authorized := Authority.CanWield(Player)
                    Authorized?
                then:
                    return option{aeonfall_sovereign_appearance_target{Player := Player, Character := Character}}
        false

    Reconcile<private>(Target:aeonfall_sovereign_appearance_target):void=
        if (PreviousPlayer := OwnedPlayer?, PreviousPlayer <> Target.Player):
            ClearOwnedDisguise()
        if (Previous := OwnedCharacter?, Previous <> Target.Character):
            # Native character identity, rather than account/session identity,
            # provides a new bounded attempt budget after a genuine respawn.
            ClearOwnedDisguise()
        if (not OwnedCharacter?):
            set OwnedPlayer = option{Target.Player}
            set OwnedCharacter = option{Target.Character}
            set Attempts = 0
            set Confirmed = false
        if (Disguise.IsDisguiseApplied[Target.Player]):
            set Confirmed = true
            return
        set Confirmed = false
        if (Attempts >= 16):
            return
        set Attempts += 1
        # Native application returns void. Never infer successful replacement
        # from this call alone, and never place it in a failure transaction.
        Disguise.ApplyDisguise(Target.Player)
        if (Disguise.IsDisguiseApplied[Target.Player]):
            set Confirmed = true

    MaintenanceLoop<private>()<suspends>:void=
        loop:
            if (not Running?):
                return
            Safe := SpawnConfigurationSafe()
            if (not Safe?):
                set Running = false
                ClearOwnedDisguise()
                if (NativeOwned?):
                    Disguise.Disable()
                    set NativeOwned = false
                return
            Candidate := FindAuthorizedTarget()
            if (Target := Candidate?):
                Reconcile(Target)
            else:
                # Revoke, disconnect, elimination and pending provisioning all
                # clear this controller's tracked appearance without a grant.
                ClearOwnedDisguise()
            Sleep(1.0)

    ClearOwnedDisguise<private>():void=
        if (Player := OwnedPlayer?, Player.IsActive[]):
            # Disable alone leaves a native disguise applied. This only removes
            # our device's disguise and never alters an unrelated disguise.
            Disguise.RemoveDisguise(Player)
        set OwnedPlayer = false
        set OwnedCharacter = false
        set Attempts = 0
        set Confirmed = false

    IsAppearanceConfirmed<public>(Player:player)<transacts>:logic=
        if:
            Running?
            Confirmed?
            Current := OwnedPlayer?
            Current = Player
            Character := OwnedCharacter?
            Character.IsActive[]
            LiveCharacter := Player.GetFortCharacter[]
            LiveCharacter = Character
            Authorized := Authority.CanWield(Player)
            Authorized?
            Disguise.IsDisguiseApplied[Player]
        then:
            return true
        false

    OnEnd<override>():void=
        set Running = false
        StopEvent.Signal()
        ClearOwnedDisguise()
        if (NativeOwned?):
            Disguise.Disable()
            set NativeOwned = false
        Session := GetSession()
        if (Existing := AEONFALLSovereignAppearanceLease[Session]?, Existing = Self):
            if (set AEONFALLSovereignAppearanceLease[Session] = false) {}
