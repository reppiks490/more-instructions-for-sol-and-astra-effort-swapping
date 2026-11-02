using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Verse }

# The existing world-event service owns region admission. This adapter only
# translates canonical changes into editor-bound trigger outputs. It creates
# no NPCs and is not a World Partition or player-relevance controller.
var AEONFALLWorldEventRegionBindings:weak_map(session, [string]aeonfall_world_event_region_binding_device) = map{}

aeonfall_world_event_region_binding_device := class(creative_device):
    @editable
    RegionId:string = ""

    # Bind to existing streamed-region presentation / encounter adapters.
    # Entry and release must not point at the same physical trigger device.
    @editable
    RegionEntered:trigger_device = trigger_device{}
    @editable
    RegionReleased:trigger_device = trigger_device{}

    var Running:logic = false
    var OwnsLease:logic = false
    var ActiveEventId:string = ""
    var Subscription:?cancelable = false

    OnBegin<override>()<suspends>:void=
        # The world registry and region bootstrap must already be initialized.
        # Invalid or duplicate adapters never fire another owner's outputs.
        if:
            RegionId <> ""
            GetAEONFALLRegionRegistry().IsRegistered[RegionId]
            GetAEONFALLRegionRuntime().GetState[RegionId]
            RegionEntered <> RegionReleased
        then:
            Leased := AcquireLease()
            if (not Leased?):
                Print("AEONFALL world-event region binding rejected duplicate owner.")
                return
        else:
            Print("AEONFALL world-event region binding rejected uninitialized/invalid region.")
            return

        set OwnsLease = true
        set Running = true
        Bound := AEONFALLRuntimeBus.RuntimeEvent.Subscribe(OnRuntimeEvent)
        set Subscription = option{Bound}
        ReconcileRegion()

        # Runtime events can be coalesced or overflow the bounded queue.
        # Periodic reconciliation consults current session state instead of
        # replaying stale event payloads or repeating unchanged triggers.
        loop:
            Sleep(1.0)
            if (not Running?):
                return
            ReconcileRegion()

    AcquireLease()<transacts>:logic=
        var Owners:[string]aeonfall_world_event_region_binding_device = map{}
        if (Current := AEONFALLWorldEventRegionBindings[GetSession()]):
            set Owners = Current
        if (Owners[RegionId]):
            return false
        if (Owners.Length >= 32):
            return false
        if:
            set Owners[RegionId] = Self
            set AEONFALLWorldEventRegionBindings[GetSession()] = Owners
        then:
            return true
        false

    ReleaseLease()<transacts>:logic=
        if:
            Owners := AEONFALLWorldEventRegionBindings[GetSession()]
            Owners[RegionId] = Self
        then:
            var Kept:[string]aeonfall_world_event_region_binding_device = map{}
            var Valid:logic = true
            for (OtherRegion -> Adapter : Owners):
                if (OtherRegion <> RegionId):
                    if (set Kept[OtherRegion] = Adapter):
                        set Kept = Kept
                    else:
                        set Valid = false
            if (Valid?, set AEONFALLWorldEventRegionBindings[GetSession()] = Kept):
                return true
        false

    ReconcileRegion():void=
        if (not Running? or not OwnsLease?):
            return
        DesiredEventId:string = GetAEONFALLWorldEventRuntime().ActiveEventForRegion(RegionId)
        if (DesiredEventId = ActiveEventId):
            return

        # Release the old owner first. Triggers are notifications, not direct
        # spawner commands; attached UEFN physical devices must enforce their
        # own relevance, exclusive ownership, budget and teardown policy.
        if (ActiveEventId <> ""):
            set ActiveEventId = ""
            RegionReleased.Trigger()

        if (DesiredEventId <> ""):
            set ActiveEventId = DesiredEventId
            RegionEntered.Trigger()

    OnRuntimeEvent(Event:aeonfall_runtime_event):void=
        if (not Running?):
            return
        # Four existing event types provide all footprint transition signals.
        # Event.SourceId is deliberately *not* treated as authority; read the
        # current canonical state to survive late/reordered notifications.
        if:
            (
                Event.EventType = "world_event.started"
                or Event.EventType = "world_event.stage_advanced"
                or Event.EventType = "world_event.completed"
                or Event.EventType = "world_event.failed"
            )
        then:
            ReconcileRegion()

    OnEnd<override>():void=
        if (not OwnsLease?):
            return
        set Running = false
        if (Bound := Subscription?):
            Bound.Cancel()
        set Subscription = false
        if (ActiveEventId <> ""):
            set ActiveEventId = ""
            RegionReleased.Trigger()
        Released := ReleaseLease()
        set OwnsLease = false
