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
        # Keep teardown synchronous. A sleeper checks this before touching
        # session services or emitting another runtime tick.
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

            # Sleep is a minimum suspension. Advance by actual simulation time
            # so stalls do not lengthen cooldowns, leases, expirations, trials,
            # deliveries, horde state, invasions, or transformation timers.
            if (DeltaSeconds > 0.0):
                AdvanceRuntime(DeltaSeconds)

    AdvanceRuntime(DeltaSeconds:float):void=
        # Deliver queued results before timeout cleanup. A second pump resolves
        # callback-generated results without waiting another scheduler turn.
        AEONFALLRuntimeBus.Pump()
        AEONFALLRuntimeBus.Pump()

        GetAEONFALLActivationCoordinator().TickPendingActivations(DeltaSeconds)
        GetAEONFALLAbilityRuntime().TickAll(DeltaSeconds)
        GetAEONFALLStatusRuntime().TickAll(DeltaSeconds)
        GetAEONFALLHordeRuntime().TickAll(DeltaSeconds)
        GetAEONFALLTargetingRuntime().TickAll(DeltaSeconds)
        GetAEONFALLPositionTargetingRuntime().TickAll(DeltaSeconds)
        GetAEONFALLSpawnRuntime().TickAll(DeltaSeconds)
        GetAEONFALLUnlockDeliveryService().TickAll(DeltaSeconds)
        GetAEONFALLInvasionRuntime().TickAll(DeltaSeconds)
        GetAEONFALLAscensionTrialRuntime().TickAll(DeltaSeconds)
        GetAEONFALLChoosingRuntime().TickAll(DeltaSeconds)
        GetAEONFALLAscendedFormRuntime().TickAll(DeltaSeconds)
        GetAEONFALLTranscendentRuntime().TickAll(DeltaSeconds)
        GetAEONFALLHallOfAscendants().TickAll(DeltaSeconds)

        # Dispatch after canonical state commits; callback-emitted events remain
        # queued for the next scheduler turn.
        AEONFALLRuntimeBus.Pump()

        AEONFALLRuntimeBus.Emit(
            aeonfall_runtime_event{
                EventType := "runtime.tick",
                Amount := 1
            }
        )
