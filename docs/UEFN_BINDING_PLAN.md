# AEONFALL — UEFN Binding Plan

## Purpose
This plan converts the validated canonical catalog into project-bound UEFN assets without coupling persistent IDs to editor asset names.

## Current Epic Surface
- Custom Items & Inventory is the Scene Graph path for custom item entities and inventories.
- Custom Weapon Templates provide Pistol, SMG, Assault Rifle, and Shotgun prefab foundations.
- Held Item Templates provide a path for carryable non-firearm ability hosts.
- NPC Character Definitions bind character type, modifiers, and Verse behavior.
- `npc_behavior` is the shared Verse extension point for custom NPC logic.
- Guard-based definitions are preferred for humanoid hireables that need built-in weapon/hiring behavior.
- Wildlife base types are used where their built-in behavior materially helps; unusual creatures use Custom definitions plus the AEONFALL tameable runtime.

## Binding Rule
Canonical IDs such as `WPN-001`, `NPC-003`, or `BOS-011` never become asset paths. Each ID resolves through an adapter/binding record. This prevents a renamed prefab or Character Definition from corrupting progression or save data.

## Slice 001 Binding Sequence
1. Create the region shell, streaming cells, encounter spaces, and navigation volumes.
2. Bind the 12 selected weapons to weapon/held-item prefab templates.
3. Create Character Definitions for 12 monsters, 6 tameables, and 8 hireables.
4. Attach reusable behavior archetypes rather than one Verse file per NPC.
5. Bind the two minibosses and major boss to encounter controllers.
6. Bind `EVT-011` to the world-event director.
7. Bind the two armor families and three vehicles.
8. Bind material drops, crafting station, Grave Market shop, and progression rewards.
9. Compile Verse, Launch Session, run persistence/rejoin tests, then profile memory/spatial cost.

## Weapon Strategy
Ballistic weapons use the nearest supported weapon template and a mechanic adapter. Weapons whose core fantasy is not conventional firearm behavior use a held-item/ability-host path instead of forcing every concept through firearm traces.

## NPC Strategy
The first slice intentionally reuses behavior archetypes:
- ambush predator
- pack corpse ecology
- artillery brood controller
- necromancer constructor/support/controller
- subterranean ambusher
- infernal pursuit
- hazard-feeding pack
- hireable medic/scout/tactician/hunter
- custom tameable mount/companion

## Boss Strategy
Boss Character Definitions own locomotion and body behavior. Encounter controllers own objectives, phases, hazards, spawn budgets, weak points, rewards, cleanup, and world-state changes. This separation is mandatory for skyscraper/continent-scale encounters later.

## Acceptance Boundary
Nothing moves from `specified` to `implemented` until the corresponding project-bound asset exists and the Verse code compiles in UEFN. Nothing moves to `tested` until Launch Session covers success, failure, cleanup, respawn/rejoin, and multiplayer behavior.

## Actor lifecycle editor acceptance (Runtime Forge)

Before enabling the first playable, import and compile the current actor
registry and NPC behavior sources in UEFN. Spawn/despawn two NPCs sharing
one canonical Character Definition and confirm unique runtime keys; respawn
and remove a human player; verify both identity indexes agree before
activation, that cleanup releases pending requests/statuses/companions, and
that a new actor never inherits the removed actor's state. Exercise duplicate
registration and a mismatched canonical identity. Confirm the registered
predicate rejects stale reverse indexes using a native test harness where
possible. The map-preflight failure path is source guarded but must not be
reported as native-tested without actual diagnostic evidence.



## Native input and encounter-volume lifecycle acceptance

First-playable ability inputs now retain `input_trigger_device.PressedEvent`
subscriptions and cancel them on `OnEnd`. Place the self, targeted and
position-input devices with nonempty canonical AbilityId bindings. In a private
two-client Launch Session, trigger one request for each, stop the device, and
verify that no further activation, resource spend or rejection event arises
from the stopped device. Start a replacement and verify one activation per
press. Source guards alone do not establish native callback behavior.

For an `aeonfall_encounter_context_volume_device`, bind its native volume and
nonempty canonical EncounterId, then spawn an already-inside player before
device startup. Confirm that startup observes that player. Duplicate enter
events must not increment encounter depth twice. Exit and device shutdown
must release only this volume's admitted context depth, leaving overlapping
encounter volumes unaffected. Denied map writes must not create phantom
encounter privileges. The `aeonfall_encounter_participant_volume_device`
also cancels its subscriptions on shutdown; do not use its stop event to
erase another director's participant list. Actor unregister and encounter
director termination remain responsible for global participant cleanup.

These are explicit native acceptance tasks; Python source mutation tests do
not assert a successful UEFN Verse compile, editor bindings or multiplayer
execution.


## Multiplayer map-rebuild safety acceptance

Actor-context teardown, encounter participant removal and target-selection
expiry now preflight **all** replacement map entries. If any map insertion
refuses allocation, the old map remains authoritative rather than silently
dropping unrelated players, encounters or transformations. Failed context,
participant and target rebuilds emit diagnostic runtime events. Target expiry
notifications are deferred until its replacement map is committed, preventing
false expiry reports on a failed rebuild.

UEFN acceptance: connect two clients with distinct transformation/encounter
contexts and selected actor targets, then remove one during a live boss
encounter. Verify the other client's context and participation survive.
Confirm target expiry is reported once only after the corresponding selection
disappears. Force constrained state-allocation tests where supported; verify
`context.owner_clear_failed`, `encounter.participant_cleanup_failed` or
`target.tick_rebuild_failed` without other players losing state.

These guards mitigate collateral state loss; they do **not** make the full
multi-service actor teardown transactional or prove that forced allocation
failures can be reproduced with standard UEFN APIs. Native compilation and
Fortnite Launch Session evidence are still required.
