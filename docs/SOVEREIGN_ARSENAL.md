# One True Omnigod Sovereign — FUS-001 Arsenal slice

**State:** authored source only; disabled by default. No native Verse compile,
physical device binding, cover/line-of-sight proof, or two-client Launch Session
has been run. This is **not** proof of a playable combat kit. This document
is the Arsenal-specific implementation/change log for this increment.

## Implementation — 2026-11-01

- `FWA-001 Blood-Iron Reaver`: short 350 cm forward-cone strike, 18 native
  damage to one selected, registered, vulnerable `MON-` NPC. The Avatar
  AttackOutput spends 10 energy and issues a one-use receipt in the same\n  deciding transaction. Arsenal consumes that receipt before its separate\n  **5-energy** debit and 2 s cooldown; an owner-tagged trigger alone\n  cannot authorize native damage.
  A validated strike marks its runtime target for 4 s.
- `FWA-002 Violet Cataclysm`: 650 cm forward-cone cleave, **at most 3**
  registered vulnerable `MON-` NPCs, **10 damage each**, 20 energy and
  8 s cooldown. If `CLS-006 Sepulchral Sovereign` is already equipped,
  the Reaver-marked target alone receives +4 within 4 s; no new class grant,
  class switch, persistent unlock or extra resource source is introduced.
  Maximum per-request damage is **34** with this combo.
- `FWA-003 Dreadframe Aegis`: self shield restoration of **at most 20**
  per use, **40 total per fusion generation**, 15 energy, 18 s cooldown,
  and always capped by the native maximum shield. No invulnerability,
  boss-mechanic immunity, status immunity or max-shield increase.
- All costs debit the already merged canonical fusion budget and require
  the Architect's owner/controller/generation authority. Arsenal's
  session lease preserves cooldowns across adapter replacement. The
  canonical owner is never re-provisioned here. No `UNI-001`,
  `Transcendent Zero`, `Axiom Heart`, profile or persistence files change.

## Physical wiring

Place one `aeonfall_sovereign_arsenal_device` with `Enabled=false`.
Bind `Controller` to the exact existing FUS-001 Avatar controller. Bind
`RendRequest` to **that controller's** `AttackOutput` trigger from
merged Avatar source; it must be a dedicated, instigator-preserving trigger with
no external/ambient transmitters, delay or global damage graph. Bind
`CollapseInput` and `BulwarkInput` to two distinct Creative Input
Trigger devices, and `Feedback` to an owner-scoped HUD device. The
existing target selector must register the player and select a live
`MON-` target for Reaver. Do **not** use the same trigger as a generic
damage relay. Keep Avatar and Arsenal disabled until all bindings are
verified in UEFN. The Titan `FUS-002` is not supported.

This adapter uses native `fort_character.Damage` and `SetShield`, not
a synthetic hit acknowledgement. Damage attribution, replication, hit
events, VFX and audio still require project-bound proof. It does **not**
perform a physics raycast: range and view-cone validation cannot
guarantee walls block strikes. **This is a blocking release condition.**
Do not enable the damage adapter in a playable/published map until
the native project implements and tests cover/line-of-sight counterplay.
It also does not override encounter vulnerability phases, damage
immunity, protected bosses, player teams or ally/companion ownership.

## Tests and handoffs

`python tools/validate_sovereign_arsenal.py` performs policy/source
checks. `python -m unittest tests.test_sovereign_arsenal -v` exercises
mutation guards and a separate deterministic **reference model**. These
tests run under the existing AEONFALL Validation workflow's unittest
discovery without changing another loop's workflow file. Neither
Python test runs Verse or proves a native effect.

- **Architect:** review direct use of the canonical state/budget with the
  Avatar controller reference, token validity, cooldown retention and
  FUS-001-only policy. No edits to Architect-owned files.
- **Avatar:** review PR #48 `AttackOutput` wiring and its 10-point
  upstream charge; verify no extra attacker can trigger it.
- **Cinematics:** add owner-scoped crimson/violet telegraphs, readable
  non-color-only attack cues, reduced-flash mode and teardown; do not
  interpret a trigger as a confirmed hit.
- **QA:** mutation tests, two-client owner/nonowner spoof, 10 rapid
  inputs, generation change, disconnect, respawn, resource depletion,
  boss/companion/army immunity, wall cover, damage attribution,
  replication, shield cap, class synergy and cooldown replacement.
  Record native compiler and Launch Session evidence separately.

**No merge without both AEONFALL Validation and Verse Static checks
passing.** No force pushes, branch deletion or unapproved spending.
