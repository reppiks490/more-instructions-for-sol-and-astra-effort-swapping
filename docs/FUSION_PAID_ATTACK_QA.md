# Independent FUS-001 paid-attack QA gate

This opt-in source audit reads **three different production files**: Avatar
`sovereign_fusion_device.verse`, Arsenal
`sovereign_arsenal_runtime.verse` and
`sovereign_arsenal_device.verse`. Run:

```bash
python -m unittest tests.test_fusion_paid_attack_audit -v
python tools/audit_fusion_paid_attack.py
```

The first command checks 13 deterministic fixtures/mutations. The second
intentionally **fails on the current main integration**: Avatar currently
debits 10 energy and signals without issuing the canonical receipt; Arsenal
charges 5 but does not consume that receipt. The physical trigger's owner
payload is not proof of a paid upstream admission. Do not merge or enable the
attack bridge on the strength of independent component tests.

The audit does not claim Verse syntax correctness, actual device binding
provenance, atomic rollback under engine semantics, real multiplayer
concurrency, native damage/LOS, or camera/VFX budget compliance. Source-only
checks can be bypassed by syntactically different code; after repair,
reconcile this checker with actual methods, add it to the blocking workflow,
and capture native UEFN compile + two-client Launch Session evidence.

Required editor cases: same-owner spoofed trigger, other-player spoof,
duplicate and expired receipt, failed secondary energy debit with no consumed
receipt, generation change, simultaneous callbacks, owner death/leave,
rollback of camera/armor effects, NPC proxy late spawn/teardown, and bounded
audio/VFX under two clients. Record the exact commit and UEFN project version.
This document creates no native evidence and changes no enabled defaults.

Coordination: Architect issue #37 and PR #62; Arsenal native acceptance #52;
Avatar Titan draft #58; Cinematics draft #61; publication gate #17.
