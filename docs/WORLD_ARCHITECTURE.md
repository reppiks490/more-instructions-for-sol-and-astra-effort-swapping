# AEONFALL — World Architecture

## Objective
Build the largest *dense, publishable, multiplayer-safe* world AEONFALL can sustain in UEFN, rather than chasing empty surface area.

## Verified UEFN Constraints
- UEFN Landscape resolution is currently capped at 2048 × 2048 vertices or an equivalent rectangle.
- World Partition automatically divides the world into streamable cells.
- UEFN prompts creators to enable Streaming when the island exceeds 1 km on its widest axis.
- Current streamed-location publication memory must remain below 100,000 memory units.
- HLOD is required strategically so large structures remain visible at distance without full-detail residency.
- Some assets/devices remain globally resident; these must be kept intentionally scarce.
- A custom Data Layer + Sequencer streaming trick may help specific single-player spaces, but Epic documents that approach as not multiplayer-compatible. AEONFALL will not depend on it for core multiplayer world streaming.

## Initial Physical Target
Start with one maximum-resolution primary Landscape and tune XY scale to target an approximately 4 km × 4 km surface envelope while retaining acceptable terrain fidelity.

This is a **design target, not a publication guarantee**. Final XY scale, cell sizing, loading range, and usable extents must be decided after:
1. actual UEFN heightfield import,
2. HLOD generation,
3. cooked memory calculation,
4. Spatial Profiler passes,
5. console/mobile playtests.

The world gains effective scale through verticality and layered spaces rather than only increasing terrain meters:
- surface wilderness/cities
- underground megadungeons
- cliff and mountain interiors
- elevated citadels / sky traversal
- ocean and abyssal encounter spaces
- mirror/dimensional pockets
- temporary world-event spaces

## Macro Layout
Sixteen primary regions form a connected 4×4 macro lattice. Borders overlap ecologically so transitions feel natural rather than like separate maps.

### R01 — THRONEFALL NECROPOLIS
A ruined imperial capital built over an active royal ossuary. Walking grave districts, rebel fortifications, throne cults, and sovereign boss infrastructure.

### R02 — VESPERGLASS MERIDIAN
Mirror desert and black-glass canyon system where reflections become traversal anchors, ambush routes, and dimensional doors.

### R03 — THE CROWN OF UNSTORM
High mountain weather kingdom beneath permanent rotating cloud architecture. Storm fauna, aerial predators, observatories, and sky-forges.

### R04 — RED ORCHARD OF SAINTLESS BLOOM
Gigantic predatory forest whose trees grow from old battlefields. Living weapons, Gravefeeding overlap, hostile botanical architecture.

### R05 — THE THIRTEEN-TIDE CATHEDRAL
Coastal megastructure descending from cliffs into abyssal trenches. Leviathans, drowned fleets, pressure vaults, and moving sea temples.

### R06 — GLOAMFORGE MEGALITH
Industrial infernal metropolis carved through a volcanic plate. Demon courts, machine foundries, rail systems, furnace wildlife, and siege engines.

### R07 — HOLLOW ASTRAL SYNOD
Cratered celestial observatory nation where fallen stars, artificial suns, and cosmic religions compete for the same sky machinery.

### R08 — MAW-COURT EXPANSE
A savage badland ecosystem dominated by the evolving Gravefeeding chain. Nests can grow into mobile settlements and, during catastrophe states, Saint Devourer territory.

### R09 — WORLDROOT SOVEREIGNTY
Ancient vertical forest whose root systems form cities, tunnels, bridges, shrines, and tameable wildlife habitats across several elevations.

### R10 — THE BLACKWAKE DOMINION
Floodplain of drowned roads, stranded warships, spectral canals, moving black-water routes, and Grave Tide factions.

### R11 — COURT OF BROKEN HOURS
Temporal ruin-zone where architecture from several ages overlaps. Chronarch trials, sequence puzzles, and time-themed boss apparatus.

### R12 — THE OSSUARY CROWN
Necromancer state built from stacked catacombs, bone railways, corpse gardens, research monasteries, and mobile funeral infrastructure.

### R13 — NIGHT BEFORE CREATION
An eldritch wasteland of negative-space structures, buried eyes, horizon predators, and areas whose geometry appears unfinished.

### R14 — STARFALL RELIQUARY
High desert/mesa region littered with celestial impacts, giant star-metal carcasses, relic forges, pilgrimage roads, and dangerous radiant fauna.

### R15 — THE THOUSAND DOORS
Dense transdimensional city whose alleys contain rotating pocket encounters, secret vendors, faction embassies, puzzle houses, and false safe zones.

### R16 — AXIOM SCAR
Endgame region surrounding the remains of a failed reality experiment. God/Absolute content, Ascension Trials, Axiom Forge access, and hidden Zero-candidate infrastructure.

## Hidden / Layered World
The sixteen regions are the visible macro-world. They do not include:
- abyssal raid trenches,
- fortress interiors,
- underworld necropolises,
- mirror layers,
- candidate-only Zero Echo spaces,
- boss-body traversal maps,
- moving world-event structures,
- temporary Genesis Storm creations.

These increase playable area without requiring the entire content set to remain resident.

## World Partition Policy
- Streaming ON from the beginning.
- Begin with Epic's default World Partition parameters because they are optimized for Fortnite BR-sized worlds.
- Tune cell/loading ranges only from measured memory and traversal behavior.
- Use Is Spatially Loaded wherever compatible.
- Avoid globally resident references to high-cost meshes/textures/devices.
- Build HLODs from proper source LODs; never rely on full-resolution custom assets as HLOD source.
- Dense interiors should have strong occlusion and short sightlines where possible.
- Event content materializes only in relevant regions.

## Internal Memory Budget
The official publication ceiling is 100,000 units at any location. AEONFALL targets a lower internal ceiling:

- 70,000 baseline region target
- 15,000 dynamic encounter/event reserve
- 10,000 boss/cinematic reserve
- 5,000 emergency headroom

This is an engineering target, not an Epic-defined allocation.

If a region exceeds baseline:
1. reduce always-loaded references,
2. replace unique meshes with instanced modular kits,
3. improve texture streaming/mips,
4. improve source LODs/HLODs,
5. reduce concurrent VFX/device sets,
6. abstract distant AI,
7. move optional content behind event activation.

## AI Population Model
The map can contain hundreds of *authored species/NPC definitions* without hundreds of live AI everywhere.

Population states:
- **abstract** — distant ecology/faction exists as data only,
- **dormant** — spawn anchors and lightweight state are present,
- **materialized** — nearby combat actors are live,
- **event surge** — temporary higher local concurrency,
- **raid reserve** — ordinary local populations are reduced while a major boss consumes the AI/VFX budget.

## Colossal Boss Rule
Skyscraper/continent-class presentation is distributed:
- global encounter brain,
- streamed visual shell,
- attack-region controllers,
- weak-point actors,
- objective actors,
- local damage volumes,
- VFX/audio layers,
- add director,
- phase state.

A giant boss is never implemented as one absurdly scaled ordinary NPC.

## Immersion Rule
Every macro-region needs:
- recognizable distant silhouette,
- unique weather/light behavior,
- traversal identity,
- hostile ecology,
- neutral/tameable ecology,
- faction presence,
- safe/social anchor,
- dungeon/stronghold,
- at least one rare event,
- at least one roaming apex threat,
- bespoke soundscape,
- night-state differences,
- HLOD silhouette plan.

## Production Gate
No macro-region can be called implemented until it has passed:
- Landscape/mesh blockout
- streaming grid validation
- baseline memory calculation
- HLOD build
- Spatial Profiler traversal pass
- AI concurrency test
- event surge test
- major boss reserve test
- minimum-spec platform playtest
