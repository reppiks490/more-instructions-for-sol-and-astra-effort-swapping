# AEONFALL Fusion — universe-first cross-loop security perimeter

**Scope:** Architect-owned source audit only. Parent #84, systems #87, independent QA #89, integration #37. This does **not** grant a player any entitlement, change FUS-001/FUS-002 gameplay, certify UEFN, or shorten the 840-entity/13-region production requirement.

Run `python tools/audit_fusion_universe_perimeter.py` and `python -m unittest tests.test_fusion_universe_perimeter -v`. The AEONFALL Validation workflow discovers the tests on ordinary branch pushes. The audit reads canonical contracts and real Verse sources in the Architect, Avatar and Arsenal lanes; it does not modify them. It detects cross-lane authority, entitlement, phase, receipt, resource and native-evidence regressions, including disabled-by-default adapters and the owner-only Titan experiment.

## Authoritative boundary

`UNI-001` remains a creator-only ability, not a progression reward. The trusted `aeonfall_sovereign_authority_device.CanWield(Player)` is the only owner grant; `content/sovereign/owner_identity.json` does not yet contain a verified native account binding. FUS-001 is the sole form admitted by the session state machine. FUS-002 is an experimental NPC proxy **under** the active FUS-001 owner and generation, not a second activatable fusion or native possession.

The state runtime owns exactly one session controller and one sticky owner. The adapter may begin FUS-001 only after current native authorization. Physical application and acknowledgment must precede confirmation. The Avatar must clear camera, powerup and cinematic effects before separation or abort. Controller release is permitted only after Dormant canonical cleanup; stale generations and outstanding paid-attack receipts must be invalidated. The Arsenal may deliver Reaver damage only after the same-owner paid receipt is consumed and secondary budget/cooldown is reserved. An instigator-tagged trigger alone never proves an authorized hit.

## Source truth versus engine proof

This audit checks source text and contract data, and the mutation suite tests that selected unsafe edits are detected. It is not a parser, compiler, runtime security proof, actual asset import, multiplayer test, anti-cheat guarantee or UEFN feature endorsement. Static substring/order checks can miss semantically equivalent changes and subtle Verse control-flow bugs; independent QA must inspect real compiled behavior and editor wiring. No source-only check may turn on authority or FUS-002 or claim that the 840 entities/13 regions are implemented.

## Integration and release gates

Avatar owns physical teardown, current `fort_character` binding and input registration; Arsenal owns server-side target/range/faction/LOS and transactional budget; Cinematics owns cancellable owner-scoped effects and non-color/reduced-flash alternatives; QA owns adversarial source review and two-client native acceptance. The Architect owns canonical state and this audit. Do not edit another lane's code to satisfy an audit without coordination. Native gates remain: exact Verse compile, verified native Player Reference, two-client spoof/respawn/disconnect/rejoin tests, FUS-001 effects and paid attack receipts, FUS-002 NPC Character Definition/SpawnAt if ever enabled, actual Fortnite mobile touch/runtime profiling, and a cooked publishing memory measurement against 300 MiB. All remain unverified until real evidence is recorded.

## Known issue not hidden by this audit

On the inspected main revision, the Avatar permits `AttackCooldownSeconds` as low as 0.2 seconds (default 1.5), while Arsenal Reaver enforces 2 seconds. Architect PR #74 proposes a compatible guard but is merge-conflicted and overlaps existing runtime validation. This branch intentionally does not edit those shared files or merge PR #74; independent review and a clean main reconciliation remain necessary.

## Zero-Codex handoff

The repository has an external **automatic Codex PR review** configuration evidenced by existing bot comments. Ordinary checked-in Actions workflows do not invoke Codex, but opening or readying a PR can trigger the external review. Under the creator's zero-Codex rule, this work is retained on an isolated branch **without opening a PR**. No review request, @codex mention, paid service, force push, or automation change is authorized. The branch can be proposed for merge only after the automatic review is disabled/verified not to trigger and the required non-Codex CI checks pass.
