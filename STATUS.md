# AEONFALL — Live Status

This file is generated from the canonical catalog by `tools/build_status.py`.

## Major Entity Catalog
**Target-counted authored entities: 400 / 800 (50.0%)**
**Additional major faction definitions: 8**
**All catalog entities: 408**

| Family | Specified | Target | Progress |
|---|---:|---:|---:|
| Weapons | 36 | 180 | 20.0% |
| Armor / major pieces | 28 | 120 | 23.3% |
| Monsters | 66 | 170 | 38.8% |
| Wildlife / tameables | 60 | 60 | 100.0% **(minimum met)** |
| Hireable / major NPCs | 64 | 60 | 106.7% **(minimum met)** |
| Bosses | 36 | 80 | 45.0% |
| Relics / artifacts | 45 | 45 | 100.0% **(minimum met)** |
| Vehicles / advanced variants | 25 | 25 | 100.0% **(minimum met)** |
| Classes / major skills | 30 | 30 | 100.0% **(minimum met)** |
| World events / special effects | 10 | 30 | 33.3% |
| **Target-counted total** | **400** | **800** | **50.0%** |

## Pipeline Status
- concept: 0
- specified: 408
- prototype: 0
- implemented: 0
- vfx_ready: 0
- animation_ready: 0
- tested: 0
- production: 0

## Premium-Designated Concepts
- 6 catalog entities currently carry `acquisition.paid=true`.
- Premium designation is a design flag only; implementation must use Epic-supported entitlement/transaction systems and publication rules.

## Integrity Gates
- canonical ID uniqueness: enforced by CI
- canonical dependency existence: enforced by CI
- declared per-wave entity counts: enforced by CI
- tier depth / presentation requirements: enforced by CI
- status dashboard freshness: enforced by CI

## Current Milestone
- 50% of the 800-major-entity authoring target is now specified.
- Five-stage cannibal horde evolution is authored through Crowned Hunger.
- Necromancer, eldritch, infernal, mythical, skyscraper-class, continent-class, Absolute, and Transcendent encounter concepts are represented in the catalog.
- Next bottlenecks: weapons, armor, monsters, bosses, and world events.

## Production Boundary
Catalog specification is not equivalent to UEFN implementation.
The next implementation gates require the UEFN project, asset binding, Verse compilation, Launch Session testing, memory profiling, VFX/animation production, and balance passes.
