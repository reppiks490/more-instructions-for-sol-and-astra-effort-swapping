# One True Omnigod Sovereign — fusion integration boundary

**Status:** Authored source contract and session-only phase service; **not** a compiled or playable UEFN fusion. Coordination issue: [#37](https://github.com/reppiks490/more-instructions-for-sol-and-astra-effort-swapping/issues/37).

## Canonical authority and entitlement

Preserve the existing `UNI-001` creator-only Sovereign Unmaking identity and its disabled-by-default `aeonfall_sovereign_authority_device`. `content/sovereign/owner_identity.json` still has no verified native Epic account binding; do not turn on the authority based on a display name, screenshot, team, class, first join, cosmetic, or client-supplied token. A trusted operator must provision the real native Player Reference after identity verification. The existing `CanWield(Player)` gate is the only authorization input; the fusion service never writes a persistent entitlement or modifies `aeonfall_player_profile`.

`FUS-001` is the source-only **Sovereign Armor Fusion** target. `FUS-002` is an experimental **Sovereign Titan Fusion** design; it is not activatable in this runtime. Both have `enabled_for_native_activation=false` until a physical adapter, native compiler and multiplayer acceptance exist.

## Runtime contract

`verse/sovereign/fusion_state_runtime.verse` is a session-keyed service. A single trusted controller leases the service with `AcquireController`. The controller may call `BeginActivation` only for the live, authority-verified creator and only while Dormant; this returns a monotonic generation token. The service moves through **Dormant → Activating → Active → Separating → Dormant**. `ConfirmActivated` is permitted only after the future physical adapters report success. `BeginSeparation` checks live authority again. The controller must remove physical effects before `CompleteSeparation`. On interruption, owner death, lost reference, disconnection or shutdown, the controller must remove owned physical effects **before** `Abort` or `ReleaseController`. `ReleaseController` now fails while the canonical phase is Activating, Active, or Separating (or FormId has not been cleared); it cannot silently reset an active phase and allow a replacement controller to inherit uncleared effects. The owner identity remains sticky after successful lease release. A failed release must be logged and the device must remain disabled until cleanup is reconciled. These cleanup paths intentionally do not require current authorization. Every new activation or abort invalidates stale async callbacks through the generation counter.

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

## Integration handoff and release evidence (2026-11-01)

**Architect-owned contract; no native entitlement granted by this document.**
Avatar PR #48 owns its attack-input bridge and Titan feasibility study. Arsenal
owns hit validation and checked resource transactions. Cinematics owns
instigator-only effects and reduced-intensity alternatives. QA owns independent
source-mutation and two-client Launch Session acceptance. No loop should edit
another loop's device adapter without coordination in issue #37.

### Handoff requirements

1. **Authority:** every activation and attack request must originate from the
   leased controller, verified live native owner, exact active character, and
   current FUS-001 generation. Never infer authority from cosmetic identity,
   display name, a trigger firing, or an NPC proxy.
2. **Activation:** reserve budget, apply native effects, confirm the dedicated
   effect acknowledgement, then commit Active. Partial failure must unwind
   physical effects before aborting. A trigger is a request, never evidence
   of damage, fusion success, or successful possession.
3. **Separation:** disable further attack inputs, cancel outstanding callbacks,
   restore camera/effects/cinematics on the original character, then finalize
   the canonical phase. Test disconnect and respawn between every transition.
4. **Arsenal:** bind Avatar's AttackOutput only to a range-, target-, team-,
   and faction-checked server-side damage adapter. Revalidate token and
   resource budget at acceptance; reject repeated inputs and stale callbacks.
5. **Cinematics:** pair crimson/violet telegraphs with shapes, motion or audio
   cues that remain legible without color; provide reduced-flash and
   reduced-intensity alternatives. Effects must be cancellable on teardown.

### Native acceptance evidence table (all unverified until captured)

| Gate | Evidence required | Owner |
| --- | --- | --- |
| Native Verse compiler | Exact commit, UEFN version, complete diagnostics | QA |
| Owner provisioning | Trusted native Player Reference, spoof and second-client denial | Architect / QA |
| Activation and recovery | Two-client phase logs, respawn/rejoin and interrupted teardown | Avatar / QA |
| Combat | Target/range/faction proof, damage receipt, budget and cooldown | Arsenal / QA |
| Presentation | Instigator-only camera/VFX/audio and accessible cue alternatives | Cinematics / QA |
| Streaming | World Partition boundary crossings, HLOD transitions, two separated clients | Avatar / QA |
| Cooked publish budget | Editor Memory Calculation at exact cook (300 MiB limit) | QA |
| Runtime memory | Spatial Profiler Live and Memory Snapshot per target platform | QA |

Epic's UEFN documentation distinguishes the **300 MiB cooked publishing
budget** from platform-specific **runtime memory**. Run Memory Calculation
after a cook, and use Spatial Profiler/Memory Snapshot in a monitored Launch
Session; a source CI pass cannot supply these measurements. Streaming and HLOD
must be checked together because generated HLODs add memory and may use
high-resolution geometry when source meshes lack appropriate LODs.

Do not promote FUS-001 to native-enabled or FUS-002 to playable, or claim a
published island, until all relevant gates have independent evidence. Preserve
canonical IDs, existing profile schemas and the owner's sticky session
identity. This handoff changes no runtime entitlement or existing gameplay.

## Authoritative Reaver admission receipt (source adapters wired; native binding unverified)

`IssueAttackReceipt(Controller, Player, Generation)` records one
**session-scoped, one-use, one-second** FUS-001 Reaver admission for the
currently authorized owner and active generation. A second issuance while
an unexpired receipt is outstanding fails. An expired receipt may be replaced.

`ConsumeAttackReceipt[Controller, Player, Generation]` is failable and
transactional: it checks the live authority, exact owner/controller, active
FUS-001 generation, outstanding receipt, and deadline, then clears the receipt.
Missing, duplicate, expired, revoked, cross-player or stale-generation requests
fail closed. `BeginActivation`, `BeginSeparation`, `CompleteSeparation`,
`Abort`, and `ReleaseController` invalidate pending receipts.

**Avatar handoff (#48):** debit the upstream 10 energy and issue the
receipt **inside the same deciding transaction**, before
`AttackOutput.Trigger(Player)`. If either admission fails, do not charge or
emit a physical attack request. Never mint a receipt from UI/display identity
or a standalone public trigger. Preserve the existing cooldown and exact
`fort_character` check.

**Arsenal handoff (#49):** consume a receipt inside the same failable
`TryRend` transaction as the secondary 5-energy debit and cooldown
reservation. The transaction must roll both back on failure. Reject any
`RendRequest.TriggeredEvent` without a paid, outstanding receipt. Only after
canonical admission and independent MON-/range/faction/vulnerability checks
should native damage be attempted. Trigger delivery and receipt consumption
are **not** hit/damage acknowledgements.

**Trust boundary:** a `trigger_device` callback supplies an instigator,
not a cryptographically authenticated call origin. A forged callback could
consume a *real* pending admission before the legitimate callback. The
one-use receipt prevents a no-upstream-debit attack and duplicate reuse; it
does not make a misconfigured editor graph trustworthy. Before enabling,
verify exclusive device bindings, latency/replay under two players, shutdown,
session replacement, and UEFN's actual callback ordering. Source-level Avatar and Arsenal receipt admission was integrated by merged
PR #64. This does **not** authenticate the editor-bound trigger graph or establish
native Verse compilation, physical hit confirmation, or source-to-native binding.
The contract's `native_adapter_wiring` remains `pending` until independently
verified in UEFN. FUS-002 remains disabled.

## Paid Reaver CI reconciliation and handoff (source only)

The Architect reconciliation branch restores a blocking cross-file source guard
against the **actual separate production files**. It requires the Avatar upstream
energy debit and acknowledged single-use receipt issuance in one admission before
the attack trigger; then Arsenal's transactional receipt consumption, downstream
5-energy debit/cooldown, and the native `OnRend` damage statement nested under
successful `TryRend`. It rejects removed receipts, modified transaction order,
missing native handlers, calls outdented from the guarded block, and additional
unpaid damage branches. This is a conservative source-text validator, **not**
a Verse compiler, formal security proof, or UEFN integration test.

Run from the repository root:

```bash
python tools/validate_fusion_architecture.py
python -m unittest discover -s tests -p 'test_fusion_*.py' -v
```

The ordinary non-Codex Verse Static Validation workflow runs both on applicable
source changes. A green job proves those source checks ran; it does not validate
physics collision, wall/cover line-of-sight, native damage attribution, input
provenance, concurrency behavior, or player-facing animation.

### Unresolved authorization and resource boundaries

- **Attack cooldown mismatch:** the Avatar's current editable
  `AttackCooldownSeconds` is 1.5 by default and accepts 0.2 seconds; Arsenal
  requires a separate 2-second Reaver cooldown. A paid upstream trigger may
  be refused downstream, creating an energy-loss experience. Avatar owns the
  proposed 2-second parity fix; it must retain a test proving no timing bypass.
- **Missing/invalid target:** the upstream 10 energy is charged before the
  Arsenal target, LOS and damage acceptance stages. Source receipts prevent
  unpaid/duplicate authorization, **not** unsuccessful charges. Arsenal/Avatar
  must specify the miss-cost policy or a two-phase reservation/acknowledgement.
- **Receipt stealing:** a misbound or injected `trigger_device` callback may
  consume a real pending receipt before the legitimate callback, even though
  it cannot mint one. Confirm exclusive device bindings and two-client ordering
  in UEFN, including expiry and rapid input races.
- **Teardown ownership:** any revocation, character replacement, disconnect,
  interrupted cinematic, or form abort must cancel callbacks and remove all
  owned physical effects before release. Reject stale generations and keep
  cleanup possible even after entitlement is lost.
- **Native hit gate:** target range/cone is not collision/cover. Keep both
  fusion forms native-disabled until an actual hit-confirmed LOS/collision
  adapter and UEFN two-client verification exist.

Preserve the original `UNI-001`, `FUS-001` and `FUS-002` identities, the
one existing player-profile root, and the universe-first source-completion
gate from issue #84. No new public entitlement, editor enablement, asset import,
real-money spending, or automatic Codex review is authorized by these guards.
