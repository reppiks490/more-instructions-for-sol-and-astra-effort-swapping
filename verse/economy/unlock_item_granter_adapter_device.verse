using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Direct physical-delivery adapter for item-backed unlocks.
# Configure ItemGranter in UEFN with the item represented by EntityId.
aeonfall_unlock_item_granter_adapter_device := class(creative_device):

    @editable
    EntityId:string = ""

    @editable
    ItemGranter:item_granter_device = item_granter_device{}

    OnBegin<override>()<suspends>:void=
        AEONFALLRuntimeBus.UnlockDeliveryRequested.Subscribe(OnDeliveryRequested)

    OnDeliveryRequested(
        Request:aeonfall_unlock_delivery_request
    )<transacts>:void=
        if (Request.EntityId <> EntityId):
            return

        var Succeeded:logic = false
        var ResultCode:string = "owner_not_registered"

        if:
            OwnerAgent := AEONFALLActorRegistry.GetAgent[Request.OwnerKey]
        then:
            ItemGranter.GrantItem(OwnerAgent)
            set Succeeded = true
            set ResultCode = "item_grant_dispatched"

        AEONFALLRuntimeBus.ReportUnlockDelivery(
            aeonfall_unlock_delivery_result{
                RequestId := Request.RequestId,
                OwnerKey := Request.OwnerKey,
                EntityId := Request.EntityId,
                Succeeded := Succeeded,
                ResultCode := ResultCode
            }
        )
