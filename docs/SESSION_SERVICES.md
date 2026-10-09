# Session-scoped runtime services

AEONFALL's mutable registries and runtimes are allocated lazily in the current
Verse `session`. Each service has a `weak_map(session, ServiceType)` and a
`GetAEONFALL…()<transacts>` accessor. The concrete classes remain available for
isolated test instances. Immutable stateless facades and authored definitions
remain module constants; the single player profile persistence root remains
unchanged.

The accessor checks for an existing service before allocating and returns a new
service only after retaining it in the session map. An unsuccessful map write
calls native `Err`; gameplay must never continue against an unretained temporary
registry. The queued event bus follows the same session ownership rule.

Call the accessor at the point of use, for example
`GetAEONFALLActorRegistry().GetRuntimeKey[Agent]`. The scheduler and devices use
the same session instance. No service is keyed by an Epic account, and no
session state is represented as persistent player data.

Keep transactional accessors out of class field defaults. A service that accepts
an isolated mutable dependency stores an optional injected instance and resolves
its session default inside a transactional method. The status runtime uses this
pattern, and its disabled saturation harness still injects an isolated registry.

`tools/migrate_session_services.py --write` updates existing allocations,
references, generator templates, regression guard strings and the service
manifest. `--check` fails if generated references or the manifest have drifted.
The structural validator also follows class default dependencies, catching
indirect mutable module allocations. Mutation tests verify retained-map writes,
fatal fallback, stale references, preserved local constructors and regeneration
stability. These are source checks; native engine compilation is still required.

Epic documents `session` as one instance per round today, with a possible future
change to one per game. Cleanup and device ownership must remain explicit;
do not rely on a round boundary to clear gameplay.

Verified API sources: [40.00 ecosystem release notes](https://dev.epicgames.com/documentation/en-us/fortnite/40-00-fortnite-ecosystem-updates-and-release-notes),
[session](https://dev.epicgames.com/documentation/en-us/uefn/verse-api/versedotorg/simulation/session),
and [Err](https://dev.epicgames.com/documentation/en-us/uefn/verse-api/versedotorg/verse/err).
The 40.00 notes state that allocating a `var` indirectly at module scope produces
a runtime error. Native `Err` is documented as
`Err<public><native>(Message:[]char)<computes><dictates>:false`.
