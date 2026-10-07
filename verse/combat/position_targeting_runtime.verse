using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /Verse.org/SpatialMath }

aeonfall_position_target_context := class:
    ContextId:string = ""
    OwnerKey:string = ""
    AbilityId:string = ""
    Position:vector3 = vector3{}
    RemainingSeconds:float = 0.0

# Short-lived world-position snapshots for placement-style abilities.
# This intentionally stores a validated request snapshot rather than making
# device adapters recalculate aim after input latency.
aeonfall_position_targeting_runtime := class():

    var NextContextNumber:int = 0
    var Contexts:[string]aeonfall_position_target_context = map{}

    CreateFromView(
        Agent:agent,
        AbilityId:string,
        DistanceWorldUnits:float,
        LifetimeSeconds:float
    )<decides><transacts>:string=
        DistanceWorldUnits > 0.0
        LifetimeSeconds > 0.0
        OwnerKey := AEONFALLActorRegistry.GetRuntimeKey[Agent]
        Character := Agent.GetFortCharacter()
        Character.IsActive[]

        Origin := Character.GetViewLocation()
        Forward := Character.GetViewRotation().GetForwardAxis()
        TargetPosition := Origin + (Forward * DistanceWorldUnits)

        set NextContextNumber += 1
        ContextId:string =
            "POS::" + OwnerKey + "::" + AbilityId + "::" + "{NextContextNumber}"

        Context := aeonfall_position_target_context:
            ContextId := ContextId
            OwnerKey := OwnerKey
            AbilityId := AbilityId
            Position := TargetPosition
            RemainingSeconds := LifetimeSeconds

        set Contexts[ContextId] = Context

        AEONFALLRuntimeBus.Emit(
            aeonfall_runtime_event{
                EventType := "target.position_created",
                SourceId := OwnerKey,
                TargetId := AbilityId,
                ContextId := ContextId
            }
        )

        ContextId

    Get(ContextId:string)<decides><transacts>:aeonfall_position_target_context=
        Context := Contexts[ContextId]
        Context.RemainingSeconds > 0.0
        Context

    Remove(ContextId:string)<transacts>:logic=
        if:
            Existing := Contexts[ContextId]
        then:
            var Updated:[string]aeonfall_position_target_context = map{}

            for (StoredId -> Context : Contexts):
                if (StoredId <> ContextId):
                    if:
                        set Updated[StoredId] = Context
                    then:
                        set Updated = Updated

            set Contexts = Updated

            AEONFALLRuntimeBus.Emit(
                aeonfall_runtime_event{
                    EventType := "target.position_removed",
                    SourceId := Existing.OwnerKey,
                    TargetId := Existing.AbilityId,
                    ContextId := ContextId
                }
            )
            return true

        false

    ClearOwner(OwnerKey:string)<transacts>:void=
        var Updated:[string]aeonfall_position_target_context = map{}

        for (ContextId -> Context : Contexts):
            if (Context.OwnerKey <> OwnerKey):
                if:
                    set Updated[ContextId] = Context
                then:
                    set Updated = Updated

        set Contexts = Updated

    TickAll(DeltaSeconds:float)<transacts>:void=
        if (DeltaSeconds <= 0.0):
            return

        var Updated:[string]aeonfall_position_target_context = map{}

        for (ContextId -> Context : Contexts):
            Remaining:float = Context.RemainingSeconds - DeltaSeconds

            if (Remaining > 0.0):
                Next := aeonfall_position_target_context:
                    ContextId := Context.ContextId
                    OwnerKey := Context.OwnerKey
                    AbilityId := Context.AbilityId
                    Position := Context.Position
                    RemainingSeconds := Remaining

                if:
                    set Updated[ContextId] = Next
                then:
                    set Updated = Updated
            else:
                AEONFALLRuntimeBus.Emit(
                    aeonfall_runtime_event{
                        EventType := "target.position_expired",
                        SourceId := Context.OwnerKey,
                        TargetId := Context.AbilityId,
                        ContextId := ContextId
                    }
                )

        set Contexts = Updated

AEONFALLPositionTargetingRuntime:aeonfall_position_targeting_runtime =
    aeonfall_position_targeting_runtime{}
