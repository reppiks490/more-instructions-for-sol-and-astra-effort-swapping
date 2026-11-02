# World-event regional shell binding: UEFN adapter

The canonical world-event service now shares a session-local state map with
invasion and faction admission. A world-scale event may be **abstract** (zero
materialized regions) or claim up to four valid, initialized regions per stage.

`aeonfall_world_event_region_binding_device` is a *binding adapter*, not a
new encounter director or NPC population pool. Place at most one adapter per
region and bind its `RegionEntered` and `RegionReleased` outputs to **existing
region-specific** presentation/materialization and retirement logic.

The adapter listens to the already-existing `world_event.started`,
`world_event.stage_advanced`, `world_event.completed` and
`world_event.failed` notifications. It never trusts event payloads as
authorization: every callback queries `ActiveEventForRegion(RegionId)` from
the canonical session service, compares it to the last dispatched owner and
triggers a release/entry pair only if ownership actually changed. The periodic
1-second reconciliation loop recovers from event-bus overflow and from a
region binder starting after an event began.

## Binding and safety

- Initialize the canonical region registry and region state before the device
  starts. Unknown/uninitialized regions, duplicate adapter leases, or using
  the same native trigger for entry and release **fail closed**.
- Use distinct editor trigger devices for each region's entry and release.
  A rejected duplicate adapter never fires or cancels another's outputs.
- Bind **RegionEntered** to an existing region-relevance controller or staged
  presentation **request**, not directly to unconstrained NPC Spawner enable.
  That controller must confirm player presence, physical spawner ownership and
  per-group AI/VFX budgets before it materializes any characters.
- Bind **RegionReleased** to the matching **owner-only** physical cleanup
  pathway. Since adapters are notifications, physical producers must still
  reconcile canonical state and perform their own NPC despawn, prop teardown
  and streaming-cell visibility cleanup.
- During an owner handoff the adapter issues release before entry. Identical
  owner after a new stage produces **no duplicate trigger**. On device end,
  the current owned shell releases once; duplicate/unbound devices do not
  touch outputs.
- This implementation neither reads player presence nor enforces World
  Partition cells or native spawn counts. Region materialization must remain
  gated by UEFN player-relevance devices and existing population caps.

## Acceptance matrix — private UEFN Launch Session

1. Compile Verse and bind `REG-001` after the region bootstrap. With no
   active event, the entry trigger must not fire; with an active canonical
   shell it must fire once, including late binder placement/restart.
2. Advance to a stage with the *same* region: no duplicate entry. Advance
   to a stage that leaves the region: one release. Re-enter in a later stage:
   one new entry. Complete/fail: one release and no orphan physical actors.
3. Duplicate region binder, invalid RegionId, uninitialized canonical region,
   and identical entry/release triggers: reject with no physical side effects.
4. Delay/out-of-order existing bus notifications, simulate queue saturation,
   and confirm the 1-second canonical resync converges to the current owner.
5. Test two clients separated by streaming cells. Verify no distant physical
   NPCs spawn without relevance and no other region's NPCs are despawned.
   Record live NPC caps, Unreal memory/Spatial Profiler, and cleanup.
6. Verify invasion/faction/world-event admission in both orders for the same
   region, and independent admission for different regions.

CI guards source structure and mutation checks only. It does **not** execute
native Verse or prove editor trigger wiring, physical AI budgets, streamed
relevance, multiplayer delivery or cooked memory usage.
