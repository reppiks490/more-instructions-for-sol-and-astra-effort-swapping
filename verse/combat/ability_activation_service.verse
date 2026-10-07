using { /Verse.org/Simulation }

# Public player/NPC-facing activation facade.
# It resolves canonical definitions, initializes state idempotently, creates a
# unique request id, then delegates the two-phase transaction to the coordinator.
aeonfall_ability_activation_service := class():

    var NextRequestNumber:int = 0

    MakeRequestId(OwnerKey:string, AbilityId:string)<transacts>:string=
        set NextRequestNumber += 1
        "REQ::" + OwnerKey + "::" + AbilityId + "::" + "{NextRequestNumber}"

    TryActivate(
        Agent:agent,
        AbilityId:string,
        TargetKey:string,
        RuntimeContextId:string,
        Magnitude:int,
        EncounterActive:logic,
        TransformationActive:logic
    )<transacts>:logic=
        if:
            OwnerKey := AEONFALLActorRegistry.GetRuntimeKey[Agent]
            Definition := AEONFALLAbilityRegistry.Get[AbilityId]
        then:
            Initialized := AEONFALLAbilityRuntime.Initialize(
                OwnerKey,
                Definition
            )

            if (not Initialized?):
                return false

            Context := aeonfall_ability_context_flags:
                EncounterActive := EncounterActive
                TransformationActive := TransformationActive

            RequestId:string = MakeRequestId(
                OwnerKey,
                AbilityId
            )

            Requested := AEONFALLActivationCoordinator.RequestActivation(
                RequestId,
                OwnerKey,
                Definition,
                Context,
                TargetKey,
                RuntimeContextId,
                Magnitude
            )

            if (Requested?):
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "ability.activation_requested",
                        SourceId := OwnerKey,
                        TargetId := AbilityId,
                        ContextId := RequestId
                    }
                )
                return true

        false

    TryActivateSelf(
        Agent:agent,
        AbilityId:string,
        RuntimeContextId:string,
        Magnitude:int
    )<transacts>:logic=
        if:
            OwnerKey := AEONFALLActorRegistry.GetRuntimeKey[Agent]
        then:
            TryActivate(
                Agent,
                AbilityId,
                OwnerKey,
                RuntimeContextId,
                Magnitude,
                false,
                false
            )
        else:
            false

AEONFALLAbilityActivationService:aeonfall_ability_activation_service =
    aeonfall_ability_activation_service{}
