# First playable loop: implemented source, awaiting UEFN execution

The saved source now includes live player loadout restoration, checked purchases/crafts and first-clear unlock delivery, an input-driven NPC target selector, and a corpse harvesting loop. This document describes intended behavior and binding requirements. No editor import, engine compilation, native device behavior or Fortnite play session has been verified.

## Ordinary corpse economy

Bind `aeonfall_corpse_harvest_device.Ecology` to the region's horde adapter, `HarvestButton` to a button accessible in the encounter space, and `Feedback` to a HUD Message device that targets the interacting player. The adapter records corpse positions only from native NPC elimination events. Harvesting checks an active player, an active character, current corpse lifetime, region, and physical distance. The region feeding radius and harvest radius both limit selection. A session ownership lease rejects a second adapter using the same region or physical NPC spawner before it enables, disables or clears gameplay.

A successful harvest gives MAT-008 ×12, MAT-003 ×4, FAC-002 reputation +5 and XP +20. An active Sepulchral Sovereign (CLS-006) also gains 20 corpse charge, capped by class capacity. A player who has unlocked and selected WPN-003 gains 25 ABL-009 meter. Crown command slots are not harvest currency. Boss material MAT-011 is excluded.

The exclusive corpse consumption, immutable profile replacement, class charge, optional meter and admitted progression event share a single transactional failure scope. A full persistence allocation or event queue leaves the corpse available and produces no reward. Another brood or player may consume a corpse first; simultaneous attempts must be tested in a real multiplayer session.

## Targets and heat

Bind the target selector's input trigger to the authored Creative Input Action. It picks the nearest active registered NPC in the configured view cone and range, limited to `TargetCanonicalIds`; default MON-043 and BOS-005. Active player-owned companions are excluded. Selection expires after eight seconds. Failure clears the player's earlier target. The selector provides spatial eligibility only: no line-of-sight raycast is available through the APIs used here. Confirm occlusion and targeting fairness in UEFN before release.

The WPN-007 heat adapter is disabled by default. Bind its NPC spawner, configure its conditional button with the exact physical item used by the WPN-007 item delivery adapter, and then enable it. Positive native damage to an observed NPC adds 10 ABL-006 meter, at most once per player every 0.25 seconds. The player must own and select WPN-007 and actually hold the configured physical item. A generic trigger, selected profile entry alone, environment damage or another player's damage cannot award heat. Native damage attribution and the item gate require editor playtesting.

## Physical walls, stairs and routes

Place three `aeonfall_prop_spawn_adapter_device` instances for ABL-001, ABL-002 and ABL-010. Their exact IDs and budgets are in `slice_001_player_loop.json`. Bind each `PropAsset` to an actual creative prop asset authored in UEFN, then enable the adapter. Do not bind the same adapter IDs to the legacy trigger/composite adapters at the same time.

The provider validates the pending request, owner/ability context, expiry, aim distance and final placement distance, reserves the canonical owner budget, calls native `SpawnProp`, and checks its returned prop and success enum. Failed tracking, status application or queue admission disposes the new prop and releases its reservation. The ability reports success only after physical creation and canonical tracking succeed. A cleanup loop disposes props after canonical expiration or owner cleanup; OnEnd disposes this provider's remaining props.

Placement uses yaw with zero pitch/roll. The starter projects the point to the owner's height with an editable pivot offset; it does not query terrain, collision clearance or navigability. Validate the offset against the actual character capsule and each asset pivot. Use this projection for the flat starter area only until editor-tested placement checks support uneven terrain. The view context pool is capped at 1,024 total and 16 per owner, with a maximum 30-second lifetime.

Engine rejection of the asset, point, bounds or prop limit reports failure and releases the budget. Ordinary source checks cannot prove that imported creative props have the intended collision, walkable stairs or damage behavior. Check those properties, negative placement cases and resource refunds in UEFN before release.

## Class transitions

Class activation resolves all abilities, changes passives, saves the equipped class, and admits its notification in one transaction. A refused save or status/event admission rolls back the transition. Selecting the current class is idempotent. Switching away retains that class's current resource and switching back restores it, preventing resource refill through repeated selection. Unregistering a player clears session history. Rejoining begins a new session life; resource history is not persisted.

## Required session checks

1. Join and respawn with the authored starter class; verify class ability inputs resolve and retained inventory is not duplicated.
2. Spend corpse charge, reselect the same class, switch away and back: resource remains spent.
3. Two players harvest one corpse; exactly one reward and one corpse consumption occur.
4. Fill the persistent profile or refuse a test save; harvest leaves the corpse and all ledgers unchanged.
5. Consume or expire a selected corpse before the button event; no reward is issued.
6. Earn ordinary materials, craft WPN-007, select it, and receive the configured physical item. Confirm rejected saves deliver no item.
7. Damage the authored NPC while holding WPN-007; heat fills. Repeat while holding another item, with another instigator, and from environment damage; heat does not fill.
8. Select an eligible NPC, let the target expire, despawn it and retry abilities. Check feedback and transaction cleanup.
9. Complete BOS-005's physical objectives and native elimination; first clear persists and requests unlock delivery once, including rejoin behavior.

Python tests mutate these source guards and verify exact source bundle delivery. They do not execute any of the session checks above.

Review this guide when class resource rules, item mappings, target eligibility, corpse rewards or the native Fortnite APIs change. Source files live in `verse/combat/`, `verse/npcs/` and `verse/progression/`; the authored policy is `content/vertical_slice/slice_001_player_loop.json`.
