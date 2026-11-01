"""Source mutation and reference-policy checks for activation timeout ownership.

These checks inspect Verse source and a Python reference policy; they are not
native UEFN compilation, Verse execution, or a Fortnite Launch Session.
"""
from __future__ import annotations

from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "verse/combat/activation_coordinator.verse"


def method(source: str, name: str, next_name: str) -> str:
    return source.split(f"    {name}(", 1)[1].split(f"    {next_name}(", 1)[0]


def source_errors(source: str) -> list[str]:
    errors: list[str] = []
    try:
        update = method(source, "TryUpdatePendingTimeout", "TickPendingActivations")
        tick = method(source, "TickPendingActivations", "ClearOwnerPending")
        cancel = method(source, "CancelPending", "TryUpdatePendingTimeout")
    except IndexError:
        return ["timeout helper or method boundaries missing"]

    for token in (
        "Existing := PendingActivations[RequestId]",
        "Existing.OwnerKey = Next.OwnerKey",
        "Existing.AbilityId = Next.AbilityId",
        "set PendingActivations[RequestId] = Next",
    ):
        if token not in update:
            errors.append("deadline update must preserve identity and original entry: " + token)

    for token in (
        "if (DeltaSeconds <= 0.0):",
        "for (RequestId -> Pending : PendingActivations):",
        "Remaining:float = Pending.TimeoutRemainingSeconds - DeltaSeconds",
        "for (RequestId -> Next : Updated):",
        "Advanced := TryUpdatePendingTimeout(RequestId, Next)",
        "for (Pending : Expired):",
        "Cancelled := CancelPending(",
        "if (Cancelled?):",
        'EventType := "ability.adapter_timeout"',
    ):
        if token not in tick:
            errors.append("timeout lifecycle guard missing: " + token)

    if "set PendingActivations = Updated" in tick:
        errors.append("timeout tick must not drop expired or failed entries via bulk replacement")
    if "ReleaseReservation" in tick:
        errors.append("timeout tick must not release class reservation outside coordinator cancel")
    if "GetAEONFALLAbilityRuntime().CancelPending" in tick:
        errors.append("timeout tick must not bypass coordinator cancellation")
    if tick.find("Cancelled := CancelPending(") > tick.find('EventType := "ability.adapter_timeout"'):
        errors.append("timeout notification must follow cancellation")
    if "Cancelled := GetAEONFALLAbilityRuntime().CancelPending" not in cancel:
        errors.append("coordinator cancellation must cancel canonical ability state")
    if "Released := GetAEONFALLClassRuntime().ReleaseReservation(RequestId)" not in cancel:
        errors.append("coordinator cancellation must release class reservation")
    return errors


def advance_reference(
    pending: dict[str, float], delta: float, cancellable: set[str]
) -> tuple[dict[str, float], list[str]]:
    """Expected timeout ownership: failed cancels stay pending for a retry."""
    remaining = pending.copy()
    timed_out: list[str] = []
    if delta <= 0:
        return remaining, timed_out
    for request_id, seconds in pending.items():
        new_seconds = seconds - delta
        if new_seconds > 0:
            remaining[request_id] = new_seconds
        elif request_id in cancellable:
            del remaining[request_id]
            timed_out.append(request_id)
    return remaining, timed_out


class ActivationTimeoutAtomicityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SOURCE.read_text(encoding="utf-8")

    def assert_mutation_rejected(self, before: str, after: str) -> None:
        self.assertIn(before, self.source)
        mutant = self.source.replace(before, after, 1)
        self.assertNotEqual(mutant, self.source)
        self.assertTrue(source_errors(mutant))

    def test_current_source(self) -> None:
        self.assertEqual(source_errors(self.source), [])

    def test_reject_bulk_map_replacement(self) -> None:
        self.assert_mutation_rejected(
            "        for (RequestId -> Next : Updated):\n            Advanced := TryUpdatePendingTimeout(RequestId, Next)",
            "        set PendingActivations = Updated",
        )

    def test_reject_direct_runtime_cancel(self) -> None:
        self.assert_mutation_rejected(
            "            Cancelled := CancelPending(\n                Pending.OwnerKey,",
            "            Cancelled := GetAEONFALLAbilityRuntime().CancelPending(\n                Pending.OwnerKey,",
        )

    def test_reject_early_class_release(self) -> None:
        self.assert_mutation_rejected(
            "        for (Pending : Expired):\n            Cancelled := CancelPending(",
            "        for (Pending : Expired):\n            Released := GetAEONFALLClassRuntime().ReleaseReservation(Pending.RequestId)\n            Cancelled := CancelPending(",
        )

    def test_reject_missing_owner_guard(self) -> None:
        self.assert_mutation_rejected(
            "Existing.OwnerKey = Next.OwnerKey",
            "Existing.OwnerKey = \"\"",
        )

    def test_reject_missing_deadline_write(self) -> None:
        self.assert_mutation_rejected(
            "set PendingActivations[RequestId] = Next",
            "set Updated[RequestId] = Next",
        )

    def test_reference_cancels_expired_only_once(self) -> None:
        result, events = advance_reference({"a": 1.0, "b": 4.0}, 2.0, {"a"})
        self.assertEqual(result, {"b": 2.0})
        self.assertEqual(events, ["a"])
        result, events = advance_reference(result, 1.0, {"a"})
        self.assertEqual(result, {"b": 1.0})
        self.assertEqual(events, [])

    def test_reference_failed_cancel_remains_retryable(self) -> None:
        result, events = advance_reference({"a": 0.5}, 1.0, set())
        self.assertEqual(result, {"a": 0.5})
        self.assertEqual(events, [])
        result, events = advance_reference(result, 0.25, {"a"})
        self.assertEqual(result, {})
        self.assertEqual(events, ["a"])

    def test_reference_nonpositive_delta_is_noop(self) -> None:
        self.assertEqual(advance_reference({"a": 0.5}, 0.0, {"a"}), ({"a": 0.5}, []))
        self.assertEqual(advance_reference({"a": 0.5}, -2.0, {"a"}), ({"a": 0.5}, []))


if __name__ == "__main__":
    unittest.main()
