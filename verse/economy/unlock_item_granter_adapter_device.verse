using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Direct physical-delivery adapter for item-backed unlocks.
# Configure ItemGranter in UEFN with the item represented by EntityId.
aeonfall_unlock_item_granter_adapter_device := class(creative_device):

    @editable
    EntityId:string = ""

    @editable
    ItemGranter:item_granter_device = item_granter_device{}

    var BusSubscription:?cancelable = false

    OnBegin<override>()<suspends>:void=
        Subscription := AEONFALLRuntimeBus.UnlockDeliveryRequested.Subscribe(OnDeliveryRequested)
        set BusSubscription = option{Subscription}

    OnEnd<override>():void=
        if (Subscription := BusSubscription?):
            Subscription.Cancel()
        set BusSubscription = false

    OnDeliveryRequested(
        Request:aeonfall_unlock_delivery_request
    ):void=
        if (Request.EntityId <> EntityId):
            return

        Claimed := GetAEONFALLUnlockDeliveryService().ClaimDelivery(Request)
        if (not Claimed?):
            # Keep an inactive owner's request retryable; ignore stale or
            # already-dispatched copies without reporting a false completion.
            return

        var Succeeded:logic = false
        var ResultCode:string = "owner_not_registered"

        if:
            OwnerAgent := GetAEONFALLActorRegistry().GetAgent[Request.OwnerKey]
        then:
            ItemGranter.GrantItem(OwnerAgent)
            set Succeeded = true
            set ResultCode = "item_grant_dispatched"

        Result := aeonfall_unlock_delivery_result{
            RequestId := Request.RequestId,
            OwnerKey := Request.OwnerKey,
            EntityId := Request.EntityId,
            Succeeded := Succeeded,
            ResultCode := ResultCode
        }
        Admitted := AEONFALLRuntimeBus.TryReportUnlockDelivery(Result)
        if (not Admitted?):
            # The physical grant already happened; preserve its canonical
            # completion even if the asynchronous result queue is saturated.
            Resolved := GetAEONFALLUnlockDeliveryService().Resolve(Result)
            if (not Resolved?):
                AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                    EventType := "unlock.delivery_result_fallback_unresolved",
                    SourceId := Result.OwnerKey,
                    TargetId := Result.EntityId,
                    ContextId := Result.RequestId
                })
