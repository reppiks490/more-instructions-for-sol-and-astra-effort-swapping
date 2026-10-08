using { /Fortnite.com/Devices }
using { /Verse.org/Diagnostics }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Real service assertions for UEFN. Does not impersonate an actual actor or
# touch player persistence; synthetic dev owners live only in session runtime.
aeonfall_activation_transaction_test_device := class(creative_device):
    @editable
    Enabled:logic = false
    Coordinator:aeonfall_activation_coordinator = aeonfall_activation_coordinator{}
    var Checks:int = 0
    var Failures:int = 0
    var RejectNext:logic = false
    var Listener:?cancelable = false

    Check(Label:string, Passed:logic):void=
        set Checks += 1
        if (not Passed?):
            set Failures += 1
            Print("ACTIVATION FAIL: {Label}")

    Fixture(Id:string, Lifetime:aeonfall_activation_lifetime)<transacts>:aeonfall_ability_definition=
        aeonfall_ability_definition{
            AbilityId := Id, AdapterId := "DEV-TRANSACTION-ADAPTER",
            ResourcePolicy := aeonfall_resource_policy.Charges,
            MaxCharges := 2, RechargeSeconds := 5.0,
            TargetPolicy := aeonfall_target_policy.Self,
            ActivationLifetime := Lifetime
        }

    Request(Definition:aeonfall_ability_definition, Id:string)<transacts>:logic=
        Coordinator.RequestActivation(Id, "DEV-TRANSACTION-OWNER", Definition,
            aeonfall_ability_context_flags{}, "DEV-TRANSACTION-OWNER", "", 1)

    RunStatusAssertions():void=
        Runtime := aeonfall_status_runtime{}
        Stack := aeonfall_status_definition{
            StatusId := "DEV-STS-STACK", StackRule := aeonfall_status_stack_rule.AddStack,
            MaxStacks := 3, BaseDurationSeconds := 5.0
        }
        Reject := aeonfall_status_definition{
            StatusId := "DEV-STS-REJECT", StackRule := aeonfall_status_stack_rule.RejectDuplicate,
            BaseDurationSeconds := 5.0
        }
        Check("stack fixture registers", AEONFALLStatusRegistry.Register(Stack))
        Check("reject fixture registers", AEONFALLStatusRegistry.Register(Reject))
        Check("seed existing stack", Runtime.ApplyStatus("DEV-STATUS-TARGET", Stack, "ORIGINAL-OWNER", 7))
        Check("seed existing rejection", Runtime.ApplyStatus("DEV-STATUS-TARGET", Reject, "ORIGINAL-OWNER", 1))
        QueueBefore := GetAEONFALLBusState().PendingRuntimeEvents.Length
        var Applied:logic = false
        if (Runtime.ApplyBatch["DEV-STATUS-TARGET", array{Stack.StatusId, Reject.StatusId}, "COMPETING-OWNER", 9]):
            set Applied = true
        Check("rejected batch fails", logic{not Applied?})
        Restored := Runtime.GetStatuses("DEV-STATUS-TARGET")
        Check("failed batch restores stack", logic{State := Restored[0], State.StackCount = 1, State.Magnitude = 7, State.SourceId = "ORIGINAL-OWNER"})
        Check("failed batch restores queued events", logic{GetAEONFALLBusState().PendingRuntimeEvents.Length = QueueBefore})
        if (Runtime.ApplyBatch["DEV-STATUS-TARGET", array{Stack.StatusId, "DEV-MISSING-STATUS"}, "COMPETING-OWNER", 9]):
            set Applied = true
        Check("missing definition fails batch", logic{not Applied?})
        AfterMissing := Runtime.GetStatuses("DEV-STATUS-TARGET")
        Check("missing definition restores stack", logic{State := AfterMissing[0], State.StackCount = 1, State.SourceId = "ORIGINAL-OWNER"})
        if (Runtime.ApplyBatch["DEV-STATUS-TARGET", array{Stack.StatusId}, "NEXT-OWNER", 9]):
            set Applied = true
        Check("valid batch commits", Applied)
        Committed := Runtime.GetStatuses("DEV-STATUS-TARGET")
        Check("valid batch changes stack once", logic{State := Committed[0], State.StackCount = 2, State.SourceId = "NEXT-OWNER"})
        Runtime.ClearTarget("DEV-STATUS-TARGET")

    OnRequest(Requested:aeonfall_ability_effect_request):void=
        if (Requested.AdapterId <> "DEV-TRANSACTION-ADAPTER"):
            return
        if (Definition := AEONFALLAbilityRegistry.Get[Requested.AbilityId]):
            Result := aeonfall_adapter_result{
                RequestId := Requested.RequestId, OwnerKey := Requested.OwnerKey,
                AbilityId := Requested.AbilityId, AdapterId := Requested.AdapterId,
                Succeeded := logic{not RejectNext?}, ResultCode := "dev_result"
            }
            if (not Coordinator.PendingActivations[Requested.RequestId]):
                Check("late callback rejected", logic{not Coordinator.ResolveAdapterResult(Definition, Result)?})
                return
            Check("tracking exists before effect", true)
            set RejectNext = false
            Check("result resolves", Coordinator.ResolveAdapterResult(Definition, Result))

    OnBegin<override>()<suspends>:void=
        if (not Enabled?):
            return
        Subscription := AEONFALLRuntimeBus.AbilityEffectRequested.Subscribe(OnRequest)
        set Listener = option{Subscription}
        Sleep(0.05)
        RunStatusAssertions()
        Instant := Fixture("DEV-ABL-INSTANT", aeonfall_activation_lifetime.Instant)
        Managed := Fixture("DEV-ABL-MANAGED", aeonfall_activation_lifetime.Managed)
        for (Definition : array{Instant, Managed}):
            Check("definition registers", AEONFALLAbilityRegistry.Register(Definition))
            Check("state initializes", AEONFALLAbilityRuntime.Initialize("DEV-TRANSACTION-OWNER", Definition))
        Check("instant requested", Request(Instant, "DEV-R1"))
        ClaimFixture := aeonfall_ability_effect_request{
            RequestId := "DEV-R1", OwnerKey := "DEV-TRANSACTION-OWNER",
            AbilityId := Instant.AbilityId, AdapterId := Instant.AdapterId
        }
        FirstClaim := AEONFALLAbilityRuntime.ClaimEffectRequest(ClaimFixture)
        SecondClaim := AEONFALLAbilityRuntime.ClaimEffectRequest(ClaimFixture)
        Check("first effect claim succeeds", FirstClaim)
        Check("duplicate effect claim rejected", logic{not SecondClaim?})
        WrongOwner := aeonfall_adapter_result{
            RequestId := "DEV-R1", OwnerKey := "OTHER-OWNER",
            AbilityId := Instant.AbilityId, AdapterId := Instant.AdapterId, Succeeded := true
        }
        Check("wrong owner rejected", logic{not Coordinator.ResolveAdapterResult(Instant, WrongOwner)?})
        Check("wrong owner preserves pending", logic{Coordinator.PendingActivations["DEV-R1"]})
        Check("duplicate request rejected", logic{not Request(Managed, "DEV-R1")?})
        Check("wrong cancel rejected", logic{not Coordinator.CancelPending("OTHER-OWNER", Instant.AbilityId, "DEV-R1")?})
        AEONFALLRuntimeBus.Pump()
        Sleep(0.05)
        Check("instant does not latch active", logic{State := AEONFALLAbilityRuntime.GetState["DEV-TRANSACTION-OWNER", Instant.AbilityId], not State.Active?})
        Check("charged once", logic{State := AEONFALLAbilityRuntime.GetState["DEV-TRANSACTION-OWNER", Instant.AbilityId], State.CurrentCharges = 1})
        Check("no phantom pending", logic{not Coordinator.PendingActivations["DEV-R1"]})
        Check("resolved claim released", logic{not AEONFALLAbilityRuntime.EffectClaims["DEV-R1"]})
        Check("instant reusable", Request(Instant, "DEV-R2"))
        set RejectNext = true
        AEONFALLRuntimeBus.Pump()
        Sleep(0.05)
        Check("rejection retains charges", logic{State := AEONFALLAbilityRuntime.GetState["DEV-TRANSACTION-OWNER", Instant.AbilityId], State.CurrentCharges = 1})
        Check("managed requested", Request(Managed, "DEV-M1"))
        AEONFALLRuntimeBus.Pump()
        Sleep(0.05)
        Check("managed remains active", logic{State := AEONFALLAbilityRuntime.GetState["DEV-TRANSACTION-OWNER", Managed.AbilityId], State.Active?})
        Check("managed blocks duplicate", logic{not Request(Managed, "DEV-M2")?})
        Check("managed ends explicitly", Coordinator.EndActivation("DEV-TRANSACTION-OWNER", Managed.AbilityId))
        Check("managed reusable after end", Request(Managed, "DEV-M3"))
        Check("correct cancellation", Coordinator.CancelPending("DEV-TRANSACTION-OWNER", Managed.AbilityId, "DEV-M3"))
        AEONFALLRuntimeBus.Pump()
        Sleep(0.05)
        # Detach before timeout assertions; late canceled results are already
        # tested above without consuming any additional charge.
        if (Subscription := Listener?):
            Subscription.Cancel()
        set Listener = false
        Check("timeout request", Request(Instant, "DEV-T1"))
        Coordinator.TickPendingActivations(5.0)
        Check("timeout clears tracking", logic{not Coordinator.PendingActivations["DEV-T1"]})
        Check("timeout clears ability pending", logic{State := AEONFALLAbilityRuntime.GetState["DEV-TRANSACTION-OWNER", Instant.AbilityId], not State.Pending?})
        AEONFALLAbilityRuntime.ClearOwner("DEV-TRANSACTION-OWNER")
        Print("ACTIVATION RESULT: {Checks} checks, {Failures} failures")

    OnEnd<override>():void=
        if (Subscription := Listener?):
            Subscription.Cancel()
        Coordinator.ClearOwnerPending("DEV-TRANSACTION-OWNER")
        AEONFALLAbilityRuntime.ClearOwner("DEV-TRANSACTION-OWNER")
