using { /Verse.org/Verse }

# Small typed event envelope used to keep gameplay services decoupled.
# Canonical IDs remain strings so runtime actors can be rebound without
# changing persistent data or authored catalog identity.
aeonfall_runtime_event := class:
    EventType:string = ""
    SourceId:string = ""
    TargetId:string = ""
    ContextId:string = ""
    Amount:int = 0
    Flag:logic = false

aeonfall_event_bus := class():

    RuntimeEvent:event(aeonfall_runtime_event) = event(aeonfall_runtime_event){}

    Emit(Event:aeonfall_runtime_event):void=
        RuntimeEvent.Signal(Event)

# One shared session bus. Persistent state is NOT stored here; this only routes
# transient runtime signals between systems such as encounters, companions,
# status effects, abilities, shops, crafting, UI, and presentation.
AEONFALLRuntimeBus:aeonfall_event_bus = aeonfall_event_bus{}
