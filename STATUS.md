# AEONFALL — Live Status

This file is generated from the canonical catalog by `tools/build_status.py`.

## Major Entity Catalog
**Target-counted authored entities: 832 / 800 (104.0%)**
**Additional major faction definitions: 8**
**All catalog entities: 840**

| Family | Specified | Target | Progress |
|---|---:|---:|---:|
| Weapons | 180 | 180 | 100.0% **(minimum met)** |
| Armor / major pieces | 120 | 120 | 100.0% **(minimum met)** |
| Monsters | 170 | 170 | 100.0% **(minimum met)** |
| Wildlife / tameables | 60 | 60 | 100.0% **(minimum met)** |
| Hireable / major NPCs | 64 | 60 | 106.7% **(minimum met)** |
| Bosses | 80 | 80 | 100.0% **(minimum met)** |
| Relics / artifacts | 45 | 45 | 100.0% **(minimum met)** |
| Vehicles / advanced variants | 25 | 25 | 100.0% **(minimum met)** |
| Classes / major skills | 30 | 30 | 100.0% **(minimum met)** |
| World events / special effects | 58 | 30 | 193.3% **(minimum met)** |
| **Target-counted total** | **832** | **800** | **104.0%** |

## Pipeline Status
- concept: 0
- specified: 840
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
- normalized-name and repeated-signature diversity audit: enforced by CI
- runtime content index generation: executed by CI
- original family minimums: protected by `tools/validate_quotas.py`
- Axiom Heart crafting graph: validated independently and in unified CI
- Axiom Heart recursive raw acquisition burden: **68,420**

## Current Milestone
- **All original 800-entity family minimums are met.**
- 832 target-counted major entities are specified, with intentional overage in hireables and world events.
- 840 total major definitions including factions.
- Wave 019: validation success.
- Wave 020: validation success.
- core persistence, progression, material ledger, faction reputation, Zero Candidate, Ascension gate, boss contract, world-event contract, and companion contract scaffolds exist in Verse.
- five-stage cannibal horde, necromancer ecology, eldritch, infernal, mythical, skyscraper-class, continent-class, God, Absolute, and Transcendent Zero content are represented.

## Next Production Priority
Quantity is no longer the bottleneck. The priority is now:
1. core runtime services and data binding;
2. one complete vertical-slice region;
3. UEFN asset/device/Scene Graph binding;
4. Verse compile + Launch Session verification;
5. VFX/animation/audio production and optimization;
6. encounter, persistence, balance, accessibility, and platform validation.

## Production Boundary
Catalog specification is not equivalent to a finished Fortnite island.
Final implementation requires the actual UEFN project, project-specific asset references, generated digests, Verse compilation, Launch Session testing, memory calculations, spatial profiling, VFX/animation production, balance passes, and Epic publication/compliance review.
