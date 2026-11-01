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


## REG-001 invasion admission and streaming contract

The first playable region reuses the existing invasion state machine and
NPC-spawn-group adapter; it does **not** create a second encounter director.
One invasion may be active per region. Starting one reserves its canonical
region event before committing the invasion state; a conflicting event or
another active invasion refuses admission without spawning. Only objective IDs
declared by the registered invasion can receive completion credit.

Every invasion wave must fit its declared `max_concurrent_ai` when the
`max_active` values of its distinct spawn groups are summed. The
REG-001 groups now reserve 6 grave scavengers, 4 necromancer supports,
10 ossuary siege actors, 10 brood actors, 6 null escorts, and 16
devouring precursors. The largest authored wave reserves 20 AI.
This is a **worst-case simultaneous event allocation**, not a requirement to
spawn the full count or an excuse to add permanent ambient actors.

For each `aeonfall_npc_spawn_group_adapter_device` in the UEFN editor:

- Set `RegionId = REG-001` and the exact canonical `SpawnGroupId`.
  Leave `StartDisabled = true` and `DespawnOnRelease = true`.
- Use **dedicated** NPC Spawners for this group. The aggregate native
  Spawn Count/live limit across those spawners must be at or below the
  group's `max_active`; no ambient, boss, hireable or other region may
  share them.
- Configure region-local player-relevance volumes and editor spawn
  distances so spawners cannot materialize distant AI. A queued event
  is not a streaming permission. Before enabling an invasion in the
  level, suppress ordinary ambient AI enough to preserve the regional
  event reserve; restore it on completion, failure and region unload.
- The adapter checks the registered active invasion, current wave,
  canonical region and group before enabling spawners. Wave release,
  completion, failure and device shutdown disable or despawn owned
  actors. No world-partition callbacks or native spawn-count enforcement
  are claimed by this source alone.

**UEFN acceptance:** verify a second same-region invasion is rejected,
foreign objective IDs do not score, cross-region or stale wave requests
cannot activate spawners, an invalid `RegionId` fails closed, each wave's
actual concurrent NPC count stays within its declared cap, and completion,
failure, unload and re-entry leave no orphan actors. Repeat with two
players separated across streaming cells. Use Spatial Profiler and cooked
memory evidence; the Python validator checks authored budgets only.

## REG-001 physical spawn ownership and lifecycle authorization

The invasion spawn-group adapter now acquires a **session-scoped exclusive
lease** before disabling or subscribing to any native NPC Spawner. At most one
adapter may own a `RegionId + SpawnGroupId` binding, and no physical NPC
Spawner may appear twice within one adapter or be shared between adapters,
even across different regions or spawn groups. An empty binding, zero spawners,
or `StartDisabled = false` is rejected without touching physical devices.
Rejected adapters do not disable or despawn another owner's NPCs during
shutdown. A lease is released only by its owner on device shutdown.

An event-bus message is never sufficient authorization to change native spawn
state. Spawn requests require the canonical invasion, current wave and region.
Wave release additionally requires a **later active wave that no longer contains
the group**; old delayed release messages cannot disable a group reused in the
current wave. Completion/failure notifications must match the authoritative
terminal state before releasing physical NPCs. A group present in consecutive
waves remains enabled without duplicate activation.

These guards protect ownership and lifecycle, **not streaming relevance**.
Keep the editor's NPC Spawn Count/live limit within the group cap, never share
spawners with ambient, boss, faction, hireable or wildlife systems, and bind
relevance/streaming gating in UEFN. Validate two competing adapters for one
group, two different groups sharing one NPC Spawner, delayed release messages,
normal completion/failure, and unload/re-entry with separated players.
Repository Python source guards cannot establish Verse compilation or actual
physical concurrency; both still require UEFN Launch Session evidence.

## Cross-director spawner ownership and corpse callback safety

Horde ecology and invasion spawn-group adapters now reject physical NPC
Spawners already leased by the other director family, **in either startup
order**. Existing per-region and per-group leases remain the authoritative
logical ownership records; the cross-check prevents two independent directors
from enabling, disabling, or despawning the same native device. Keep horde,
invasion, ambient, hireable, wildlife and boss NPC Spawners distinct in UEFN:
only the horde/invasion cross-family case is enforced in Verse so far.

Elimination callbacks create logical remains only while their ecology adapter
is running **and** the actor still has a registered death subscription and a
brood record belonging to that region. Late callbacks after pruning/unload
must not mint corpses or unregister a replacement actor. Apex trigger callbacks
are ignored after adapter shutdown. Corpse denial and feeding remain
exclusive and do not increase the authored AI reserves.

**Acceptance in UEFN:** place one invasion and one horde adapter pointing to
the same NPC Spawner, test both OnBegin orders, and verify only one acquires
ownership and the rejected adapter never touches the physical spawner.
Repeat with separate spawners and concurrent regions. Eliminate a brood actor
during shutdown/despawn and confirm no duplicate corpse, orphan brood record,
or leaked NPC remains. Native Verse compilation and multiplayer streaming
tests remain required; Python source guards do not establish those outcomes.

## Corpse-denial corruption counterplay (2026-11-01)

The existing horde corpse-use transaction now reconciles **canonical** regional
corruption before removing a corpse. This is a deterministic consequence, not a
new ecology director or another source of AI spawns:

| First successful corpse use | Corruption change | Interpretation |
| --- | ---: | --- |
| Burn | -2 | Destroy fuel for gravefeeding and necromancy. |
| Sanctify | -4 | Stronger cleansing at the same exclusive corpse token. |
| Necromancy | +5 | Reanimation pollutes the local region; counterplay is denial. |
| Harvest | 0 | Existing material/XP reward route; no corruption change. |

Changes clamp to the canonical 0–100 region range and immediately reconcile
existing hostility/mutation thresholds. If a registered region's runtime state
is not initialized, burn/sanctify/necromancy **fail closed** and leave the corpse
available. Unregistered test-only horde regions retain standalone corpse rules.
A corpse cannot be used twice; a rejected, expired, foreign, or previously
consumed corpse cannot modify corruption. A valid first use still emits its
existing `horde.corpse_*` event. No new persistent records, NPC spawners,
additional waves, or stat multipliers were added.

This makes corruption bands respond to player corpse denial and necromancer
success without forcing a fixed spawn count. An existing invasion can remain
active while pressure changes; native spawner allocation and streaming gates
are **not** overridden by corruption. UEFN acceptance must exercise both
sides of a threshold (19/20, 39/40, 59/60, 79/80, 94/95), simultaneous
attempts to claim one corpse, missing region initialization, and a region
unload during denial. Verify the physical corruption/biome presentation and
multiplayer replication in Launch Session. Python source guards are not a
native Verse compilation or runtime proof.
