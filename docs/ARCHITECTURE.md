# AEONFALL — Technical Architecture

## Objective
Build a modular UEFN/Verse game architecture that can support 800+ major authored entities without requiring 800 permanently loaded actors or 800 monolithic scripts.

## Runtime Layers
1. **Canonical Content Layer**
   - Permanent entity IDs and authored definitions.
   - Design-time source of truth lives in `content/catalog/`.
   - Every entity declares dependencies, rarity/tier, mechanics, VFX, animation, audio, acquisition, performance profile, and implementation state.

2. **Gameplay Systems Layer**
   - combat/status effects
   - classes and abilities
   - progression/mastery
   - crafting/refinement
   - factions/reputation
   - hiring/taming
   - boss encounters
   - world events
   - persistence
   - shops/economy
   - ascension/Transcendent Zero

3. **UEFN Integration Layer**
   - Scene Graph entities/components for custom items.
   - Custom Weapon Templates where supported.
   - NPC Character Definitions + Verse npc_behavior for authored NPC logic.
   - World Partition + Streaming + HLOD for large-world delivery.
   - Creative/UEFN devices where they are more stable or efficient than custom Verse.

4. **Presentation Layer**
   - HUD / menus / shops
   - animation state
   - VFX state
   - audio cues
   - boss telegraphs
   - world-event presentation

## Content Composition
Each major entity is composed from reusable modules plus bespoke overrides.

### Example weapon composition
- identity
- weapon template family
- base stat profile
- fire behavior
- signature mechanic
- status package
- evolution package
- VFX profile
- animation profile
- audio profile
- acquisition recipe
- rarity/tier
- performance class
- bespoke Verse component(s)

### Example NPC composition
- character definition
- faction
- disposition
- perception/aggression profile
- navigation profile
- combat kit
- tame/hire contract
- dialogue state
- loot state
- world-event hooks
- boss/elite state
- bespoke npc_behavior when needed

## Persistence Strategy
Use versioned persistable classes for player data so later fields can be added safely with defaults.

Persistent domains:
- account/profile version
- XP and level
- class mastery
- faction reputation
- discovered POIs
- boss clears
- trial clears
- crafting material ledger
- durable unlocks
- Zero Candidate state
- ascension state/history
- entitlement mirrors where permitted

Never couple persistent schemas directly to transient actor instances.

## World Population Strategy
The world must feel densely alive without keeping every creature active.

- **Abstract state:** distant encounters/factions exist as lightweight data.
- **Materialized state:** nearby or event-critical entities are spawned.
- **Dormant state:** entities outside relevance range retain only required state.
- **Event state:** raids/world bosses temporarily raise local concurrency budget.

## Boss Architecture
Skyscraper and continent-class bosses are distributed encounters:
- one authoritative encounter state machine
- multiple body/weak-point controllers
- local attack directors
- arena/environment controller
- add/minion director
- shared health/phase logic
- cinematic/VFX shell
- staged streaming activation

The visual creature may be enormous, while gameplay is divided into optimized attackable regions.

## Transcendent Zero Architecture
Core services:
- ZeroCandidateManager
- AscensionTrialDirector
- MaterialLedger
- AxiomForge
- ChoosingDirector
- TranscendentController
- AuthorityRuntime
- RealityEngineDirector
- AscendantRegistry

The tier is a temporary high-authority gameplay state layered over ordinary systems, not an uncontrolled bypass of core game rules.

## Performance Gates
Every entity must declare:
- expected concurrent instances
- streaming locality
- NPC tick/behavior intensity
- VFX complexity band
- animation complexity band
- replication intensity
- fallback/LOD behavior

Every region must define:
- baseline memory budget
- event headroom
- AI concurrency ceiling
- VFX concurrency ceiling
- boss activation reserve

## Current UEFN Guardrails
- Custom Items/Inventories and custom Weapon Templates are current UEFN/Scene Graph systems and should be treated as evolving platform features.
- Weapon templates currently cover four ranged families; mechanics outside those families must be simulated or built through other supported systems.
- World Partition/Streaming/HLOD are mandatory architectural tools for the intended world scale.
- Published streamed cells must remain within Fortnite's memory constraints.
