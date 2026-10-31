using { /Fortnite.com/AI }
using { /Verse.org/Simulation }

# Minimal project-bound NPC lifecycle behavior.
# Character Definitions / NPC Spawners supply canonical/profile IDs. Every
# spawned NPC receives a unique session RuntimeKey so statuses and abilities
# target an instance rather than every NPC that shares the same catalog ID.
aeonfall_npc_lifecycle_behavior<public> := class(npc_behavior):

    @editable
    CanonicalId:string = ""

    @editable
    BehaviorProfileId:string = ""

    @editable
    CompanionCapable:logic = false

    @editable
    BossControlled:logic = false

    var RuntimeKey:string = ""

    OnBegin<override>()<suspends>:void=
        if:
            Agent := GetAgent[]
            RegisteredKey := GetAEONFALLActorRegistry().Register[CanonicalId, Agent]
        then:
            set RuntimeKey = RegisteredKey

            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "npc.spawned",
                    SourceId := CanonicalId,
                    TargetId := RuntimeKey,
                    ContextId := BehaviorProfileId,
                    Flag := CompanionCapable
                }
            )
        else:
            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "npc.runtime_identity_failed",
                    SourceId := CanonicalId,
                    ContextId := BehaviorProfileId
                }
            )

    OnEnd<override>():void=
        if (RuntimeKey <> ""):
            Removed := GetAEONFALLActorRegistry().Unregister(RuntimeKey)
            if (not Removed?):
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "npc.runtime_identity_cleanup_failed",
                        SourceId := CanonicalId,
                        TargetId := RuntimeKey
                    }
                )

        AEONFALLRuntimeBus.Emit(
            aeonfall_runtime_event{
                EventType := "npc.removed",
                SourceId := CanonicalId,
                TargetId := RuntimeKey,
                ContextId := BehaviorProfileId,
                Flag := BossControlled
            }
        )
