# AEONFALL — UEFN Capability Matrix

This file prevents design language from drifting beyond implementable platform behavior.

## Directly Supported Foundations

### Custom items and inventories
Use Scene Graph item/inventory components plus Verse-authored behavior for AEONFALL-specific equipment, materials, relics, and inventory rules.

**Project policy:** treat the current custom item/inventory feature set as platform-evolving. Build adapters so gameplay logic is not inseparable from one experimental API shape.

### Custom ranged weapons
Current UEFN Weapon Templates provide customizable ranged weapon foundations for:
- assault rifle
- submachine gun
- pistol
- shotgun

Custom meshes, damage/range/fire behavior, icons/descriptions, rarity presentation, and Verse components can be layered on top.

**Project policy:** AEONFALL weapons may use these templates as firing foundations while signature mechanics remain modular Verse/gameplay systems.

### Custom NPC behavior
NPC Character Definitions and Verse npc_behavior support custom NPC logic. Guard/wildlife foundations can also provide perception, alertness, hiring, and taming features where appropriate.

**Project policy:** do not author one massive universal AI. Use behavior families:
- predator
- pack
- caster
- commander
- hireable
- tameable
- elite
- boss part
- encounter director

### Persistent player progression
Verse persistable weak maps support per-player progression across sessions.

**Project policy:** use versioned persistable classes with defaults so future fields can be added safely.

### Large worlds
World Partition, Streaming, and HLODs support large experiences by loading world cells around players.

**Project policy:** all large regions must be designed for streaming from day one.

## Must Be Simulated / Authored Rather Than Literally Engine-Rewritten

These AEONFALL concepts are design goals whose effects must be built from supported systems:
- "turn gravity off for the world"
- "rewind reality"
- "continent-sized AI actor"
- "freeze every projectile globally"
- "rewrite death"
- "change universal engine rules"

Implementation pattern:
1. bound the effect to an authored encounter region;
2. identify affected agents/entities;
3. reproduce the intended player experience with supported movement, teleportation, impulses, VFX, damage, status, spawn, environment, and device logic;
4. protect critical boss/quest state from undefined transitions;
5. provide readable telegraphs and recovery paths.

## Distributed Colossus Rule
A continent-class boss is not one ordinary NPC scaled to absurd size.

Use:
- distant visual shell
- encounter-state brain
- local body-region arenas
- synchronized health/phase state
- separately streamed hazards
- authored traversal
- cinematic transitions
- multi-squad objectives

## Publication Safety Gates
No feature is considered production-ready until:
- UEFN compiles the Verse;
- Launch Session passes;
- persistence compatibility passes;
- memory calculation passes every relevant cell;
- Spatial Profiler validates runtime behavior;
- platform-specific playtests pass.
