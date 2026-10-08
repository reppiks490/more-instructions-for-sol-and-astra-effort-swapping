using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Royal Scent does not instantly tame anything. It validates an eligible
# aggressive creature, applies the tracking mark, starts its authored species
# challenge, then reports success so the ability charge/bandwidth transaction
# can commit.
aeonfall_royal_scent_adapter_device := class(creative_device):

    var EffectSubscription:?cancelable = false

    OnBegin<override>()<suspends>:void=
        Subscription := AEONFALLRuntimeBus.AbilityEffectRequested.Subscribe(OnRequest)
        set EffectSubscription = option{Subscription}

    OnEnd<override>():void=
        if (Subscription := EffectSubscription?):
            Subscription.Cancel()
        set EffectSubscription = false

    # Rejecting a competing challenge restores the previous owner's mark and
    # queued presentation. Removing a refreshed mark is not a valid rollback.
    StartMarkedChallenge(
        Request:aeonfall_ability_effect_request, SpeciesId:string
    )<decides><transacts>:void=
        MarkDefinition := AEONFALLStatusRegistry.Get["STS-005"]
        Marked := AEONFALLStatusRuntime.ApplyStatus(
            Request.TargetKey, MarkDefinition, Request.OwnerKey, Request.Magnitude
        )
        Marked?
        Started := AEONFALLTamingRuntime.StartChallenge(
            Request.RequestId, Request.OwnerKey, Request.TargetKey, SpeciesId
        )
        Started?

    OnRequest(Request:aeonfall_ability_effect_request):void=
        if (Request.AdapterId <> "royal_scent_adapter"):
            return
        Claimed := AEONFALLAbilityRuntime.ClaimEffectRequest(Request)
        if (not Claimed?):
            return

        var Succeeded:logic = false
        var ResultCode:string = "invalid_target"

        if:
            SpeciesId := AEONFALLActorRegistry.GetCanonicalId[Request.TargetKey]
            Definition := AEONFALLTamingRegistry.Get[SpeciesId]
            Definition.AbilityId = Request.AbilityId
            ClassState := AEONFALLClassRuntime.GetState[Request.OwnerKey]
            ClassState.ClassId = Definition.RequiredClassId
            ClassState.Active?
            AEONFALLCompanionRuntime.CanBind(
                Request.OwnerKey,
                Request.TargetKey
            )?
            StartMarkedChallenge[Request, SpeciesId]
        then:
            spawn{
                AEONFALLTamingRuntime.WatchTimeout(
                    Request.TargetKey, Request.RequestId, Definition.MaxChallengeSeconds
                )
            }
            set Succeeded = true
            set ResultCode = "taming_challenge_started"

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
