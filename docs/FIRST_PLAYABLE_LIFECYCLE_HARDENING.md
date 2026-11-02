# First-playable actor identity and cancellation ownership

This source pass addresses two preventable first-playable runtime errors. It
does **not** establish that the Verse code compiles in UEFN or that any
Fortnite Launch Session has run.

## 1. Single actor-bootstrap owner

`aeonfall_actor_registry_bootstrap_device` now owns a session-scoped lease.
It must acquire the lease before subscribing to player-added/removed events
or enumerating existing players. A second device fails closed and cannot
repeat `player.runtime_identity_ready`, run Hall refresh, or unregister
a player after another bootstrap owns the registry. OnEnd stops callbacks,
cancels subscriptions, and releases the lease only if Self still owns it.

**UEFN acceptance:** Place two actor registry bootstrap devices in a private
test island. Verify that only the owner registers each player and emits
one ready event. Remove the rejected device; ensure the owner still operates.
End the owner and start a replacement; verify new joins and removals are
processed once. Repeat with two simultaneous players and rejoin.

## 2. Activation result and cancellation transaction

The activation coordinator now refuses to advance an adapter result if
`RemovePendingRecord` fails to rebuild the request ledger. It must not
commit a charge, cooldown, meter debit, or class-resource spend in that case.

Coordinator `CancelPending` validates the request owner, ability, and
canonical pending ID before calling a failable transactional helper.
The helper removes the coordinator pending record, cancels the canonical
ability request, and conditionally releases its class reservation within
**one failure transaction**. A failed step rolls back prior Verse state
mutations, retaining the pending request and reservation for investigation
or retry. A timeout event remains conditional on successful cancellation.

**UEFN acceptance:** Compile integrated Verse, bind one real effect adapter,
result router, ability input and tick owner. Trigger an effect that withholds
the result, then verify the five-second timeout clears exactly one pending
request and its matching class reservation. Inject a stale owner/request ID
and a second player's simultaneous request; neither may be released by an
unrelated callback. Exercise forced failed map writes or reservation release
using a test harness, then verify no partial cancellation or resource debit.
Verify late callbacks are rejected. Observe actual event counts.

## Evidence and rollout boundaries

- `python tools/validate_activation_transactions.py`
- `python tools/test_activation_transaction_validation.py`
- `python -m unittest tests.test_activation_timeout_atomicity tests.test_first_playable_actor_bootstrap -v`
- Full AEONFALL Validation and Verse Static Validation GitHub workflows.

These are source/static checks and Python reference/mutation tests only.
No Python result is proof of an Epic Verse compiler pass, placed editor
bindings, physical NPC behavior, replication correctness or gameplay.
Record those separately with the actual editor diagnostics and a Launch
Session capture. Preserve the single persistent player profile root.
