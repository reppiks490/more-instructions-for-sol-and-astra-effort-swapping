# AEONFALL — Living World Simulation

## Goal
Make the world feel continuously hostile, reactive, and populated without requiring every creature and conflict to exist as a fully simulated actor at all times.

## Three-State Population Model

### Abstract
Distant populations exist as lightweight records:
- faction
- region
- strength
- hunger/corruption
- elite chance
- current objective
- relationship state
- mutation pressure

### Materialized
When a player or major event enters relevance:
- spawn selected representatives
- resolve equipment/loadout
- resolve mutation/tier
- attach behavior package
- attach loot package
- activate VFX/audio only as needed

### Dormant
When actors leave relevance:
- preserve only meaningful state
- despawn or deactivate expensive actors
- return the region to abstract simulation

## Aggression Model
NPC hostility is not binary.

Suggested axes:
- territorial aggression
- hunger
- fear
- faction hatred
- corruption
- pack confidence
- injury
- player reputation
- taming pressure
- leader presence

NPCs can:
- stalk
- warn
- retreat
- ambush
- call reinforcements
- swarm
- protect young/territory
- frenzy
- surrender
- become tameable
- become hireable

## Taming
Taming is a state machine rather than an interaction prompt.

Example phases:
1. hostile
2. observing
3. weakened or impressed
4. trust opportunity
5. bonded
6. loyal
7. evolved companion

Taming methods vary by species:
- food
- rescue
- dominance trial
- shared combat
- relic resonance
- faction reputation
- rare ritual
- class affinity

## Horde Evolution
The original cannibal-zombie idea is replaced by a broader predatory necrotic ecology.

### Tier I — Riven
Fast, desperate scavenger-dead. Hunt in loose packs.

### Tier II — Carrionbound
Consume battlefield biomass and incorporate visible armor/bone traits from defeated creatures.

### Tier III — Choir-Fused
Multiple infected bodies form cooperative hunting organisms with shared sensory behavior.

### Tier IV — Grave Architects
Intelligent necrotic predators that build nests, traps, flesh barricades, and resurrection nodes.

### Tier V — Crowned Devourers
Rare apex organisms formed only when regional biomass/corruption thresholds are crossed. They lead hordes, mutate nearby undead, and can become minibosses.

## Necromancers
Necromancers are not simple summoners.

Archetypes:
- Bone Cartographers — reshape navigation lanes with skeletal structures
- Choir Mothers — coordinate horde senses
- Corpse Economists — trade health, corpses, and summons as resources
- Pale Astronomers — use celestial cycles to alter spawn tables
- Sepulcher Knights — combat necromancers with resurrection anchors
- Memory Eaters — steal player/NPC combat patterns for temporary mimic skills

## Eldritch Ecology
Eldritch creatures should violate normal monster expectations:
- attacks originate from geometry rather than bodies
- perception changes what attack pattern occurs
- weak points move between dimensions
- names/UI corrupt under specific phases
- arena topology changes in authored steps
- some attacks target objectives, light, sound, or navigation rather than health

## Demon Ecology
Demons have courts rather than one generic faction:
- Ash Court — pressure/heat and territory denial
- Brass Court — armored war demons and siege behavior
- Velvet Court — deception, charm-like aggro redirection, illusions
- Hollow Court — anti-healing and absence/void mechanics
- Red Choir — frenzy, sound attacks, group buffs

## Regional Director
Every region maintains:
- danger budget
- faction pressure
- horde pressure
- boss probability
- weather/event state
- available encounters
- cooldowns
- player heat
- corruption

The director chooses authored encounters from those constraints rather than purely random spawns.

## Performance Rule
No region should exceed its baseline AI/VFX budget except during a deliberately reserved event window.
