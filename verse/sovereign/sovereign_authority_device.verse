using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Exactly one authority device owns this session's provisioned reference.
var AEONFALLSovereignAuthorityLease:weak_map(session, ?aeonfall_sovereign_authority_device) = map{}

# This is a trusted provisioning boundary, not an Epic-account lookup API.
# Leave disabled until an operator has verified the owner and secured every
# registration path into OwnerReference. Never connect a public spawn/button.
aeonfall_sovereign_authority_device := class(creative_device):
    @editable
    Enabled:logic = false
    @editable
    OwnerReference:player_reference_device = player_reference_device{}

    var Owner<private>:?player = false
    var Running<private>:logic = false
    var Revoked<private>:logic = false
    StopEvent<private>:event() = event(){}

    AcquireLease<private>()<decides><transacts>:void=
        Session := GetSession()
        if (Existing := AEONFALLSovereignAuthorityLease[Session]?):
            Existing = Self
        else:
            set AEONFALLSovereignAuthorityLease[Session] = option{Self}

    OnBegin<override>()<suspends>:void=
        if (not Enabled?):
            return
        if (AcquireLease[]):
            set Running = true
        else:
            Print("AEONFALL sovereign authority rejected a duplicate authority device.")
            return
        race:
            ObserveReference()
            StopEvent.Await()

    ObserveReference<private>()<suspends>:void=
        loop:
            # GetAgent returns an option; it is not a decides function.
            Reference := OwnerReference.GetAgent()
            if (Bound := Owner?):
                if (Current := Reference?, Current = Bound, Bound.IsActive[]):
                    Sleep(0.1)
                else:
                    # Clearing/replacing/disconnecting permanently revokes this
                    # session's grant. Another player can never inherit it.
                    set Revoked = true
                    return
            else:
                if (Agent := Reference?, Candidate := player[Agent], Candidate.IsActive[]):
                    set Owner = option{Candidate}
                Sleep(0.1)

    CanWield<public>(Player:player)<transacts>:logic=
        if:
            Enabled?
            Running?
            not Revoked?
            Bound := Owner?
            Bound = Player
            Player.IsActive[]
            OwnerReference.IsReferenced[Player]
        then:
            return true
        false

    OnEnd<override>():void=
        set Running = false
        set Revoked = true
        set Owner = false
        StopEvent.Signal()
        Session := GetSession()
        if (Existing := AEONFALLSovereignAuthorityLease[Session]?, Existing = Self):
            if (set AEONFALLSovereignAuthorityLease[Session] = false) {}
