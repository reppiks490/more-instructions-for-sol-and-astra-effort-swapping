# One True Omnigod Sovereign — fusion integration boundary

**Status:** Authored source contract and session-only phase service; **not** a compiled or playable UEFN fusion. Coordination issue: [#37](https://github.com/reppiks490/more-instructions-for-sol-and-astra-effort-swapping/issues/37).

## Canonical authority and entitlement

Preserve the existing `UNI-001` creator-only Sovereign Unmaking identity and its disabled-by-default `aeonfall_sovereign_authority_device`. `content/sovereign/owner_identity.json` still has no verified native Epic account binding; do not turn on the authority based on a display name, screenshot, team, class, first join, cosmetic, or client-supplied token. A trusted operator must provision the real native Player Reference after identity verification. The existing `CanWield(Player)` gate is the only authorization input; the fusion service never writes a persistent entitlement or modifies `aeonfall_player_profile`.

`FUS-001` is the source-only **Sovereign Armor Fusion** target. `FUS-002` is an experimental **Sovereign Titan Fusion** design; it is not activatable in this runtime. Both have `enabled_for_native_activation=false` until a physical adapter, native compiler and multiplayer acceptance exist.

## Runtime contract

`verse/sovereign/fusion_state_runtime.verse` is a session-keyed service. A single trusted controller leases the service with `AcquireController`. The controller may call `BeginActivation` only for the live, authority-verified creator and only while Dormant; this returns a monotonic generation token. The service moves through **Dormant → Activating → Active → Separating → Dormant**. `ConfirmActivated` is permitted only after the future physical adapters report success. `BeginSeparation` checks live authority again. The controller must remove physical effects before `CompleteSeparation`. On interruption, owner death, lost reference, disconnection or shutdown, the controller must remove owned physical effects **before** `Abort` or `ReleaseController`. These cleanup paths intentionally do not require current authorization. Every new activation or abort invalidates stale async callbacks through the generation counter.

The first verified session owner remains sticky after abort or controller release, so another player cannot inherit the fusion. A fresh Verse session starts Dormant, with no fusion state persisted; rejoining requires a newly verified owner and a new activation. An already-active owner must not silently reactivate after a respawn. No independent ability, appearance, monster allegiance or persistent progression is granted by this source-only state service.

## Cross-loop ownership and handoffs

**Fusion Architect:** owns the machine-readable contract, phase runtime, source validator, mutation tests and this guide. The state service is deliberately free of native presentation and inventory operations.

**Omnigod Avatar:** implement the project-bound controller and Armor/Titan presentation. On native apply failure, roll back every partial effect before `Abort`. On respawn, character change or disconnect, reconcile the previous native character and cleanup. Do not implement an alternate owner grant or a competing fusion state machine.

**Sovereign Arsenal:** consume `IsAuthorizedActive(Device, Player, Token)` before accepting a fusion ability. Reject stale generation tokens and use canonical ability/resource reservations and existing checked profile transactions. No direct player-profile entitlement flags.

**Fusion Cinematics:** stage VFX, audio, UI and telegraphs behind the same generation token. Every effect must have a cancel/cleanup path, reduced-intensity visual fallback and non-color-only combat cue. No timeline completion may confirm activation after abort.

**Fusion QA:** independently test source and native lifecycle, including duplicate controller, owner spoof, cross-player calls, stale generation, interrupted activation, interrupted separation, revoked authority, respawn, session restart, repeated activation, and partial adapter failures.

## Release and editor gates

Source validation: `python tools/validate_fusion_architecture.py` and `python -m unittest tests.test_fusion_architecture -v`. The repository's normal `python -m unittest discover -s tests -v` also exercises mutation tests. These are **not Verse execution tests**.

Before enabling any native fusion, record the exact source SHA, editor version and successful Verse compile; verify real owner reference provisioning and a physical controller in UEFN; run two-client Launch Sessions for authorization, character lifecycle and replication; prove every partial-effect teardown; and profile World Partition/HLOD transitions, streaming, Spatial Profiler, Memory Snapshot and platform runtime memory under full fusion VFX. Include readable telegraphs, audio alternatives and photosensitivity-safe fallback. Publication remains blocked until native evidence and current Epic feature/API eligibility are verified.

No invented `.uefnproject`, `.uasset`, `.umap`, character mesh or editor evidence is supplied here. No native effect adapters are implemented in this PR. The runtime is a stable integration contract, **not a playable transformation**.
