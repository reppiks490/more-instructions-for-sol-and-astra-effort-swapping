# AEONFALL — Live Status

This file is generated from the canonical catalog by `tools/build_status.py`.

## Major Entity Catalog
**Target-counted authored entities: 684 / 800 (85.5%)**
**Additional major faction definitions: 8**
**All catalog entities: 692**

| Family | Specified | Target | Progress |
|---|---:|---:|---:|
| Weapons | 120 | 180 | 66.7% |
| Armor / major pieces | 100 | 120 | 83.3% |
| Monsters | 114 | 170 | 67.1% |
| Wildlife / tameables | 60 | 60 | 100.0% **(minimum met)** |
| Hireable / major NPCs | 64 | 60 | 106.7% **(minimum met)** |
| Bosses | 68 | 80 | 85.0% |
| Relics / artifacts | 45 | 45 | 100.0% **(minimum met)** |
| Vehicles / advanced variants | 25 | 25 | 100.0% **(minimum met)** |
| Classes / major skills | 30 | 30 | 100.0% **(minimum met)** |
| World events / special effects | 58 | 30 | 193.3% **(minimum met)** |
| **Target-counted total** | **684** | **800** | **85.5%** |

## Pipeline Status
- concept: 0
- specified: 692
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
- canonical ID uniqueness: **passing in GitHub Actions**
- canonical dependency existence: enforced by CI
- declared per-wave entity counts: enforced by CI
- tier depth / presentation requirements: enforced by CI
- Axiom Heart crafting graph: validated independently and in unified CI
- Axiom Heart recursive raw acquisition burden: **68,420**
- status dashboard generation: available through `tools/build_status.py`

## Current Milestone
- 684 / 800 target-counted major entities authored.
- 692 total major definitions including factions.
- latest Wave 017 validation: **success**.
- persistent profile, material ledger, progression, faction reputation, Zero Candidate, and Ascension gate scaffolds exist in Verse.
- five-stage cannibal horde, necromancer ecology, eldritch, infernal, mythical, skyscraper-class, continent-class, Absolute, and Transcendent content are represented.

## Remaining Under-Target Families
- Weapons: 60 remaining to minimum target
- Armor: 20 remaining
- Monsters: 56 remaining
- Bosses: 12 remaining

Meeting every family minimum will intentionally take the catalog beyond 800 because hireables and world events already exceed their original minimum allocations.

## Production Boundary
Catalog specification is not equivalent to UEFN implementation.
Final implementation requires the UEFN project, asset binding, Verse compilation, Launch Session testing, memory profiling, VFX/animation production, and balance passes.
