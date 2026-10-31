# Physical adapter effects execute in a listener task after the producer's
# transaction commits. Preserve their canonical resource resolution even when
# the result queue is saturated; a successful physical effect must not become
# a resource-release timeout merely because result admission was rejected.
aeonfall_adapter_result_delivery_service := class:
    Report(Result:aeonfall_adapter_result)<transacts>:void=
        Admitted := AEONFALLRuntimeBus.TryReportAdapterResult(Result)
        if (Admitted?):
            return

        if (Definition := GetAEONFALLAbilityRegistry().Get[Result.AbilityId]):
            Resolved := GetAEONFALLActivationCoordinator().ResolveAdapterResult(Definition, Result)
            if (Resolved?):
                return

        AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
            EventType := "ability.adapter_result_fallback_unresolved",
            SourceId := Result.OwnerKey,
            TargetId := Result.AbilityId,
            ContextId := Result.RequestId
        })

AEONFALLAdapterResultDelivery:aeonfall_adapter_result_delivery_service = aeonfall_adapter_result_delivery_service{}
