# AEONFALL — Performance Budget

## Non-Negotiable Constraint
The experience must be spectacular without exceeding Fortnite publication/runtime limits.

## Regional Budget Model
Each streamed region owns a budget envelope with four reserves:

1. **Baseline world**
   - terrain
   - buildings
   - static props
   - ordinary ambient audio/VFX

2. **Population**
   - wildlife
   - hostile mobs
   - hireables
   - faction agents

3. **Event reserve**
   - invasion actors
   - temporary structures
   - encounter VFX
   - event UI/audio

4. **Boss reserve**
   - boss body-region assets
   - weak points
   - boss hazards
   - cinematics
   - encounter-only props

A region that consumes all available headroom in baseline state is invalid even if it technically passes before events spawn.

## AI Concurrency Bands
These are design budgets, not engine guarantees.

- Ambient light AI: high count, simple behavior
- Standard combat AI: moderate count
- Elite AI: low count, richer behavior
- Mythic/God AI: very low count
- Absolute/Transcendent encounter logic: unique/serialized where possible

## Horde Rule
A "massive horde" is a layered illusion:
- active nearby agents
- pooled/recycled waves
- distant impostor crowds or environmental motion
- abstract regional population counters
- authored spawn fronts
- audio/VFX density

Do not attempt to keep the entire conceptual horde as fully simulated AI.

## VFX Bands
- low: ambient/standard repeated effects
- medium: elite repeated effects
- high: limited major abilities
- extreme: bosses, transformations, world events; strict concurrency and fallback required

Every extreme effect must define:
- max simultaneous instances
- distance culling
- simplified fallback
- cleanup trigger
- interrupted-state cleanup

## Animation Budget
High-tier entities may have bespoke locomotion/ability packages, but shared rigs and reusable motion layers should be used where visual identity permits.

## Streaming Policy
- World Partition enabled for large-world production.
- HLODs generated from sensible source LODs.
- Regions designed around cell locality.
- Avoid global references that force large assets to remain resident everywhere.
- Event assets should stream/activate only when required.

## Testing
For each production region:
- memory calculation
- worst-case event memory
- boss + squad + hireable stress test
- multiple-player separation stress test
- repeated spawn/despawn soak
- VFX cleanup audit
- NPC navigation audit
- persistence reconnect test
