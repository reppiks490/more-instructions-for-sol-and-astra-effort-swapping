# Project-binding metadata for temporary spawned gameplay objects.
# Physical asset/prefab/device references intentionally live outside this core.

aeonfall_spawn_binding := class:
    SpawnId:string = ""
    RuntimeBindingId:string = ""
    MaxPerOwner:int = 1
    LifetimeSeconds:float = 10.0
    RequiresPositionContext:logic = false
    CleanupEventId:string = ""
