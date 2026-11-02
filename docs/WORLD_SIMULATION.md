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

## Corruption-gated Devouring Moon admission (2026-11-01)

The canonical invasion director now enforces the optional authored
`min_corruption` field **at admission**, in addition to hostility and its
existing single-invasion/region event reservation. The default is `0`, so
faction conflicts and other invasion profiles retain their prior admission
rules. REG-001's `INV-R001-005` (Devouring Moon Precursor) requires corruption
`>= 80`, matching the Tier V Crowned Devourer ecological gate. A region at
corruption 79 may still be hostile because of another event, but cannot start
the Devouring Moon encounter. At 80 the encounter is eligible, subject to its
existing hostility and event/AI-budget constraints. Sanctifying or burning
remains before admission can deny the encounter without stat inflation.

The gate is **not** an automatic cancellation of an invasion already active;
mid-event cleansing changes pressure but does not abruptly despawn objectives
or break wave progression. Invasion admission reads initialized canonical
region state and fails closed if that state is absent. `min_corruption` must be
an integer in 0..100, validated in authored JSON and Verse registry.
No new NPC Spawners, wave allocations, or director services are introduced.

**UEFN acceptance:** verify Devouring Moon is denied at corruption 79 even
when hostility is 4 or higher; allowed at 80 only when existing event admission
passes; and denied when region state is missing or another invasion is active.
Test cleansing from 80 to 76 before Start, and cleansing during an active wave.
Record actual physical AI counts, streaming transitions, and multiplayer
behavior separately; Python source tests are not native Verse compilation.

## Shared world-event transition integrity (source-level)

The shared `aeonfall_world_event_service` rejects empty event IDs and empty
objective IDs. Stage changes must advance from the active stage to **exactly
its immediate successor**; duplicate, rewind and jump requests fail closed.
Completion and failure both clear the active region set and turn off the event
before emitting the terminal notification. Only successful completion invokes
the registered reward pathway; failure clears encounter participation.

This is a structural and logical transition contract, **not** an engine
streaming/unloading implementation. A stage transition must still be authorized
by its canonical event director; the shared service does not yet verify an
objective against an authored per-stage registry. Native UEFN multiplayer
acceptance must attempt phase skips, repeated/late completion, disconnects,
and region unloading under world-event/boss contention. Capture Spatial
Profiler and Memory Snapshot data before declaring cleanup proven.

## Terminal invasion NPC cleanup contract (2026-11-01)

The canonical invasion runtime **already emits** `invasion.completed` and
`invasion.failed` terminal events. The owning spawn-group adapter validates
those events against canonical terminal state and requester ownership, then
disables its physical spawners. It must additionally call `DespawnAll(false)`
on **every** successfully owned terminal transition, including when the
editable `DespawnOnRelease` value is false. Device shutdown also enforces
unconditional owned-NPC despawn before releasing its physical lease. This is
important for non-retroactive ecology gates: a completed or failed encounter
must not leave unrelated physical pressure after its authorization ends.

`DespawnOnRelease` now controls **intermediate wave retirement only** (and
should remain enabled for production). It does not grant an exception to
terminal completion, failure, timeout, or adapter shutdown cleanup. A reused
spawn group in consecutive waves is not retired mid-wave. Rejected duplicate
adapters must not clean up another owner's NPCs. No additional event types,
spawners, encounter directors, or AI allocation were introduced.

**UEFN acceptance:** With `DespawnOnRelease = false`, finish and fail a live
invasion (including timeout) and confirm that all owned NPCs are physically
removed, not merely prevented from respawning. Repeat with a duplicate
adapter, two players in different streamed cells, and `OnEnd` during an active
wave. Confirm a rejected adapter cannot despawn a legitimate owner. Also
verify native Verse compilation; Python source checks cannot prove it.

## Mandatory wave-retirement despawn admission (2026-11-01)

An earlier physical adapter permitted `DespawnOnRelease = false` for an
intermediate invasion wave transition. This could allow outgoing NPCs to stay
alive after the new wave began: authored per-wave AI reserves are **not**
additive across waves. Every invasion spawn-group adapter now rejects that
configuration **before acquiring its ownership lease, touching spawners, or
subscribing to the event bus**. Set `DespawnOnRelease = true` in UEFN.

The property remains editable for compatibility with existing placed devices,
but **false is no longer an authorized production or test runtime setting**.
Canonical completion, failure and adapter shutdown continue to despawn owned
actors unconditionally; the earlier source fix still protects those paths.
Failed admission cannot clean up actors from a legitimate owner.

The project must still test actual native NPC counts (including a group shared
between consecutive waves), physical streaming unload/re-entry, two players
in separate cells and the no-spawn guarantee for a rejected adapter. The
`StartDisabled` and `DespawnOnRelease` properties are authoring declarations,
not evidence that physical NPC Spawner settings were read or enforced in Verse.

## Bounded cross-region world-event shells (2026-11-01)

World-scale events can continue as **abstract global state** without forcing
NPC bodies to stay loaded. The existing world-event state machine now limits
any *materialized stage footprint* to **four distinct regions**. Regions must
be valid in the canonical region registry and initialized in runtime state.
Empty footprints remain legal for cinematic/abstract phases, but grant no
physical region ownership. A stage with unknown, blank, duplicate, unloaded,
or too many region IDs is rejected **before** its stage index or region claims
can change. This prevents a world-scale event from silently treating the full
world as an active NPC spawn region.

The world-event session service now exposes the same one-service-per-session
pattern used by existing invasion and faction conflict services. Its footprint
claim checks active world-event owners as well as invasion and faction-war
activity; invasions and faction wars reciprocally check for an active
world-event claim. At most **one major battle/shell** among those three
families can own a region at a time. Different regions can run separate events.
Normal completion/failure clears the event's region footprint; advancing a
stage can change regions only after validation. A stage-local shell is a
logical ownership reservation, **not** a native AI-spawner, World Partition
load request or editor relevance guarantee.

**UEFN acceptance:** Register and initialize a test region before using it;
attempt abstract start with `array{}`, then one/four/five-region stage
footprints. Verify rejection at five, duplicates, unknown or uninitialized
regions. Start an invasion, war, then world event in every ordering and confirm
only the initial regional owner admits; unrelated regions must remain
independent. Advance a multiregion world event between cells, fail/complete it,
and verify leases and region claims are released without resurrecting physical
actors. Run with two separated clients and record native Verse compilation,
actual NPC counts, device ownership, streaming relevance and memory. The CI
source tests do not execute any of these engine operations.

## World-event shell trigger binding (2026-11-01)

The shared world-event service now exposes the *active* owning event ID for a
region, and an existing-bus subscriber maps canonical owner transitions to
region-local `RegionEntered`/`RegionReleased` UEFN trigger outputs. This is
not a new population director. It reuses `world_event.started`,
`stage_advanced`, `completed`, and `failed` events and periodically reads
authoritative session state so delayed, lost, or coalesced events do not
create permanent incorrect ownership. Entry is emitted once per owner change;
release precedes entry during handoff and fires on owned-device shutdown.

The editor must still gate any physical spawn requests through player
relevance, existing NPC spawner leases, authored caps, and cell teardown.
See [WORLD_EVENT_REGION_BINDING.md](WORLD_EVENT_REGION_BINDING.md) for wiring
and native two-player acceptance. Source tests do not establish physical
streaming, native Verse compilation or cooked memory correctness.
