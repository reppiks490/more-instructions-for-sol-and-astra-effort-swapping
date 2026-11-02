"""Independent production-source guard for paid FUS-001 Rend authorization.

This deliberately fails against an unpaired adapter. Source inspection only:
native UEFN compilation and multiplayer behavior require separate evidence.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
ARSENAL = ROOT / "verse/sovereign/sovereign_arsenal_runtime.verse"

def method_body(source: str, name: str) -> str:
    # Strip Verse comments before checking authorization tokens.
    code = "\n".join(line.split("#", 1)[0] for line in source.splitlines())
    match = re.search(r"^    " + re.escape(name) + r"\(", code, re.M)
    if not match:
        raise AssertionError(f"missing {name} method")
    rest = code[match.end():]
    next_method = re.search(r"^    [A-Za-z_]\w*\(", rest, re.M)
    return code[match.start():match.end() + next_method.start() if next_method else len(code)]

class PaidRendProductionGuard(unittest.TestCase):
    def test_receipt_consumed_before_secondary_debit(self):
        body = method_body(ARSENAL.read_text(encoding="utf-8"), "TryRend")
        self.assertIn("<decides><transacts>", body, "Rend must be a deciding transaction")
        receipt = re.search(r"State\.ConsumeAttackReceipt\s*\[", body)
        debit = re.search(r"Budget\.Spend\s*\[", body)
        self.assertIsNotNone(receipt, "Rend must consume one-use canonical receipt")
        self.assertIsNotNone(debit, "Rend must debit its secondary energy cost")
        self.assertLess(receipt.start(), debit.start(), "receipt must precede debit")
        self.assertLess(debit.start(), body.find("set LastRendAt"), "cooldown must follow payment")

if __name__ == "__main__":
    unittest.main()
