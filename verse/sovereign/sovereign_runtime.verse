using { /Verse.org/Simulation }

# Session lifetime, with exactly one verified owner and one physical controller.
# No first-join grant, display-name comparison, team grant or public grant button.
aeonfall_sovereign_runtime := class:
    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}
    var Controller:?aeonfall_sovereign_controller_device = false
    var Owner:?player = false
    var Active:logic = false
    var Generation:int = 0
    var Deadline:float = 0.0
    var Participants:[player]aeonfall_sovereign_participant = map{}
    var Army:[agent]int = map{}
    var NextArmySlot:int = 0
    var MaxArmy:int = 64

    AcquireController(Device:aeonfall_sovereign_controller_device)<transacts>:logic=
        if (Controller?):
            return false
        set Controller = option{Device}
        true

    OwnsController(Device:aeonfall_sovereign_controller_device)<transacts>:logic=
        if (Current := Controller?, Current = Device):
            return true
        false

    ReleaseController(Device:aeonfall_sovereign_controller_device)<transacts>:void=
        if (Current := Controller?, Current = Device):
            set Active = false
            set Participants = map{}
            set Army = map{}
            set Controller = false

    # Called only after the injected authority verifies this exact player.
    # The first VERIFIED owner becomes immutable for this running session.
    BindVerifiedOwner(Player:player)<transacts>:logic=
        if (Existing := Owner?):
            if (Existing = Player):
                return true
            return false
        if (Player.IsActive[]):
            set Owner = option{Player}
            return true
        false

    IsOwner(Player:player)<transacts>:logic=
        if (Existing := Owner?, Existing = Player):
            return true
        false

    Begin(
        Device:aeonfall_sovereign_controller_device,
        Player:player,
        Duration:float,
        ArmyCap:int
    )<decides><transacts>:int=
        Current := Controller?
        Current = Device
        Existing := Owner?
        Existing = Player
        Player.IsActive[]
        not Active?
        Duration >= 30.0
        Duration <= 600.0
        ArmyCap > 0
        ArmyCap <= 96
        set Generation += 1
        set Active = true
        set Deadline = GetSimulationElapsedTime() + Duration
        set MaxArmy = ArmyCap
        set Army = map{}
        set NextArmySlot = 0
        set Participants = map{}
        Generation

    IsCurrent(Token:int)<transacts>:logic=
        if (Active?, Generation = Token):
            return true
        false

    Enroll(Player:player, Token:int)<transacts>:logic=
        if:
            Active?
            Generation = Token
            Player.IsActive[]
            OwnerPlayer := Owner?
            Player <> OwnerPlayer
        then:
            if (Participants[Player]):
                return true
            if (Participants.Length >= 512):
                return false
            if (set Participants[Player] = aeonfall_sovereign_participant{
                Generation := Token,
                JoinedAt := GetSimulationElapsedTime()
            }):
                return true
        false

    GetParticipant(Player:player, Token:int)<decides><transacts>:aeonfall_sovereign_participant=
        Active?
        Generation = Token
        State := Participants[Player]
        State.Generation = Token
        State

    Defy(Player:player, Token:int)<decides><transacts>:void=
        State := GetParticipant[Player, Token]
        State.State = aeonfall_sovereign_quest_state.Demanded
        set Participants[Player] = aeonfall_sovereign_participant{
            Generation := Token,
            State := aeonfall_sovereign_quest_state.Defiant,
            JoinedAt := State.JoinedAt,
            MayBeEliminated := true
        }

    # Two checked profile writes and the quest resolution share ONE rollback
    # scope. A failed owner save restores the payer's ledger and quest state.
    PayTribute(
        Payer:player,
        Token:int,
        MaterialId:string,
        Amount:int
    )<decides><transacts>:void=
        State := GetParticipant[Payer, Token]
        State.State = aeonfall_sovereign_quest_state.Demanded or
            State.State = aeonfall_sovereign_quest_state.Defiant
        Sovereign := Owner?
        Sovereign <> Payer
        Payer.IsActive[]
        Sovereign.IsActive[]
        Amount > 0
        Amount <= 10000
        MaterialId <> ""
        OldPayer := ProfileService.GetProfile[Payer]
        OldOwner := ProfileService.GetProfile[Sovereign]
        Held := OldPayer.MaterialLedger[MaterialId]
        Held >= Amount
        var OwnerAmount:int = 0
        if (Existing := OldOwner.MaterialLedger[MaterialId]):
            set OwnerAmount = Existing
        # Cap the aggregate against overflowing a persistent integer ledger.
        OwnerAmount >= 0
        OwnerAmount <= 1000000000 - Amount
        var PayerLedger:[string]int = OldPayer.MaterialLedger
        var OwnerLedger:[string]int = OldOwner.MaterialLedger
        set PayerLedger[MaterialId] = Held - Amount
        set OwnerLedger[MaterialId] = OwnerAmount + Amount
        NewPayer := aeonfall_player_profile:
            MakeAEONFALLPlayerProfile<constructor>(OldPayer)
            MaterialLedger := PayerLedger
        NewOwner := aeonfall_player_profile:
            MakeAEONFALLPlayerProfile<constructor>(OldOwner)
            MaterialLedger := OwnerLedger
        PayerSaved := ProfileService.TrySaveProfile(Payer, NewPayer)
        PayerSaved?
        OwnerSaved := ProfileService.TrySaveProfile(Sovereign, NewOwner)
        OwnerSaved?
        set Participants[Payer] = aeonfall_sovereign_participant{
            Generation := Token,
            State := aeonfall_sovereign_quest_state.Tributed,
            JoinedAt := State.JoinedAt
        }

    ClaimArmy(Agent:agent, Token:int)<decides><transacts>:int=
        Active?
        Generation = Token
        if (Existing := Army[Agent]):
            Existing
        else:
            Army.Length < MaxArmy
            Slot := NextArmySlot
            set NextArmySlot += 1
            set Army[Agent] = Slot
            Slot

    GetCommand(Agent:agent)<decides><transacts>:aeonfall_sovereign_command=
        Active?
        Sovereign := Owner?
        Sovereign.IsActive[]
        Slot := Army[Agent]
        aeonfall_sovereign_command{Owner := Sovereign, Generation := Generation, Slot := Slot}

    RemoveArmyMember(Agent:agent)<transacts>:void=
        var Kept:[agent]int = map{}
        for (Other -> Slot : Army, Other <> Agent):
            if (set Kept[Other] = Slot):
                set Kept = Kept
        set Army = Kept

    Resolve(Token:int, Stopped:logic, MinimumExposureSeconds:float)<decides><transacts>:void=
        Active?
        Generation = Token
        Now := GetSimulationElapsedTime()
        var Resolved:[player]aeonfall_sovereign_participant = map{}
        for (Player -> State : Participants):
            var NewState:aeonfall_sovereign_quest_state = State.State
            if (State.State <> aeonfall_sovereign_quest_state.Tributed):
                if (Stopped? or Now - State.JoinedAt < MinimumExposureSeconds):
                    set NewState = aeonfall_sovereign_quest_state.Released
                else:
                    set NewState = aeonfall_sovereign_quest_state.Unmade
            set Resolved[Player] = aeonfall_sovereign_participant{
                Generation := Token,
                State := NewState,
                JoinedAt := State.JoinedAt,
                MayBeEliminated := State.MayBeEliminated
            }
        set Participants = Resolved
        set Active = false
        set Army = map{}

var AEONFALLSovereignRuntimes:weak_map(session, aeonfall_sovereign_runtime) = map{}

# Failable allocation fails closed instead of returning an unretained singleton.
GetAEONFALLSovereignRuntime()<decides><transacts>:aeonfall_sovereign_runtime=
    if (Existing := AEONFALLSovereignRuntimes[GetSession()]):
        Existing
    else:
        Created := aeonfall_sovereign_runtime{}
        set AEONFALLSovereignRuntimes[GetSession()] = Created
        Created
