# FUS-001 Sovereign Arsenal — per-pulse source observation gate

**Status: executable offline reference only.** This is not a Verse adapter, a
UEFN collision result, a paid native transaction, an imported asset, a source
package approval, or a playable prototype. Master issue #84 requires the
complete 840+-entity, 13-region, 13-system source universe first. The
non-editor-toggleable `NativeSourceGate=false` stays in place. FUS-002 Titan,
Transcendent Zero, Axiom Heart, and all creator entitlements remain unchanged.

## New source contract

`tools/sovereign_arsenal_observation_gate.py` wraps the existing
`SourceHitJournal` and adds a **fresh per-pulse actor/cover/authority check**.
The existing journal alone deliberately accepts a boolean hit confirmation;
that boolean is insufficient for safe native effects. A native server must
produce the complete observation after real collision/LOS and before each
separately acknowledged effect. The Python class is a behavioral oracle only.

1. **Paid admission precedes staging.** Architect's native server must bind
   the sole owner, controller lease, session generation, monotonic event ID,
   atomic upstream+downstream energy debit, cooldown, and exact target list.
   A Python `HitPlan`, `BoundActor`, or `HitObservation` can be forged by a
   caller; none is a credential. The gate cannot authenticate the payment.
2. **Actor identity is instance-bound.** Each canonical `MON-` target is bound
   to a unique live server actor key and exactly one of `REG-001`–`REG-013`.
   All targets of an attack must occupy the same region. Actor replacement,
   region transfer/unload or key mismatch closes the event without damage.
3. **Each pulse rechecks live protections.** Registry membership, life,
   vulnerability, boss/player/friendly/companion/sovereign-army exclusion,
   invulnerability, physical cover/LOS, cone, finite range and health are
   independently checked on every callback. SFA-007 respects native status
   immunity; SFA-011 requires current health at or below 25%. No direct
   native status, displacement, teleport, shield or damage call exists here.
4. **Misses are terminal.** A valid but protected/covered target consumes its
   unique pulse slot with zero proposed damage, as does a real collision miss.
   Malformed observations do not mutate the journal. Duplicate pulses cannot
   be converted from misses to hits. The class-specific SFA-002/CLS-006
   four-point bonus remains one-use on the bound marked target.
5. **Finite lifecycle.** A plan lasts at most 6,000 ms, contains at most
   three targets and two pulses, and the journal holds at most 64 active
   events. These are runtime bounds, **not universe content limits**.
   Completion closes the event; owner/lease revocation clears all plans and
   blocks restaging until the generation increases. A stale generation never
   replays. Event damage stays within the canonical 54-point request cap.
6. **Presentation is separate.** Cinematics must attach unique crimson/violet
   telegraphs, non-color-only silhouettes, audio/subtitles, reduced-flash and
   touch-safe cues to each SFA ID. Presentation must not drive targeting or
   gameplay authorization. Region-specific audio/VFX streaming must honor
   mobile concurrency budgets and cleanup on unload.

## Thirteen-region stream epoch and actor retirement source contract

The offline gate now models world-stream unload and actor despawn without
changing any native enablement, privilege or progression. Each `BoundActor`
and `HitObservation` carries a positive, bounded `region_epoch` (initial
reference epoch 1). A staged paid plan must use the current epoch for its
single canonical region; every pulse must match both the bound instance key
and epoch. An epoch mismatch closes the whole event with no further proposed
damage. Existing 54-point, three-target, two-pulse and 64-plan ceilings hold.

- `retire_region(REG-nnn)` synchronously closes every outstanding paid event
  bound to that region, including partly settled multi-pulse attacks. It
  quarantines the region from *new* staging. Repeat unload is idempotent.
- `resume_region(REG-nnn, new_epoch)` requires a **strictly increasing**
  positive server-issued epoch after retirement. It does not revive any old
  event or refund spent resources. New actors must be rebound to that epoch.
  A controller generation change does **not** clear a retired region.
- `retire_actor(actor_key, region_id, region_epoch)` closes every active
  event containing that exact server actor incarnation. It does not authorize
  reuse of an actor key; native registry keys must remain incarnation-unique.
- Malformed regions/epochs/actor keys are rejected without mutation. This
  bounded ledger stores at most one epoch per canonical region, with no
  unbounded region or retired-event history.

**Required native integration order:** world-stream unload/despawn must first
stop native collision callbacks, then retire matching paid events under the
same server serialization boundary, and only then release actor bindings.
Region reload must register fresh actors and publish a new authoritative
epoch before staging. No client, cinematic event or editable device can
supply or advance the epoch. A native effect acknowledgement and actual
collision/LOS remain separate missing work; these Python methods cannot
prove physical ordering, atomicity or Fortnite replication.

## Mandatory native handoff (not completed)

Architect #37/#87 owns one-use atomic paid receipts and trusted owner lease.
Avatar owns live actor keys, FUS-001 armor controller, and region teardown.
World #86 owns the 13-region lifecycle and unload signal. Cinematics #88 owns
individual per-ability art/audio/animation, accessible telegraphs and mobile
fallback. Content #85 owns the distinct catalog entity packages, not an
Omnigod-only substitution. Independent QA #89 must mutate actor keys,
protected flags, time, paid receipts and generation; verify real UEFN Verse
compilation, native collision, two-client replication, Fortnite-mobile
controls/performance, and actual cooked publishing memory <=300 MiB later.

A native adapter must serialize concurrent callbacks and perform effect writes
atomically with the hit acknowledgement; **this Python reference does not**.
No callback can be trusted merely because it resembles a dataclass or carries
`MON-` text. Source tests exercise all eight offensive SFA contracts and all
13 region IDs; they cannot establish UEFN gameplay correctness.

Run focused tests with:

`python -m unittest discover -s tests -p 'test_sovereign_arsenal_observation_gate.py' -v`

Keep the full source-completion and native-completion audit gates independent.
No Codex, no unapproved spend, no branch deletion or early playable claim.
