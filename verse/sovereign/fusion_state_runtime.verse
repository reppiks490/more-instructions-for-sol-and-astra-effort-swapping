using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Fusion Architect integration boundary. Source-only until a trusted native
# controller and the Avatar/Arsenal/Cinematics adapters are implemented.
# This service does not grant entitlement or create any physical effects.
aeonfall_fusion_phase := enum:
    Dormant
    Activating
    Active
    Separating

aeonfall_fusion_state_runtime := class:
    var Controller:?creative_device = false
    var Authority:?aeonfall_sovereign_authority_device = false
    # Once bound, the verified owner cannot change during this Verse session.
    var Owner:?player = false
    var Phase:aeonfall_fusion_phase = aeonfall_fusion_phase.Dormant
    var Generation:int = 0
    var FormId:string = ""

    AcquireController(Device:creative_device, VerifiedAuthority:aeonfall_sovereign_authority_device)<transacts>:logic=
        if (Controller?):
            return false
        set Controller = option{Device}
        set Authority = option{VerifiedAuthority}
        true

    OwnsController(Device:creative_device)<transacts>:logic=
        if (Current := Controller?, Current = Device):
            return true
        false

    # Only the session's leased controller can begin a fusion. The native
    # authority verifies the actual player; a supplied name/team/ID cannot.
    # FUS-002 (Titan) is intentionally disabled pending UEFN feasibility.
    BeginActivation(Device:creative_device, Player:player, RequestedFormId:string)<transacts>:?int=
        if (Phase <> aeonfall_fusion_phase.Dormant or RequestedFormId <> "FUS-001"):
            return false
        if:
            Current := Controller?
            Current = Device
            Gate := Authority?
            Player.IsActive[]
        then:
            Authorized := Gate.CanWield(Player)
            if (not Authorized?):
                return false
            if (Existing := Owner?, Existing <> Player):
                return false
            set Owner = option{Player}
            set Generation += 1
            set FormId = RequestedFormId
            set Phase = aeonfall_fusion_phase.Activating
            return option{Generation}
        false

    # Call only after the Avatar/Arsenal/Cinematics adapters acknowledge
    # successful application. Source existence is not native activation.
    ConfirmActivated(Device:creative_device, Player:player, Token:int)<transacts>:logic=
        if:
            Current := Controller?
            Current = Device
            Existing := Owner?
            Existing = Player
            Generation = Token
            Phase = aeonfall_fusion_phase.Activating
            Gate := Authority?
            Player.IsActive[]
        then:
            Authorized := Gate.CanWield(Player)
            if (Authorized?):
                set Phase = aeonfall_fusion_phase.Active
                return true
        false

    # All owner-driven operations revalidate native authority. Revocation is
    # handled by the controller's unconditional cleanup/Abort path instead.
    BeginSeparation(Device:creative_device, Player:player, Token:int)<transacts>:logic=
        if:
            Current := Controller?
            Current = Device
            Existing := Owner?
            Existing = Player
            Generation = Token
            Phase = aeonfall_fusion_phase.Active
            Gate := Authority?
            Player.IsActive[]
        then:
            Authorized := Gate.CanWield(Player)
            if (Authorized?):
                set Phase = aeonfall_fusion_phase.Separating
                return true
        false

    # The physical controller must finish its owned teardown first.
    CompleteSeparation(Device:creative_device, Token:int)<transacts>:logic=
        if:
            Current := Controller?
            Current = Device
            Generation = Token
            Phase = aeonfall_fusion_phase.Separating
        then:
            set Phase = aeonfall_fusion_phase.Dormant
            set FormId = ""
            set Generation += 1
            return true
        false

    IsAuthorizedActive(Device:creative_device, Player:player, Token:int)<transacts>:logic=
        if:
            Current := Controller?
            Current = Device
            Existing := Owner?
            Existing = Player
            Generation = Token
            Phase = aeonfall_fusion_phase.Active
            Gate := Authority?
            Player.IsActive[]
        then:
            Authorized := Gate.CanWield(Player)
            if (Authorized?):
                return true
        false

    # Abort must remain available after owner death, disconnect, or authority
    # revocation. The controller cleans up physical effects BEFORE calling it.
    Abort(Device:creative_device, Token:int)<transacts>:logic=
        if:
            Current := Controller?
            Current = Device
            Generation = Token
        then:
            set Phase = aeonfall_fusion_phase.Dormant
            set FormId = ""
            set Generation += 1
            return true
        false

    # Lease transfer is allowed only after an acknowledged Dormant phase.
    # A controller must first remove physical effects and CompleteSeparation
    # or Abort with the current generation. Otherwise releasing the lease
    # would let a replacement controller mask still-active presentation.
    # Never clear Owner: entitlement cannot transfer within this session.
    ReleaseController(Device:creative_device)<transacts>:logic=
        if (Phase <> aeonfall_fusion_phase.Dormant or FormId <> ""):
            return false
        if (Current := Controller?, Current = Device):
            set Phase = aeonfall_fusion_phase.Dormant
            set FormId = ""
            set Generation += 1
            set Controller = false
            set Authority = false
            return true
        false

var AEONFALLFusionStateSessions:weak_map(session, aeonfall_fusion_state_runtime) = map{}

GetAEONFALLFusionState()<transacts>:aeonfall_fusion_state_runtime=
    CurrentSession := GetSession()
    if (Existing := AEONFALLFusionStateSessions[CurrentSession]):
        return Existing
    Created := aeonfall_fusion_state_runtime{}
    if (set AEONFALLFusionStateSessions[CurrentSession] = Created):
        return Created
    Err("AEONFALL could not retain fusion state in its Verse session")
