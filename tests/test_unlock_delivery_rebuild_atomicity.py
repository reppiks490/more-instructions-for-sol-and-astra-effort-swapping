"""Post-commit delivery map integrity source/mutation checks.

These tests inspect Verse text and Python reference policy. They do not
compile Verse or prove item delivery in an actual UEFN Launch Session.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "verse/economy/unlock_delivery_service.verse"


def section(source: str, start: str, end: str) -> str:
    if start not in source or end not in source.split(start, 1)[-1]:
        return ""
    return source.split(start, 1)[1].split(end, 1)[0]


def source_errors(source: str) -> list[str]:
    errors: list[str] = []
    deferred = section(source, "    TickDeferred(", "    RequestEquipmentRestore(")
    remove = section(source, "    Remove(RequestId:string)", "    ClearOwner(")
    clear = section(source, "    ClearOwner(OwnerKey:string)", "    TickAll(")
    tick = section(source, "    TickAll(DeltaSeconds:float)", "# Mutable service allocation")
    for name, code, write, failure, guard, commit, event in (
        ("deferred", deferred, "set Remaining[Key] = State", "set Valid = false",
         "if (not Valid?):", "set Deferred = Remaining",
         'EventType := "unlock.deferred_rebuild_failed"'),
        ("remove", remove, "set Updated[StoredId] = State", "set Valid = false",
         "if (not Valid?):", "set Pending = Updated",
         'EventType := "unlock.pending_remove_failed"'),
        ("clear", clear, "set KeptDeferred[Key] = State", "set Valid = false",
         "if (not Valid?):", "set Deferred = KeptDeferred",
         'EventType := "unlock.owner_clear_failed"'),
        ("tick", tick, "set Updated[RequestId] = Next", "set Valid = false",
         "if (not Valid?):", "set Pending = Updated",
         'EventType := "unlock.pending_tick_rebuild_failed"'),
    ):
        for token in ("var Valid:logic = true", write, failure, guard, commit, event):
            if token not in code:
                errors.append(name + " missing preflight: " + token)
        if not (0 <= code.find(write) < code.find(failure) <
                code.find(guard) < code.find("return", code.find(guard)) <
                code.find(commit)):
            errors.append(name + " must abort on failed rebuild before replacement")
    for token in ("set Updated[RequestId] = State", "set KeptDeferred[Key] = State",
                  "set Pending = Updated", "set Deferred = KeptDeferred"):
        if token not in clear:
            errors.append("owner cleanup must stage both pending and deferred maps: " + token)
    if not (0 <= clear.find("if (not Valid?):") <
            clear.find("set Pending = Updated") < clear.find("set Deferred = KeptDeferred")):
        errors.append("owner cleanup must preflight both maps before either is swapped")
    if "return false" not in remove[remove.find("if (not Valid?):"):]:
        errors.append("pending removal must return failure on invalid rebuild")
    if not (0 <= deferred.find("HasPendingDelivery(State.OwnerKey, State.EntityId)") <
            deferred.find("Request(Agent, State.EntityId, State.SourceId)") <
            deferred.find("set Deferred = Remaining")):
        errors.append("deferred backlog must deduplicate successful prior admission")
    for token in ("set Updated[RequestId] = Retry", "set Valid = false",
                  "set Retries += array{Retry}", "set Expired += array{State}"):
        if token not in tick:
            errors.append("retry/timeout tracking missing: " + token)
    if not (0 <= tick.find("if (not Valid?):") < tick.find("set Pending = Updated") <
            tick.find("for (Retry : Retries):") < tick.find("for (State : Expired):")):
        errors.append("delivery retries and expiry cannot dispatch before map commit")
    return errors


def reference_drop(
    pending: dict[str, str], remove_id: str, fail_on: str | None
) -> tuple[dict[str, str], bool]:
    kept: dict[str, str] = {}
    for key, item in pending.items():
        if key == remove_id:
            continue
        if key == fail_on:
            return pending.copy(), False
        kept[key] = item
    return kept, True


class UnlockDeliveryPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")

    def mutate(self, original: str, changed: str) -> None:
        self.assertIn(original, self.text)
        mutant = self.text.replace(original, changed, 1)
        self.assertNotEqual(mutant, self.text)
        self.assertTrue(source_errors(mutant))

    def test_current_source(self):
        self.assertEqual(source_errors(self.text), [])

    def test_deferred_unallocated_entry_cannot_disappear(self):
        self.mutate("                        set Valid = false", "                        set Valid = Valid")

    def test_deferred_rebuild_must_refuse_partial_commit(self):
        self.mutate('EventType := "unlock.deferred_rebuild_failed"',
                    'EventType := "unlock.deferred_consumed"')

    def test_removal_must_track_failed_insert(self):
        self.mutate("                    else:\n                        set Valid = false",
                    "                    else:\n                        set Valid = Valid")

    def test_removal_must_report_failure(self):
        self.mutate('EventType := "unlock.pending_remove_failed"',
                    'EventType := "unlock.pending_removed"')

    def test_removal_cannot_report_success_after_invalid_map(self):
        self.mutate('            if (not Valid?):\n                AEONFALLRuntimeBus.Emit(',
                    '            if (Valid?):\n                AEONFALLRuntimeBus.Emit(')

    def test_owner_clear_must_keep_deferred(self):
        self.mutate('                if (set KeptDeferred[Key] = State):',
                    '                if (set Deferred[Key] = State):')

    def test_owner_clear_must_not_publish_early(self):
        self.mutate('EventType := "unlock.owner_clear_failed"',
                    'EventType := "unlock.owner_cleared"')

    def test_tick_cannot_release_when_rebuild_fails(self):
        self.mutate('EventType := "unlock.pending_tick_rebuild_failed"',
                    'EventType := "unlock.pending_tick_completed"')

    def test_tick_retries_are_only_scheduled_after_commit(self):
        self.mutate('        for (Retry : Retries):',
                    '        for (Retry : array{}):')

    def test_tick_must_reject_retry_map_insert_failure(self):
        self.mutate('                    else:\n                        set Valid = false\n\n                else:',
                    '                    else:\n                        set Valid = Valid\n\n                else:')

    def test_reference_failure_keeps_other_player_grants(self):
        pending = {"Alice": "WPN-001", "Bob": "WPN-007", "C": "WPN-126"}
        snapshot, ok = reference_drop(pending, "Alice", "C")
        self.assertFalse(ok)
        self.assertEqual(snapshot, pending)

    def test_reference_success_removes_only_resolved(self):
        pending = {"Alice": "WPN-001", "Bob": "WPN-007"}
        snapshot, ok = reference_drop(pending, "Alice", None)
        self.assertTrue(ok)
        self.assertEqual(snapshot, {"Bob": "WPN-007"})


if __name__ == "__main__":
    unittest.main()
