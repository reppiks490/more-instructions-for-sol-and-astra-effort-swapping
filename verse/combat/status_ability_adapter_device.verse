using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Generic adapter for abilities whose canonical effect is one or more AEONFALL
# statuses. Physical gameplay/presentation for each status is handled by
# project-bound status effect bridges; this adapter owns target validation,
# canonical status state, and ability transaction success/failure.
aeonfall_status_ability_adapter_device := class(creative_device):

    @editable
    SupportedAdapterIds:[]string = array{}

    OnBegin<override>()<suspends>:void=
        AEONFALLRuntimeBus.AbilityEffectRequested.Subscribe(OnAbilityEffectRequested)

    Supports(AdapterId:string)<transacts>:logic=
        if:
            SupportedAdapterIds.Find[AdapterId]
        then:
            true
        else:
            false

    OnAbilityEffectRequested(
        Request:aeonfall_ability_effect_request
    )<transacts>:void=
        if (not Supports(Request.AdapterId)?):
            return

        var Succeeded:logic = true
        var ResultCode:string = "ok"

        if:
            AEONFALLActorRegistry.IsRegistered[Request.TargetKey]
        then:
            set Succeeded = Succeeded
        else:
            set Succeeded = false
            set ResultCode = "target_not_registered"

        if (Succeeded?):
            if:
                Definition := AEONFALLAbilityRegistry.Get[Request.AbilityId]
            then:
                if (Definition.StatusIds.Length <= 0):
                    set Succeeded = false
                    set ResultCode = "ability_has_no_statuses"

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

                        if (not Applied?):
                            set Succeeded = false
                            set ResultCode = "status_apply_failed"
                    else:
                        set Succeeded = false
                        set ResultCode = "status_definition_missing"
            else:
                set Succeeded = false
                set ResultCode = "ability_definition_missing"

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
