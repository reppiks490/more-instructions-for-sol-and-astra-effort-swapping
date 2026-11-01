# Transcendent Zero — Canonical Ascension Contract

## Qualification is not a grant

Transcendent Zero sits above God and Absolute and is awarded only by the Choosing service. The canonical order is **Level 1000 + broad mastery → Trials I–IX → Axiom Heart → Trial X → Zero Candidate → Choosing → Transcendent Zero**. Neither a shop, a recipe completion, a single boss, a triggered effect graph, nor an admin-facing public gameplay control may grant it.

## Candidate baseline

Design prerequisites include Level **1000**, ten mastered classes, forty eligible major/super/world boss clears, twenty eligible world-event clears, completed God and Absolute progression, ten completed Ascension Trials, the crafted Axiom Heart, and hidden lore/mastery gates. These are demanding balance inputs, not a claim that all gates have been verified in a published UEFN session. Do not lower them without evidence.

## The ten canonical trials

These names, ordering and allowed powers mirror `content/transcendent/ascension_trials.json`:

### I — Severance
Enter alone, survive three archetypes, and clear without companions or God/Absolute abilities. No external carry can satisfy the proof.

### II — Collection
Deposit distinct ecology, faction, boss and world-event tributes. Companions and God abilities are permitted; Absolute is not. Repetition of one farming route is insufficient.

### III — Hunter
Defeat eldritch, infernal, colossal, necromantic and mythical threat representatives through their specific counterplay. God is permitted; Absolute is not.

### IV — Dominion
Win a faction conflict, stabilize a corrupted region, hold two objectives and preserve neutral population. Destruction alone cannot substitute for governance.

### V — Memory
Recognize three remixed boss patterns, solve a sequence without HUD prompting and clear the Memory Echo without companions or Absolute abilities.

### VI — Genesis
Build a defensive network, protect three nodes, repair a broken link and win using created space. God abilities and companions are permitted; Absolute is not.

### VII — Restraint
Spare an optional target, disable without an ultimate, protect an ally objective and clear under a power cap. God and Absolute abilities are forbidden.

### VIII — Sacrifice
Temporarily seal the highest-tier loadout, offer designated sovereign sigils, clear with reduced slots and recover sealed relics. No companion or transformed powers; trial-specific tributes may be consumed but equipment must not be destructively deleted.

### IX — Convergence
Stabilize three regions, defeat the Convergence Warden and open the Axiom Forge. God and Absolute abilities are permitted. This is the last trial **before** Heart crafting.

### X — The Final Witness
Requires the crafted Axiom Heart. Complete Force, Shelter, Choice, Company and Final Witness objectives without companions, God or Absolute. Completion creates a Zero Candidate; it is **not** a Transcendent grant.

## Axiom Heart and Choosing

The authoritative material/recipe graph is `content/crafting/axiom_heart_recipe.json`, with a computed design total of **68,420 raw-equivalent acquisitions**, including earned Seed of Zero. `content/progression/axiom_heart_recipe.json` is a non-authoritative progression summary. The final Choosing must consider combat, puzzles, resource discipline, leadership and mastery without purchases, lotteries or a single-stat leaderboard. Live population caps require actual concurrency/persistence testing.

## Bounded apex power

God and Absolute have exact transformation IDs, mutual exclusion and session-only duration/exhaustion. Transcendent Authorities are also temporary, and only persistent eligibility/history survives a session. All physical world-bending effects require project-bound preflight, boss immunity and encounter exception checks, resource budgets, and deterministic teardown. See `docs/APEX_MECHANICS_EXECUTION.md` for the fail-closed adapter boundary. An imported asset, static validator or Python test is not native UEFN compilation or multiplayer Launch Session proof.

## Failure philosophy

Mastery clears and ordinary collected resources remain; designated trial consumables may be lost; failed Choosing attempts use requalification windows rather than account deletion. All checked persistence writes must succeed before an irreversible grant.


## Trial I–X durable completion and retry boundary

Trial completion now requires an acknowledged persistent profile write before
the session trial is marked finished. The trial service cannot emit a completion,
open the Trial IX Axiom Forge, or evaluate a Trial X Zero Candidate after a
rejected save. This protects the intended **Trials I–IX → Axiom Heart → Trial X**
sequence from false success telemetry and session-only progression.

If the final objective is recorded but persistence fails (for example, because
the player becomes inactive or the persistent map refuses the write), the
trial remains active while time remains. Replaying an already-recorded final
objective attempts the *same* durable commit without incrementing objective
counts or charging any material. An expired trial cannot accept another
objective or finalize. After expiry or disconnect, the player must start the
trial again; completion is never fabricated from a session snapshot.

**Verification boundary:** `tests/test_ascension_trial_commit.py` checks
source invariants and the ten canonical IDs. UEFN compilation and a two-player
Launch Session must still exercise (1) normal completion, (2) failed save then
same-objective retry, (3) timer expiry at the final objective, (4) disconnect,
and (5) Trial IX forge / Trial X candidate events. The 68,420-acquisition
Axiom Heart recipe remains a design graph, not an implemented in-island
crafting transaction; this change does not claim to implement that forge.
