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
    # The native SpawnAt agent is not gameplay-ready until its own NPC
    # behavior explicitly acknowledges the same authorized binding.
    var BehaviorReady:logic = false
    # OnEnd is terminal for the acknowledged epoch. A late OnBegin poll
    # cannot re-acknowledge an NPC after its behavior has been withdrawn.
    var BehaviorTerminated:logic = false
    # A stop does not release an in-flight native SpawnAt. Never resummon
    # until the old async request actually returned an agent or false.
    var SpawnInFlight:logic = false
    var SpawnEpoch:int = 0
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
            not SpawnInFlight?
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
            set BehaviorReady = false
            set BehaviorTerminated = false
            set Active = true
            set Generation = Token
            set Sequence = 0
            set Pending = false
            set Epoch += 1
            set SpawnEpoch = Epoch
            set SpawnInFlight = true
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

    # SpawnAt is suspending: GetAgents may expose the newly created NPC
    # BEFORE SpawnAt returns it. This flag allows inventory observation
    # only during the current reserved request; it never grants ownership,
    # behavior readiness, movement, cues, or a second summon.
    SpawnPendingForCurrentEpoch()<transacts>:logic=
        if (Active?, SpawnInFlight?, SpawnEpoch = Epoch):
            return true
        false

    # A generation-addressable native SpawnAt return, never SpawnedEvent,
    # is the only candidate association. Clear the single in-flight lease on
    # return even if timeout, owner loss or teardown already invalidated it.
    CompleteSpawn(ExpectedEpoch:int, Spawned:?agent)<transacts>:logic=
        if (not SpawnInFlight? or SpawnEpoch <> ExpectedEpoch):
            return false
        set SpawnInFlight = false
        set SpawnEpoch = 0
        if (IsCurrentEpoch(ExpectedEpoch)?):
            if (Agent := Spawned?):
                return BindSpawn(Agent)
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
            set BehaviorReady = false
            return true
        false

    # Handshake from the NPC's own behavior after native GetAgent and
    # GetNavigatable succeeded. No input/attack is permitted before this.
    AcknowledgeBehavior(Agent:agent)<transacts>:logic=
        if (not BehaviorTerminated?, BoundNpc(Agent)?):
            set BehaviorReady = true
            return true
        false

    # A stopped npc_behavior must not leave a live but commandable NPC.
    # The epoch and exact agent both have to match; this is not a grant.
    BoundEpochFor(Agent:agent)<decides><transacts>:int=
        BoundNpc(Agent)?
        Epoch

    WithdrawBehavior(Agent:agent, ExpectedEpoch:int)<transacts>:logic=
        if:
            Active?
            Epoch = ExpectedEpoch
            Current := OwnedNpc?
            Current = Agent
        then:
            set BehaviorTerminated = true
            set BehaviorReady = false
            set Pending = false
            return true
        false

    # An acknowledged behavior can end before the 0.25s owner monitor
    # registers command inputs. Its terminal latch must be visible even
    # when no command HUD was ever activated.
    HasTerminatedBehavior()<transacts>:logic=
        if (Active?, BehaviorTerminated?):
            return true
        false

    IsReadyForCurrentNpc()<transacts>:logic=
        if (Npc := OwnedNpc?, IsBehaviorReady(Npc)?):
            return true
        false

    IsBehaviorReady(Agent:agent)<transacts>:logic=
        if (not BehaviorTerminated?, BehaviorReady?, BoundNpc(Agent)?):
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

    # Elimination callbacks must match this dedicated proxy agent. Never
    # use a shared spawner's unrelated NPC death to clear the owner session.
    IsOwnedNpc(Agent:agent)<transacts>:logic=
        if (Current := OwnedNpc?, Current = Agent):
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
            BehaviorReady?
            not BehaviorTerminated?
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
        BehaviorReady?
        not BehaviorTerminated?
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
            BehaviorReady?
            not BehaviorTerminated?
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
            set BehaviorReady = false
            set BehaviorTerminated = true
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
