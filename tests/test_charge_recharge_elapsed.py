"""Source mutation and reference-model checks for elapsed-time charge recovery.

These tests do not compile Verse or execute Fortnite gameplay.
"""
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "verse/combat/ability_runtime.verse"


def source_errors(source: str) -> list[str]:
    errors: list[str] = []
    for name, start, end in (
        ("TickAbility", "    TickAbility(", "    TickAll("),
        ("TickAll", "    TickAll(", "    ClearOwner("),
    ):
        if start not in source or end not in source:
            errors.append(f"{name}: missing function boundaries")
            continue
        body = source.split(start, 1)[1].split(end, 1)[0]
        required = (
            "if (Recharge > 0.0):",
            "set Recharge = Recharge - DeltaSeconds",
            "loop:",
            "if (Charges >= Definition.MaxCharges or Recharge > 0.0):",
            "break",
            "set Charges = Charges + 1",
            "set Recharge = Recharge + Definition.RechargeSeconds",
            "set Recharge = 0.0",
        )
        for token in required:
            if token not in body:
                errors.append(f"{name}: missing {token}")
        if "set Recharge = Definition.RechargeSeconds" in body:
            errors.append(f"{name}: discards elapsed-time remainder")
        positions = [body.find(token) for token in (
            "set Recharge = Recharge - DeltaSeconds",
            "loop:",
            "if (Charges >= Definition.MaxCharges or Recharge > 0.0):",
            "set Charges = Charges + 1",
            "set Recharge = Recharge + Definition.RechargeSeconds",
        )]
        if any(p < 0 for p in positions) or positions != sorted(positions):
            errors.append(f"{name}: charge catch-up ordering is unsafe")
    return errors


def recharge_reference(
    charges: int, maximum: int, remaining: float, period: float, delta: float
) -> tuple[int, float]:
    """Executable reference policy; the Verse source is checked separately."""
    if delta <= 0 or charges >= maximum:
        return charges, remaining
    if remaining > 0:
        remaining -= delta
    while charges < maximum and remaining <= 0:
        charges += 1
        if charges < maximum:
            remaining += period
        else:
            remaining = 0.0
    return charges, remaining


class ChargeRechargeElapsedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_both_runtime_paths_preserve_elapsed_remainder(self) -> None:
        self.assertEqual(source_errors(self.source), [])

    def test_reject_single_charge_per_tick_mutation(self) -> None:
        mutated = self.source.replace(
            "loop:\n                    if (Charges >= Definition.MaxCharges",
            "if (Recharge <= 0.0):\n                    if (Charges >= Definition.MaxCharges",
            1,
        )
        self.assertNotEqual(mutated, self.source)
        self.assertTrue(source_errors(mutated))

    def test_reject_recharge_timer_reset_mutation(self) -> None:
        mutated = self.source.replace(
            "set Recharge = Recharge + Definition.RechargeSeconds",
            "set Recharge = Definition.RechargeSeconds",
            1,
        )
        self.assertNotEqual(mutated, self.source)
        self.assertTrue(source_errors(mutated))

    def test_short_tick_only_reduces_timer(self) -> None:
        self.assertEqual(recharge_reference(1, 4, 3.0, 3.0, 1.0), (1, 2.0))

    def test_stall_recovers_multiple_charges_and_remainder(self) -> None:
        self.assertEqual(recharge_reference(0, 5, 3.0, 3.0, 10.0), (3, 2.0))

    def test_stall_caps_at_maximum(self) -> None:
        self.assertEqual(recharge_reference(1, 4, 2.0, 2.0, 100.0), (4, 0.0))

    def test_zero_or_negative_delta_does_not_advance(self) -> None:
        self.assertEqual(recharge_reference(0, 3, 2.0, 2.0, 0.0), (0, 2.0))
        self.assertEqual(recharge_reference(0, 3, 2.0, 2.0, -1.0), (0, 2.0))


if __name__ == "__main__":
    unittest.main()
