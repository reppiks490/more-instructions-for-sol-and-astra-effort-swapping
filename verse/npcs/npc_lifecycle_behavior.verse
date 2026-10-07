using { /Fortnite.com/AI }
using { /Verse.org/Simulation }

# Minimal project-bound NPC lifecycle behavior.
# Attach this only as a foundation or subclass it with movement/combat logic.
# Editable canonical/profile IDs are configured in the Character Definition or
# NPC Spawner so runtime events remain linked to the catalog.
aeonfall_npc_lifecycle_behavior<public> := class(npc_behavior):

    @editable
    CanonicalId:string = ""

    @editable
    BehaviorProfileId:string = ""

    @editable
    CompanionCapable:logic = false

    @editable
    BossControlled:logic = false

    OnBegin<override>()<suspends>:void=
        AEONFALLRuntimeBus.Emit(
            aeonfall_runtime_event{
                EventType := "npc.spawned",
                SourceId := CanonicalId,
                ContextId := BehaviorProfileId,
                Flag := CompanionCapable
            }
        )

    OnEnd<override>():void=
        AEONFALLRuntimeBus.Emit(
            aeonfall_runtime_event{
                EventType := "npc.removed",
                SourceId := CanonicalId,
                ContextId := BehaviorProfileId,
                Flag := BossControlled
            }
        )
