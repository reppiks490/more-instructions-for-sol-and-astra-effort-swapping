# Runtime clock continuation — 2026-10-07

The canonical scheduler previously advanced all seven services by the requested sleep
interval. A delayed frame therefore extended cooldowns, status lifetimes, targeting
leases, spawn reservations, and pending activation/delivery deadlines. The scheduler
now samples simulation elapsed time on each wake and sends one measured delta to every
service. It does not drop elapsed simulation time or generate a catch-up event burst.
OnEnd closes the running guard; the sleeper checks it before further work.

Catalog validation now runs for ordinary Verse changes on pull requests, as well as
pushes. The runtime invariant gate checks measured-delta wiring and shutdown ordering.

## Evidence and remaining gate

- All 18 repository validate_*.py scripts passed locally.
- Five in-memory unsafe source mutations were rejected by the new clock checker:
  requested-interval propagation, missing clock sample, missing shutdown guards,
  missing OnEnd override, and missing positive-delta guard.
- These are catalog/source checks, not execution of Verse.
- Launch tests LT-023 and LT-024 cover delayed frames, runtime interval changes,
  expiration semantics, session shutdown, and fresh-session clock baselines.
- UEFN compile and Launch Session remain pending. The existing service methods use
  transacts while some call the default-effect event emitter; generated project
  digests and the Verse compiler must resolve this pre-existing effect compatibility
  concern. No module has been promoted to implemented or production.
- Place one canonical runtime tick device per session, as already required by its
  design; duplicate authored tick devices remain unsupported.

## Epic API references checked

- https://dev.epicgames.com/documentation/en-us/fortnite/verse-api/versedotorg/simulation/getsimulationelapsedtime
- https://dev.epicgames.com/documentation/en-us/fortnite/verse-api/fortnitedotcom/devices/creative_device/onend

Epic defines the clock as seconds elapsed since world simulation began and cautions
that coroutines spawned inside OnEnd may never execute. Cleanup here is synchronous.
