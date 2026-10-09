using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }
using { /UnrealEngine.com/Temporary/SpatialMath }

aeonfall_prepared_prop_spawn := class:
    HandleId:string = ""
    Position:vector3 = vector3{}
    Rotation:rotation = rotation{}

# Place one configured adapter per supported position ability. The asset must
# be an actual editor-authored creative_prop_asset, not a mesh path string.
aeonfall_prop_spawn_adapter_device := class(creative_device):
    @editable
    Enabled:logic = false
    @editable
    AbilityId:string = "ABL-001"
    @editable
    AdapterId:string = "grave_architecture_redoubt_adapter"
    @editable
    SpawnId:string = "SPAWN-GRAVE-WALL"
    @editable
    PropAsset:creative_prop_asset = DefaultCreativePropAsset
    @editable
    MaxPerOwner:int = 2
    @editable
    LifetimeSeconds:float = 30.0
    @editable
    MaximumDistanceCm:float = 1500.0
    @editable
    MinimumDistanceCm:float = 250.0
    @editable
    ProjectToOwnerHeight:logic = true
    @editable
    VerticalOffsetCm:float = -90.0

    StopEvent:event() = event(){}
    var Running:logic = false
    var Subscription:?cancelable = false
    var PhysicalProps:[string]creative_prop = map{}

    ValidSettings()<transacts>:logic=
        if:
            AbilityId <> ""
            AdapterId <> ""
            SpawnId <> ""
            MaxPerOwner > 0
            MaxPerOwner <= 4
            LifetimeSeconds > 0.0
            LifetimeSeconds <= 120.0
            MinimumDistanceCm >= 200.0
            MaximumDistanceCm > MinimumDistanceCm
            MaximumDistanceCm <= 2000.0
            VerticalOffsetCm >= -200.0
            VerticalOffsetCm <= 200.0
        then:
            return true
        false

    OnBegin<override>()<suspends>:void=
        if (not ValidSettings()?):
            Print("AEONFALL prop adapter rejected invalid settings.")
            return
        set Running = true
        Bound := AEONFALLRuntimeBus.AbilityEffectRequested.Subscribe(OnRequest)
        set Subscription = option{Bound}
        race:
            CleanupLoop()
            StopEvent.Await()

    OnRequest(Request:aeonfall_ability_effect_request):void=
        if (Request.AbilityId <> AbilityId or Request.AdapterId <> AdapterId):
            return
        Claimed := GetAEONFALLAbilityRuntime().ClaimEffectRequest(Request)
        if (not Claimed?):
            return
        var ResultCode:string = "spawn_preflight_failed"
        if (Prepared := PrepareSpawn[Request]):
            # Capture the native return outside a failure scope. Compensation
            # explicitly disposes a created prop when later logical steps fail.
            Spawned := SpawnProp(PropAsset, Prepared.Position, Prepared.Rotation)
            if:
                Prop := Spawned(0)?
                Spawned(1) = spawn_prop_result.Ok
                Prop.IsValid[]
            then:
                if (CommitSpawnTracking[Request, Prepared.HandleId, Prop]):
                    RemovedContext := GetAEONFALLPositionTargetingRuntime().Remove(Request.ContextId)
                    AEONFALLAdapterResultDelivery.Report(aeonfall_adapter_result{
                        RequestId := Request.RequestId,
                        OwnerKey := Request.OwnerKey,
                        AbilityId := Request.AbilityId,
                        AdapterId := Request.AdapterId,
                        Succeeded := true,
                        ResultCode := "ok"
                    })
                    return
                Prop.Dispose()
                set ResultCode = "spawn_tracking_or_status_failed"
            else:
                if (UnexpectedProp := Spawned(0)?):
                    if (UnexpectedProp.IsValid[]):
                        UnexpectedProp.Dispose()
                set ResultCode = NativeSpawnFailureCode(Spawned(1))
            Released := GetAEONFALLSpawnRuntime().Release(Prepared.HandleId, ResultCode)
        AEONFALLAdapterResultDelivery.Report(aeonfall_adapter_result{
            RequestId := Request.RequestId,
            OwnerKey := Request.OwnerKey,
            AbilityId := Request.AbilityId,
            AdapterId := Request.AdapterId,
            Succeeded := false,
            ResultCode := ResultCode
        })

    NativeSpawnFailureCode(Result:spawn_prop_result)<transacts>:string=
        if (Result = spawn_prop_result.InvalidAsset):
            return "native_invalid_asset"
        if (Result = spawn_prop_result.InvalidSpawnPoint):
            return "native_invalid_spawn_point"
        if (Result = spawn_prop_result.SpawnPointOutOfBounds):
            return "native_spawn_out_of_bounds"
        if (Result = spawn_prop_result.TooManyProps):
            return "native_prop_limit"
        "native_spawn_failed"

    PrepareSpawn(Request:aeonfall_ability_effect_request)<decides><transacts>:aeonfall_prepared_prop_spawn=
        Running?
        Enabled?
        ValidSettings()?
        PhysicalProps.Length < 64
        GetAEONFALLSpawnRuntime().Records.Length < 160
        Definition := GetAEONFALLAbilityRegistry().Get[Request.AbilityId]
        Definition.AdapterId = AdapterId
        Definition.TargetPolicy = aeonfall_target_policy.Position
        Definition.SpawnIds.Length = 1
        Definition.SpawnIds.Find[SpawnId]
        Context := GetAEONFALLPositionTargetingRuntime().Get[Request.ContextId]
        Context.OwnerKey = Request.OwnerKey
        Context.AbilityId = Request.AbilityId
        Owner := GetAEONFALLActorRegistry().GetAgent[Request.OwnerKey]
        Character := Owner.GetFortCharacter[]
        Character.IsActive[]
        Origin := Character.GetTransform().Translation
        Distance(Origin, Context.Position) >= MinimumDistanceCm
        Distance(Origin, Context.Position) <= MaximumDistanceCm

        var Position:vector3 = Context.Position
        if (ProjectToOwnerHeight?):
            set Position = vector3{
                X := Context.Position.X,
                Y := Context.Position.Y,
                Z := Origin.Z + VerticalOffsetCm
            }
        else:
            set Position = Position + vector3{Z := VerticalOffsetCm}
        # Validate the actual projected placement as well as the aim snapshot.
        Distance(Origin, Position) >= MinimumDistanceCm
        Distance(Origin, Position) <= MaximumDistanceCm
        Angles := Character.GetViewRotation().GetYawPitchRollDegrees()
        Yaw := Angles[0]
        Handle := GetAEONFALLSpawnRuntime().Reserve(
            Request.OwnerKey, Request.AbilityId, SpawnId, Request.ContextId,
            LifetimeSeconds, MaxPerOwner
        )?
        aeonfall_prepared_prop_spawn{
            HandleId := Handle,
            Position := Position,
            Rotation := MakeRotationFromYawPitchRollDegrees(Yaw, 0.0, 0.0)
        }

    # Canonical status changes and ownership tracking roll back together. A
    # failed commit is compensated by disposing the physical prop in OnRequest.
    CommitSpawnTracking(
        Request:aeonfall_ability_effect_request, Handle:string, Prop:creative_prop
    )<decides><transacts>:void=
        GetAEONFALLAbilityRuntime().IsCurrentEffectRequest(Request)?
        GetAEONFALLSpawnRuntime().Records[Handle]
        Prop.IsValid[]
        Definition := GetAEONFALLAbilityRegistry().Get[Request.AbilityId]
        GetAEONFALLStatusRuntime().ApplyBatch[
            Request.TargetKey, Definition.StatusIds, Request.OwnerKey, Request.Magnitude
        ]
        set PhysicalProps[Handle] = Prop
        Admitted := AEONFALLRuntimeBus.TryEmit(aeonfall_runtime_event{
            EventType := "spawn.physical_created",
            SourceId := Request.OwnerKey,
            TargetId := SpawnId,
            ContextId := Handle
        })
        Admitted?

    CleanupLoop()<suspends>:void=
        loop:
            Sleep(0.1)
            if (not Running?):
                return
            var Kept:[string]creative_prop = map{}
            for (Handle -> Prop : PhysicalProps):
                if:
                    Record := GetAEONFALLSpawnRuntime().Records[Handle]
                    Record.Active?
                    Record.RemainingSeconds > 0.0
                    Prop.IsValid[]
                then:
                    if (set Kept[Handle] = Prop):
                        set Kept = Kept
                    else:
                        Prop.Dispose()
                        Released := GetAEONFALLSpawnRuntime().Release(Handle, "tracking_failed")
                else:
                    if (Prop.IsValid[]):
                        Prop.Dispose()
                    Released := GetAEONFALLSpawnRuntime().Release(Handle, "physical_or_canonical_expired")
            set PhysicalProps = Kept

    OnEnd<override>():void=
        set Running = false
        StopEvent.Signal()
        if (Bound := Subscription?):
            Bound.Cancel()
        for (Handle -> Prop : PhysicalProps):
            if (Prop.IsValid[]):
                Prop.Dispose()
            Released := GetAEONFALLSpawnRuntime().Release(Handle, "adapter_ended")
        set PhysicalProps = map{}
        set Subscription = false
