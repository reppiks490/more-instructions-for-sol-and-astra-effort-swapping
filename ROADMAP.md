# AEONFALL — Execution Roadmap

## Gate 0 — Repository Foundation
- [x] dedicated clean repository
- [x] master design
- [x] tier system
- [x] 800-entity allocation
- [x] technical architecture
- [x] machine-validated content schema
- [x] CI catalog and crafting validation
- [x] canonical status dashboard

## Gate 1 — Core Runtime
- [x] canonical runtime content-index generator
- [x] canonical Verse content/entity registries and generated bootstrap data
- [ ] actual UEFN asset/prefab/Character Definition binding
- [x] typed runtime event bus scaffold
- [x] shared status-effect contract
- [x] shared ability/resource contract
- [x] two-phase ability activation/execution coordinator + publish-safe adapter bridges
- [ ] project-bound physical effect graphs for every declared adapter
- [x] boss encounter state machine scaffold
- [x] world-event state machine scaffold
- [x] cooldown / charge / meter / external-class / transformation resource runtime
- [x] progression service scaffold
- [x] persistent player profile
- [x] persistent profile service
- [x] material ledger
- [x] recipe/refinement graph specification + validation
- [x] faction/reputation service
- [x] Zero Candidate qualification scaffold

## Gate 2 — Vertical Slice
One production-quality region containing:
- [x] 12-monster slice manifest + Character Definition binding plan
- [ ] 12+ implemented/compiled monsters
- [x] 6-tameable slice manifest + Character Definition binding plan
- [ ] 6+ implemented/compiled tameables
- [x] 8-hireable slice manifest + Guard Character Definition binding plan
- [ ] 8+ implemented/compiled hireables
- [x] 12-weapon slice manifest + custom weapon template binding plan
- [ ] 12+ implemented/compiled custom weapons
- [x] 2-armor slice manifest + binding plan
- [ ] 2 implemented/compiled armor sets
- [x] first dungeon structure specified: The Ossuary Exchange
- [ ] dungeon built and Launch Session tested
- [x] 2 minibosses selected + encounter bindings specified
- [ ] 2 minibosses implemented/tested
- [x] major boss selected + encounter binding specified
- [ ] major boss implemented/tested
- [x] world event selected + director binding specified
- [ ] world event implemented/tested
- [x] atomic crafting transaction scaffold + validated first-slice recipes
- [x] crafting transaction + recipe-button runtime scaffold
- [ ] crafting UI/device placement and UEFN playtest
- [x] class resource/runtime loop + generated first-slice class bootstrap
- [ ] project-bound class ability effect graphs and UEFN playtest
- [ ] persistent progression compiled in UEFN
- [x] first shop specification: Grave Market Quartermaster
- [x] in-island shop offer + unlock-delivery runtime scaffold
- [ ] UEFN shop UI/device placement and any current-policy-compliant monetization integration
- [x] 13-region streamed world topology + event-shell architecture specified and CI validated
- [ ] Spatial Profiler / Memory Snapshot validation in bound UEFN project

## Gate 3 — Content Factory
- [x] authored entity schema
- [x] generator for status dashboards
- [x] canonical runtime content-index generator
- [x] first-slice Verse registration generator
- [ ] asset/VFX/animation checklists
- [ ] balance linting
- [x] duplicate-name / repeated-signature audit
- [ ] semantic duplicate-mechanic detection
- [x] tier-complexity validation

## Gate 4 — 800 Major Entities ✅
Current target-counted status: **832 / 800 (104.0%) — every original family minimum met**

Targets:
- Weapons: 180
- Armor/major pieces: 120
- Monsters/demons/eldritch/necromantic: 170
- Wildlife/tameables: 60
- Hireable/major NPCs: 60
- Bosses: 80
- Relics/artifacts: 45
- Vehicles/advanced variants: 25
- Classes/major skills: 30
- World-event/special-map-effect entities: 30

## Gate 5 — Living World
- [x] first-region faction conflict/territory runtime scaffold
- [x] first-region regional escalation runtime scaffold
- [x] shared companion + AI behavior contracts and first-slice binding matrix
- [x] taming + hiring execution runtimes and generated first-slice bootstraps
- [ ] UEFN Character Definition/NPC Spawner binding and playtest
- [x] world-event lifecycle contract
- [x] shared world-event state machine scaffold
- [x] invasion + spawn-group runtime scaffolds
- [ ] UEFN NPC spawner/device binding and soak test
- [x] five-tier cannibal horde evolution specified
- [x] necromancer ecosystem baseline specified
- [x] roaming mythic threat baseline specified
- [x] first-region faction conflict runtime scaffold
- [ ] regional mutation/corruption runtime

## Gate 6 — Endgame
- [x] God Form session runtime (45s active / 120s exhaustion) + 5 exact-ID world-bending abilities
- [x] Absolute Form session runtime (30s active / 240s exhaustion) + 5 exact-ID rule-bending abilities
- [x] Zero Candidate qualification specification/scaffold
- [x] 10 sequential Ascension Trials data/registry/runtime + canonical generator
- [x] Axiom Heart 68,420+ raw-acquisition crafting graph
- [x] one-time Choosing contract/runtime + persistent completion commit
- [x] Transcendent Zero session runtime with 8 Authorities / 24 exact-ID abilities / history gates
- [x] 8 canonical Authorities including Reality Engine specified, generated, registered, and adapter-covered
- [x] session Hall of Ascendants derived from connected players' persistent progression
- [x] 16-case transformation Launch Session acceptance matrix
- [ ] bind 34 God/Absolute/Transcendent effect graphs in UEFN and pass the transformation acceptance matrix

## Gate 7 — Production
- [ ] UEFN project binding
- [ ] Verse compile verification
- [ ] memory calculations
- [ ] spatial profiling
- [ ] console/platform validation
- [ ] persistence migration tests
- [ ] encounter soak tests
- [ ] balance passes
- [ ] accessibility/readability
- [ ] publication/compliance review

## Completion Rule
An entity is not production-ready because its name or concept exists. It must pass:
concept → specified → prototype → implemented → vfx_ready → animation_ready → tested → production.
