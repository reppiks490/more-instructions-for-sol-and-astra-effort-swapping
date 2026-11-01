"""Mutation guards for the first-acquisition debit boundary.

These tests inspect Verse source; they do NOT compile or execute Verse.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "verse/persistence/profile_service.verse"


def validate_unlock_commit(source: str) -> list[str]:
    errors: list[str] = []
    start = source.find("    CommitMaterialAndUnlock(")
    end = source.find("    SetEquippedClass(", start)
    if start < 0 or end <= start:
        return ["missing durable unlock commit boundary"]
    block = source[start:end]
    duplicate_guard = re.search(
        r"if:\s+Old\.UnlockedEntityIds\.Find\[UnlockEntityId\]"
        r"\s+then:\s+return false",
        block,
    )
    if not duplicate_guard:
        errors.append("duplicate unlock must be rejected at commit")
    if "for (MaterialId -> OldAmount : Old.MaterialLedger):" not in block:
        errors.append("existing ledger keys must be preserved")
    if "UpdatedAmount := NewLedger[MaterialId]" not in block:
        errors.append("existing ledger values must be checked")
    if "for (MaterialId -> UpdatedAmount : NewLedger):" not in block:
        errors.append("new ledger keys must be checked")
    if "OldAmount := Old.MaterialLedger[MaterialId]" not in block:
        errors.append("candidate must not invent new material keys")
    if block.count("UpdatedAmount <= OldAmount") < 2:
        errors.append("candidate ledger must not mint materials")
    if block.count("UpdatedAmount >= 0") < 2:
        errors.append("candidate ledger must reject negative balances")
    invalid_guard = re.search(r"if \(not ValidLedger\?\):\s+return false", block)
    if not invalid_guard:
        errors.append("invalid ledger must abort")
    commit = block.find("return TrySaveProfile(Player, Candidate)")
    if commit < 0:
        errors.append("durable save acknowledgement missing")
    elif (
        not duplicate_guard
        or not invalid_guard
        or duplicate_guard.end() > commit
        or invalid_guard.end() > commit
    ):
        errors.append("guards must precede durable save")
    if "UnlockedEntityIds := Old.UnlockedEntityIds + array{UnlockEntityId}" not in block:
        errors.append("new unlock must be appended exactly once")
    return errors


class UnlockCommitSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_current_source(self):
        self.assertEqual(validate_unlock_commit(self.source), [])

    def test_duplicate_guard_mutation(self):
        mutant = self.source.replace(
            "Old.UnlockedEntityIds.Find[UnlockEntityId]\n            then:\n                return false",
            "Old.UnlockedEntityIds.Find[UnlockEntityId]\n            then:\n                return true",
            1,
        )
        self.assertNotEqual(mutant, self.source)
        self.assertIn("duplicate unlock", " ".join(validate_unlock_commit(mutant)))

    def test_material_mint_mutation(self):
        mutant = self.source.replace("UpdatedAmount <= OldAmount", "UpdatedAmount >= OldAmount", 1)
        self.assertNotEqual(mutant, self.source)
        self.assertIn("mint materials", " ".join(validate_unlock_commit(mutant)))

    def test_sparse_key_deletion_mutation(self):
        mutant = self.source.replace(
            "for (MaterialId -> OldAmount : Old.MaterialLedger):",
            "for (MaterialId -> OldAmount : map{}):",
            1,
        )
        self.assertNotEqual(mutant, self.source)
        self.assertIn("preserved", " ".join(validate_unlock_commit(mutant)))

    def test_invalid_ledger_guard_mutation(self):
        mutant = self.source.replace(
            "if (not ValidLedger?):\n                return false",
            "if (not ValidLedger?):\n                return true",
            1,
        )
        self.assertNotEqual(mutant, self.source)
        self.assertIn("invalid ledger", " ".join(validate_unlock_commit(mutant)))


if __name__ == "__main__":
    unittest.main()
