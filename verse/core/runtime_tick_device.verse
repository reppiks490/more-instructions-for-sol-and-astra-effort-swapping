using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# One low-frequency canonical runtime scheduler.
# Physical effects, movement, damage, VFX, and AI still live in adapters.
# This device advances only lightweight AEONFALL state.
aeonfall_runtime_tick_device := class(creative_device):

    @editable
    TickIntervalSeconds:float = 0.25

    var Running:logic = false

    OnEnd<override>():void=
        # Do not spawn cleanup coroutines from OnEnd. A resumed sleeper checks
        # this guard before touching session state or emitting another tick.
        set Running = false

    OnBegin<override>()<suspends>:void=
        set Running = true
        var PreviousTime:float = GetSimulationElapsedTime()
        loop:
            if (not Running?):
                break
            Interval:float =
                if (TickIntervalSeconds > 0.05):
                    TickIntervalSeconds
                else:
                    0.05

            Sleep(Interval)

            if (not Running?):
                break

            CurrentTime:float = GetSimulationElapsedTime()
            DeltaSeconds:float = CurrentTime - PreviousTime
            set PreviousTime = CurrentTime

            # Sleep specifies a minimum suspension, not the elapsed time.
            # Account for frame stalls without dropping elapsed simulation time.
            # Ignore non-advancing/reset clocks rather than extending timers.
            if (DeltaSeconds > 0.0):
                AdvanceRuntime(DeltaSeconds)

    AdvanceRuntime(DeltaSeconds:float):void=
        AEONFALLActivationCoordinator.TickPendingActivations(DeltaSeconds)
        AEONFALLAbilityRuntime.TickAll(DeltaSeconds)
        AEONFALLStatusRuntime.TickAll(DeltaSeconds)
        AEONFALLTargetingRuntime.TickAll(DeltaSeconds)
        AEONFALLPositionTargetingRuntime.TickAll(DeltaSeconds)
        AEONFALLSpawnRuntime.TickAll(DeltaSeconds)
        AEONFALLUnlockDeliveryService.TickAll(DeltaSeconds)

        AEONFALLRuntimeBus.Emit(
            aeonfall_runtime_event{
                EventType := "runtime.tick",
                Amount := 1
            }
        )
