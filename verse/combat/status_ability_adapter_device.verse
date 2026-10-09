using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Generic adapter for abilities whose canonical effect is one or more AEONFALL
# statuses. Physical gameplay/presentation for each status is handled by
# project-bound status effect bridges; this adapter owns target validation,
# canonical status state, and ability transaction success/failure.
aeonfall_status_ability_adapter_device := class(creative_device):

    @editable
    SupportedAdapterIds:[]string = array{}

    var EffectSubscription:?cancelable = false

    OnBegin<override>()<suspends>:void=
        Subscription := AEONFALLRuntimeBus.AbilityEffectRequested.Subscribe(OnAbilityEffectRequested)
        set EffectSubscription = option{Subscription}

    OnEnd<override>():void=
        if (Subscription := EffectSubscription?):
            Subscription.Cancel()
        set EffectSubscription = false

    Supports(AdapterId:string)<transacts>:logic=
        if:
            SupportedAdapterIds.Find[AdapterId]
        then:
            true
        else:
            false

    OnAbilityEffectRequested(
        Request:aeonfall_ability_effect_request
    ):void=
        if (not Supports(Request.AdapterId)?):
            return
        Claimed := GetAEONFALLAbilityRuntime().ClaimEffectRequest(Request)
        if (not Claimed?):
            return

        var Succeeded:logic = true
        var ResultCode:string = "ok"

        if:
            GetAEONFALLActorRegistry().IsRegistered[Request.TargetKey]
        then:
            set Succeeded = Succeeded
        else:
            set Succeeded = false
            set ResultCode = "target_not_registered"

        if (Succeeded?):
            if:
                Definition := GetAEONFALLAbilityRegistry().Get[Request.AbilityId]
            then:
                if (Definition.StatusIds.Length <= 0):
                    set Succeeded = false
                    set ResultCode = "ability_has_no_statuses"

                if (Succeeded?):
                    if (GetAEONFALLStatusRuntime().ApplyBatch[Request.TargetKey, Definition.StatusIds, Request.OwnerKey, Request.Magnitude]):
                        set Succeeded = true
                    else:
                        set Succeeded = false
                        set ResultCode = "status_batch_rejected"

            else:
                set Succeeded = false
                set ResultCode = "ability_definition_missing"

        AEONFALLAdapterResultDelivery.Report(
            aeonfall_adapter_result{
                RequestId := Request.RequestId,
                OwnerKey := Request.OwnerKey,
                AbilityId := Request.AbilityId,
                AdapterId := Request.AdapterId,
                Succeeded := Succeeded,
                ResultCode := ResultCode
            }
        )
