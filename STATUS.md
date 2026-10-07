# AEONFALL — Live Status

This file is generated from the canonical catalog by `tools/build_status.py`.

## Major Entity Catalog
**Target-counted authored entities: 624 / 800 (78.0%)**
**Additional major faction definitions: 8**
**All catalog entities: 632**

| Family | Specified | Target | Progress |
|---|---:|---:|---:|
| Weapons | 96 | 180 | 53.3% |
| Armor / major pieces | 88 | 120 | 73.3% |
| Monsters | 96 | 170 | 56.5% |
| Wildlife / tameables | 60 | 60 | 100.0% **(minimum met)** |
| Hireable / major NPCs | 64 | 60 | 106.7% **(minimum met)** |
| Bosses | 62 | 80 | 77.5% |
| Relics / artifacts | 45 | 45 | 100.0% **(minimum met)** |
| Vehicles / advanced variants | 25 | 25 | 100.0% **(minimum met)** |
| Classes / major skills | 30 | 30 | 100.0% **(minimum met)** |
| World events / special effects | 58 | 30 | 193.3% **(minimum met)** |
| **Target-counted total** | **624** | **800** | **78.0%** |

## Pipeline Status
- concept: 0
- specified: 632
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
- 624 / 800 target-counted major entities authored.
- 632 total major definitions including factions.
- five-stage cannibal horde evolution authored.
- necromancer, eldritch, infernal, mythical, skyscraper-class, continent-class, Absolute, and Transcendent encounter concepts represented.
- persistent profile, material ledger, progression, faction reputation, Zero Candidate, and Ascension gate scaffolds exist in Verse.
- latest catalog validation run: **success**.

## Remaining Under-Target Families
- Weapons: 84 remaining to minimum target
- Armor: 32 remaining
- Monsters: 74 remaining
- Bosses: 18 remaining

## Production Boundary
Catalog specification is not equivalent to UEFN implementation.
Final implementation requires the UEFN project, asset binding, Verse compilation, Launch Session testing, memory profiling, VFX/animation production, and balance passes.
