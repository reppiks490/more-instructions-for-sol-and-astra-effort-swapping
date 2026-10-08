using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Real Verse service assertions, disabled by default. All definitions, state,
# and queued commands are isolated from the gameplay registries and event bus.
# Compile and run this in UEFN before recording runtime evidence.
aeonfall_status_saturation_test_device := class(creative_device):
    @editable
    Enabled:logic = false
    var Checks:int = 0
    var Failures:int = 0
    var Commands:[]string = array{}
    var Subscription:?cancelable = false

    Check(Label:string, Passed:logic):void=
        set Checks += 1
        if (not Passed?):
            set Failures += 1
            Print("STATUS SATURATION FAIL: {Label}")

    OnCommand(Event:aeonfall_runtime_event):void=
        set Commands += array{Event.EventType}

    Fill(LocalBus:aeonfall_event_bus):void=
        Check("capacity filler admitted", LocalBus.TryEmit(aeonfall_runtime_event{EventType := "test.filler"}))

    OnBegin<override>()<suspends>:void=
        if (not Enabled?):
            return
        State := aeonfall_event_bus_state{QueueCapacity := 1}
        LocalBus := aeonfall_event_bus{
            RuntimeEvent := aeonfall_runtime_event_channel{StateOverride := option{State}},
            AbilityEffectRequested := aeonfall_ability_request_channel{StateOverride := option{State}},
            AdapterResult := aeonfall_adapter_result_channel{StateOverride := option{State}},
            UnlockDeliveryRequested := aeonfall_unlock_request_channel{StateOverride := option{State}},
            UnlockDeliveryResult := aeonfall_unlock_result_channel{StateOverride := option{State}}
        }
        LocalRegistry := aeonfall_status_registry{}
        Runtime := aeonfall_status_runtime{EventBus := LocalBus, StatusRegistry := LocalRegistry}
        Timed := aeonfall_status_definition{
            StatusId := "DEV-SAT-TIMED", BaseDurationSeconds := 0.1,
            StackRule := aeonfall_status_stack_rule.RefreshDuration
        }
        Persistent := aeonfall_status_definition{StatusId := "DEV-SAT-PERSISTENT"}
        if:
            set LocalRegistry.Definitions[Timed.StatusId] = Timed
            set LocalRegistry.Definitions[Persistent.StatusId] = Persistent
        then:
            Check("isolated definitions seeded", true)
        else:
            Check("isolated definitions seeded", false)
        Listener := LocalBus.RuntimeEvent.Subscribe(OnCommand)
        set Subscription = option{Listener}

        Fill(LocalBus)
        AppliedFull := Runtime.ApplyStatus("target", Timed, "original", 1)
        Check("full queue rejects application", logic{not AppliedFull?})
        Check("rejected application leaves no state", logic{not Runtime.HasStatus("target", Timed.StatusId)?})
        LocalBus.Pump()
        Check("application admitted after drain", Runtime.ApplyStatus("target", Timed, "original", 1))
        Check("application command queued", logic{State.PendingRuntimeEvents[0].EventType = "status.applied"})
        LocalBus.Pump()

        Fill(LocalBus)
        RefreshedFull := Runtime.ApplyStatus("target", Timed, "refresh", 9)
        Check("full queue rejects refresh", logic{not RefreshedFull?})
        Check("rejected refresh preserves instance", logic{Old := Runtime.GetStatuses("target")[0], Old.SourceId = "original", Old.Magnitude = 1, Old.RemainingSeconds = 0.1})
        RemovedFull := Runtime.RemoveStatus("target", Timed.StatusId)
        Check("full queue rejects removal", logic{not RemovedFull?})
        Check("rejected removal preserves instance", Runtime.HasStatus("target", Timed.StatusId))
        Runtime.Tick("target", 1.0)
        Check("single target expiry retries positive duration", logic{Old := Runtime.GetStatuses("target")[0], Old.RemainingSeconds > 0.0})
        LocalBus.Pump()
        Runtime.Tick("target", 1.0)
        Check("single target expiry commits after drain", logic{not Runtime.HasStatus("target", Timed.StatusId)?})
        Check("expiry command admitted", logic{State.PendingRuntimeEvents[0].EventType = "status.expired"})
        LocalBus.Pump()

        Check("timed fixture reapplies", Runtime.ApplyStatus("target", Timed, "original", 1))
        LocalBus.Pump()
        Check("valid refresh admitted", Runtime.ApplyStatus("target", Timed, "refreshed", 2))
        Check("refresh command queued", logic{State.PendingRuntimeEvents[0].EventType = "status.applied"})
        Check("valid refresh updates instance", logic{Instance := Runtime.GetStatuses("target")[0], Instance.SourceId = "refreshed", Instance.Magnitude = 2})
        LocalBus.Pump()
        Fill(LocalBus)
        Runtime.TickAll(1.0)
        Check("tick all expiry retries positive duration", logic{Old := Runtime.GetStatuses("target")[0], Old.RemainingSeconds > 0.0})
        LocalBus.Pump()
        Runtime.TickAll(1.0)
        Check("tick all expiry commits after drain", logic{not Runtime.HasStatus("target", Timed.StatusId)?})
        LocalBus.Pump()

        var BatchAdmitted:logic = false
        if (Runtime.ApplyBatch["batch", array{Timed.StatusId, Persistent.StatusId}, "batch-source", 5]):
            set BatchAdmitted = true
        Check("saturated batch rejected", logic{not BatchAdmitted?})
        Check("saturated batch restores all canonical state", logic{Runtime.GetStatuses("batch").Length = 0})
        Check("saturated batch restores queued commands", logic{State.PendingRuntimeEvents.Length = 0})

        Check("persistent fixture admitted", Runtime.ApplyStatus("persistent", Persistent, "original", 1))
        LocalBus.Pump()
        Runtime.TickAll(100.0)
        Check("zero duration remains persistent", logic{Instance := Runtime.GetStatuses("persistent")[0], Instance.RemainingSeconds = 0.0})
        Fill(LocalBus)
        Runtime.ClearTarget("persistent")
        Check("forced clear commits under saturation", logic{Runtime.GetStatuses("persistent").Length = 0})
        LocalBus.Pump()

        Check("removal fixture admitted", Runtime.ApplyStatus("remove", Timed, "original", 1))
        LocalBus.Pump()
        Check("removal admitted after drain", Runtime.RemoveStatus("remove", Timed.StatusId))
        Check("removal commits canonical state", logic{not Runtime.HasStatus("remove", Timed.StatusId)?})
        Check("removal command queued", logic{State.PendingRuntimeEvents[0].EventType = "status.removed"})
        LocalBus.Pump()
        Check("admitted commands reach callback", logic{Commands.Find["status.applied"], Commands.Find["status.expired"], Commands.Find["status.removed"]})
        Listener.Cancel()
        set Subscription = false
        Print("STATUS SATURATION TEST: {Checks} checks, {Failures} failures. Record the actual UEFN Launch Session result.")

    OnEnd<override>():void=
        if (Listener := Subscription?):
            Listener.Cancel()
        set Subscription = false
