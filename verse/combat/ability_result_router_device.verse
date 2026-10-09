using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Central adapter-result router.
# Project-bound ability adapters report success/failure to AEONFALLRuntimeBus.
# This device resolves the canonical two-phase resource transaction.
aeonfall_ability_result_router_device := class(creative_device):

    var BusSubscription:?cancelable = false

    OnBegin<override>()<suspends>:void=
        Subscription := AEONFALLRuntimeBus.AdapterResult.Subscribe(OnAdapterResult)
        set BusSubscription = option{Subscription}

    OnEnd<override>():void=
        if (Subscription := BusSubscription?):
            Subscription.Cancel()
        set BusSubscription = false

    OnAdapterResult(Result:aeonfall_adapter_result)<transacts>:void=
        if:
            Definition := GetAEONFALLAbilityRegistry().Get[Result.AbilityId]
        then:
            Resolved := GetAEONFALLActivationCoordinator().ResolveAdapterResult(
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
