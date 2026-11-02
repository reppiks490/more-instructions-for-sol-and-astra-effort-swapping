# AEONFALL FUS-001 — deterministic hit/pulse journal (source-only)

**Scope:** creator-only One True Omnigod Sovereign Arsenal, under master issue #84 and the full 840+-entity, 13-region, 13-system universe-first source policy. This source increment is **not** a playable prototype, a native UEFN adapter, a completed system pack or an entitlement. The non-editor-toggleable Verse NativeSourceGate remains false; FUS-002 Titan remains disabled.

## Implemented source

- `tools/sovereign_arsenal_hit_journal.py` models a finite post-admission hit journal for the eight offensive SFA abilities; self-only armor, tempo and reposition actions intentionally have no damage slots.
- Canonical offensive damage/pulse/target bounds are pinned. Each generation+event sequence is staged once; each target+pulse is resolved once. Well-formed server-observed misses consume their slot, while malformed evidence consumes nothing. An expired/closed event cannot be reopened. Revocation invalidates all outstanding plans.
- Each request is capped at 54 damage, three registered monster targets, and two pulses (only SFA-005 uses two). The CLS-006/SFA-002 four-point synergy applies only once on the specifically marked target if its hit is confirmed. Journal capacity is 64 simultaneous active events, a **runtime memory bound**, not a limit on authored universe content.
- `plan_from_admission()` translates a source-only admitted receipt into a checked hit plan. **It cannot authenticate any receipt, actor, LOS, controller, energy debit, or native collision.** It must never be exposed to clients as a gameplay authorization mechanism.

## Required future authoritative Verse/UEFN handoff — NOT IMPLEMENTED

1. Architect validates the sole creator owner, session generation, controller lease, and one-use paid attack receipt. Avatar upstream and Arsenal downstream debits must be a single atomic transaction; current two-phase Reaver miss-cost remains an unresolved native-source issue (#52).
2. Server resolves real registered actor keys, live vulnerable/nonfriendly/nonboss/nonplayer/noncompanion status, finite range and cone, physical LOS/cover and collision. A `MON-` string and a Python `RegisteredTarget` are never sufficient native evidence. Status immunity and boss mechanics cannot be bypassed.
3. After real atomic admission, bind one paid receipt to its exact target/pulse plan. Native hit/miss callbacks must be generation-scoped, serialized, revalidated before effect, and acknowledged once. Teardown, owner revocation, disconnect, death and region unload must invalidate pending callbacks.
4. Native code must ensure concurrency cannot exceed the request cap or apply any effect before admission. No player, ally, companion, sovereign-army or invulnerable damage, unbounded effects, persistent owner grant or permission changes.
5. Native verification still requires actual Windows UEFN Verse compilation, editor bindings, real collision/LOS, multiplayer/two-client tests, Fortnite-mobile performance/accessibility, and actual cooked publishing memory under 300 MiB. Offline source tests are not proof of any of these.

## Tests and collaboration

Run `python -m unittest discover -s tests -p 'test_sovereign_arsenal_hit_journal.py' -v` and the full test discovery. The focused suite exercises pulse ceilings, miss replay, malformed evidence, marked-target bonus, stale generation, closure, finite capacity, and handoff from the existing `ArsenalAdmissionOracle`. Source-only results must not be registered as native or approved universe source packages without independent review.

Architect (#37/#87): atomic paid receipt/lease. Avatar: actor identity and teardown. Cinematics (#88): accessible hit telegraphs. QA (#89): independent mutation review, source/native truth. Arsenal: combat bounds and this source journal. No Codex, no new spending, no publication, no changes to other automations or canonical Transcendent Zero/Axiom Heart progression.
