using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Resource/time budget ONLY. The canonical FUS-001/FUS-002 state machine and
# identity lease are owned by fusion_state_runtime.verse (Fusion Architect).
# Never create an alternative owner, form phase or native entitlement here.
aeonfall_sovereign_fusion_budget_runtime := class:
    var Controller:?creative_device = false
    var Token:int = 0
    var Active:logic = false
    var Remaining:int = 0
    var Deadline:float = 0.0
    var CooldownUntil:float = 0.0

    AcquireController(Device:creative_device)<transacts>:logic=
        if (Controller?):
            return false
        set Controller = option{Device}
        true

    OwnsController(Device:creative_device)<transacts>:logic=
        if (Current := Controller?, Current = Device):
            return true
        false

    CanBegin(Device:creative_device)<transacts>:logic=
        if:
            Current := Controller?
            Current = Device
            not Active?
            GetSimulationElapsedTime() >= CooldownUntil
        then:
            return true
        false

    # Called by the leased physical adapter ONLY AFTER the canonical
    # BeginActivation admission returns its new generation.
    Start(Device:creative_device, NewToken:int, DurationSeconds:float, Capacity:int)<transacts>:logic=
        if:
            CanBegin(Device)?
            NewToken > 0
            DurationSeconds >= 15.0
            DurationSeconds <= 180.0
            Capacity >= 30
            Capacity <= 120
        then:
            set Token = NewToken
            set Active = true
            set Remaining = Capacity
            set Deadline = GetSimulationElapsedTime() + DurationSeconds
            return true
        false

    # An external arsenal adapter may spend ONLY against the canonical
    # active and authorized fusion state, same owner, same generation.
    Spend(
        Device:creative_device,
        Player:player,
        NewToken:int,
        State:aeonfall_fusion_state_runtime,
        Cost:int
    )<decides><transacts>:int=
        Current := Controller?
        Current = Device
        Active?
        Token = NewToken
        GetSimulationElapsedTime() < Deadline
        Authorized := State.IsAuthorizedActive(Device, Player, NewToken)
        Authorized?
        Cost > 0
        Cost <= 25
        Remaining >= Cost
        set Remaining -= Cost
        Remaining

    IsExpired(Device:creative_device, NewToken:int)<transacts>:logic=
        if (Current := Controller?, Current = Device, Active?, Token = NewToken):
            if (GetSimulationElapsedTime() >= Deadline or Remaining <= 0):
                return true
        false

    Stop(Device:creative_device, NewToken:int, CooldownSeconds:float)<transacts>:logic=
        if:
            Current := Controller?
            Current = Device
            Active?
            Token = NewToken
            CooldownSeconds >= 30.0
            CooldownSeconds <= 300.0
        then:
            set Active = false
            set Remaining = 0
            set Deadline = 0.0
            set CooldownUntil = GetSimulationElapsedTime() + CooldownSeconds
            return true
        false

    ReleaseController(Device:creative_device)<transacts>:void=
        if (Current := Controller?, Current = Device):
            set Active = false
            set Remaining = 0
            set Deadline = 0.0
            # Keep session cooldown when editor controller is replaced.
            set Controller = false

var AEONFALLSovereignFusionBudgets:weak_map(session, aeonfall_sovereign_fusion_budget_runtime) = map{}

GetAEONFALLSovereignFusionBudget()<decides><transacts>:aeonfall_sovereign_fusion_budget_runtime=
    if (Existing := AEONFALLSovereignFusionBudgets[GetSession()]):
        Existing
    else:
        Created := aeonfall_sovereign_fusion_budget_runtime{}
        set AEONFALLSovereignFusionBudgets[GetSession()] = Created
        Created
