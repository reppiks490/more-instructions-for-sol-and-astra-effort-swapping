using { /Verse.org/Verse }

# Small typed event envelope used to keep gameplay services decoupled.
# Canonical IDs remain strings so runtime actors can be rebound without
# changing persistent data or authored catalog identity.
aeonfall_runtime_event := class:
    EventType:string = ""
    SourceId:string = ""
    TargetId:string = ""
    ContextId:string = ""
    Amount:int = 0
    Flag:logic = false

aeonfall_ability_effect_request := class:
    RequestId:string = ""
    OwnerKey:string = ""
    AbilityId:string = ""
    AdapterId:string = ""
    TargetKey:string = ""
    ContextId:string = ""
    Magnitude:int = 0

aeonfall_adapter_result := class:
    RequestId:string = ""
    OwnerKey:string = ""
    AbilityId:string = ""
    AdapterId:string = ""
    Succeeded:logic = false
    ResultCode:string = ""

aeonfall_unlock_delivery_request := class:
    RequestId:string = ""
    OwnerKey:string = ""
    EntityId:string = ""
    SourceId:string = ""

aeonfall_unlock_delivery_result := class:
    RequestId:string = ""
    OwnerKey:string = ""
    EntityId:string = ""
    Succeeded:logic = false
    ResultCode:string = ""

aeonfall_event_bus := class():

    RuntimeEvent:event(aeonfall_runtime_event) = event(aeonfall_runtime_event){}
    AbilityEffectRequested:event(aeonfall_ability_effect_request) = event(aeonfall_ability_effect_request){}
    AdapterResult:event(aeonfall_adapter_result) = event(aeonfall_adapter_result){}
    UnlockDeliveryRequested:event(aeonfall_unlock_delivery_request) = event(aeonfall_unlock_delivery_request){}
    UnlockDeliveryResult:event(aeonfall_unlock_delivery_result) = event(aeonfall_unlock_delivery_result){}

    Emit(Event:aeonfall_runtime_event):void=
        RuntimeEvent.Signal(Event)

    RequestAbilityEffect(Request:aeonfall_ability_effect_request):void=
        AbilityEffectRequested.Signal(Request)

    ReportAdapterResult(Result:aeonfall_adapter_result):void=
        AdapterResult.Signal(Result)

    RequestUnlockDelivery(Request:aeonfall_unlock_delivery_request):void=
        UnlockDeliveryRequested.Signal(Request)

    ReportUnlockDelivery(Result:aeonfall_unlock_delivery_result):void=
        UnlockDeliveryResult.Signal(Result)

# One shared session bus. Persistent state is NOT stored here; this only routes
# transient runtime signals between systems such as encounters, companions,
# status effects, abilities, shops, crafting, UI, and presentation.
AEONFALLRuntimeBus:aeonfall_event_bus = aeonfall_event_bus{}
