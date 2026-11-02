using { /Verse.org/Simulation }

# Session-only owner-exclusive fusion. This is a mode of existing sovereign
# authority UNI-001, not a new collectible, class, persistent flag, or grant.
aeonfall_sovereign_fusion_mode := enum:
    Dormant
    Armor

aeonfall_sovereign_fusion_runtime := class:
    var Controller:?aeonfall_sovereign_fusion_device = false
    var Owner:?player = false
    var Mode:aeonfall_sovereign_fusion_mode = aeonfall_sovereign_fusion_mode.Dormant
    var Generation:int = 0
    var Deadline:float = 0.0
    var CooldownUntil:float = 0.0
    var Energy:int = 0
    var MaxEnergy:int = 0

    AcquireController(Device:aeonfall_sovereign_fusion_device)<transacts>:logic=
        if (Controller?):
            return false
        set Controller = option{Device}
        true

    OwnsController(Device:aeonfall_sovereign_fusion_device)<transacts>:logic=
        if (Current := Controller?, Current = Device):
            return true
        false

    # This resets transient state only. No second controller may inherit a
    # previous lease, no profile is written, and generations never reset.
    ReleaseController(Device:aeonfall_sovereign_fusion_device)<transacts>:void=
        if (Current := Controller?, Current = Device):
            set Mode = aeonfall_sovereign_fusion_mode.Dormant
            set Energy = 0
            set MaxEnergy = 0
            set Deadline = 0.0
            set Controller = false

    # Caller authority must be the same trusted, provisioned native device
    # already used by sovereign appearance and Unmaking. No display-name gate.
    Begin(
        Device:aeonfall_sovereign_fusion_device,
        Player:player,
        Authority:aeonfall_sovereign_authority_device,
        DurationSeconds:float,
        Capacity:int
    )<decides><transacts>:int=
        Current := Controller?
        Current = Device
        Player.IsActive[]
        Authorized := Authority.CanWield(Player)
        Authorized?
        Mode = aeonfall_sovereign_fusion_mode.Dormant
        Now := GetSimulationElapsedTime()
        Now >= CooldownUntil
        DurationSeconds >= 15.0
        DurationSeconds <= 180.0
        Capacity >= 30
        Capacity <= 120
        if (Bound := Owner?):
            Bound = Player
        else:
            set Owner = option{Player}
        set Generation += 1
        set Mode = aeonfall_sovereign_fusion_mode.Armor
        set Deadline = Now + DurationSeconds
        set Energy = Capacity
        set MaxEnergy = Capacity
        Generation

    IsCurrent(Player:player, Token:int)<transacts>:logic=
        if:
            Mode = aeonfall_sovereign_fusion_mode.Armor
            Current := Owner?
            Current = Player
            Player.IsActive[]
            Generation = Token
            GetSimulationElapsedTime() < Deadline
        then:
            return true
        false

    # Atomic, epoch-bound expenditure for the future bounded arsenal.
    # No timer or stale callback may withdraw from a replacement fusion.
    Spend(Device:aeonfall_sovereign_fusion_device, Player:player, Token:int, Cost:int)<decides><transacts>:int=
        Current := Controller?
        Current = Device
        IsCurrent(Player, Token)?
        Cost > 0
        Cost <= 25
        Energy >= Cost
        set Energy -= Cost
        Energy

    # Separation is allowed after revocation/disconnect: cleanup cannot
    # depend on successfully reauthorizing a player who just lost access.
    End(Device:aeonfall_sovereign_fusion_device, Token:int, CooldownSeconds:float)<transacts>:logic=
        if:
            Current := Controller?
            Current = Device
            Mode = aeonfall_sovereign_fusion_mode.Armor
            Generation = Token
            CooldownSeconds >= 30.0
            CooldownSeconds <= 300.0
        then:
            set Mode = aeonfall_sovereign_fusion_mode.Dormant
            set Deadline = 0.0
            set Energy = 0
            set MaxEnergy = 0
            set CooldownUntil = GetSimulationElapsedTime() + CooldownSeconds
            return true
        false

var AEONFALLSovereignFusionRuntimes:weak_map(session, aeonfall_sovereign_fusion_runtime) = map{}

GetAEONFALLSovereignFusionRuntime()<decides><transacts>:aeonfall_sovereign_fusion_runtime=
    if (Existing := AEONFALLSovereignFusionRuntimes[GetSession()]):
        Existing
    else:
        Created := aeonfall_sovereign_fusion_runtime{}
        set AEONFALLSovereignFusionRuntimes[GetSession()] = Created
        Created
