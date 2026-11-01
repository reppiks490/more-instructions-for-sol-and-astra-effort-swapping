# Horde runtime build brief

Continue AEONFALL's authored predatory ecology with executable session logic, preserving all existing catalog identities. This pass implements corpse denial, exclusive consumption, five evolution tiers, two readable mutation traits, and event-gated regional apexes. It does not claim authored NPC meshes or navigation exist.

## Rules

- Each runtime corpse receives a monotonic session ID; consumed/expired IDs cannot be reused.
- Corpse and brood records are bounded to 128 each. Corpses expire after 60 seconds. No persistent player schema changes.
- Biomass thresholds are 20, 60, 140, and 300. One feed advances at most one tier; accumulated biomass is retained.
- Tier III and above inherit at most two distinct traits from consumed remains.
- Tier V requires an open regional apex event, 600 consumed regional biomass, and no other living Tier V in that region. Denied promotion leaves biomass intact.
- Burn, sanctify, harvest, and necromancer use compete for the same corpse; only the first successful use removes it. Harvest signals an event, not an unverified persistent reward.
- Consumption is synchronous and validates consumer identity, region, capacity and corpse state before mutation. Physical range is checked by the project device, never inferred by the logical service.
- Unregistering an actor releases its brood record/apex slot. Regional shutdown clears corpses, brood, event eligibility, and cumulative biomass.

## Implementation plan

1. Add focused Verse contracts and session runtime under `verse/npcs/`; implement validation, record caps, corpse lifetime, feeding, traits, denial and cleanup.
2. Bind NPC spawner elimination and volume feeding through a Creative device, checking physical distance. Expose burn/sanctify interaction buttons with the same range rules. Emit promotion events for project-bound Character Definition/VFX adapters.
3. Wire the existing runtime scheduler and actor cleanup. Add a dev-only harness that calls the actual runtime for replay, expiry, cross-region, threshold, trait, apex and cleanup cases.
4. Protect lifecycle integration and harness coverage in repository validation; run the existing validation and generator drift checks. Deliver a review branch with compilation and physical mutation explicitly pending UEFN.

## Validation evidence

The existing repository validation commands and the horde integration guard run in Linux. The guard checks lifecycle wiring and acceptance coverage; it does not execute Verse. The dev harness exercises actual Verse services when compiled and enabled in UEFN, with results logged as `HORDE RESULT`. Physical evolution triggers must be bound to authored effects; no appearance/animation change is implied by promotion alone.

## UEFN acceptance

Compile with the existing flat-module layout. Place one runtime tick device, one horde ecology adapter per region, and the dev harness in a private test level. Bind the spawner to valid Character Definitions, feed volumes to NPC-capable zones, and denial buttons to world-space interaction. Run the harness, then test simultaneous consumption, corpse expiration, elimination, region unload, presentation changes, navigation, multiplayer replication and memory. A promotion event alone does not transform a physical NPC.


## Physical spawner and identity admission (2026-11-01)

The horde ecology adapter now refuses to start unless its region and canonical
NPC ID are set, `StartDisabled` is true, feeding range is positive, and its
configured corpse biomass is within the current runtime policy (1 through
`CrownedBiomass`). It obtains exclusive spawner ownership, registers the region,
and subscribes to spawn/death inputs **before** calling `Spawner.Enable()`.
The editable flag is only an authoring assertion: the actual NPC Spawner must
be set to **Spawn Character at Game Start = False**, with physical NPC limits
and streaming behavior independently verified in UEFN. A duplicate/rejected
adapter must never disable a spawner owned by another director.

NPC lifecycle behavior may register an actor before the ecology adapter sees its
spawn event. In that case, the adapter reuses the runtime key only when the
registry's canonical ID matches its configured `CanonicalId`. It does not
unregister a lifecycle-owned key on shutdown. Delayed elimination callbacks
recheck canonical identity as well as brood membership before creating remains.
This closes cross-species biomass attribution without introducing a new actor
registry, a second encounter director, extra NPCs, or stat scaling.

Regression: `python -m unittest tests/test_horde_binding_guards.py`. The source
checks do not prove Verse compilation, physical NPC caps, editor start settings,
streaming-cell unload behavior, or multiplayer elimination ordering; those remain
Launch Session acceptance gates.
