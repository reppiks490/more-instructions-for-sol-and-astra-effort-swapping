using { /Verse.org/Verse }
using { /Verse.org/Simulation }

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

# Concrete typed queues avoid mutable members on a parametric class.
# This state is allocated lazily inside the current session, never as part of
# module-level facade initialization.
AEONFALLBusQueueCapacity:int = 1024

aeonfall_event_bus_state := class:
    QueueCapacity:int = AEONFALLBusQueueCapacity
    RuntimeEvent:event(aeonfall_runtime_event) = event(aeonfall_runtime_event){}
    var PendingRuntimeEvents:[]aeonfall_runtime_event = array{}
    var RuntimeOverflow:int = 0
    AbilityEffectRequested:event(aeonfall_ability_effect_request) = event(aeonfall_ability_effect_request){}
    var PendingAbilityRequests:[]aeonfall_ability_effect_request = array{}
    var AbilityRequestOverflow:int = 0
    AdapterResult:event(aeonfall_adapter_result) = event(aeonfall_adapter_result){}
    var PendingAdapterResults:[]aeonfall_adapter_result = array{}
    var AdapterResultOverflow:int = 0
    UnlockDeliveryRequested:event(aeonfall_unlock_delivery_request) = event(aeonfall_unlock_delivery_request){}
    var PendingUnlockRequests:[]aeonfall_unlock_delivery_request = array{}
    var UnlockRequestOverflow:int = 0
    UnlockDeliveryResult:event(aeonfall_unlock_delivery_result) = event(aeonfall_unlock_delivery_result){}
    var PendingUnlockResults:[]aeonfall_unlock_delivery_result = array{}
    var UnlockResultOverflow:int = 0
    var ReportedOverflow:int = 0
    var Dispatching:logic = false

    OverflowCount()<transacts>:int=
        RuntimeOverflow + AbilityRequestOverflow + AdapterResultOverflow + UnlockRequestOverflow + UnlockResultOverflow

var AEONFALLBusStates:weak_map(session, aeonfall_event_bus_state) = map{}

GetAEONFALLBusState()<transacts>:aeonfall_event_bus_state=
    if (State := AEONFALLBusStates[GetSession()]):
        return State
    State := aeonfall_event_bus_state{}
    if (set AEONFALLBusStates[GetSession()] = State):
        return State
    # A failed map write cannot retain a queue. A temporary zero-capacity state
    # reports admission failure instead of pretending to accept a message.
    aeonfall_event_bus_state{QueueCapacity := 0}

# Cancel only mutates transactional state; native event.Signal has no_rollback.
# The listener's race releases an idle subscription within 0.05 simulation
# seconds, and its delivery branch checks the flag before every callback.
aeonfall_event_subscription := class(cancelable):
    var Canceled:logic = false

    Cancel<override>()<transacts>:void=
        set Canceled = true

# All fields of the generic listener are immutable. This class is instantiated
# only when a device subscribes, and is not a stock subscribable/listenable.
aeonfall_event_listener(t:type) := class:
    Inner:event(t)
    Callback:type{_(:t):void}
    Subscription:aeonfall_event_subscription

    Run()<suspends>:void=
        race:
            WatchCancellation()
            Deliver()

    WatchCancellation()<suspends>:void=
        loop:
            Sleep(0.05)
            if (Subscription.Canceled?):
                return

    Deliver()<suspends>:void=
        loop:
            Payload := Inner.Await()
            if (Subscription.Canceled?):
                return
            Callback(Payload)

SubscribeAEONFALLEvent(Inner:event(t), Callback:type{_(:t):void} where t:type):cancelable=
    Subscription := aeonfall_event_subscription{}
    Listener := aeonfall_event_listener(t){Inner := Inner, Callback := Callback, Subscription := Subscription}
    # spawn enters Run and parks its Await before Subscribe returns.
    spawn{Listener.Run()}
    Subscription

aeonfall_runtime_event_channel := class:
    StateOverride:?aeonfall_event_bus_state = false

    State()<transacts>:aeonfall_event_bus_state=
        if (Override := StateOverride?):
            return Override
        GetAEONFALLBusState()

    Subscribe(Callback:type{_(:aeonfall_runtime_event):void}):cancelable=
        SubscribeAEONFALLEvent(State().RuntimeEvent, Callback)

    Await()<suspends>:aeonfall_runtime_event=
        State().RuntimeEvent.Await()

    Signal(Payload:aeonfall_runtime_event)<transacts>:void=
        Accepted := TrySignal(Payload)

    TrySignal(Payload:aeonfall_runtime_event)<transacts>:logic=
        Queue := State()
        if (Queue.PendingRuntimeEvents.Length < Queue.QueueCapacity):
            set Queue.PendingRuntimeEvents += array{Payload}
            return true
        set Queue.RuntimeOverflow += 1
        false

aeonfall_ability_request_channel := class:
    StateOverride:?aeonfall_event_bus_state = false

    State()<transacts>:aeonfall_event_bus_state=
        if (Override := StateOverride?):
            return Override
        GetAEONFALLBusState()

    Subscribe(Callback:type{_(:aeonfall_ability_effect_request):void}):cancelable=
        SubscribeAEONFALLEvent(State().AbilityEffectRequested, Callback)

    Await()<suspends>:aeonfall_ability_effect_request=
        State().AbilityEffectRequested.Await()

    Signal(Payload:aeonfall_ability_effect_request)<transacts>:void=
        Accepted := TrySignal(Payload)

    TrySignal(Payload:aeonfall_ability_effect_request)<transacts>:logic=
        Queue := State()
        if (Queue.PendingAbilityRequests.Length < Queue.QueueCapacity):
            set Queue.PendingAbilityRequests += array{Payload}
            return true
        set Queue.AbilityRequestOverflow += 1
        false

aeonfall_adapter_result_channel := class:
    StateOverride:?aeonfall_event_bus_state = false

    State()<transacts>:aeonfall_event_bus_state=
        if (Override := StateOverride?):
            return Override
        GetAEONFALLBusState()

    Subscribe(Callback:type{_(:aeonfall_adapter_result):void}):cancelable=
        SubscribeAEONFALLEvent(State().AdapterResult, Callback)

    Await()<suspends>:aeonfall_adapter_result=
        State().AdapterResult.Await()

    Signal(Payload:aeonfall_adapter_result)<transacts>:void=
        Accepted := TrySignal(Payload)

    TrySignal(Payload:aeonfall_adapter_result)<transacts>:logic=
        Queue := State()
        if (Queue.PendingAdapterResults.Length < Queue.QueueCapacity):
            set Queue.PendingAdapterResults += array{Payload}
            return true
        set Queue.AdapterResultOverflow += 1
        false

aeonfall_unlock_request_channel := class:
    StateOverride:?aeonfall_event_bus_state = false

    State()<transacts>:aeonfall_event_bus_state=
        if (Override := StateOverride?):
            return Override
        GetAEONFALLBusState()

    Subscribe(Callback:type{_(:aeonfall_unlock_delivery_request):void}):cancelable=
        SubscribeAEONFALLEvent(State().UnlockDeliveryRequested, Callback)

    Await()<suspends>:aeonfall_unlock_delivery_request=
        State().UnlockDeliveryRequested.Await()

    Signal(Payload:aeonfall_unlock_delivery_request)<transacts>:void=
        Accepted := TrySignal(Payload)

    TrySignal(Payload:aeonfall_unlock_delivery_request)<transacts>:logic=
        Queue := State()
        if (Queue.PendingUnlockRequests.Length < Queue.QueueCapacity):
            set Queue.PendingUnlockRequests += array{Payload}
            return true
        set Queue.UnlockRequestOverflow += 1
        false

aeonfall_unlock_result_channel := class:
    StateOverride:?aeonfall_event_bus_state = false

    State()<transacts>:aeonfall_event_bus_state=
        if (Override := StateOverride?):
            return Override
        GetAEONFALLBusState()

    Subscribe(Callback:type{_(:aeonfall_unlock_delivery_result):void}):cancelable=
        SubscribeAEONFALLEvent(State().UnlockDeliveryResult, Callback)

    Await()<suspends>:aeonfall_unlock_delivery_result=
        State().UnlockDeliveryResult.Await()

    Signal(Payload:aeonfall_unlock_delivery_result)<transacts>:void=
        Accepted := TrySignal(Payload)

    TrySignal(Payload:aeonfall_unlock_delivery_result)<transacts>:logic=
        Queue := State()
        if (Queue.PendingUnlockResults.Length < Queue.QueueCapacity):
            set Queue.PendingUnlockResults += array{Payload}
            return true
        set Queue.UnlockResultOverflow += 1
        false

# Immutable global facade; payloads remain typed throughout admission and
# delivery. Critical producers should use Try* and handle false explicitly.
aeonfall_event_bus := class:
    RuntimeEvent:aeonfall_runtime_event_channel = aeonfall_runtime_event_channel{}
    AbilityEffectRequested:aeonfall_ability_request_channel = aeonfall_ability_request_channel{}
    AdapterResult:aeonfall_adapter_result_channel = aeonfall_adapter_result_channel{}
    UnlockDeliveryRequested:aeonfall_unlock_request_channel = aeonfall_unlock_request_channel{}
    UnlockDeliveryResult:aeonfall_unlock_result_channel = aeonfall_unlock_result_channel{}

    Emit(Event:aeonfall_runtime_event)<transacts>:void=
        RuntimeEvent.Signal(Event)

    TryEmit(Event:aeonfall_runtime_event)<transacts>:logic=
        RuntimeEvent.TrySignal(Event)

    RequestAbilityEffect(Request:aeonfall_ability_effect_request)<transacts>:void=
        AbilityEffectRequested.Signal(Request)

    TryRequestAbilityEffect(Request:aeonfall_ability_effect_request)<transacts>:logic=
        AbilityEffectRequested.TrySignal(Request)

    ReportAdapterResult(Result:aeonfall_adapter_result)<transacts>:void=
        AdapterResult.Signal(Result)

    TryReportAdapterResult(Result:aeonfall_adapter_result)<transacts>:logic=
        AdapterResult.TrySignal(Result)

    RequestUnlockDelivery(Request:aeonfall_unlock_delivery_request)<transacts>:void=
        UnlockDeliveryRequested.Signal(Request)

    TryRequestUnlockDelivery(Request:aeonfall_unlock_delivery_request)<transacts>:logic=
        UnlockDeliveryRequested.TrySignal(Request)

    ReportUnlockDelivery(Result:aeonfall_unlock_delivery_result)<transacts>:void=
        UnlockDeliveryResult.Signal(Result)

    TryReportUnlockDelivery(Result:aeonfall_unlock_delivery_result)<transacts>:logic=
        UnlockDeliveryResult.TrySignal(Result)

    OverflowCount()<transacts>:int=
        RuntimeEvent.State().OverflowCount()

    # Call only from a no_rollback device boundary after gameplay mutations.
    # Snapshot and clear every queue before signaling. A callback can enqueue
    # further messages; they are retained for the NEXT Pump, including messages
    # on the same channel. Reentrant Pump calls are ignored.
    Pump():void=
        Queue := RuntimeEvent.State()
        if (Queue.Dispatching?):
            return
        set Queue.Dispatching = true
        PendingRuntimeEvents := Queue.PendingRuntimeEvents
        set Queue.PendingRuntimeEvents = array{}
        PendingAbilityRequests := Queue.PendingAbilityRequests
        set Queue.PendingAbilityRequests = array{}
        PendingAdapterResults := Queue.PendingAdapterResults
        set Queue.PendingAdapterResults = array{}
        PendingUnlockRequests := Queue.PendingUnlockRequests
        set Queue.PendingUnlockRequests = array{}
        PendingUnlockResults := Queue.PendingUnlockResults
        set Queue.PendingUnlockResults = array{}

        for (Payload : PendingRuntimeEvents):
            Queue.RuntimeEvent.Signal(Payload)
        for (Payload : PendingAbilityRequests):
            Queue.AbilityEffectRequested.Signal(Payload)
        for (Payload : PendingAdapterResults):
            Queue.AdapterResult.Signal(Payload)
        for (Payload : PendingUnlockRequests):
            Queue.UnlockDeliveryRequested.Signal(Payload)
        for (Payload : PendingUnlockResults):
            Queue.UnlockDeliveryResult.Signal(Payload)
        set Queue.Dispatching = false

        Overflow := Queue.OverflowCount()
        if (Overflow > Queue.ReportedOverflow):
            set Queue.ReportedOverflow = Overflow
            Print("AEONFALL BUS OVERFLOW: runtime={Queue.RuntimeOverflow}, ability_requests={Queue.AbilityRequestOverflow}, adapter_results={Queue.AdapterResultOverflow}, unlock_requests={Queue.UnlockRequestOverflow}, unlock_results={Queue.UnlockResultOverflow}")

# One immutable facade resolves transient routing state per current session.
# Persistent player state is not stored on this bus.
AEONFALLRuntimeBus:aeonfall_event_bus = aeonfall_event_bus{}
