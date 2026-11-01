# Activation timeout ownership — source-level correction (2026-11-01)

## Failure mode

The activation coordinator previously rebuilt `PendingActivations` from only
nonexpired entries **before** canceling expired requests. It also released the
class-resource reservation before verifying that the matching ability request
could be canceled. A failed cancellation could therefore lose coordinator
ownership of an in-flight request, and a failed map reconstruction could drop
unrelated requests. Both are unacceptable for first-playable combat.

## New policy

- Collect timeout candidates without mutating the pending map during iteration.
- Advance live deadlines with identity-checked, per-request map writes; a failed
  write retains the previous record rather than replacing the whole map.
- For expired requests, call `aeonfall_activation_coordinator.CancelPending`
  while the original pending record still exists. This checks owner, ability,
  request ID, and canonical pending state.
- Only that coordinator cancellation path releases the class reservation.
- Emit `ability.adapter_timeout` only when cancellation succeeds.
- Keep an expired request whose cancellation fails for another attempt. Do not
  silently erase its ownership or claim that it timed out successfully.
- Preserve existing ability/resource policy, timeout duration, persistence
  schema, and adapter contracts.

The source-mutation tests in `tests/test_activation_timeout_atomicity.py`
cover the ordering and the retry policy. The Python reference policy does not
execute Verse; it is not proof of atomicity under Fortnite runtime effects.

## Native UEFN acceptance gate

1. Compile the integrated Verse project in UEFN. Record compiler version and
   diagnostics; source validation cannot replace this step.
2. Place the runtime tick device, an ability input, the effect adapter and
   result router. Trigger an ability whose adapter intentionally withholds its
   result. Verify its pending state and any reserved class resource.
3. Advance more than the five-second timeout with a delayed simulation update.
   Verify exactly one cancellation, exactly one class-resource release, and
   exactly one timeout event; a late adapter callback must not spend resources.
4. With two players, keep one player's request pending while the other expires.
   Verify the first player's deadline and reservation remain intact.
5. Exercise a deliberate cancellation failure (stale identity or missing
   canonical pending state) and confirm no timeout success event or premature
   class release. Check that the pending record remains available for diagnosis
   or retry.
6. Verify player disconnect and replacement session do not retain stale
   pending requests or resource reservations.

**Evidence boundary:** Repository Python tests and GitHub Actions are static
source checks. There is no claim of a successful UEFN compile, device binding,
or Fortnite Launch Session until the editor provides that evidence.
