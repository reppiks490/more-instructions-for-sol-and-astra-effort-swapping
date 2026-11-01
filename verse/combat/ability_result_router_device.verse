using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Central adapter-result router.
# Project-bound ability adapters report success/failure to AEONFALLRuntimeBus.
# This device resolves the canonical two-phase resource transaction.
aeonfall_ability_result_router_device := class(creative_device):

    var BusSubscription:?cancelable = false
    var LeaseOwned:logic = false

    OnBegin<override>()<suspends>:void=
        # Only one result router may resolve this session's queued results.
        Acquired := GetAEONFALLAbilityResultRouterLease().Acquire(Self)
        if (not Acquired?):
            Print("AEONFALL ability result router rejected duplicate device.")
            return
        set LeaseOwned = true
        Subscription := AEONFALLRuntimeBus.AdapterResult.Subscribe(OnAdapterResult)
        set BusSubscription = option{Subscription}

    OnEnd<override>():void=
        if (LeaseOwned?):
            set LeaseOwned = false
            if (Subscription := BusSubscription?):
                Subscription.Cancel()
            set BusSubscription = false
            Released := GetAEONFALLAbilityResultRouterLease().Release(Self)

    OnAdapterResult(Result:aeonfall_adapter_result)<transacts>:void=
        if:
            Definition := GetAEONFALLAbilityRegistry().Get[Result.AbilityId]
        then:
            Resolved := GetAEONFALLActivationCoordinator().ResolveAdapterResult(
                Definition,
                Result
            )

            if (not Resolved?):
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "ability.adapter_result_unresolved",
                        SourceId := Result.OwnerKey,
                        TargetId := Result.AbilityId,
                        ContextId := Result.RequestId
                    }
                )

# Session-exclusive subscription ownership. A duplicate router must not
# resolve the same callback or emit a spurious unresolved-result event.
aeonfall_ability_result_router_lease := class():
    var Owner:?aeonfall_ability_result_router_device = false

    Acquire(Device:aeonfall_ability_result_router_device)<transacts>:logic=
        if (Owner?):
            return false
        set Owner = option{Device}
        true

    Release(Device:aeonfall_ability_result_router_device)<transacts>:logic=
        if (Current := Owner?, Current = Device):
            set Owner = false
            return true
        false

var AEONFALLAbilityResultRouterLeaseSessions:weak_map(session, aeonfall_ability_result_router_lease) = map{}

GetAEONFALLAbilityResultRouterLease()<transacts>:aeonfall_ability_result_router_lease=
    CurrentSession := GetSession()
    if (Existing := AEONFALLAbilityResultRouterLeaseSessions[CurrentSession]):
        return Existing
    Created := aeonfall_ability_result_router_lease{}
    if (set AEONFALLAbilityResultRouterLeaseSessions[CurrentSession] = Created):
        return Created
    Err("AEONFALL could not retain ability result router lease in its session")
