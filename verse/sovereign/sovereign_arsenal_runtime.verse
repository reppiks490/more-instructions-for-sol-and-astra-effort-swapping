using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Arsenal-owned session lease, per-ability cooldowns and bounded combo/shield
# state. Canonical owner/form authority remains in fusion_state_runtime.verse;
# energy remains in sovereign_fusion_runtime.verse. No persistence is written.
aeonfall_sovereign_arsenal_runtime := class:
    var Controller:?creative_device = false
    var LastRendAt:float = -1000.0
    var LastCollapseAt:float = -1000.0
    var LastBulwarkAt:float = -1000.0
    var MarkTargetKey:string = ""
    var MarkToken:int = 0
    var MarkUntil:float = 0.0
    var ShieldToken:int = 0
    var ShieldGranted:float = 0.0

    AcquireController(Device:creative_device)<transacts>:logic=
        if (Controller?):
            return false
        set Controller = option{Device}
        true

    OwnsController(Device:creative_device)<transacts>:logic=
        if (Current := Controller?, Current = Device):
            return true
        false

    # The upstream Avatar AttackOutput already charges 10 energy; this
    # independently charges 5 and enforces a second server-side cooldown.
    # A spoofed Trigger(Player) can never produce free damage.
    TryRend(
        Device:creative_device, Player:player, Token:int,
        State:aeonfall_fusion_state_runtime,
        Budget:aeonfall_sovereign_fusion_budget_runtime,
        TargetKey:string
    )<decides><transacts>:void=
        Current := Controller?
        Current = Device
        Token > 0
        TargetKey <> ""
        Now := GetSimulationElapsedTime()
        Now >= LastRendAt + 2.0
        # Only Avatar may mint a paid receipt. A bare TriggeredEvent
        # carrying the owner is not proof of the upstream energy debit.
        # Both consumption and the secondary debit roll back together.
        State.ConsumeAttackReceipt[Device, Player, Token]
        Budget.Spend[Device, Player, Token, State, 5]
        set LastRendAt = Now
        set MarkTargetKey = TargetKey
        set MarkToken = Token
        set MarkUntil = Now + 4.0

    TryCollapse(
        Device:creative_device, Player:player, Token:int,
        State:aeonfall_fusion_state_runtime,
        Budget:aeonfall_sovereign_fusion_budget_runtime
    )<decides><transacts>:void=
        Current := Controller?
        Current = Device
        Token > 0
        Now := GetSimulationElapsedTime()
        Now >= LastCollapseAt + 8.0
        Budget.Spend[Device, Player, Token, State, 20]
        set LastCollapseAt = Now

    HasMark(Token:int, TargetKey:string)<transacts>:logic=
        if:
            Token > 0
            MarkToken = Token
            MarkTargetKey = TargetKey
            GetSimulationElapsedTime() < MarkUntil
        then:
            return true
        false

    RemainingBulwark(Token:int)<transacts>:float=
        if (ShieldToken = Token):
            return 40.0 - ShieldGranted
        40.0

    TryBulwark(
        Device:creative_device, Player:player, Token:int,
        State:aeonfall_fusion_state_runtime,
        Budget:aeonfall_sovereign_fusion_budget_runtime,
        Amount:float
    )<decides><transacts>:void=
        Current := Controller?
        Current = Device
        Token > 0
        Amount >= 1.0
        Amount <= 20.0
        Now := GetSimulationElapsedTime()
        Now >= LastBulwarkAt + 18.0
        var PreviouslyGranted:float = 0.0
        if (ShieldToken = Token):
            set PreviouslyGranted = ShieldGranted
        PreviouslyGranted + Amount <= 40.0
        Budget.Spend[Device, Player, Token, State, 15]
        set ShieldToken = Token
        set ShieldGranted = PreviouslyGranted + Amount
        set LastBulwarkAt = Now

    ReleaseController(Device:creative_device)<transacts>:void=
        if (Current := Controller?, Current = Device):
            # Cooldowns survive controller replacement in this session.
            set Controller = false
            set MarkTargetKey = ""
            set MarkToken = 0
            set MarkUntil = 0.0

var AEONFALLSovereignArsenalRuntimeSessions:weak_map(session, aeonfall_sovereign_arsenal_runtime) = map{}

GetAEONFALLSovereignArsenalRuntime()<transacts>:aeonfall_sovereign_arsenal_runtime=
    CurrentSession := GetSession()
    if (Existing := AEONFALLSovereignArsenalRuntimeSessions[CurrentSession]):
        return Existing
    Created := aeonfall_sovereign_arsenal_runtime{}
    if (set AEONFALLSovereignArsenalRuntimeSessions[CurrentSession] = Created):
        return Created
    Err("AEONFALL could not retain arsenal state in its Verse session")
