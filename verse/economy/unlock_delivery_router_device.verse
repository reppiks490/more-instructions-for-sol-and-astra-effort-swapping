using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Resolves project-bound physical-delivery results back into the session
# delivery coordinator. Durable unlock state was already committed beforehand.
aeonfall_unlock_delivery_router_device := class(creative_device):

    var BusSubscription:?cancelable = false

    OnBegin<override>()<suspends>:void=
        Subscription := AEONFALLRuntimeBus.UnlockDeliveryResult.Subscribe(OnResult)
        set BusSubscription = option{Subscription}

    OnEnd<override>():void=
        if (Subscription := BusSubscription?):
            Subscription.Cancel()
        set BusSubscription = false

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
