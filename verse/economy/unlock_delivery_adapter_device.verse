using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# One project-bound physical-delivery binding for a canonical unlocked entity.
# The linked TriggerOutput performs the editor-specific grant/spawn/equip action.
aeonfall_unlock_delivery_adapter_device := class(creative_device):

    @editable
    EntityId:string = ""

    @editable
    TriggerOutput:trigger_device = trigger_device{}

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
            TriggerOutput.Trigger(OwnerAgent)
            set Succeeded = true
            set ResultCode = "trigger_dispatched"

        AEONFALLRuntimeBus.ReportUnlockDelivery(
            aeonfall_unlock_delivery_result{
                RequestId := Request.RequestId,
                OwnerKey := Request.OwnerKey,
                EntityId := Request.EntityId,
                Succeeded := Succeeded,
                ResultCode := ResultCode
            }
        )
