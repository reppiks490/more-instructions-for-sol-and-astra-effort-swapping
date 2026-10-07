# AEONFALL — UEFN Platform Contract

This document captures the current platform assumptions AEONFALL is allowed to rely on.

## Custom NPCs
Epic currently exposes custom NPC behavior through Verse `npc_behavior`.
NPC behavior scripts are attached to NPC Character Definitions or NPC Spawners.

Guard and wildlife character types retain useful native behavior surfaces:
- guard perception/alertness
- guard hiring
- wildlife taming
- navigation support

Custom NPC types can use authored Verse behavior, but weapon/equipment capabilities differ by character type and must be validated in UEFN before committing a design.

Official reference:
https://dev.epicgames.com/documentation/fortnite/create-custom-npc-behavior-in-unreal-editor-for-fortnite

## Custom Items / Inventories
Custom Items and Inventories are available through Scene Graph + Verse and are currently a Beta/experimental platform area.

AEONFALL rule:
- abstract item logic behind project-owned services
- avoid hard-coupling the entire game to one unstable beta API surface
- retain migration adapters for item definitions and inventory persistence

Official reference:
https://dev.epicgames.com/documentation/en-us/fortnite/custom-items-and-inventory-overview-in-fortnite

## Custom Weapons
Current official Weapon Templates provide these ranged families:
- assault rifle
- sub machine gun
- pistol
- shotgun

Templates can be subclassed/modified and their meshes can be replaced.
Custom weapon behavior should be layered through supported Scene Graph/Verse components.

Current compatibility warning:
Custom Weapon Templates are incompatible with the First Person Camera Device.

Official reference:
https://dev.epicgames.com/documentation/fortnite/weapon-templates-in-fortnite

## Persistence
Persistent per-player Verse state uses module-scoped `weak_map(player, T)`.

Important current constraints:
- persistable classes must be `final` + `persistable`
- persistable classes cannot contain mutable `var` members
- classes are the preferred persistent value type because fields with defaults can be added later
- player records have an approximate 256 KB limit
- use `FitsInPlayerMap` when growing dynamic persisted data
- an island can have up to four persistent player weak maps

AEONFALL rule:
Use one primary versioned profile class and keep catalog definitions outside player persistence.

Official references:
https://dev.epicgames.com/documentation/fortnite/using-persistable-data-in-verse
https://dev.epicgames.com/documentation/fortnite/verse-persistence-best-practices

## Scale
AEONFALL must treat spectacle and simulation as streamed/runtime-managed systems:
- World Partition
- Streaming
- HLOD
- relevance-based NPC materialization
- VFX LOD
- event-local concurrency reserves

## Implementation Policy
A design can be fantastical.
An implementation contract cannot be fictional.

If UEFN cannot literally expose a requested engine function, AEONFALL must reproduce the gameplay fantasy through supported movement, devices, Scene Graph, VFX, damage, navigation, state machines, and authored encounter transitions.
