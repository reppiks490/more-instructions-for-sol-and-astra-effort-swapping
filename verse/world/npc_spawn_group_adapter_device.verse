using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# Session-scoped physical ownership: a region/group has one adapter and an
# NPC Spawner may not be shared by different adapters or repeated in one list.
var AEONFALLInvasionSpawnerLeases:weak_map(session, [string]aeonfall_npc_spawn_group_adapter_device) = map{}

# Project-bound adapter from canonical invasion spawn-group requests to one or
# more configured NPC Spawner devices.
#
# Place one adapter per spawn-group binding in UEFN. The NPC Spawners themselves
# own Character Definitions, spawn count/interval, patrol setup, and local device
# limits. This adapter owns enable/disable lifecycle and deterministic cleanup.
aeonfall_npc_spawn_group_adapter_device := class(creative_device):

    @editable
    SpawnGroupId:string = ""

    # Fail closed until this device is bound to its canonical streamed region.
    @editable
    RegionId:string = ""

    @editable
    Spawners:[]npc_spawner_device = array{}

    @editable
    StartDisabled:logic = true

    @editable
    DespawnOnRelease:logic = true

    var ActiveInvasionIds:[]string = array{}
    var OwnsLease:logic = false

    var BusSubscription:?cancelable = false

    OnBegin<override>()<suspends>:void=
        # Never disable a spawner before acquiring exclusive ownership.
        # Fail closed on unbound or game-start-enabled editor configurations.
        if (RegionId = "" or SpawnGroupId = "" or Spawners.Length = 0 or not StartDisabled?):
            Print("AEONFALL invasion spawn adapter rejected invalid binding.")
            return
        Leased := AcquireAdapterLease()
        if (not Leased?):
            Print("AEONFALL invasion spawn adapter rejected duplicate group or shared spawner.")
            return
        set OwnsLease = true
        DisableAll()
        Subscription := AEONFALLRuntimeBus.RuntimeEvent.Subscribe(OnRuntimeEvent)
        set BusSubscription = option{Subscription}

    OnEnd<override>():void=
        # Rejected adapters must never touch another owner's physical devices.
        if (not OwnsLease?):
            return
        if (Subscription := BusSubscription?):
            Subscription.Cancel()
        set BusSubscription = false
        set ActiveInvasionIds = array{}
        DisableAll()
        if (DespawnOnRelease?):
            DespawnAll()
        Released := ReleaseAdapterLease()
        set OwnsLease = false

    AcquireAdapterLease()<transacts>:logic=
        var Owners:[string]aeonfall_npc_spawn_group_adapter_device = map{}
        if (Current := AEONFALLInvasionSpawnerLeases[GetSession()]):
            set Owners = Current
        Key:string = "{RegionId}::{SpawnGroupId}"
        if (Existing := Owners[Key]):
            if (Existing = Self):
                return true
            return false
        if (Owners.Length >= 128):
            return false
        for (Index -> Spawner : Spawners):
            for (OtherIndex -> OtherSpawner : Spawners):
                if (Index <> OtherIndex, Spawner = OtherSpawner):
                    return false
            for (OtherKey -> OtherAdapter : Owners):
                for (OwnedSpawner : OtherAdapter.Spawners):
                    if (Spawner = OwnedSpawner):
                        return false
        if:
            set Owners[Key] = Self
            set AEONFALLInvasionSpawnerLeases[GetSession()] = Owners
        then:
            return true
        false

    ReleaseAdapterLease()<transacts>:logic=
        Key:string = "{RegionId}::{SpawnGroupId}"
        if:
            Owners := AEONFALLInvasionSpawnerLeases[GetSession()]
            Owners[Key] = Self
        then:
            var Kept:[string]aeonfall_npc_spawn_group_adapter_device = map{}
            var Ready:logic = true
            for (OtherKey -> OtherAdapter : Owners):
                if (OtherKey <> Key):
                    if (set Kept[OtherKey] = OtherAdapter):
                        set Ready = Ready
                    else:
                        set Ready = false
            if (Ready?, set AEONFALLInvasionSpawnerLeases[GetSession()] = Kept):
                return true
        false

    # Runtime events are notifications, not authorization. Verify the active
    # canonical invasion, its region, current wave and declared group before
    # touching any physical NPC Spawner.
    IsActiveWaveRequest(InvasionId:string, WaveIndex:int)<transacts>:logic=
        if:
            RegionId <> ""
            SpawnGroupId <> ""
            Definition := GetAEONFALLInvasionRegistry().Get[InvasionId]
            Definition.RegionId = RegionId
            State := GetAEONFALLInvasionRuntime().GetState[InvasionId]
            State.Active?
            State.RegionId = RegionId
            State.CurrentWaveIndex = WaveIndex
            Wave := Definition.WaveSpawnGroupIds[WaveIndex]
            Wave.Find[SpawnGroupId]
        then:
            return true
        false

    # Release notifications are not authority: only an older wave which no
    # longer owns this group may release its physical NPC Spawners.
    IsValidWaveRelease(InvasionId:string, OldWaveIndex:int)<transacts>:logic=
        if:
            Definition := GetAEONFALLInvasionRegistry().Get[InvasionId]
            Definition.RegionId = RegionId
            State := GetAEONFALLInvasionRuntime().GetState[InvasionId]
            State.RegionId = RegionId
            State.Active?
            State.CurrentWaveIndex > OldWaveIndex
            CurrentWave := Definition.WaveSpawnGroupIds[State.CurrentWaveIndex]
            not CurrentWave.Find[SpawnGroupId]
        then:
            return true
        false

    IsTerminalInvasion(InvasionId:string, WasCompleted:logic)<transacts>:logic=
        if:
            Definition := GetAEONFALLInvasionRegistry().Get[InvasionId]
            Definition.RegionId = RegionId
            State := GetAEONFALLInvasionRuntime().GetState[InvasionId]
            State.RegionId = RegionId
            not State.Active?
        then:
            if (WasCompleted?):
                if (State.Completed?):
                    return true
            else:
                if (State.Failed?):
                    return true
        false

    AddRequester(InvasionId:string)<transacts>:logic=
        if (InvasionId = ""):
            return false

        if:
            ActiveInvasionIds.Find[InvasionId]
        then:
            return false

        # Region admission is exclusive; refuse stale/parallel requesters.
        if (ActiveInvasionIds.Length >= 1):
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
        if (not OwnsLease?):
            return
        if:
            Event.EventType = "invasion.spawn_group_requested"
            Event.TargetId = SpawnGroupId
            Event.ContextId = RegionId
            IsActiveWaveRequest(Event.SourceId, Event.Amount)?
        then:
            Added := AddRequester(Event.SourceId)
            if (Added?):
                EnableAll()
            return

        if:
            Event.EventType = "invasion.spawn_group_released"
            Event.TargetId = SpawnGroupId
            Event.ContextId = RegionId
            IsValidWaveRelease(Event.SourceId, Event.Amount)?
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
            Event.TargetId = RegionId
            IsTerminalInvasion(Event.SourceId, true)?
        then:
            RemovedCompleted := RemoveRequester(Event.SourceId)
            if (RemovedCompleted?, ActiveInvasionIds.Length = 0):
                DisableAll()
                if (DespawnOnRelease?):
                    DespawnAll()
            return

        if:
            Event.EventType = "invasion.failed"
            Event.TargetId = RegionId
            IsTerminalInvasion(Event.SourceId, false)?
        then:
            RemovedFailed := RemoveRequester(Event.SourceId)
            if (RemovedFailed?, ActiveInvasionIds.Length = 0):
                DisableAll()
                if (DespawnOnRelease?):
                    DespawnAll()
