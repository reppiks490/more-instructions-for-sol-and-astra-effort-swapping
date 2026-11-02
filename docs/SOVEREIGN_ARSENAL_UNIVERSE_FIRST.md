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
