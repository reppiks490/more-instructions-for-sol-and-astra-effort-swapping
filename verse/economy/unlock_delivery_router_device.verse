using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Resolves project-bound physical-delivery results back into the session
# delivery coordinator. Durable unlock state was already committed beforehand.
aeonfall_unlock_delivery_router_device := class(creative_device):

    var BusSubscription:?cancelable = false
    var LeaseOwned:logic = false

    OnBegin<override>()<suspends>:void=
        # Only one result router may resolve this session's queued results.
        Acquired := GetAEONFALLUnlockDeliveryRouterLease().Acquire(Self)
        if (not Acquired?):
            Print("AEONFALL unlock delivery result router rejected duplicate device.")
            return
        set LeaseOwned = true
        Subscription := AEONFALLRuntimeBus.UnlockDeliveryResult.Subscribe(OnResult)
        set BusSubscription = option{Subscription}

    OnEnd<override>():void=
        if (LeaseOwned?):
            set LeaseOwned = false
            if (Subscription := BusSubscription?):
                Subscription.Cancel()
            set BusSubscription = false
            Released := GetAEONFALLUnlockDeliveryRouterLease().Release(Self)

    OnResult(Result:aeonfall_unlock_delivery_result)<transacts>:void=
        Resolved := GetAEONFALLUnlockDeliveryService().Resolve(Result)

        if (not Resolved?):
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "unlock.delivery_result_unresolved",
                    SourceId := Result.OwnerKey,
                    TargetId := Result.EntityId,
                    ContextId := Result.RequestId
                }
            )

# Session-exclusive subscription ownership. A duplicate router must not
# resolve the same callback or emit a spurious unresolved-result event.
aeonfall_unlock_delivery_router_lease := class():
    var Owner:?aeonfall_unlock_delivery_router_device = false

    Acquire(Device:aeonfall_unlock_delivery_router_device)<transacts>:logic=
        if (Owner?):
            return false
        set Owner = option{Device}
        true

    Release(Device:aeonfall_unlock_delivery_router_device)<transacts>:logic=
        if (Current := Owner?, Current = Device):
            set Owner = false
            return true
        false

var AEONFALLUnlockDeliveryRouterLeaseSessions:weak_map(session, aeonfall_unlock_delivery_router_lease) = map{}

GetAEONFALLUnlockDeliveryRouterLease()<transacts>:aeonfall_unlock_delivery_router_lease=
    CurrentSession := GetSession()
    if (Existing := AEONFALLUnlockDeliveryRouterLeaseSessions[CurrentSession]):
        return Existing
    Created := aeonfall_unlock_delivery_router_lease{}
    if (set AEONFALLUnlockDeliveryRouterLeaseSessions[CurrentSession] = Created):
        return Created
    Err("AEONFALL could not retain unlock delivery result router lease in its session")
