using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Fortnite.com/Game }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }
using { /UnrealEngine.com/Temporary/SpatialMath }

ArsenalRejected<localizes>:message = "SOVEREIGN ARSENAL: denied, out of range, or insufficient energy."
ArsenalRend<localizes>:message = "BLOOD-IRON REAVER — validated monster strike."
ArsenalCollapse<localizes>:message = "VIOLET CATACLYSM — bounded cone strike."
ArsenalBulwark<localizes>:message = "DREADFRAME AEGIS — shield restored."

# Project-bound, disabled-by-default FUS-001 adapter. The Avatar controller
# still owns native player/armor/camera and the Architect owns authority.
# This device owns no persistent unlocks, spawned NPCs or shared global VFX.
aeonfall_sovereign_arsenal_device := class(creative_device):
    @editable
    Enabled:logic = false
    @editable
    Controller:aeonfall_sovereign_fusion_device = aeonfall_sovereign_fusion_device{}
    # Bind ONLY to Avatar's instigator-tagged AttackOutput in PR #48.
    @editable
    RendRequest:trigger_device = trigger_device{}
    @editable
    CollapseInput:input_trigger_device = input_trigger_device{}
    @editable
    BulwarkInput:input_trigger_device = input_trigger_device{}
    @editable
    Feedback:hud_message_device = hud_message_device{}

    var Running:logic = false
    var Runtime:?aeonfall_sovereign_arsenal_runtime = false
    var Subscriptions:[]cancelable = array{}

    ValidSettings()<transacts>:logic=
        if (CollapseInput <> BulwarkInput):
            return true
        false

    OnBegin<override>()<suspends>:void=
        if (not Enabled? or not ValidSettings()?):
            return
        Service := GetAEONFALLSovereignArsenalRuntime()
        Acquired := Service.AcquireController(Controller)
        if (not Acquired?):
            Print("AEONFALL arsenal rejected duplicate controller lease.")
            return
        set Runtime = option{Service}
        set Running = true
        set Subscriptions = array{
            RendRequest.TriggeredEvent.Subscribe(OnRend),
            CollapseInput.PressedEvent.Subscribe(OnCollapse),
            BulwarkInput.PressedEvent.Subscribe(OnBulwark)
        }

    # Every ability rechecks live native owner, exact original character,
    # Architect generation and active authority. Input registration is NOT
    # an owner credential, nor is a trigger-device payload.
    ValidOwner(Agent:agent)<decides><transacts>:player=
        Running?
        Controller.Running?
        Player := player[Agent]
        Player.IsActive[]
        Owner := Controller.VisualOwner?
        Owner = Player
        Original := Controller.VisualCharacter?
        Character := Player.GetFortCharacter[]
        Character = Original
        Character.IsActive[]
        Controller.Token > 0
        State := GetAEONFALLFusionState()
        Authorized := State.IsAuthorizedActive(Controller, Player, Controller.Token)
        Authorized?
        Player

    IsMonsterId(Id:string)<transacts>:logic=
        if (Id.Length >= 4, Id[0] = 'M', Id[1] = 'O', Id[2] = 'N', Id[3] = '-'):
            return true
        false

    IsHostileMonster(Key:string, Candidate:agent)<transacts>:logic=
        if (Binding := GetAEONFALLCompanionRuntime().GetBinding[Key]):
            if (Binding.Active?):
                return false
        if (Sovereign := GetAEONFALLSovereignRuntime[]):
            if (Sovereign.GetCommand[Candidate]):
                return false
        true

    # No raycast is claimed: cone/range are necessary, not sufficient,
    # for editor-certified cover/LOS counterplay. Keep Enabled=false until
    # the project verifies cover handling and native damage in Launch Session.
    EligibleTarget(
        Player:player, Key:string, MaxRange:float, MinimumCosine:float
    )<decides><transacts>:fort_character=
        Registry := GetAEONFALLActorRegistry()
        Registry.IsRegistered[Key]
        Candidate := Registry.GetAgent[Key]
        not player[Candidate]
        Canonical := Registry.GetCanonicalId[Key]
        IsMonsterId(Canonical)?
        Hostile := IsHostileMonster(Key, Candidate)
        Hostile?
        Target := Candidate.GetFortCharacter[]
        Target.IsActive[]
        Target.IsVulnerable[]
        Source := Player.GetFortCharacter[]
        Source.IsActive[]
        Origin := Source.GetViewLocation()
        TargetLocation := Target.GetTransform().Translation
        Delta := TargetLocation - Origin
        Range := Distance(Origin, TargetLocation)
        Range > 0.0
        Range <= MaxRange
        DotProduct(Delta, Source.GetViewRotation().GetForwardAxis()) >= Range * MinimumCosine
        Target

    HasSepulchralSynergy(Player:player)<transacts>:logic=
        if:
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Player]
            Equipped := GetAEONFALLClassRuntime().GetState[OwnerKey]
            Equipped.Active?
            Equipped.ClassId = "CLS-006"
        then:
            return true
        false

    OnRend(MaybeAgent:?agent):void=
        if:
            Agent := MaybeAgent?
            Player := ValidOwner[Agent]
            Service := Runtime?
            Budget := GetAEONFALLSovereignFusionBudget[]
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Player]
            Selection := GetAEONFALLTargetingRuntime().GetSelection[OwnerKey]
            Target := EligibleTarget[Player, Selection.TargetKey, 350.0, 0.70]
        then:
            State := GetAEONFALLFusionState()
            if (Service.TryRend[Controller, Player, Controller.Token, State, Budget, Selection.TargetKey]):
                # Explicit bounded native damage to one eligible MON- NPC.
                # No player/BOS-/companion/army target is admitted.
                Target.Damage(18.0)
                Feedback.Show(Player, ArsenalRend, 2.0)
                return
        if (Agent := MaybeAgent?):
            Feedback.Show(Agent, ArsenalRejected, 2.0)

    OnCollapse(Agent:agent):void=
        if:
            Player := ValidOwner[Agent]
            Service := Runtime?
            Budget := GetAEONFALLSovereignFusionBudget[]
        then:
            # Three nearest eligible MON- actors. Repeated bounded passes
            # avoid granting damage to arbitrary players or protected bosses.
            var ChosenKeys:[]string = array{}
            for (Pass := 1..3):
                var BestKey:string = ""
                var BestRange:float = 650.0
                for (Key -> Candidate : GetAEONFALLActorRegistry().AgentByKey):
                    if (ChosenKeys.Find[Key]):
                        set BestKey = BestKey
                    else if (Target := EligibleTarget[Player, Key, 650.0, 0.85]):
                        if (Source := Player.GetFortCharacter[]):
                            Range := Distance(Source.GetViewLocation(), Target.GetTransform().Translation)
                            if (Range < BestRange):
                                set BestKey = Key
                                set BestRange = Range
                if (BestKey <> ""):
                    set ChosenKeys += array{BestKey}
            if (ChosenKeys.Length > 0):
                State := GetAEONFALLFusionState()
                if (Service.TryCollapse[Controller, Player, Controller.Token, State, Budget]):
                    for (Key : ChosenKeys):
                        if (Target := EligibleTarget[Player, Key, 650.0, 0.85]):
                            var Amount:float = 10.0
                            if (HasSepulchralSynergy(Player)?, Service.HasMark(Controller.Token, Key)?):
                                set Amount = 14.0
                            Target.Damage(Amount)
                    Feedback.Show(Player, ArsenalCollapse, 2.0)
                    return
        Feedback.Show(Agent, ArsenalRejected, 2.0)

    OnBulwark(Agent:agent):void=
        if:
            Player := ValidOwner[Agent]
            Service := Runtime?
            Budget := GetAEONFALLSovereignFusionBudget[]
            Character := Player.GetFortCharacter[]
            Character.IsActive[]
        then:
            Current := Character.GetShield()
            Maximum := Character.GetMaxShield()
            if (Maximum > Current and Maximum <= 500.0):
                var Restore:float = 20.0
                if (Current + Restore > Maximum):
                    set Restore = Maximum - Current
                Allowance := Service.RemainingBulwark(Controller.Token)
                if (Restore > Allowance):
                    set Restore = Allowance
                if (Restore >= 1.0):
                    State := GetAEONFALLFusionState()
                    if (Service.TryBulwark[Controller, Player, Controller.Token, State, Budget, Restore]):
                        Character.SetShield(Current + Restore)
                        if (Character.GetShield() > Current):
                            Feedback.Show(Player, ArsenalBulwark, 2.0)
                            return
        Feedback.Show(Agent, ArsenalRejected, 2.0)

    OnEnd<override>():void=
        set Running = false
        for (Subscription : Subscriptions):
            Subscription.Cancel()
        set Subscriptions = array{}
        if (Service := Runtime?, Service.OwnsController(Controller)?):
            Service.ReleaseController(Controller)
        set Runtime = false
