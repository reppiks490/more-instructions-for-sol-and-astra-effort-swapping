using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Generic publish-safe bridge from canonical ability requests into an
# editor-linked UEFN device graph. Configure one instance per AdapterId.
#
# The linked TriggerOutput may drive VFX, prop manipulation, damage volumes,
# item systems, sequencers, or other supported Creative/UEFN devices.
aeonfall_trigger_ability_adapter_device := class(creative_device):

    @editable
    AdapterId:string = ""

    @editable
    TriggerOutput:trigger_device = trigger_device{}

    @editable
    RequireRegisteredTarget:logic = false

    @editable
    UseTargetAgent:logic = false

    OnBegin<override>()<suspends>:void=
        AEONFALLRuntimeBus.AbilityEffectRequested.Subscribe(OnRequest)

    OnRequest(Request:aeonfall_ability_effect_request)<transacts>:void=
        if (Request.AdapterId <> AdapterId):
            return

        var Succeeded:logic = true
        var ResultCode:string = "ok"

        if (AdapterId = ""):
            set Succeeded = false
            set ResultCode = "adapter_id_empty"

        if:
            OwnerAgent := AEONFALLActorRegistry.GetAgent[Request.OwnerKey]
        then:
            if:
                Succeeded?
                RequireRegisteredTarget?
            then:
                if:
                    AEONFALLActorRegistry.IsRegistered[Request.TargetKey]
                then:
                    set Succeeded = Succeeded
                else:
                    set Succeeded = false
                    set ResultCode = "target_not_registered"

            if (Succeeded?):
                if (UseTargetAgent?):
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
