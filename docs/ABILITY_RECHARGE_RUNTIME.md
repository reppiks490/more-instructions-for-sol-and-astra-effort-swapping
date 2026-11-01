# Charge recovery under scheduler stalls

The canonical scheduler advances Verse runtime state by elapsed simulation time rather than the requested Sleep duration. The ability runtime now applies that elapsed delta to **every charge period crossed**, rather than replenishing at most one charge per scheduler iteration. Both `TickAbility` and `TickAll` share the same policy.

A depleted ability with 0/5 charges, 3 seconds to its next charge, a 3-second recharge period, and a 10-second elapsed tick should recover **3 charges** and retain **2 seconds** until the next charge. Recovery stops at `MaxCharges` and clears the recharge timer when full. Zero/negative elapsed ticks do not advance state.

The authored first-slice combat validator requires `RechargeSeconds > 0` for charge abilities. A project-bound native UEFN compile must still verify Verse syntax, and a Launch Session must exercise short ticks, long stalls, multiple players, cancellation, respawn/rejoin, and late adapter results. The Python reference tests and source mutation checks are **not** a native Verse execution or Fortnite test.

Manual first-playable acceptance:
1. Equip a charge-based ability with at least four charges and a positive recharge period.
2. Spend multiple charges; record displayed charge count and next recharge deadline.
3. Simulate or observe an elapsed interval spanning multiple recharge periods; verify the count catches up and preserves the partial remainder.
4. Repeat near maximum charges and across multiple players; verify no overfill or cross-player leakage.
5. Verify native Verse Build succeeds and capture actual Launch Session evidence before marking this behavior implemented/tested in UEFN.
