# AEONFALL — paid FUS-001 Reaver attack receipt handoff

## What this change actually enforces

The existing `aeonfall_fusion_state_runtime` is the **only** authority for
FUS-001 creator identity and the short-lived attack-receipt state.
`IssueAttackReceipt` allows at most one outstanding, one-second,
generation-scoped receipt for the verified live owner and controller.

The Avatar `sovereign_fusion_device.Attack` now requires, inside a single
deciding `if:` transaction:

1. Live native owner and original `fort_character` unchanged;
2. Existing authoritative fusion form/generation and 1.5-second cooldown;
3. The upstream `Budget.Spend[Self, Player, Token, State, AttackEnergyCost]`
   (10 energy by default);
4. `State.IssueAttackReceipt(Self, Player, Token)` returns true, verified by
   `Issued?`.

Only after that admission succeeds can
`AttackOutput.Trigger(Player)` publish an instigator-tagged signal. A refused
receipt issuance must roll back the upstream energy spend. This is **not** an
independently authenticated physical trigger; the server-side receipt is
required for the next stage.

The Arsenal `sovereign_arsenal_runtime.TryRend` then checks the two-second
cooldown and, inside one deciding `<decides><transacts>` function:

1. Calls `State.ConsumeAttackReceipt[Device, Player, Token]` for the same
   owner, leased controller, active FUS-001 generation, native authority,
   and unexpired one-use receipt;
2. Debits an additional 5 energy from the authoritative budget;
3. Updates Reaver cooldown/mark only after both checks.

A failed second spend rolls back receipt consumption and damage is not
authorized. Damage must remain downstream of successful `TryRend`. Missing,
stale, replayed or ambient `TriggeredEvent` payloads do not grant damage by
themselves. Receipt lifetime is one second; delayed native delivery past that
window is a miss, not a license to bypass the gate.

## Remaining non-negotiable native blockers

- `Enabled=false` on the attack bridge and Arsenal until *actual* UEFN
  editor bindings, native Verse compile and a two-player Launch Session pass.
- **Line of sight remains unimplemented.** View-cone/range checks are not
  collision or cover checks. Direct `Target.Damage` cannot be enabled until
  a native projectile/melee hit-confirmation or supported collision preflight
  proves cover resistance.
- Upstream 10-energy charging for a miss/invalid target is currently
  intentional in the source *request* protocol, but not a validated or
  finalized gameplay design. A later two-phase reservation/effect receipt
  may refund misses; do not silently treat every triggered request as a hit.
- One receipt outstanding per fusion generation is not an unlimited attack
  queue. Test burst input, delayed native trigger, expired receipt, duplicate
  binding, spoofed `Trigger(Player)`, rejected secondary debit, controller
  restart, boss/ally/player exclusion, disconnect, respawn, stale callbacks,
  and Axiom/Transcendent state independence.
- The legitimate source model is: **upstream admission → one-use canonical
  receipt → downstream budget/target checks → supported physical effect**.
  No client-supplied token, display name, team, costume or proximity grant.
- Verify actual adapter lifecycle and physical feedback in source-exact
  Fortnite Launch Session; Python tests do not compile or run Verse.

The Architect validator PR #62 and independent QA audit PR #63 provide
additional cross-file regression gates. Integrate them after this wiring,
rather than treating the basic static checks alone as release approval.
