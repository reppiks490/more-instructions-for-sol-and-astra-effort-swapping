# AEONFALL — Live Status

This file is generated from the canonical catalog by `tools/build_status.py`.

## Major Entity Catalog
**Target-counted authored entities: 288 / 800 (36.0%)**
**Additional major faction definitions: 8**
**All catalog entities: 296**

| Family | Specified | Target | Progress |
|---|---:|---:|---:|
| Weapons | 12 | 180 | 6.7% |
| Armor / major pieces | 4 | 120 | 3.3% |
| Monsters | 42 | 170 | 24.7% |
| Wildlife / tameables | 60 | 60 | 100.0% **(minimum met)** |
| Hireable / major NPCs | 64 | 60 | 106.7% **(minimum met)** |
| Bosses | 4 | 80 | 5.0% |
| Relics / artifacts | 45 | 45 | 100.0% **(minimum met)** |
| Vehicles / advanced variants | 25 | 25 | 100.0% **(minimum met)** |
| Classes / major skills | 30 | 30 | 100.0% **(minimum met)** |
| World events / special effects | 2 | 30 | 6.7% |
| **Target-counted total** | **288** | **800** | **36.0%** |

## Pipeline Status
- concept: 0
- specified: 296
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

## Production Boundary
Catalog specification is not equivalent to UEFN implementation.
The next implementation gates require the UEFN project, asset binding, Verse compilation, Launch Session testing, memory profiling, VFX/animation production, and balance passes.
