using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Resolves project-bound physical-delivery results back into the session
# delivery coordinator. Durable unlock state was already committed beforehand.
aeonfall_unlock_delivery_router_device := class(creative_device):

    OnBegin<override>()<suspends>:void=
        AEONFALLRuntimeBus.UnlockDeliveryResult.Subscribe(OnResult)

    OnResult(Result:aeonfall_unlock_delivery_result)<transacts>:void=
        Resolved := AEONFALLUnlockDeliveryService.Resolve(Result)

        if (not Resolved?):
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "unlock.delivery_result_unresolved",
                    SourceId := Result.OwnerKey,
                    TargetId := Result.EntityId,
                    ContextId := Result.RequestId
                }
            )
