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

            AEONFALLActivationCoordinator.TickPendingActivations(Interval)
            AEONFALLAbilityRuntime.TickAll(Interval)
            AEONFALLStatusRuntime.TickAll(Interval)
            AEONFALLTargetingRuntime.TickAll(Interval)
            AEONFALLPositionTargetingRuntime.TickAll(Interval)
            AEONFALLSpawnRuntime.TickAll(Interval)
            AEONFALLUnlockDeliveryService.TickAll(Interval)
            AEONFALLInvasionRuntime.TickAll(Interval)
            AEONFALLAscensionTrialRuntime.TickAll(Interval)
            AEONFALLChoosingRuntime.TickAll(Interval)
            AEONFALLAscendedFormRuntime.TickAll(Interval)
            AEONFALLTranscendentRuntime.TickAll(Interval)
            AEONFALLHallOfAscendants.TickAll(Interval)

            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "runtime.tick",
                    Amount := 1
                }
            )
