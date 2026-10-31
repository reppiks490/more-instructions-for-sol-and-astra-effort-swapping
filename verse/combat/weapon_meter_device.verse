using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Fortnite.com/Game }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

aeonfall_heat_damage_listener := class:
    Adapter:aeonfall_weapon_meter_device
    Character:fort_character

    OnDamaged(Result:damage_result):void=
        Adapter.OnNPCDamaged(Character, Result)

# Bind ItemGate to the exact Fortnite item used by the WPN-007 delivery adapter.
# A logical weapon selection alone cannot heat the meter: the instigating player
# must currently hold that configured item and actually damage an observed NPC.
aeonfall_weapon_meter_device := class(creative_device):
    @editable
    Enabled:logic = false
    @editable
    NPCSpawner:npc_spawner_device = npc_spawner_device{}
    @editable
    NPCCanonicalId:string = "MON-043"
    @editable
    ItemGate:conditional_button_device = conditional_button_device{}

    ProfileService:aeonfall_profile_service = aeonfall_profile_service{}
    StopEvent:event() = event(){}
    var Running:logic = false
    var SpawnSubscription:?cancelable = false
    var DamageSubscriptions:[agent]cancelable = map{}
    var LastChargeAt:[string]float = map{}

    OnBegin<override>()<suspends>:void=
        if (not Enabled? or NPCCanonicalId = ""):
            return
        set Running = true
        Bound := NPCSpawner.SpawnedEvent.Subscribe(OnSpawned)
        set SpawnSubscription = option{Bound}
        # Recover actors registered before this device's OnBegin.
        for (Key -> Agent : GetAEONFALLActorRegistry().AgentByKey):
            if (GetAEONFALLActorRegistry().GetCanonicalId[Key] = NPCCanonicalId):
                OnSpawned(Agent)
        race:
            PruneLoop()
            StopEvent.Await()

    OnSpawned(Agent:agent):void=
        if:
            Running?
            not player[Agent]
            Character := Agent.GetFortCharacter[]
            Character.IsActive[]
        then:
            if (Old := DamageSubscriptions[Agent]):
                Old.Cancel()
            Listener := aeonfall_heat_damage_listener{Adapter := Self, Character := Character}
            Bound := Character.DamagedEvent().Subscribe(Listener.OnDamaged)
            if (set DamageSubscriptions[Agent] = Bound):
                return
            Bound.Cancel()

    OnNPCDamaged(Character:fort_character, Result:damage_result):void=
        if (CommitHeat[Character, Result]):
            return

    CommitHeat(Character:fort_character, Result:damage_result)<decides><transacts>:void=
        Running?
        fort_character[Result.Target] = Character
        Result.Amount > 0.0
        Result.Amount <= 100000.0
        Instigator := Result.Instigator?
        Agent := Instigator.GetInstigatorAgent[]
        Player := player[Agent]
        Player.IsActive[]
        OwnerCharacter := Agent.GetFortCharacter[]
        OwnerCharacter.IsActive[]
        ItemGate.IsHoldingItem[Agent]
        OwnerKey := GetAEONFALLActorRegistry().GetRuntimeKey[Agent]
        Profile := ProfileService.GetProfile[Player]
        Profile.UnlockedEntityIds.Find["WPN-007"]
        Profile.EquippedWeaponIds.Find["WPN-007"]
        Now := GetSimulationElapsedTime()
        if (Last := LastChargeAt[OwnerKey]):
            Now - Last >= 0.25
        Definition := GetAEONFALLAbilityRegistry().Get["ABL-006"]
        Initialized := GetAEONFALLAbilityRuntime().Initialize(OwnerKey, Definition)
        Initialized?
        Filled := GetAEONFALLAbilityRuntime().AddMeter(OwnerKey, Definition, 10)
        Filled?
        set LastChargeAt[OwnerKey] = Now
        Admitted := AEONFALLRuntimeBus.TryEmit(aeonfall_runtime_event{
            EventType := "ability.heat_earned",
            SourceId := OwnerKey,
            TargetId := "ABL-006",
            Amount := 10
        })
        Admitted?

    PruneLoop()<suspends>:void=
        loop:
            Sleep(1.0)
            if (not Running?):
                return
            var Kept:[agent]cancelable = map{}
            for (Agent -> Bound : DamageSubscriptions):
                if:
                    Character := Agent.GetFortCharacter[]
                    Character.IsActive[]
                then:
                    if (set Kept[Agent] = Bound):
                        set Kept = Kept
                    else:
                        Bound.Cancel()
                else:
                    Bound.Cancel()
            set DamageSubscriptions = Kept
            var KeptChargeAt:[string]float = map{}
            for (OwnerKey -> Last : LastChargeAt):
                if (GetAEONFALLActorRegistry().IsRegistered[OwnerKey]):
                    if (set KeptChargeAt[OwnerKey] = Last):
                        set KeptChargeAt = KeptChargeAt
            set LastChargeAt = KeptChargeAt

    OnEnd<override>():void=
        set Running = false
        StopEvent.Signal()
        if (Bound := SpawnSubscription?):
            Bound.Cancel()
        for (Agent -> Bound : DamageSubscriptions):
            Bound.Cancel()
        set SpawnSubscription = false
        set DamageSubscriptions = map{}
        set LastChargeAt = map{}
