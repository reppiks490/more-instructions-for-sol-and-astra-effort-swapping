using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }
using { /UnrealEngine.com/Temporary/SpatialMath }

# One adapter per region. NPC spawners supply authored appearance/navigation.
# This adapter consumes logical remains only when a living brood NPC is nearby.
aeonfall_horde_death_listener := class:
    Adapter:aeonfall_horde_ecology_adapter_device
    ActorKey:string
    var Handled:logic = false

    OnEliminated(Result:elimination_result):void=
        if (not Handled?):
            set Handled = true
            Adapter.RecordDeath(ActorKey, Result.EliminatedCharacter.GetTransform().Translation)

aeonfall_horde_ecology_adapter_device := class(creative_device):
    @editable
    RegionId:string = "REG-001"
    @editable
    CanonicalId:string = ""
    @editable
    Spawner:npc_spawner_device = npc_spawner_device{}
    @editable
    CorpseBiomass:int = 20
    @editable
    CorpseTrait:aeonfall_horde_trait = aeonfall_horde_trait.Plated
    @editable
    FeedingRadiusCm:float = 250.0
    @editable
    BurnButton:button_device = button_device{}
    @editable
    SanctifyButton:button_device = button_device{}
    @editable
    OpenApexTrigger:trigger_device = trigger_device{}
    @editable
    CloseApexTrigger:trigger_device = trigger_device{}

    @editable
    GorgedEffects:trigger_device = trigger_device{}
    @editable
    RemadeEffects:trigger_device = trigger_device{}
    @editable
    ApostateEffects:trigger_device = trigger_device{}
    @editable
    CrownedEffects:trigger_device = trigger_device{}

    StopEvent:event() = event(){}
    var Running:logic = false
    var Subscriptions:[]cancelable = array{}
    var DeathSubscriptions:[string]cancelable = map{}
    var CorpsePositions:[int]vector3 = map{}

    OnBegin<override>()<suspends>:void=
        if (RegionId = "" or CanonicalId = "" or FeedingRadiusCm <= 0.0):
            return
        set Running = true
        set Subscriptions = array{
            Spawner.SpawnedEvent.Subscribe(OnSpawned),
            BurnButton.InteractedWithEvent.Subscribe(BurnNearest),
            SanctifyButton.InteractedWithEvent.Subscribe(SanctifyNearest),
            OpenApexTrigger.TriggeredEvent.Subscribe(OpenApex),
            CloseApexTrigger.TriggeredEvent.Subscribe(CloseApex)
        }
        # Configure spawner to start disabled so no spawn precedes registration.
        Spawner.Enable()
        race:
            FeedLoop()
            WatchEvolution()
            StopEvent.Await()

    WatchEvolution()<suspends>:void=
        loop:
            Event := AEONFALLRuntimeBus.RuntimeEvent.Await()
            if:
                Running?
                Event.EventType = "horde.evolved"
                Event.TargetId = RegionId
                DeathSubscriptions[Event.SourceId]
                Agent := AEONFALLActorRegistry.GetAgent[Event.SourceId]
            then:
                # Bind these triggers to project-authored tier presentation and
                # physical effects; a logical promotion does not replace meshes.
                if (Event.Amount = 2):
                    GorgedEffects.Trigger(Agent)
                else if (Event.Amount = 3):
                    RemadeEffects.Trigger(Agent)
                else if (Event.Amount = 4):
                    ApostateEffects.Trigger(Agent)
                else if (Event.Amount = 5):
                    CrownedEffects.Trigger(Agent)

    FeedLoop()<suspends>:void=
        loop:
            Sleep(1.0)
            if (not Running?):
                return
            PrunePositions()
            for (Key -> Subscription : DeathSubscriptions):
                if:
                    Agent := AEONFALLActorRegistry.GetAgent[Key]
                    Character := Agent.GetFortCharacter[]
                    Character.IsActive[]
                    CorpseId := FindNearest(Character.GetTransform().Translation)?
                then:
                    Fed := AEONFALLHordeRuntime.Feed(Key, CorpseId)
                    if (Fed?):
                        PrunePositions()
            PruneListeners()

    OnSpawned(Agent:agent):void=
        PruneListeners()
        if:
            Running?
            Key := AEONFALLActorRegistry.Register[CanonicalId, Agent]
            Character := Agent.GetFortCharacter[]
            Character.IsActive[]
            not DeathSubscriptions[Key]
            AEONFALLHordeRuntime.RegisterBrood(Key, RegionId)?
        then:
            Listener := aeonfall_horde_death_listener{Adapter := Self, ActorKey := Key}
            Subscription := Character.EliminatedEvent().Subscribe(Listener.OnEliminated)
            if (set DeathSubscriptions[Key] = Subscription):
                return
            Subscription.Cancel()
            AEONFALLHordeRuntime.RemoveBrood(Key)

    RecordDeath(ActorKey:string, Position:vector3):void=
        if (Running?):
            PrunePositions()
            Id := AEONFALLHordeRuntime.AddCorpse(RegionId, CorpseBiomass, CorpseTrait)
            if (Id > 0):
                if (set CorpsePositions[Id] = Position):
                    set CorpsePositions = CorpsePositions
                else:
                    AEONFALLHordeRuntime.RemoveCorpse(Id)
        AEONFALLHordeRuntime.RemoveBrood(ActorKey)
        RemoveListener(ActorKey)

    FindNearest(Position:vector3)<transacts>:?int=
        var Nearest:?int = false
        var BestDistance:float = FeedingRadiusCm
        for (Id -> CorpsePosition : CorpsePositions):
            if:
                Corpse := AEONFALLHordeRuntime.GetCorpse[Id]
                Corpse.RegionId = RegionId
                Corpse.RemainingSeconds > 0.0
            then:
                Range := Distance(Position, CorpsePosition)
                if (Range <= BestDistance):
                    set BestDistance = Range
                    set Nearest = option{Id}
        Nearest

    BurnNearest(Agent:agent):void=
        DenyNearest(Agent, aeonfall_corpse_use.Burn)

    SanctifyNearest(Agent:agent):void=
        DenyNearest(Agent, aeonfall_corpse_use.Sanctify)

    DenyNearest(Agent:agent, Use:aeonfall_corpse_use):void=
        if:
            Running?
            player[Agent]
            Character := Agent.GetFortCharacter[]
            Character.IsActive[]
            Id := FindNearest(Character.GetTransform().Translation)?
        then:
            Used := AEONFALLHordeRuntime.UseCorpse(RegionId, Id, Use)
            if (Used?):
                PrunePositions()

    OpenApex(MaybeAgent:?agent):void=
        Changed := AEONFALLHordeRuntime.SetApexEvent(RegionId, true)

    CloseApex(MaybeAgent:?agent):void=
        Changed := AEONFALLHordeRuntime.SetApexEvent(RegionId, false)

    PrunePositions()<transacts>:void=
        var Kept:[int]vector3 = map{}
        for (Id -> Position : CorpsePositions):
            if (AEONFALLHordeRuntime.GetCorpse[Id], set Kept[Id] = Position):
                set Kept = Kept
        set CorpsePositions = Kept

    RemoveListener(ActorKey:string):void=
        var Kept:[string]cancelable = map{}
        for (Key -> Subscription : DeathSubscriptions):
            if (Key = ActorKey):
                Subscription.Cancel()
            else:
                if (set Kept[Key] = Subscription):
                    set Kept = Kept
        set DeathSubscriptions = Kept

    PruneListeners():void=
        var Stale:[]string = array{}
        for (Key -> Subscription : DeathSubscriptions):
            if (not AEONFALLActorRegistry.IsRegistered[Key]):
                set Stale += array{Key}
        for (Key : Stale):
            RemoveListener(Key)

    OnEnd<override>():void=
        if (not Running?):
            return
        set Running = false
        StopEvent.Signal()
        Spawner.Disable()
        for (Subscription : Subscriptions):
            Subscription.Cancel()
        for (Key -> Subscription : DeathSubscriptions):
            Subscription.Cancel()
        set Subscriptions = array{}
        set DeathSubscriptions = map{}
        set CorpsePositions = map{}
        AEONFALLHordeRuntime.ClearRegion(RegionId)
