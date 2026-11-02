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

## Canonical apex corruption admission (2026-11-01)

Tier V Crowned Devourers now require **regional corruption >= 80** (the
authored `devouring_front` band) **in addition** to the existing 300 brood
biomass, 600 regional biomass, open apex event, and single-apex-per-region
conditions. Only a registered canonical world region is subject to this extra
gate; the isolated unregistered horde test region retains its original
standalone policy. A canonical region registered in the world registry but
missing initialized runtime state **fails closed**.

This creates reversible ecological counterplay: burning (-2) and sanctifying
(-4) remains can push corruption below 80 and prevent *future* Crowned
Devourers even when a brood has accumulated sufficient biomass. Necromancy
(+5) can reopen the ecological window. A blocked promotion retains biomass
and tier, and consumes no extra NPC budget. Cleansing does **not** silently
devolve an already spawned apex; its removal remains the responsibility of
the encounter lifecycle. An open apex trigger alone no longer overrides
canonical environmental conditions.

**Validation:** `python -m unittest tests/test_horde_apex_corruption_gate.py`
checks source admission and the authored REG-001 corruption band. These are
source/data tests, not native Verse execution. UEFN acceptance must set a
canonical region to corruption 79/80, open the apex event, feed a Tier IV
brood across its threshold, verify denied/allowed promotions, repeat after
sanctifying a corpse, and test missing region initialization and region
unload/re-entry. Verify that physical Crowned presentation and streaming
population caps remain correct with separated multiplayer clients.

## Devouring Moon: evolved horde substrate gate (2026-11-01)

The canonical Devouring Moon Precursor (INV-R001-005) now requires three
independent ecological conditions **at admission**: corruption >=80,
regional consumed horde biomass >=600, and at least one living Tier IV or
Tier V brood in REG-001. It retains its existing hostility, invasion/event
exclusivity, wave budgets, and 20-AI authored maximum. The existing session
horde service provides the cumulative feed ledger and the bounded brood scan;
there is no new encounter director, spawned population, or persistent root.

Necromancy still raises corruption by +5 from the same exclusive corpse token,
but cannot substitute for actual horde feeding or a progressed Grave Architect.
Burning, sanctifying, and harvesting remains deny the food supply, while
burning/sanctifying can also lower corruption below 80. A post-admission
cleansing or brood death does not retroactively stop an active invasion or
improperly release its owned spawners. Horde region teardown clears biomass
and brood; a reloaded region must rebuild the required substrate and cannot
admit a stale Devouring Moon event from old session state.

All non-Devouring invasions retain optional defaults of zero for both new
authoring fields. The validator enforces integer bounds 0..6000 for consumed
biomass and 0..5 for minimum brood tier, and the Verse registry rejects
out-of-range definitions. These numbers gate *eligibility*, never NPC stats.

**UEFN acceptance:** At corruption 80 and hostility 4, assert that 599 biomass
and a Tier IV brood still refuse INV-R001-005; at 600 biomass with only Tier III
also refuse; at 600 with Tier IV it becomes eligible, provided no other
regional battle is active. Repeat with corruption 79, absent horde adapter,
region unload/re-entry (ledger reset), two players in different streamed cells,
and corpse denial competing with feed. Ensure admission refusal has no physical
spawner, objective or event reservation effects. Then verify native Verse
compilation, actual NPC caps and multiplayer state before enabling the event.

## Owned horde NPC teardown before region ledger release (2026-11-01)

The ecology adapter previously disabled its NPC Spawner and deleted the brood
ledger on `OnEnd`, but **did not despawn the already-materialized NPC bodies**.
Those characters could outlive the stream-region ecology that owned their
biomass, tier and death callbacks, then overlap a replacement adapter's actors.
The existing **single leased spawner** now unconditionally calls
`Spawner.DespawnAll(false)` before clearing the canonical region and releasing
its ownership lease. `Running` is set to false and native subscriptions are
canceled **before** spawner shutdown, so despawn/elimination callbacks cannot
mint orphan corpses or increase regional biomass after teardown.

The adapter's existing `if (not Running?): return` path remains intact: a
rejected duplicate or invalid binding does **not** disable or despawn another
owner's physical NPCs. Other regions and other spawner devices are untouched.
This is cleanup of existing NPC bodies only; no new director, cap, spawner,
corruption mechanic, persistent profile, or gameplay stat scaling was added.

**UEFN acceptance:** In a development island, run a horde ecology with active
Tier I–IV members and stored corpses, end/unload the region, and verify that
physical characters, actor-registration ownership, death subscriptions,
corpses and regional biomass are removed. Confirm no `horde.corpse_created`
or `horde.fed` fires from eliminated/despawned bodies after teardown. Then
restart the adapter with its same physical NPC Spawner; observe no overlapping
old actors. Run the same test with two players in separate streaming cells,
plus a duplicate adapter rejected by the lease (must not affect the rightful
owner). Capture native Verse compilation, actual actor counts and memory;
source tests alone cannot establish these physical properties.

## UEFN runtime query assertions for evolved horde substrate (2026-11-01)

The existing disabled-by-default `aeonfall_horde_runtime_test_device` now
calls the **real Verse** `HasBroodAtLeastTier` query during its progression
through five evolution stages. It checks Tier I exists while Tier II does not,
Tier IV exists before Tier V, and Tier V becomes available only after the
current test sequence feeds the regional ledger from 599 to 600 consumed
biomass. It also verifies that unregistered/unrelated regions cannot inherit
a Tier IV brood, invalid query tiers (0 and 6) fail, cleared-region queries
fail, and another region's living brood survives the clear. These tests use
the existing standalone `test` ecology region and do not seed fake canonical
invasion or UEFN spawner state.

The source-only validator `tools/validate_horde_runtime.py` now requires
those labels and query guards in CI. **Passing CI only proves the harness
contains the assertions**; it does not mean they have executed. To obtain
runtime evidence, import sources into UEFN, compile Verse, place the horde
harness with `Enabled = true` in a private development Launch Session, and
capture the printed `HORDE RESULT: <checks> checks, 0 failures` message,
compiler output and run context. Do not enable the harness in production.
The Devouring Moon's canonical registration, corruption, real physical actors,
actual NPC limits and streaming admission must still be verified separately.
