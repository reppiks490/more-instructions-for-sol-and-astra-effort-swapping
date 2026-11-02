using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Fortnite.com/Game }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

FusionAwakened<localizes>:message = "SOVEREIGN ARMOR FUSION — crimson core online."
FusionDenied<localizes>:message = "Fusion denied: owner authority, cooldown, or active session gate."
FusionSeparated<localizes>:message = "SOVEREIGN SEPARATION — armor link disengaged."

# Step-two native presentation bridge. This controls the player's OWN camera
# and a bounded outline/glow powerup; it does NOT possess an NPC, attach a
# custom skeletal mesh, grant permanent items, or modify a player profile.
# Keep disabled until operator-only authority and unique editor devices bind.
aeonfall_sovereign_fusion_device := class(creative_device):
    @editable
    Enabled:logic = false
    @editable
    Authority:aeonfall_sovereign_authority_device = aeonfall_sovereign_authority_device{}
    @editable
    FuseInput:input_trigger_device = input_trigger_device{}
    @editable
    SeparateInput:input_trigger_device = input_trigger_device{}
    @editable
    ArmorGlow:visual_effect_powerup_device = visual_effect_powerup_device{}
    @editable
    ArmorCamera:gameplay_camera_orbit_device = gameplay_camera_orbit_device{}
    @editable
    FusionSequence:cinematic_sequence_device = cinematic_sequence_device{}
    @editable
    Feedback:hud_message_device = hud_message_device{}
    @editable
    DurationSeconds:float = 90.0
    @editable
    CooldownSeconds:float = 90.0
    @editable
    InitialEnergy:int = 100

    StopEvent:event() = event(){}
    var Running:logic = false
    var Runtime:?aeonfall_sovereign_fusion_runtime = false
    var Subscriptions:[]cancelable = array{}
    var VisualOwner:?player = false
    var VisualCharacter:?fort_character = false
    var Token:int = 0

    ValidSettings()<transacts>:logic=
        if:
            FuseInput <> SeparateInput
            DurationSeconds >= 15.0
            DurationSeconds <= 180.0
            CooldownSeconds >= 30.0
            CooldownSeconds <= 300.0
            InitialEnergy >= 30
            InitialEnergy <= 120
        then:
            return true
        false

    OnBegin<override>()<suspends>:void=
        if (not Enabled? or not ValidSettings()?):
            return
        if (Service := GetAEONFALLSovereignFusionRuntime[]):
            Acquired := Service.AcquireController(Self)
            if (not Acquired?):
                Print("AEONFALL fusion rejected duplicate controller.")
                return
            set Runtime = option{Service}
        else:
            return
        set Running = true
        set Subscriptions = array{
            FuseInput.PressedEvent.Subscribe(Fuse),
            SeparateInput.PressedEvent.Subscribe(Separate),
            GetPlayspace().PlayerRemovedEvent().Subscribe(PlayerLeft)
        }
        race:
            MaintenanceLoop()
            StopEvent.Await()

    Fuse(Agent:agent):void=
        if:
            Running?
            Player := player[Agent]
            Player.IsActive[]
            Character := Player.GetFortCharacter[]
            Character.IsActive[]
            Service := Runtime?
            not VisualOwner?
        then:
            if (Started := Service.Begin[Self, Player, Authority, DurationSeconds, InitialEnergy]):
                set Token = Started
                set VisualOwner = option{Player}
                set VisualCharacter = option{Character}
                # These are irreversible native presentation calls, made only
                # AFTER the authoritative, owner-only successful admission.
                ArmorGlow.Pickup(Player)
                ArmorCamera.AddTo(Player)
                # Must be configured for instigator-only playback in the editor.
                FusionSequence.Play(Player)
                Feedback.Show(Player, FusionAwakened, 3.0)
                return
        Feedback.Show(Agent, FusionDenied, 3.0)

    Separate(Agent:agent):void=
        if (Player := player[Agent], Owner := VisualOwner?, Owner = Player):
            FinishActive()

    PlayerLeft(Player:player):void=
        if (Owner := VisualOwner?, Owner = Player):
            FinishActive()

    FinishActive():void=
        if (Service := Runtime?):
            Stopped := Service.End(Self, Token, CooldownSeconds)
        ClearPhysical()
        set Token = 0

    ClearPhysical():void=
        if (Owner := VisualOwner?):
            # Separate on authority loss, death, disconnect, and timeout.
            # No other player's camera, aura or outfit is altered.
            FusionSequence.Stop(Owner)
            ArmorCamera.RemoveFrom(Owner)
            ArmorGlow.Clear(Owner)
        set VisualOwner = false
        set VisualCharacter = false

    MaintenanceLoop()<suspends>:void=
        loop:
            Sleep(1.0)
            if (not Running?):
                return
            if (Player := VisualOwner?, Service := Runtime?):
                if:
                    Granted := Authority.CanWield(Player)
                    Granted?
                    Service.IsCurrent(Player, Token)?
                    OriginalCharacter := VisualCharacter?
                    Character := Player.GetFortCharacter[]
                    Character = OriginalCharacter
                    Character.IsActive[]
                then:
                    # One energy per elapsed maintenance tick. Burst attacks
                    # must request additional atomic Spend with this epoch.
                    if (Remaining := Service.Spend[Self, Player, Token, 1]):
                        set Token = Token
                    else:
                        FinishActive()
                else:
                    FinishActive()

    OnEnd<override>():void=
        set Running = false
        StopEvent.Signal()
        for (Subscription : Subscriptions):
            Subscription.Cancel()
        set Subscriptions = array{}
        if (Service := Runtime?, Service.OwnsController(Self)?):
            FinishActive()
            Service.ReleaseController(Self)
        else:
            ClearPhysical()
        set Runtime = false
