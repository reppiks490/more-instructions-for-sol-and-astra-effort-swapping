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
