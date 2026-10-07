using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Composite adapter for abilities that combine canonical status state with one
# project-bound UEFN device graph (for example Corpse Route: status + route spawn).
#
# Canonical status application happens first. If the linked graph cannot be
# addressed, applied statuses are rolled back before reporting failure.
aeonfall_composite_ability_adapter_device := class(creative_device):

    @editable
    SupportedAdapterIds:[]string = array{}

    @editable
    TriggerOutput:trigger_device = trigger_device{}

    @editable
    TriggerOnTargetAgent:logic = false

    @editable
    RequireRegisteredTarget:logic = true

    Supports(AdapterId:string)<transacts>:logic=
        if:
            SupportedAdapterIds.Find[AdapterId]
        then:
            true
        else:
            false

    OnBegin<override>()<suspends>:void=
        AEONFALLRuntimeBus.AbilityEffectRequested.Subscribe(OnRequest)

    OnRequest(Request:aeonfall_ability_effect_request)<transacts>:void=
        if (not Supports(Request.AdapterId)?):
            return

        var Succeeded:logic = true
        var ResultCode:string = "ok"
        var AppliedStatusIds:[]string = array{}

        if:
            Definition := AEONFALLAbilityRegistry.Get[Request.AbilityId]
        then:
            if (RequireRegisteredTarget?):
                if:
                    AEONFALLActorRegistry.IsRegistered[Request.TargetKey]
                then:
                    set Succeeded = Succeeded
                else:
                    set Succeeded = false
                    set ResultCode = "target_not_registered"

            if (Succeeded?):
                for (StatusId : Definition.StatusIds):
                    if:
                        StatusDefinition := AEONFALLStatusRegistry.Get[StatusId]
                    then:
                        Applied := AEONFALLStatusRuntime.ApplyStatus(
                            Request.TargetKey,
                            StatusDefinition,
                            Request.OwnerKey,
                            Request.Magnitude
                        )

                        if (Applied?):
                            set AppliedStatusIds = AppliedStatusIds + array{StatusId}
                        else:
                            set Succeeded = false
                            set ResultCode = "status_apply_failed"
                    else:
                        set Succeeded = false
                        set ResultCode = "status_definition_missing"

            if (Succeeded?):
                if:
                    OwnerAgent := AEONFALLActorRegistry.GetAgent[Request.OwnerKey]
                then:
                    if (TriggerOnTargetAgent?):
                        if:
                            TargetAgent := AEONFALLActorRegistry.GetAgent[Request.TargetKey]
                        then:
                            TriggerOutput.Trigger(TargetAgent)
                        else:
                            set Succeeded = false
                            set ResultCode = "target_agent_not_registered"
                    else:
                        TriggerOutput.Trigger(OwnerAgent)
                else:
                    set Succeeded = false
                    set ResultCode = "owner_not_registered"
        else:
            set Succeeded = false
            set ResultCode = "ability_definition_missing"

        if (not Succeeded?):
            for (StatusId : AppliedStatusIds):
                RolledBack := AEONFALLStatusRuntime.RemoveStatus(
                    Request.TargetKey,
                    StatusId
                )
                if (RolledBack?):
                    set Succeeded = Succeeded

        AEONFALLRuntimeBus.ReportAdapterResult(
            aeonfall_adapter_result{
                RequestId := Request.RequestId,
                OwnerKey := Request.OwnerKey,
                AbilityId := Request.AbilityId,
                AdapterId := Request.AdapterId,
                Succeeded := Succeeded,
                ResultCode := ResultCode
            }
        )
