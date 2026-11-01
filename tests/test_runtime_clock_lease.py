"""Source mutation tests for the single-owner Verse runtime scheduler.

These tests inspect text and do not compile Verse or run Fortnite.
"""
from pathlib import Path
import unittest

from tools.validate_runtime_invariants import check_runtime_clock

ROOT = Path(__file__).resolve().parents[1]
CLOCK = ROOT / "verse/core/runtime_tick_device.verse"


class RuntimeClockLeaseSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = CLOCK.read_text(encoding="utf-8")

    def assert_rejected(self, original: str, changed: str, expected: str):
        self.assertIn(original, self.source)
        mutant = self.source.replace(original, changed, 1)
        self.assertNotEqual(mutant, self.source)
        self.assertIn(expected, " ".join(check_runtime_clock(mutant)))

    def test_current_clock_has_single_owner(self):
        self.assertEqual(check_runtime_clock(self.source), [])

    def test_reject_removed_acquisition(self):
        self.assert_rejected(
            "Acquired := GetAEONFALLRuntimeClockLease().Acquire(Self)",
            "Acquired := true",
            "single-owner lease",
        )

    def test_reject_removed_duplicate_guard(self):
        self.assert_rejected(
            "if (not Acquired?):",
            "if (Acquired?):",
            "single-owner lease",
        )

    def test_reject_wrong_owner_release(self):
        self.assert_rejected(
            "if (Current := Owner?, Current = Device):",
            "if (Current := Owner?):",
            "single-owner lease",
        )

    def test_reject_early_clock_start(self):
        self.assert_rejected(
            "        Acquired := GetAEONFALLRuntimeClockLease().Acquire(Self)",
            "        set Running = true\n        Acquired := GetAEONFALLRuntimeClockLease().Acquire(Self)",
            "reject duplicate ownership",
        )

    def test_reject_missing_shutdown_release(self):
        self.assert_rejected(
            "Released := GetAEONFALLRuntimeClockLease().Release(Self)",
            "Released := true",
            "single-owner lease",
        )

    def test_reject_shutdown_without_ownership_guard(self):
        self.assert_rejected(
            "        if (Running?):\n            set Running = false",
            "        if (not Running?):\n            set Running = false",
            "release only its own active lease",
        )


if __name__ == "__main__":
    unittest.main()
