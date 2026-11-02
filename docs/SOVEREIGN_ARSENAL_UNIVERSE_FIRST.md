# AEONFALL — Sovereign Arsenal universe-first completion contract

**Decision:** Finish the complete authored UEFN universe before attempting a playable prototype. This is a source-only expansion of the creator-exclusive One True Omnigod Sovereign arsenal, **not** native gameplay completion. `FUS-001` remains disabled; `FUS-002` Titan remains experimental and disabled.

## Inventory and status

`content/sovereign/sovereign_arsenal_universe_contract.json` now specifies twelve distinct crimson-violet machine-demon abilities across weapon, armor and class slots. SFA-001 Reaver, SFA-002 Cataclysm and SFA-003 Aegis mirror the three existing disabled Verse-source abilities exactly. SFA-004 Chainhook, SFA-005 Graviton Lattice, SFA-006 Overclock, SFA-007 Null-Tether, SFA-008 Bastion Vent, SFA-009 Scarlet Fracture, SFA-010 Echo Step, SFA-011 Verdict and SFA-012 Requiem are **design-only**: no new native adapters or device bindings are claimed.

Each ability has a unique mechanical identity, quantitative energy/cooldown/target/damage/shield/duration ceilings, an explicit counterplay rule, a readable telegraph, and separate planned mesh/animation/VFX/audio/accessibility artifacts. The schema is intentionally conservative: damage targets are vulnerable registered `MON-` NPCs only; no player, boss, companion or sovereign-army damage; no immunity, permissions, status or progression bypass. Shield restoration shares the existing 40-point per-generation allowance. The existing Reaver 10+5 energy payment and four-second CLS-006 mark bonus remain unchanged. All twelve require existing creator authority and a canonical FUS-001 controller/generation lease.

## Deterministic validation

Run `python tools/validate_sovereign_arsenal_universe.py` and `python -m unittest tests.test_sovereign_arsenal_universe -v`. The validator compares the first three definitions against the existing live-source policy and rejects loosened ownership, unlocked prototype/native gates, unsafe targeting, resource overflows, duplicate mechanics, missing asset plans, and fabricated native evidence. The dry-run model exercises all twelve bounded contracts, cooldown persistence, mark expiry, shield sharing, cover rejection, finisher thresholds and denied requests. It is **not** a Verse compiler or a damage simulator.

## Non-negotiable remaining work

Complete the rest of the universe-wide world, progression, enemy, encounter, map, content, animation and accessibility specifications and source assets before authorizing prototype work. For Arsenal specifically, the nine design-only abilities still require reviewed Verse/UEFN implementations; all twelve require real collision/LOS hit-confirmation, device wiring, creator-identity provisioning, native compile, multiplayer Launch Session, replication and performance/accessibility evidence. Existing direct `fort_character.Damage` paths cannot be enabled merely because source tests pass. Keep the seven native acceptance fields `not_run` until verified evidence exists.

Cross-loop ownership: Architect owns identity/receipt state, Avatar owns physical character/armor integration, Arsenal owns combat contracts and adapters, Cinematics owns visual/audio telegraphs and reduced-flash alternatives, QA owns independent mutation and native acceptance. Preserve `UNI-001`, Transcendent Zero, Axiom Heart, the existing controller and every unrelated branch. Do not merge without normal non-Codex CI checks; do not enable gameplay before universe completion and native acceptance.

## Authoritative admission handoff — reference model, not a live adapter

`tools/sovereign_arsenal_admission.py` supplies a deterministic, **offline** `ArsenalAdmissionOracle` and immutable `AuthoritativeSnapshot`/`RegisteredTarget` evidence interfaces. The reference oracle rejects replayed/out-of-order server events, generation or controller drift, covered or protected targets, duplicate or over-range targets, invalid status/health/shield evidence, and unsafe Echo Step destinations. Tests: `python -m unittest tests.test_sovereign_arsenal_admission -v`. It does not read controller devices, authenticate any actual Fortnite player, raycast, reserve Verse budget or call native damage, shields, movement or VFX. Its result is **never** an authorization token.

**Architect → Avatar → Arsenal (required future native contract):**

1. Architect checks the real session-scoped `IsAuthorizedActive` owner, bound original character, form `FUS-001`, generation and sole controller lease. Client payload, name, team, cosmetics or trigger-device instigator cannot substitute for this check.
2. Avatar uses its ordinary paid-attack transaction and Architect's generation-bound, one-use `AttackReceiptSequence`; Arsenal must verify the sequence directly with the Architect transaction, not accept a client-supplied sequence. A monotonic server clock and single-use record are necessary. On revocation, respawn, separation and loss of lease, stale evidence is invalid.
3. The future native targeting adapter enumerates the **registered actor key and canonical MON- family** of each selected target. It proves alive/vulnerable/nonfriendly/nonboss/nonplayer/noncompanion/nonarmy status, and obtains a real native LOS/cover/geometry-hit result **for each** target in the group. Range and forward cone are only preliminary checks; neither proves a wall is clear. Do not turn on direct `fort_character.Damage` until true collision/LOS preflight or physical hit-confirmation is established.
4. A single authoritative admission transaction binds one event to one ability, debits total **upstream + Arsenal** energy exactly once, respects shared shields and persistent per-ability cooldowns, and records bounded targets and damage. No secondary effect may occur before admission and no retry may spend the same receipt. A multi-pulse attack also needs a per-target/pulse hit ledger to prevent exceeding its one-request damage ceiling.
5. `SFA-010` must have a clear, authored, collision-tested destination in LOS and within **400 cm**, not merely a valid-sounding destination string. `SFA-011` needs a server-observed target health fraction no higher than **25%**. `SFA-007` cannot override native status immunity. `SFA-006` never modifies ability cooldowns and its proposed tempo scalar is capped at **1.15x**. All these mechanics remain design-only until individual Verse adapters and genuine editor proof exist.
6. On successful or failed effect application, the controller should emit a separate attribution/telemetry receipt (generation, event sequence, ability ID, target keys, reason, resource delta, hit/miss and cleanup status) without writing a persistent entitlement or emitting live damage on a source-only build.

**Known source/native mismatch:** the current disabled Reaver path charges the Avatar's upstream 10 energy before downstream targeting; an invalid/missing target can therefore consume upstream energy without a hit. The reference model intentionally describes the stronger future **single transaction** target-preflight/receipt/reservation contract, **not** the existing implemented two-phase native behavior. Do not cite reference tests as proof that this miss-cost, cover gap, or device binding is fixed; issue #52 tracks the required native solution. Existing Arsenals' disabled native source stays untouched by this PR.

**Validation and counterexample scope:** `tests/test_sovereign_arsenal_universe.py` guards contract drift; `tests/test_sovereign_arsenal_admission.py` adversarially exercises target isolation, owner and lease failures, bad timestamps, replay, exhausted energy and shields, class-mark boundedness, destination checks and generation teardown. Passing source tests means these declared reference invariants hold; it does **not** imply Verse compilation, physical line-of-sight, editor bindings, two-client play, Fortnite-mobile performance, or full-universe readiness.


## Malformed-evidence event policy (independent QA finding, 2026-11-01)

The offline admission oracle now performs **exact runtime shape validation before
touching the replay clock or event sequence**. Python dataclass annotations are
not a security boundary. It rejects non-snapshot objects, non-target objects,
unhashable/non-string target IDs, forged target subclasses, bool-as-int fields,
truthy-string booleans, non-finite measurements, malformed shield and destination
fields, and mutable target containers with a denied receipt rather than an
exception. Rejection leaves energy, cooldowns, mark, shield allowance,
last-event sequence and server time unchanged.

The event policy is intentionally split: **malformed evidence never consumes
an event**; a structurally valid, authenticated event that fails a gameplay
preflight (LOS, vulnerability, cooldown, insufficient energy, etc.) **does
consume its sequence and monotonic timestamp**, but does not debit energy or
apply any effect. This prevents reusing the same valid event after a miss
without allowing malformed data to corrupt the deterministic ledger. Eight
adversarial tests enforce both cases, including a successful cast followed by
a malformed cast and a same-sequence valid retry.

This is a source-only safety model. The actual Verse adapter must obtain
typed evidence from the server's authoritative actor registry, native collision
checks and identity/receipt service; client-provided snapshots and this Python
oracle are **never** permission or damage authorization. The existing disabled
native Reaver path still has the upstream miss-cost/LOS blockers documented
above. The complete-universe source gate remains closed, and native UEFN,
Fortnite-mobile and 300 MiB cooked-memory acceptance are unverified.


## Native combat hard stop — not editor-toggleable

`verse/sovereign/sovereign_arsenal_device.verse` now has a
**non-`@editable` `NativeSourceGate:logic = false`**, checked as the
first executable operation in `OnBegin`. Merely setting the existing
`Enabled` property in UEFN cannot subscribe inputs or reach direct
`Damage`/`SetShield` while this source-first lock remains closed.
The three existing bounded native-source routines remain in place for
future integration; the nine additional abilities remain design-only.

`python tools/validate_sovereign_arsenal_source_lock.py` and
`python -m unittest tests.test_sovereign_arsenal_source_lock -v`
validate the hard stop and mutation-test its non-editable placement,
unconditional early return, unchanged entrypoints, and universe-first
contract. These are static/source checks, not native Verse compilation.
After **all** #84 full-universe source packages are complete, a dedicated
reviewed native-verification branch may replace this lock **together with**
a genuine collision/LOS adapter. Do not merge or enable/publish that change
until actual UEFN compilation, multiplayer, Fortnite-mobile, accessibility
and 300 MiB cooked-memory acceptance have passed. Do not claim that editor
toggles or green Python tests activate abilities.
