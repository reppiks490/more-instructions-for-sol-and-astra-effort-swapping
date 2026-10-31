using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Disabled by default. These assertions exercise the actual Verse bus and have
# not run until this device compiles and executes in a UEFN Launch Session.
# The injected state keeps all test messages off the shared gameplay bus.
aeonfall_runtime_event_bus_test_device := class(creative_device):
    @editable
    Enabled:logic = false
    var Bus:?aeonfall_event_bus = false
    var Subscriptions:[]cancelable = array{}
    var Checks:int = 0
    var Failures:int = 0
    var Received:[]int = array{}
    var SecondReceived:int = 0
    var AbilityRequests:int = 0
    var AdapterResults:int = 0
    var UnlockRequests:int = 0
    var UnlockResults:int = 0
    var LastAbilityId:string = ""
    var LastUnlockId:string = ""
    var AwaitedAmount:int = 0

    Check(Label:string, Passed:logic):void=
        set Checks += 1
        if (not Passed?):
            set Failures += 1
            Print("BUS FAIL: {Label}")

    OnRuntime(Event:aeonfall_runtime_event):void=
        set Received += array{Event.Amount}
        if (Event.Amount = 7, LocalBus := Bus?):
            Check("callback enqueue admitted", LocalBus.TryEmit(aeonfall_runtime_event{Amount := 8}))
            # This call must not recursively dispatch a batch already running.
            LocalBus.Pump()

    OnSecondRuntime(Event:aeonfall_runtime_event):void=
        set SecondReceived += 1

    OnAbilityRequest(Request:aeonfall_ability_effect_request):void=
        set AbilityRequests += 1
        if (LocalBus := Bus?):
            Check("ability result enqueue admitted", LocalBus.TryReportAdapterResult(
                aeonfall_adapter_result{RequestId := Request.RequestId, Succeeded := true}
            ))

    OnAdapterResult(Result:aeonfall_adapter_result):void=
        set AdapterResults += 1
        set LastAbilityId = Result.RequestId

    OnUnlockRequest(Request:aeonfall_unlock_delivery_request):void=
        set UnlockRequests += 1
        if (LocalBus := Bus?):
            Check("unlock result enqueue admitted", LocalBus.TryReportUnlockDelivery(
                aeonfall_unlock_delivery_result{RequestId := Request.RequestId, Succeeded := true}
            ))

    OnUnlockResult(Result:aeonfall_unlock_delivery_result):void=
        set UnlockResults += 1
        set LastUnlockId = Result.RequestId

    AwaitOnce(LocalBus:aeonfall_event_bus)<suspends>:void=
        Event := LocalBus.RuntimeEvent.Await()
        set AwaitedAmount = Event.Amount

    OnBegin<override>()<suspends>:void=
        if (not Enabled?):
            return

        State := aeonfall_event_bus_state{QueueCapacity := 2}
        LocalBus := aeonfall_event_bus{
            RuntimeEvent := aeonfall_runtime_event_channel{StateOverride := option{State}},
            AbilityEffectRequested := aeonfall_ability_request_channel{StateOverride := option{State}},
            AdapterResult := aeonfall_adapter_result_channel{StateOverride := option{State}},
            UnlockDeliveryRequested := aeonfall_unlock_request_channel{StateOverride := option{State}},
            UnlockDeliveryResult := aeonfall_unlock_result_channel{StateOverride := option{State}}
        }
        set Bus = option{LocalBus}
        First := LocalBus.RuntimeEvent.Subscribe(OnRuntime)
        Second := LocalBus.RuntimeEvent.Subscribe(OnSecondRuntime)
        set Subscriptions = array{
            First, Second,
            LocalBus.AbilityEffectRequested.Subscribe(OnAbilityRequest),
            LocalBus.AdapterResult.Subscribe(OnAdapterResult),
            LocalBus.UnlockDeliveryRequested.Subscribe(OnUnlockRequest),
            LocalBus.UnlockDeliveryResult.Subscribe(OnUnlockResult)
        }

        Check("runtime admitted", LocalBus.TryEmit(aeonfall_runtime_event{Amount := 1}))
        Check("ability request admitted", LocalBus.TryRequestAbilityEffect(aeonfall_ability_effect_request{RequestId := "ability"}))
        Check("unlock request admitted", LocalBus.TryRequestUnlockDelivery(aeonfall_unlock_delivery_request{RequestId := "unlock"}))
        Check("delivery waits for pump", logic{Received.Length = 0, AbilityRequests = 0, UnlockRequests = 0})
        LocalBus.Pump()
        Check("all request channels delivered", logic{Received.Length = 1, AbilityRequests = 1, UnlockRequests = 1})
        Check("results wait for next pump", logic{AdapterResults = 0, UnlockResults = 0})
        LocalBus.Pump()
        Check("typed results delivered", logic{AdapterResults = 1, UnlockResults = 1, LastAbilityId = "ability", LastUnlockId = "unlock"})

        Check("reentrant input admitted", LocalBus.TryEmit(aeonfall_runtime_event{Amount := 7}))
        LocalBus.Pump()
        Check("same channel callback deferred", logic{Received.Length = 2, Received[1] = 7, SecondReceived = 2})
        LocalBus.Pump()
        Check("same channel callback retained", logic{Received.Length = 3, Received[2] = 8, SecondReceived = 3})

        spawn{AwaitOnce(LocalBus)}
        Check("await input admitted", LocalBus.TryEmit(aeonfall_runtime_event{Amount := 22}))
        LocalBus.Pump()
        Check("await compatibility", logic{AwaitedAmount = 22})

        Check("runtime capacity first", LocalBus.TryEmit(aeonfall_runtime_event{Amount := 101}))
        Check("runtime capacity second", LocalBus.TryEmit(aeonfall_runtime_event{Amount := 202}))
        RejectionQuery := logic{not LocalBus.TryEmit(aeonfall_runtime_event{Amount := 909})?}
        Check("rejection query succeeds", RejectionQuery)
        Check("rejected transaction telemetry rolls back", logic{State.RuntimeOverflow = 0})
        RuntimeAdmission := LocalBus.TryEmit(aeonfall_runtime_event{Amount := 303})
        Check("runtime capacity rejects excess", logic{not RuntimeAdmission?})
        Check("ability capacity first", LocalBus.TryRequestAbilityEffect(aeonfall_ability_effect_request{RequestId := "a1"}))
        Check("ability capacity second", LocalBus.TryRequestAbilityEffect(aeonfall_ability_effect_request{RequestId := "a2"}))
        AbilityAdmission := LocalBus.TryRequestAbilityEffect(aeonfall_ability_effect_request{RequestId := "a3"})
        Check("ability capacity rejects excess", logic{not AbilityAdmission?})
        Check("unlock capacity first", LocalBus.TryRequestUnlockDelivery(aeonfall_unlock_delivery_request{RequestId := "u1"}))
        Check("unlock capacity second", LocalBus.TryRequestUnlockDelivery(aeonfall_unlock_delivery_request{RequestId := "u2"}))
        UnlockAdmission := LocalBus.TryRequestUnlockDelivery(aeonfall_unlock_delivery_request{RequestId := "u3"})
        Check("unlock capacity rejects excess", logic{not UnlockAdmission?})
        LocalBus.Pump()
        Check("per channel FIFO", logic{Received[4] = 101, Received[5] = 202})
        AdapterAdmission := LocalBus.TryReportAdapterResult(aeonfall_adapter_result{RequestId := "extra"})
        Check("adapter result capacity rejects excess", logic{not AdapterAdmission?})
        UnlockResultAdmission := LocalBus.TryReportUnlockDelivery(aeonfall_unlock_delivery_result{RequestId := "extra"})
        Check("unlock result capacity rejects excess", logic{not UnlockResultAdmission?})
        Check("overflow counted", logic{LocalBus.OverflowCount() = 5})
        LocalBus.Pump()
        Check("accepted critical results retained", logic{AdapterResults = 3, UnlockResults = 3, LastAbilityId = "a2", LastUnlockId = "u2"})

        FailedAdmissionTransaction := logic{LocalBus.TryEmit(aeonfall_runtime_event{Amount := 707})?, 1 = 2}
        Check("admission transaction fails", logic{not FailedAdmissionTransaction?})
        LocalBus.Pump()
        Check("failed transaction rolls back admission", logic{Received.Length = 6, SecondReceived = 6})
        FailedCancellationTransaction := logic{First.Cancel(), 1 = 2}
        Check("cancellation transaction fails", logic{not FailedCancellationTransaction?})
        Check("rollback cancellation input admitted", LocalBus.TryEmit(aeonfall_runtime_event{Amount := 606}))
        LocalBus.Pump()
        Check("rolled back cancellation remains active", logic{Received.Length = 7, SecondReceived = 7})
        Check("drained capacity reusable", LocalBus.TryEmit(aeonfall_runtime_event{Amount := 404}))

        BeforeCancellation := Received.Length
        SecondBeforeCancellation := SecondReceived
        First.Cancel()
        First.Cancel()
        LocalBus.Pump()
        Check("cancel is idempotent", logic{Received.Length = BeforeCancellation})
        Check("other subscriber remains active", logic{SecondReceived = SecondBeforeCancellation + 1})
        for (Subscription : Subscriptions):
            Subscription.Cancel()
        Sleep(0.06)
        Check("post cancel input admitted", LocalBus.TryEmit(aeonfall_runtime_event{Amount := 505}))
        LocalBus.Pump()
        Check("idle cancellation suppresses callback", logic{Received.Length = BeforeCancellation, SecondReceived = SecondBeforeCancellation + 1})
        set Subscriptions = array{}
        set Bus = false
        Print("BUS TEST: {Checks} checks, {Failures} failures. Record this UEFN session result; static validation does not execute it.")

    OnEnd<override>():void=
        for (Subscription : Subscriptions):
            Subscription.Cancel()
        set Subscriptions = array{}
        set Bus = false
