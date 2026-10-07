using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Central adapter-result router.
# Project-bound ability adapters report success/failure to AEONFALLRuntimeBus.
# This device resolves the canonical two-phase resource transaction.
aeonfall_ability_result_router_device := class(creative_device):

    OnBegin<override>()<suspends>:void=
        AEONFALLRuntimeBus.AdapterResult.Subscribe(OnAdapterResult)

    OnAdapterResult(Result:aeonfall_adapter_result)<transacts>:void=
        if:
            Definition := AEONFALLAbilityRegistry.Get[Result.AbilityId]
        then:
            Resolved := AEONFALLActivationCoordinator.ResolveAdapterResult(
                Definition,
                Result
            )

            if (not Resolved?):
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "ability.adapter_result_unresolved",
                        SourceId := Result.OwnerKey,
                        TargetId := Result.AbilityId,
                        ContextId := Result.RequestId
                    }
                )
