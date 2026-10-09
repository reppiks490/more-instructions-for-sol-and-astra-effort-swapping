using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# One low-frequency canonical runtime scheduler.
# Physical effects, movement, damage, VFX, and AI still live in adapters.
# This device advances only lightweight AEONFALL state.
aeonfall_runtime_tick_device := class(creative_device):

    @editable
    TickIntervalSeconds:float = 0.25

    OnBegin<override>()<suspends>:void=
        loop:
            Interval:float =
                if (TickIntervalSeconds > 0.05):
                    TickIntervalSeconds
                else:
                    0.05

            Sleep(Interval)

            # Deliver queued effects/results before timeout cleanup. A second
            # pump resolves callback-generated results without waiting a turn.
            AEONFALLRuntimeBus.Pump()
            AEONFALLRuntimeBus.Pump()
            GetAEONFALLActivationCoordinator().TickPendingActivations(Interval)
            GetAEONFALLAbilityRuntime().TickAll(Interval)
            GetAEONFALLStatusRuntime().TickAll(Interval)
            GetAEONFALLHordeRuntime().TickAll(Interval)
            GetAEONFALLTargetingRuntime().TickAll(Interval)
            GetAEONFALLPositionTargetingRuntime().TickAll(Interval)
            GetAEONFALLSpawnRuntime().TickAll(Interval)
            GetAEONFALLUnlockDeliveryService().TickAll(Interval)
            GetAEONFALLInvasionRuntime().TickAll(Interval)
            GetAEONFALLAscensionTrialRuntime().TickAll(Interval)
            GetAEONFALLChoosingRuntime().TickAll(Interval)
            GetAEONFALLAscendedFormRuntime().TickAll(Interval)
            GetAEONFALLTranscendentRuntime().TickAll(Interval)
            GetAEONFALLHallOfAscendants().TickAll(Interval)
            # Dispatch callbacks after canonical state commits; events emitted
            # by callbacks remain queued for the next scheduler turn.
            AEONFALLRuntimeBus.Pump()

            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "runtime.tick",
                    Amount := 1
                }
            )
