using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Royal Scent does not instantly tame anything. It validates an eligible
# aggressive creature, applies the tracking mark, starts its authored species
# challenge, then reports success so the ability charge/bandwidth transaction
# can commit.
aeonfall_royal_scent_adapter_device := class(creative_device):

    OnBegin<override>()<suspends>:void=
        AEONFALLRuntimeBus.AbilityEffectRequested.Subscribe(OnRequest)

    OnRequest(Request:aeonfall_ability_effect_request)<transacts>:void=
        if (Request.AdapterId <> "royal_scent_adapter"):
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
            MarkDefinition := AEONFALLStatusRegistry.Get["STS-005"]
        then:
            Marked := AEONFALLStatusRuntime.ApplyStatus(
                Request.TargetKey,
                MarkDefinition,
                Request.OwnerKey,
                Request.Magnitude
            )

            if (Marked?):
                Started := AEONFALLTamingRuntime.StartChallenge(
                    Request.RequestId,
                    Request.OwnerKey,
                    Request.TargetKey,
                    SpeciesId
                )

                if (Started?):
                    set Succeeded = true
                    set ResultCode = "taming_challenge_started"
                else:
                    Removed := AEONFALLStatusRuntime.RemoveStatus(
                        Request.TargetKey,
                        "STS-005"
                    )
                    if (Removed?):
                        Removed = true
                    set ResultCode = "challenge_start_failed"
            else:
                set ResultCode = "tracking_mark_failed"

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
