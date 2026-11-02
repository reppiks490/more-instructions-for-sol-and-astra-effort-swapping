using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Fortnite.com/Game }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

FusionAwakened<localizes>:message = "SOVEREIGN ARMOR FUSION — crimson core online."
FusionDenied<localizes>:message = "Fusion denied: owner authority, cooldown, or active session gate."
FusionSeparated<localizes>:message = "SOVEREIGN SEPARATION — armor link disengaged."

# Physical FUS-001 adapter of the Architect-owned canonical state machine.
# This is not native NPC possession or arbitrary imported player skin support.
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
    AttackInput:input_trigger_device = input_trigger_device{}
    @editable
    AttackOutput:trigger_device = trigger_device{}
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
    @editable
    AttackEnergyCost:int = 10
    @editable
    AttackCooldownSeconds:float = 1.5

    StopEvent:event() = event(){}
    var Running:logic = false
    var Runtime:?aeonfall_fusion_state_runtime = false
    var Budget:?aeonfall_sovereign_fusion_budget_runtime = false
    var Subscriptions:[]cancelable = array{}
    var VisualOwner:?player = false
    var VisualCharacter:?fort_character = false
    var Token:int = 0
    var LastAttackAt:float = -1000.0

    ValidSettings()<transacts>:logic=
        if:
            FuseInput <> SeparateInput
            FuseInput <> AttackInput
            SeparateInput <> AttackInput
            AttackEnergyCost >= 1
            AttackEnergyCost <= 25
            AttackCooldownSeconds >= 0.2
            AttackCooldownSeconds <= 10.0
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
        if:
            State := GetAEONFALLFusionState[]
            Resource := GetAEONFALLSovereignFusionBudget[]
        then:
            StateLease := State.AcquireController(Self, Authority)
            if (not StateLease?):
                Print("AEONFALL fusion rejected duplicate canonical controller.")
                return
            BudgetLease := Resource.AcquireController(Self)
            if (not BudgetLease?):
                State.ReleaseController(Self)
                Print("AEONFALL fusion rejected duplicate resource controller.")
                return
            set Runtime = option{State}
            set Budget = option{Resource}
        else:
            return
        set Running = true
        set Subscriptions = array{
            FuseInput.PressedEvent.Subscribe(Fuse),
            SeparateInput.PressedEvent.Subscribe(Separate),
            AttackInput.PressedEvent.Subscribe(Attack),
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
            State := Runtime?
            Resource := Budget?
            not VisualOwner?
            Free := Resource.CanBegin(Self)
            Free?
        then:
            NewToken := State.BeginActivation(Self, Player, "FUS-001")
            if (Started := NewToken?):
                Reserved := Resource.Start(Self, Started, DurationSeconds, InitialEnergy)
                if (Reserved?):
                    set Token = Started
                    set VisualOwner = option{Player}
                    set VisualCharacter = option{Character}
                    # Native presentation is requested only AFTER authentic
                    # FUS-001 admission, never from an arbitrary input event.
                    ArmorGlow.Pickup(Player)
                    ArmorCamera.AddTo(Player)
                    FusionSequence.Play(Player)
                    # A same-type native effect is the most observable signal
                    # currently exposed; dedicated editor bindings are required.
                    if (ArmorGlow.HasEffect[Player]):
                        Confirmed := State.ConfirmActivated(Self, Player, Started)
                        if (Confirmed?):
                            Feedback.Show(Player, FusionAwakened, 3.0)
                            return
                    # A failed physical acknowledgement aborts the canonical
                    # activation after removing any partial presentation.
                    FinishActive()
                else:
                    Aborted := State.Abort(Self, Started)
        Feedback.Show(Agent, FusionDenied, 3.0)

    # A native player retains normal Fortnite movement and the owned orbit
    # camera. This attack bridge requests an instigator-scoped device graph;
    # it does NOT attest a hit, damage, animation or replicated target state.
    Attack(Agent:agent):void=
        if:
            Running?
            Player := player[Agent]
            Player.IsActive[]
            Owner := VisualOwner?
            Owner = Player
            OriginalCharacter := VisualCharacter?
            Character := Player.GetFortCharacter[]
            Character = OriginalCharacter
            Character.IsActive[]
            State := Runtime?
            Resource := Budget?
            Authorized := State.IsAuthorizedActive(Self, Player, Token)
            Authorized?
            Now := GetSimulationElapsedTime()
            Now >= LastAttackAt + AttackCooldownSeconds
            Resource.Spend[Self, Player, Token, State, AttackEnergyCost]
        then:
            # Charge and cooldown are server-side, bound to the canonical
            # generation and owner. Physical output is editor-owned.
            set LastAttackAt = Now
            AttackOutput.Trigger(Player)

    Separate(Agent:agent):void=
        if (Player := player[Agent], Owner := VisualOwner?, Owner = Player):
            FinishActive()

    PlayerLeft(Player:player):void=
        if (Owner := VisualOwner?, Owner = Player):
            FinishActive()

    FinishActive():void=
        # No physical cleanup depends on current authority. This must run
        # before CompleteSeparation/Abort as required by the architect state.
        LocalToken := Token
        Owner := VisualOwner
        ClearPhysical()
        if (State := Runtime?, Player := Owner?):
            Began := State.BeginSeparation(Self, Player, LocalToken)
            if (Began?):
                Complete := State.CompleteSeparation(Self, LocalToken)
            else:
                Aborted := State.Abort(Self, LocalToken)
        else if (State := Runtime?):
            Aborted := State.Abort(Self, LocalToken)
        if (Resource := Budget?):
            Stopped := Resource.Stop(Self, LocalToken, CooldownSeconds)
        set Token = 0
        set LastAttackAt = -1000.0

    ClearPhysical():void=
        if (Owner := VisualOwner?):
            # Only the owner's specifically bound presentation rig is changed.
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
            if (Player := VisualOwner?, State := Runtime?, Resource := Budget?):
                if:
                    Authorized := State.IsAuthorizedActive(Self, Player, Token)
                    Authorized?
                    OriginalCharacter := VisualCharacter?
                    Character := Player.GetFortCharacter[]
                    Character = OriginalCharacter
                    Character.IsActive[]
                    not Resource.IsExpired(Self, Token)?
                then:
                    # One energy per second, plus bounded ability expenditures
                    # admitted through the same authoritative resource budget.
                    if (Remaining := Resource.Spend[Self, Player, Token, State, 1]):
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
        FinishActive()
        if (State := Runtime?, State.OwnsController(Self)?):
            Released := State.ReleaseController(Self)
        if (Resource := Budget?, Resource.OwnsController(Self)?):
            Resource.ReleaseController(Self)
        set Runtime = false
        set Budget = false
