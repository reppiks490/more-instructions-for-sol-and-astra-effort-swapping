# Runtime event routing

`verse/core/runtime_event_bus.verse` owns five typed, session-scoped channels.
Verse's native `event(T)` offers `Await` and `Signal`, and does not offer
`Subscribe`. The channel facades preserve the project's `Subscribe`, `Await`,
and `Signal` call sites without claiming native `listenable` conformance.

Gameplay emission is transactional queue admission. Each channel has a separate
capacity of 1,024 messages, so runtime telemetry cannot consume request/result
capacity. The immutable module-level facade resolves concrete mutable state
lazily through `weak_map(session, aeonfall_event_bus_state)`.

Call `AEONFALLRuntimeBus.Pump()` at a device boundary after the producing
gameplay transaction commits. Pump is deliberately `no_rollback`: native `event.Signal` cannot
be forwarded from a transactional emitter. Pump snapshots and clears all five
queues before delivery; callback-generated messages wait for the next Pump.
Messages preserve FIFO order within each channel; there is no ordering promise
between channels. An awaiting task is armed before `Subscribe` returns, and
native delivery resumes the listener through its next suspension. Reentrant
Pump calls are ignored. The scheduler pumps twice before advancing timeouts,
so queued requests and their callback-produced results resolve before deadline
cleanup. It pumps once more after canonical tick updates. A callback-generated
message waits for the next Pump invocation, which can be in the same scheduler
turn; this does not promise a whole-tick delay.

Use the transactional `TryEmit`, `TryRequestAbilityEffect`,
`TryReportAdapterResult`, `TryRequestUnlockDelivery`, and `TryReportUnlockDelivery`
methods when admission matters. They return `false` on capacity exhaustion.
`Signal` and the original void methods remain compatible convenience methods;
they cannot communicate rejection. Critical request producers must release
reservations or otherwise reject work when a Try method returns false. A full
result queue is a failed admission, never proof of successful resolution. Ability
adapters use `AEONFALLAdapterResultDelivery.Report` from
`verse/combat/adapter_result_delivery.verse`; when result admission is rejected,
it resolves the result directly through the canonical activation coordinator.
Unlock adapters similarly call the canonical delivery service when their Try
method returns false. This synchronous fallback runs inside the physical
callback task, after the producing gameplay transaction commits. A successful
physical effect therefore retains its canonical completion under queue
saturation. Unresolved fallback results emit diagnostics. The
bus counts overflow separately by channel and prints cumulative diagnostic
counts from Pump. Existing pending-operation timeouts are still required.
Capture an admission result outside a failure context before querying it, for
example `Admitted := Bus.TryRequestAbilityEffect(Request)` followed by
`if (Admitted?):`. Directly querying a rejected transactional call rolls back
its overflow-counter update along with other mutations. Overflow counts measure
committed rejected admissions; they are not an out-of-transaction audit log.

Subscriptions return `cancelable`. Cancel sets a transactional flag; the
listener checks it before each callback. A cancellation watcher releases idle
Await registrations within 0.05 simulation seconds using structured `race`.
Device owners should retain tokens and cancel them during `OnEnd`. Generic
listener fields are immutable; concrete state holds the mutable typed queues.
Subscribe is a project `no_rollback` method because it spawns a listener. Capture
its token in an ordinary statement before wrapping it in `option{}`; constructing
an option evaluates its operand in a failure context. The existing bus clients
now retain their token and cancel it in `OnEnd`.

`python tools/validate_runtime_event_bus.py` checks the API, callback payload
types, and listener ownership. Its Python mutation tests catch raw-event fields,
wrong callback types, missing cleanup, and no-rollback calls inside options.
The guard also checks native device callback boundaries and canonical resolution
fallbacks when result admission fails.
It is a source check, not a Verse compiler. The disabled-by-default
`verse/testing/runtime_event_bus_test_device.verse` exercises real Verse routing
with injected isolated state: all channels, deferred delivery, same-channel
callback emission, nested Pump, native Await, FIFO, per-channel saturation,
overflow counters, capacity reuse, cancellation, and failed-transaction rollback
of admission and cancellation. Compile it and run it in a
UEFN Launch Session, then record its check/failure totals before claiming runtime
verification. The Python validation cannot execute those assertions.

API evidence inspected for this change:

- [Epic event(T) API](https://dev.epicgames.com/documentation/fortnite/verse-api/versedotorg/verse/event/event%28t%29)
- [Epic cancelable.Cancel API](https://dev.epicgames.com/documentation/en-us/fortnite/verse-api/versedotorg/verse/cancelable/cancel)
- [Public generated Verse digest mirror](https://future.uefncentral.com/de/verse-library/verse-digest), identifying build `++Fortnite+Release-41.20-CL-55550516`; native Signal has no effect annotation, Subscribe and Cancel are transactional.
- [Epic-linked Book of Verse runtime API reference](https://verselang.github.io/book/api/verse_runtime_api.html); this reference also describes unreleased main-branch features, so generic mutable classes were avoided.

The repository has no attached UEFN compiler. The project's installed digest,
effect inference, generic listener instantiation, spawn/race startup ordering,
session lifetime, and dispatch performance still need in-editor verification.

Status commands use the runtime-event channel as physical presentation work,
so `ApplyStatus` and `RemoveStatus` require queue admission and the canonical map
write in one deciding transaction. Rejected admission restores the previous
instance. `ApplyBatch` rolls back every earlier status and queued command if one
application fails. A legitimate refresh still queues its own `status.applied`
command and retriggers the bridge's authored ApplyTrigger and VFX Begin calls.

Timed expiration retries when presentation capacity is unavailable: it keeps
the original positive-duration instance until its expiry command is admitted.
It never writes zero as a retry sentinel, because zero means a persistent status.
`TickAll` shares this per-target policy. `ClearTarget` always clears canonical
state; its presentation hint can be dropped when the queue is full.

The status bridge stores the affected agent before applying physical effects
and reconciles every 0.1 simulation seconds. It cleans stored agents when their
status disappears or their actor registration vanishes or changes, even if the
clear event could not be queued. Queued stale applications are ignored, and a
queued stale removal does not clean a newly reapplied active status. `OnEnd`
cancels the bus listener, stops reconciliation, and cleans all tracked effects.

`verse/testing/status_saturation_test_device.verse` is disabled by default and
uses isolated real bus, registry, and status-runtime instances. It exercises
application and refresh rejection, atomic removal, single-target and all-target
expiry retry, batch rollback, persistent zero-duration statuses, forced clear,
and callback receipt of admitted commands. The Python source/mutation checks do
not execute these assertions. UEFN acceptance should additionally verify a
configured bridge with a real agent: apply and refresh, fill the queue and clear,
unregister the actor, reapply before an old removal is pumped, and end the device.
The configured RemoveTrigger/VFX cleanup must run for removed effects, while
refreshed active effects must remain applied.
