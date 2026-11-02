using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Transient command mailbox for ONE dedicated, independently simulated NPC.
# This is not a new fusion form or owner grant; FUS-002 remains disabled.
aeonfall_titan_proxy_move_command := class:
    Sequence:int = 0
    Destination:vector3 = vector3{X := 0.0, Y := 0.0, Z := 0.0}

aeonfall_titan_proxy_command_runtime := class:
    var Lease:?creative_device = false
    var FusionController:?aeonfall_sovereign_fusion_device = false
    var Owner:?player = false
    var OriginalCharacter:?fort_character = false
    var OwnedNpc:?agent = false
    var Active:logic = false
    var Generation:int = 0
    var Epoch:int = 0
    var Sequence:int = 0
    var Pending:?aeonfall_titan_proxy_move_command = false
    var NextMoveAt:float = 0.0
    var NextCueAt:float = 0.0

    Acquire(OwnerDevice:creative_device)<transacts>:logic=
        if (Lease?):
            return false
        set Lease = option{OwnerDevice}
        true

    Owns(OwnerDevice:creative_device)<transacts>:logic=
        if (Current := Lease?, Current = OwnerDevice):
            return true
        false

    # The live FUS-001 controller (not the proxy harness) owns canonical
    # authority. Never call BeginActivation for FUS-002 from this service.
    Begin(
        OwnerDevice:creative_device,
        Controller:aeonfall_sovereign_fusion_device,
        Player:player,
        Character:fort_character,
        Token:int
    )<transacts>:?int=
        if:
            Owns(OwnerDevice)?
            not Active?
            Token > 0
            Controller.Running?
            Controller.Token = Token
            CurrentOwner := Controller.VisualOwner?
            CurrentOwner = Player
            CurrentCharacter := Controller.VisualCharacter?
            CurrentCharacter = Character
            Player.IsActive[]
            LiveCharacter := Player.GetFortCharacter[]
            LiveCharacter = Character
            Character.IsActive[]
            State := GetAEONFALLFusionState()
            Authorized := State.IsAuthorizedActive(Controller, Player, Token)
            Authorized?
        then:
            set FusionController = option{Controller}
            set Owner = option{Player}
            set OriginalCharacter = option{Character}
            set OwnedNpc = false
            set Active = true
            set Generation = Token
            set Sequence = 0
            set Pending = false
            set Epoch += 1
            set NextMoveAt = 0.0
            set NextCueAt = 0.0
            return option{Epoch}
        false

    IsAuthorized()<transacts>:logic=
        if:
            Active?
            Controller := FusionController?
            CurrentOwner := Owner?
            Character := OriginalCharacter?
            CurrentOwner.IsActive[]
            Current := CurrentOwner.GetFortCharacter[]
            Current = Character
            Current.IsActive[]
            Controller.Running?
            Controller.Token = Generation
            PhysicalOwner := Controller.VisualOwner?
            PhysicalOwner = CurrentOwner
            PhysicalCharacter := Controller.VisualCharacter?
            PhysicalCharacter = Character
            State := GetAEONFALLFusionState()
            Authorized := State.IsAuthorizedActive(Controller, CurrentOwner, Generation)
            Authorized?
        then:
            return true
        false

    IsCurrentEpoch(Expected:int)<transacts>:logic=
        if (Active?, Epoch = Expected):
            return true
        false

    HasNpc()<transacts>:logic=
        if (OwnedNpc?):
            return true
        false

    BindSpawn(Agent:agent)<transacts>:logic=
        if:
            IsAuthorized()?
            not OwnedNpc?
            not player[Agent]
            Character := Agent.GetFortCharacter[]
            Character.IsActive[]
        then:
            set OwnedNpc = option{Agent}
            return true
        false

    BoundNpc(Agent:agent)<transacts>:logic=
        if:
            IsAuthorized()?
            Spawned := OwnedNpc?
            Spawned = Agent
            Character := Agent.GetFortCharacter[]
            Character.IsActive[]
        then:
            return true
        false

    # The NPC behavior is the ONLY native navigation owner. The creative
    # device writes commands, never races its own NavigateTo against behavior.
    RequestMove(Player:player, Destination:vector3)<transacts>:logic=
        if:
            IsAuthorized()?
            OwnerPlayer := Owner?
            OwnerPlayer = Player
            Npc := OwnedNpc?
            NpcChar := Npc.GetFortCharacter[]
            NpcChar.IsActive[]
            Source := OriginalCharacter?
            Range := Distance(Source.GetTransform().Translation, Destination)
            Range <= 1600.0
            Now := GetSimulationElapsedTime()
            Now >= NextMoveAt
        then:
            set Sequence += 1
            set Pending = option{aeonfall_titan_proxy_move_command{
                Sequence := Sequence, Destination := Destination
            }}
            set NextMoveAt = Now + 0.5
            return true
        false

    GetNewMove(Agent:agent, SeenSequence:int)<decides><transacts>:aeonfall_titan_proxy_move_command=
        BoundNpc(Agent)?
        Command := Pending?
        Command.Sequence > SeenSequence
        Command

    # Attack is a bounded instigator-only CUE, NOT damage or NPC possession.
    RequestAttackCue(Player:player)<transacts>:logic=
        if:
            IsAuthorized()?
            Actual := Owner?
            Actual = Player
            Owned := OwnedNpc?
            Monster := Owned.GetFortCharacter[]
            Monster.IsActive[]
            Controller := FusionController?
            State := GetAEONFALLFusionState()
            Budget := GetAEONFALLSovereignFusionBudget[]
            Now := GetSimulationElapsedTime()
            Now >= NextCueAt
            Budget.Spend[Controller, Player, Generation, State, 5]
        then:
            set NextCueAt = Now + 2.0
            return true
        false

    # Invalidate mailbox/epoch BEFORE the device despawns the owned NPC.
    # Teardown deliberately needs no current owner authorization.
    End(OwnerDevice:creative_device)<transacts>:logic=
        if (Owns(OwnerDevice)?):
            set Active = false
            set OwnedNpc = false
            set OriginalCharacter = false
            set Owner = false
            set FusionController = false
            set Generation = 0
            set Pending = false
            set Sequence = 0
            set Epoch += 1
            return true
        false

    Release(OwnerDevice:creative_device)<transacts>:void=
        if (Owns(OwnerDevice)?):
            Stopped := End(OwnerDevice)
            set Lease = false

var AEONFALLTitanProxyCommandsSessions:weak_map(session, aeonfall_titan_proxy_command_runtime) = map{}

GetAEONFALLTitanProxyCommands()<transacts>:aeonfall_titan_proxy_command_runtime=
    CurrentSession := GetSession()
    if (Existing := AEONFALLTitanProxyCommandsSessions[CurrentSession]):
        return Existing
    Created := aeonfall_titan_proxy_command_runtime{}
    if (set AEONFALLTitanProxyCommandsSessions[CurrentSession] = Created):
        return Created
    Err("Unable to retain AEONFALL Titan proxy mailbox")
