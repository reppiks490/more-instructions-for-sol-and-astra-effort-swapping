using { /Verse.org/Verse }
using { /Verse.org/Simulation }

# Session actor identity registry.
# Canonical IDs describe what an actor is. Runtime keys distinguish individual
# spawned instances such as MON-043::127 from every other MON-043.
aeonfall_actor_registry := class():

    var NextActorNumber:int = 0
    var AgentByKey:[string]agent = map{}
    var KeyByAgent:[agent]string = map{}
    var CanonicalByKey:[string]string = map{}

    Register(
        CanonicalId:string,
        Agent:agent
    )<decides><transacts>:string=
        # Reject empty NPC Character Definition IDs before assigning a runtime
        # key. A duplicate registration is idempotent only for the same
        # canonical identity and a consistent forward/reverse mapping.
        CanonicalId <> ""
        if:
            Existing := KeyByAgent[Agent]
        then:
            ExistingAgent := AgentByKey[Existing]
            ExistingAgent = Agent
            ExistingCanonical := CanonicalByKey[Existing]
            ExistingCanonical = CanonicalId
            Existing
        else:
            set NextActorNumber += 1
            RuntimeKey:string = "{CanonicalId}::{NextActorNumber}"
            set AgentByKey[RuntimeKey] = Agent
            set KeyByAgent[Agent] = RuntimeKey
            set CanonicalByKey[RuntimeKey] = CanonicalId

            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "actor.registered",
                    SourceId := CanonicalId,
                    TargetId := RuntimeKey
                }
            )

            RuntimeKey

    GetAgent(RuntimeKey:string)<decides><transacts>:agent=
        AgentByKey[RuntimeKey]

    GetRuntimeKey(Agent:agent)<decides><transacts>:string=
        KeyByAgent[Agent]

    GetCanonicalId(RuntimeKey:string)<decides><transacts>:string=
        CanonicalByKey[RuntimeKey]

    IsRegistered(RuntimeKey:string)<decides><transacts>:void=
        Agent := AgentByKey[RuntimeKey]
        ReverseKey := KeyByAgent[Agent]
        ReverseKey = RuntimeKey
        CanonicalId := CanonicalByKey[RuntimeKey]
        CanonicalId <> ""

    Unregister(RuntimeKey:string)<transacts>:logic=
        if:
            Agent := AgentByKey[RuntimeKey]
            ReverseKey := KeyByAgent[Agent]
            ReverseKey = RuntimeKey
            CanonicalId := CanonicalByKey[RuntimeKey]
            CanonicalId <> ""
        then:
            # Preflight all three replacement maps before any dependent
            # runtime teardown. A failed rebuild must not clear live actor
            # abilities, companions or pending requests while keeping identity.
            var UpdatedAgents:[string]agent = map{}
            var UpdatedKeys:[agent]string = map{}
            var UpdatedCanonical:[string]string = map{}
            var Valid:logic = true

            for (Key -> StoredAgent : AgentByKey):
                if (Key <> RuntimeKey):
                    if:
                        set UpdatedAgents[Key] = StoredAgent
                    then:
                        set Valid = Valid
                    else:
                        set Valid = false

            for (StoredAgent -> Key : KeyByAgent):
                if (StoredAgent <> Agent):
                    if:
                        set UpdatedKeys[StoredAgent] = Key
                    then:
                        set Valid = Valid
                    else:
                        set Valid = false

            for (Key -> CanonicalId : CanonicalByKey):
                if (Key <> RuntimeKey):
                    if:
                        set UpdatedCanonical[Key] = CanonicalId
                    then:
                        set Valid = Valid
                    else:
                        set Valid = false

            if (not Valid?):
                return false

            # Never clear a different actor's gameplay state through an
            # incomplete or inconsistent identity mapping.
            # Release dependent runtime state while the key is still resolvable.
            GetAEONFALLActivationCoordinator().ClearOwnerPending(RuntimeKey)
            GetAEONFALLCompanionRuntime().ReleaseAllForOwner(
                RuntimeKey,
                "owner_unregistered"
            )
            ReleasedAsCompanion := GetAEONFALLCompanionRuntime().ReleaseByCompanionKey(
                RuntimeKey,
                "companion_unregistered"
            )

            ClearedTarget := GetAEONFALLTargetingRuntime().Clear(RuntimeKey)

            GetAEONFALLActorContextRuntime().Clear(RuntimeKey)
            GetAEONFALLPositionTargetingRuntime().ClearOwner(RuntimeKey)
            GetAEONFALLSpawnRuntime().ClearOwner(
                RuntimeKey,
                "owner_unregistered"
            )
            GetAEONFALLUnlockDeliveryService().ClearOwner(RuntimeKey)
            GetAEONFALLHordeRuntime().RemoveBrood(RuntimeKey)
            GetAEONFALLStatusRuntime().ClearTarget(RuntimeKey)
            GetAEONFALLAbilityRuntime().ClearOwner(RuntimeKey)
            GetAEONFALLClassRuntime().ClearOwner(RuntimeKey)
            GetAEONFALLEncounterParticipation().RemoveRuntimeKey(RuntimeKey)
            GetAEONFALLAscensionTrialRuntime().ClearOwner(RuntimeKey)
            GetAEONFALLChoosingRuntime().ClearOwner(RuntimeKey)
            GetAEONFALLAscendedFormRuntime().ClearOwner(RuntimeKey)
            GetAEONFALLTranscendentRuntime().ClearOwner(RuntimeKey)
            GetAEONFALLHallOfAscendants().RemoveOwner(RuntimeKey)

            set AgentByKey = UpdatedAgents
            set KeyByAgent = UpdatedKeys
            set CanonicalByKey = UpdatedCanonical

            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "actor.unregistered",
                    SourceId := RuntimeKey
                }
            )
            return true

        false

# Mutable service allocation is scoped to the current Verse session.
var AEONFALLActorRegistrySessions:weak_map(session, aeonfall_actor_registry) = map{}

GetAEONFALLActorRegistry()<transacts>:aeonfall_actor_registry=
    CurrentSession := GetSession()
    if (Existing := AEONFALLActorRegistrySessions[CurrentSession]):
        return Existing
    Created := aeonfall_actor_registry{}
    if (set AEONFALLActorRegistrySessions[CurrentSession] = Created):
        return Created
    # Never return an unretained temporary gameplay service.
    Err("AEONFALL could not retain AEONFALLActorRegistry in its session")
