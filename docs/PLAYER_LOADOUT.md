# Player startup, entitlement and checked item delivery

The player loop has executable Verse source and source-level mutation checks. Native UEFN compilation, device binding and Fortnite session behavior remain unverified.

Place one `aeonfall_player_loadout_device`, a profile bootstrap, actor registry bootstrap, Slice 001 combat/class bootstrap, the runtime tick device, and the unlock delivery router. The loadout device claims a session ownership lease before subscribing; duplicate loadout devices are rejected. Bind every active player spawn pad in `PlayerSpawners`, its five class/weapon selection buttons, and a HUD Message device in `Feedback`.

Startup subscribes before enumerating present players. Join and native spawn events enqueue one bounded restore task per player. That task waits up to ten simulation seconds for an active player and character, a saved profile, a registered runtime identity, both authored classes and every first-slice ability. Failure produces a HUD diagnostic and a `player.loadout_startup_failed` event instead of silently constructing defaults. A saved unsupported or locked class must be repaired through an authored selection; the runtime does not replace it silently.

New players receive the logical WPN-001 starter unlock and equipment selection only through a checked immutable profile save. The initial physical grant is queued afterward. Their default class is CLS-006; returning players restore their saved class. Class selection uses the class runtime's atomic transition, including prerequisites and resource history. Repeated selection cannot refill class resources.

Weapon selection accepts a durably unlocked WPN identifier, initializes its registered ability states, and saves the selected equipment in one transaction. This selects logical equipment; it does not prove possession of a native inventory item. Physical delivery requires the correct configured adapter, and mechanics that depend on holding an item must additionally use their physical item gate.

Player ability activation checks the registered owner identity before initializing or spending anything. The active class grants only its registered `AbilityIds`. A weapon ability requires its owner weapon to be both unlocked and selected; an outside-class skill requires its skill unlock. NPC activations retain their authored NPC path. Owner-exclusive world powers use their separate authenticated controller.

## Rejoin generation isolation

The loadout restore waiter is now bound to a monotonically increasing,
session-local token for each queued player lifecycle. Player removal drops
that token, so an older suspended readiness task cannot act on a rejoined
player, clear the new task's pending flag, or emit a false startup-failed
diagnostic. Shutdown invalidates all tokens and cancels callbacks before the
loadout owner lease is released. This is transient state; it does not modify
the existing persistent profile schema.

**Native acceptance:** Delay class bootstrap until the loadout readiness wait
is active, disconnect the player, then reconnect them while the new restore
is pending. Confirm that only the new task can initialize class abilities and
request the physical starter grant; the stale task must not clear its pending
slot, enqueue additional equipment, or show the failure HUD. Repeat with
two clients and a session restart. Test respawn with inventory retained and
enabled physical restore separately. These checks need a UEFN Launch Session;
source mutation tests do not execute Verse.

## Inventory lifecycle

`RestoreEquipmentOnFirstSpawn` and `RestoreEquipmentOnRespawn` default to false. Enable a flag only after configuring and testing the corresponding Island Settings inventory removal. Otherwise retained inventory could receive another physical item. Duplicate callbacks for the same native character are ignored. Initial starter delivery remains automatic for a newly saved starter unlock.

Persistent unlocks and Fortnite inventory are different systems. Rejoining does not replay a shop, crafting or boss transaction. Authors can enable tested first-spawn reconstruction to recreate selected weapons from existing durable unlocks. Successful purchases/crafts can use the selection buttons afterward; selection itself does not grant another physical item.

## Delivery contract

`TrySaveProfile(Player, Candidate)<transacts>:logic` checks an active player, `FitsInPlayerMap[Candidate]`, and the persistent map write. `GetProfile[]` fails for missing or inactive records. Purchases and crafts stop if their material/unlock save is rejected. First-clear rewards queue only newly unlocked entities after successful persistence; an already owned weapon is not granted again.

The delivery coordinator admits pending state and the typed request together. A full queue rolls back that request. Post-commit callers use `QueueAfterCommit`, which retains a bounded deferred backlog and retries queue admission through the runtime scheduler; existing work for the same owner/entity satisfies the request. Pending deliveries are capped at 1,024 and deferred deliveries at 256. A completely full backlog reports failure while the durable unlock remains saved. Missing bindings and exhausted physical-delivery retries produce timeout events; they require editor repair, not another purchase.

Each physical adapter claims the canonical request once, checking its request/owner/entity/source identity, durable unlock, and active character. Duplicate adapters, retries and duplicate queued events cannot dispatch the same request twice. Claim state survives retry timer updates. Native Item Granter and Trigger APIs acknowledge dispatch, so the source records `item_grant_dispatched` or `trigger_dispatched`, not verified inventory possession.

Delivery coverage now includes the first-clear WPN-126 output as `GRANT_WPN_126`, alongside all shop/crafting outputs. Configure the actual native item represented by each WPN identifier. Armor and vehicle outputs still require their authored trigger graph bindings.

All native join, leave, spawn and button subscriptions are canceled on device shutdown. Actor removal clears pending and deferred delivery work before the identity is released; departing-player cleanup does not read an inactive persistent record.

## Editor acceptance

1. Join before and after the bootstrap devices begin; each player reaches one live class state and one starter delivery.
2. Disable a required bootstrap and observe the bounded startup diagnostic; repair the binding and restart.
3. Respawn with inventory retained and default flags: no extra item is granted. Test inventory removal separately before enabling reconstruction.
4. Reject a persistent save in the test map: shop/craft costs and unlocks remain unchanged and no item dispatch occurs.
5. Try an unlocked unequipped weapon ability, a locked skill, a substituted runtime owner and an outside-class ability; all are rejected.
6. Wire two adapters for one entity, replay a request and allow a retry: only one physical dispatch occurs.
7. Saturate request admission; a successfully saved unlock waits in the deferred backlog and dispatches after capacity recovers.
8. Clear BOS-006 with WPN-126 newly locked, then repeat the clear and test an already owned WPN-126: exactly one new first-clear item delivery is requested.
9. Leave during startup/delivery and end the round; subscriptions, ownership leases and player work are cleared.

Source checks are `tools/validate_player_loadout.py`, `tests/test_player_loadout.py`, and the delivery coverage validator. They guard checked-save ordering, entitlements, lifecycle cleanup, claims and bounded queue behavior; they do not execute the native acceptance cases.


## Post-commit delivery map integrity

Physical delivery is an independent, retryable session workflow after a checked
profile unlock. Pending-delivery resolution, per-owner disconnect cleanup,
deferred-backlog pumping and scheduler retries now preflight the replacement
maps. A failed insertion retains the old map and must not report successful
physical delivery, erase another player's pending item, or announce an expiry
that did not commit. On successful deferred retry admission, a retained deferred
entry is deduplicated through the canonical pending request identity during the
following tick.

A private UEFN Launch Session must test two players with different pending
weapon grants and a saturated deferred backlog. Disconnect one player during
the other's retry; verify the second retains delivery ownership and receives
only one physical grant. Attempt a refused replacement allocation where a
native test harness allows it, and inspect
`unlock.pending_remove_failed`, `unlock.owner_clear_failed`,
`unlock.deferred_rebuild_failed` and
`unlock.pending_tick_rebuild_failed`. None of these static guards is proof
of item possession, UEFN compilation or an editor-tested physical adapter.
