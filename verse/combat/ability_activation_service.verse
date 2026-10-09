using { /Verse.org/Verse }
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
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
            Definition := GetAEONFALLAbilityRegistry().Get[AbilityId]
        then:
            if (Player := player[Agent]):
                Entitled := AEONFALLPlayerLoadoutService.CanActivateForPlayer(
                    Player, OwnerKey, Definition
                )
                if (not Entitled?):
                    AEONFALLRuntimeBus.Emit(aeonfall_runtime_event{
                        EventType := "ability.entitlement_rejected",
                        SourceId := OwnerKey,
                        TargetId := AbilityId
                    })
                    return false
            Initialized := GetAEONFALLAbilityRuntime().Initialize(
                OwnerKey,
                Definition
            )

            if (not Initialized?):
                return false

            # Resolve authoritative context from the registered owner instead
            # of trusting caller-provided booleans. The legacy parameters remain
            # for source compatibility with current input devices.
            Context := GetAEONFALLActorContextRuntime().GetFlags(OwnerKey)

            RequestId:string = MakeRequestId(
                OwnerKey,
                AbilityId
            )

            Requested := GetAEONFALLActivationCoordinator().RequestActivation(
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
            OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
        then:
            Flags := GetAEONFALLActorContextRuntime().GetFlags(OwnerKey)

            TryActivate(
                Agent,
                AbilityId,
                OwnerKey,
                RuntimeContextId,
                Magnitude,
                Flags.EncounterActive,
                Flags.TransformationActive
            )
        else:
            false

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLAbilityActivationServiceSessions:weak_map(session, aeonfall_ability_activation_service) = map{}

GetAEONFALLAbilityActivationService()<transacts>:aeonfall_ability_activation_service=
    CurrentSession := GetSession()
    if (Existing := AEONFALLAbilityActivationServiceSessions[CurrentSession]):
        return Existing
    Created := aeonfall_ability_activation_service{}
    if (set AEONFALLAbilityActivationServiceSessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLAbilityActivationService in its session")
