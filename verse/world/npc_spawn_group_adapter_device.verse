using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Project-bound adapter from canonical invasion spawn-group requests to one or
# more configured NPC Spawner devices.
#
# Place one adapter per spawn-group binding in UEFN. The NPC Spawners themselves
# own Character Definitions, spawn count/interval, patrol setup, and local device
# limits. This adapter owns enable/disable lifecycle and deterministic cleanup.
aeonfall_npc_spawn_group_adapter_device := class(creative_device):

    @editable
    SpawnGroupId:string = ""

    @editable
    Spawners:[]npc_spawner_device = array{}

    @editable
    StartDisabled:logic = true

    @editable
    DespawnOnRelease:logic = true

    var ActiveInvasionIds:[]string = array{}

    var BusSubscription:?cancelable = false

    OnBegin<override>()<suspends>:void=
        if (StartDisabled?):
            DisableAll()

        Subscription := AEONFALLRuntimeBus.RuntimeEvent.Subscribe(OnRuntimeEvent)
        set BusSubscription = option{Subscription}

    OnEnd<override>():void=
        if (Subscription := BusSubscription?):
            Subscription.Cancel()
        set BusSubscription = false

    AddRequester(InvasionId:string)<transacts>:logic=
        if (InvasionId = ""):
            return false

        if:
            ActiveInvasionIds.Find[InvasionId]
        then:
            return false

        set ActiveInvasionIds = ActiveInvasionIds + array{InvasionId}
        true

    RemoveRequester(InvasionId:string)<transacts>:logic=
        var Updated:[]string = array{}
        var Removed:logic = false

        for (ExistingId : ActiveInvasionIds):
            if (ExistingId = InvasionId):
                set Removed = true
            else:
                set Updated = Updated + array{ExistingId}

        if (Removed?):
            set ActiveInvasionIds = Updated

        Removed

    EnableAll():void=
        for (Spawner : Spawners):
            Spawner.Enable()

        AEONFALLRuntimeBus.Emit(
            aeonfall_runtime_event{
                EventType := "spawn_group.enabled",
                SourceId := SpawnGroupId,
                Amount := Spawners.Length
            }
        )

    DisableAll():void=
        for (Spawner : Spawners):
            Spawner.Disable()

        AEONFALLRuntimeBus.Emit(
            aeonfall_runtime_event{
                EventType := "spawn_group.disabled",
                SourceId := SpawnGroupId,
                Amount := Spawners.Length
            }
        )

    DespawnAll():void=
        for (Spawner : Spawners):
            Spawner.DespawnAll(false)

        AEONFALLRuntimeBus.Emit(
            aeonfall_runtime_event{
                EventType := "spawn_group.despawned",
                SourceId := SpawnGroupId,
                Amount := Spawners.Length
            }
        )

    OnRuntimeEvent(Event:aeonfall_runtime_event):void=
        if:
            Event.EventType = "invasion.spawn_group_requested"
            Event.TargetId = SpawnGroupId
        then:
            Added := AddRequester(Event.SourceId)
            if (Added?):
                EnableAll()
            return

        if:
            Event.EventType = "invasion.spawn_group_released"
            Event.TargetId = SpawnGroupId
        then:
            RemovedWave := RemoveRequester(Event.SourceId)
            if:
                RemovedWave?
                ActiveInvasionIds.Length = 0
            then:
                DisableAll()
                if (DespawnOnRelease?):
                    DespawnAll()
            return

        if:
            Event.EventType = "invasion.completed"
            RemovedCompleted := RemoveRequester(Event.SourceId)
            RemovedCompleted?
            ActiveInvasionIds.Length = 0
        then:
            DisableAll()
            if (DespawnOnRelease?):
                DespawnAll()
            return

        if:
            Event.EventType = "invasion.failed"
            RemovedFailed := RemoveRequester(Event.SourceId)
            RemovedFailed?
            ActiveInvasionIds.Length = 0
        then:
            DisableAll()
            if (DespawnOnRelease?):
                DespawnAll()
