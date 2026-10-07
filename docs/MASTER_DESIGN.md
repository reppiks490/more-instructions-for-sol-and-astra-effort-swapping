# AEONFALL — Master Design

## Vision
AEONFALL is a maximalist open-world action-RPG/PvE experience built in UEFN. It combines large-scale exploration, faction systems, aggressive but potentially tameable NPCs, escalating monster ecologies, custom equipment, crafting, progression, raids, world events, and ultra-rare ascension systems.

## Design Pillars
1. Scale with density — enormous without becoming empty.
2. Escalating uniqueness — higher tiers gain new mechanics, silhouettes, VFX, animation language, audio, and encounter rules rather than simple stat inflation.
3. Living hostility — factions, wildlife, monsters, invasions, and bosses react to players.
4. Earned power — the strongest power is gated by mastery, trials, crafting, discovery, and long-term progression.
5. Readable insanity — extreme spectacle with clear combat telegraphs and counterplay.
6. Data-driven content factory — 800+ entities built from reusable systems plus unique modules.

## Tier Ladder
Common → Uncommon → Rare → Epic → Legendary → Mythic → Exotic → God → Absolute → Transcendent Zero

## Content Scope
The 800+ target covers original weapons, armor, artifacts, monsters, wildlife, hireables, bosses, vehicles, classes/skills, and world-event entities. Ordinary crafting materials and trivial consumables do not count toward the 800.

## Boss Scale
Massive bosses use distributed encounter architecture: shared boss state, destructible regions, attack controllers, environmental hazards, event scripting, VFX shells, and phase-based encounter spaces instead of one conventionally scaled NPC.

## Performance Rule
No system is complete until it has a streaming strategy, spawn/concurrency budget, VFX fallback/LOD plan, NPC activation/deactivation rules, replication assumptions, and failure recovery behavior.
