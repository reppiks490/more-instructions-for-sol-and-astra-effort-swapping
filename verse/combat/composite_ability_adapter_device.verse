using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Composite adapter for abilities that combine canonical status state with one
# project-bound UEFN device graph (for example Corpse Route: status + route spawn).
#
# Recipient validation precedes transactional all-or-none status application.
# Failed batches restore previous stacks and roll back queued status events.
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

    var EffectSubscription:?cancelable = false

    OnBegin<override>()<suspends>:void=
        Subscription := AEONFALLRuntimeBus.AbilityEffectRequested.Subscribe(OnRequest)
        set EffectSubscription = option{Subscription}

    OnEnd<override>():void=
        if (Subscription := EffectSubscription?):
            Subscription.Cancel()
        set EffectSubscription = false

    OnRequest(Request:aeonfall_ability_effect_request):void=
        if (not Supports(Request.AdapterId)?):
            return
        Claimed := GetAEONFALLAbilityRuntime().ClaimEffectRequest(Request)
        if (not Claimed?):
            return
        var Succeeded:logic = false
        var ResultCode:string = "effect_preflight_failed"
        # Resolve graph recipient before the batch. A missing recipient cannot
        # erase a previously active status or leave a partial new status set.
        if:
            Definition := GetAEONFALLAbilityRegistry().Get[Request.AbilityId]
            OwnerAgent := GetAEONFALLActorRegistry().GetAgent[Request.OwnerKey]
        then:
            var Recipient:?agent = option{OwnerAgent}
            if (RequireRegisteredTarget?):
                if (not GetAEONFALLActorRegistry().IsRegistered[Request.TargetKey]):
                    set Recipient = false
            if (TriggerOnTargetAgent?):
                if (TargetAgent := GetAEONFALLActorRegistry().GetAgent[Request.TargetKey]):
                    if (Recipient?):
                        set Recipient = option{TargetAgent}
                else:
                    set Recipient = false
            if:
                DispatchAgent := Recipient?
                GetAEONFALLStatusRuntime().ApplyBatch[Request.TargetKey, Definition.StatusIds, Request.OwnerKey, Request.Magnitude]
            then:
                TriggerOutput.Trigger(DispatchAgent)
                set Succeeded = true
                set ResultCode = "ok"
        AEONFALLAdapterResultDelivery.Report(aeonfall_adapter_result{
            RequestId := Request.RequestId, OwnerKey := Request.OwnerKey,
            AbilityId := Request.AbilityId, AdapterId := Request.AdapterId,
            Succeeded := Succeeded, ResultCode := ResultCode
        })
