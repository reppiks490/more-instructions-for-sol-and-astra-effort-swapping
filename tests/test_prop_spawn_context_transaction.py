"""Mutation guards for native prop creation and canonical placement commits.

This checks Verse source ordering, not native UEFN compilation, the physical
creative_prop lifecycle or a Fortnite Launch Session.
"""
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROP = ROOT / "verse/core/prop_spawn_adapter_device.verse"


def check_prop(text: str) -> list[str]:
    errors: list[str] = []
    start = text.find("    CommitSpawnTracking(")
    cleanup_at = text.find("    CommitCleanup(")
    on_end = text.find("    OnEnd<override>()")
    commit = text[start:cleanup_at] if 0 <= start < cleanup_at else ""
    cleanup = text[cleanup_at:on_end] if 0 <= cleanup_at < on_end else ""
    request = text[text.find("    OnRequest("):start] if start >= 0 else ""

    for fragment in (
        "CommitSpawnTracking[Request, Prepared.HandleId, Prop]",
        "if (CommitSpawnTracking[Request, Prepared.HandleId, Prop]):",
        "Succeeded := true",
        "Prop.Dispose()",
        "Released := GetAEONFALLSpawnRuntime().Release(Prepared.HandleId",
    ):
        if fragment not in request:
            errors.append("physical spawn must compensate/commit: " + fragment)
    if "RemovedContext :=" in request:
        errors.append("cannot consume snapshot outside spawn transaction")

    for fragment in (
        ")<decides><transacts>:void=",
        "GetAEONFALLAbilityRuntime().IsCurrentEffectRequest(Request)?",
        "GetAEONFALLPositionTargetingRuntime().Get[Request.ContextId]",
        "Context.OwnerKey = Request.OwnerKey",
        "Context.AbilityId = Request.AbilityId",
        "Consumed := GetAEONFALLPositionTargetingRuntime().Remove(Request.ContextId)",
        "Consumed?",
        "GetAEONFALLStatusRuntime().ApplyBatch[",
        "set PhysicalProps[Handle] = Prop",
        "Admitted?",
    ):
        if fragment not in commit:
            errors.append("canonical placement admission missing: " + fragment)
    required_order = [
        "GetAEONFALLPositionTargetingRuntime().Get[Request.ContextId]",
        "Consumed := GetAEONFALLPositionTargetingRuntime().Remove(Request.ContextId)",
        "Consumed?",
        "GetAEONFALLStatusRuntime().ApplyBatch[",
        "set PhysicalProps[Handle] = Prop",
        "Admitted?",
    ]
    positions = [commit.find(x) for x in required_order]
    if any(n < 0 for n in positions) or positions != sorted(positions):
        errors.append("placement context, status and tracking must commit in sequence")

    for fragment in (
        "CommitCleanup()<decides><transacts>:[]creative_prop=",
        "set Kept[Handle] = Prop",
        "Released := GetAEONFALLSpawnRuntime().Release(",
        "Released?",
        "set DisposeAfterCommit += array{Prop}",
        "set PhysicalProps = Kept",
        "if (Disposable := CommitCleanup[]):",
        "for (Prop : Disposable):",
        "Prop.Dispose()",
        'EventType := "spawn.physical_cleanup_retry"',
    ):
        if fragment not in cleanup:
            errors.append("tracked native cleanup missing: " + fragment)
    commit_release = cleanup.find("Released?")
    physical_map_swap = cleanup.find("set PhysicalProps = Kept")
    cleanup_call = cleanup.find("if (Disposable := CommitCleanup[]):")
    physical_disposal = cleanup.find("Prop.Dispose()")
    if not (0 <= commit_release < physical_map_swap < cleanup_call < physical_disposal):
        errors.append("physical disposal must follow successful canonical release/map commit")
    if "Prop.Dispose()" in cleanup[:physical_map_swap]:
        errors.append("irreversible native disposal is inside rollback scope")
    if "Prop.Dispose()" not in request[request.find("if (CommitSpawnTracking"):]:
        errors.append("failed native admission must dispose its prop")
    return errors


class PropSpawnContextTransactionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = PROP.read_text(encoding="utf-8")

    def mutation(self, before: str, after: str):
        self.assertIn(before, self.text)
        changed = self.text.replace(before, after, 1)
        self.assertTrue(check_prop(changed))

    def test_committed_source(self):
        self.assertEqual(check_prop(self.text), [])

    def test_consumed_position_must_be_acknowledged(self):
        self.mutation("        Consumed?\n", "        Print(\"context removal unchecked\")\n")

    def test_cannot_replay_missing_position_snapshot(self):
        self.mutation(
            "        Context := GetAEONFALLPositionTargetingRuntime().Get[Request.ContextId]",
            "        Context := aeonfall_position_target_context{}")

    def test_context_owner_must_match_request(self):
        self.mutation("        Context.OwnerKey = Request.OwnerKey",
                      '        Context.OwnerKey <> ""')

    def test_context_ability_must_match_request(self):
        self.mutation("        Context.AbilityId = Request.AbilityId",
                      '        Context.AbilityId <> ""')

    def test_spawn_context_consumed_before_status_commit(self):
        self.mutation(
            "        Consumed := GetAEONFALLPositionTargetingRuntime().Remove(Request.ContextId)",
            '        Consumed := GetAEONFALLPositionTargetingRuntime().Get(Request.ContextId)')

    def test_unchecked_early_success_is_forbidden(self):
        self.mutation(
            "                if (CommitSpawnTracking[Request, Prepared.HandleId, Prop]):",
            "                if (Prepared.HandleId <> \"\"):")

    def test_transaction_must_be_failable(self):
        self.mutation(
            "    )<decides><transacts>:void=\n        GetAEONFALLAbilityRuntime().IsCurrentEffectRequest(Request)?",
            "    )<transacts>:void=\n        GetAEONFALLAbilityRuntime().IsCurrentEffectRequest(Request)?")

    def test_cleanup_release_is_checked(self):
        self.mutation("                    Released?\n", "                    Print(\"unchecked release\")\n")

    def test_cleanup_must_keep_live_tracking_map(self):
        self.mutation("                set Kept[Handle] = Prop",
                      '                Print("lost tracked prop")')

    def test_cleanup_must_not_dispose_before_commit(self):
        self.mutation(
            "        set PhysicalProps = Kept\n        DisposeAfterCommit",
            "        Prop.Dispose()\n        set PhysicalProps = Kept\n        DisposeAfterCommit")

    def test_cleanup_must_run_commit_before_dispose(self):
        self.mutation(
            "            if (Disposable := CommitCleanup[]):",
            "            if (Disposable := array{creative_prop{}}):")

    def test_failure_compensation_must_dispose_native_prop(self):
        self.mutation("                Prop.Dispose()\n                set ResultCode",
                      '                Print("prop leaked")\n                set ResultCode')

    def test_cleanup_failure_is_reported(self):
        self.mutation('EventType := "spawn.physical_cleanup_retry"',
                      'EventType := "spawn.cleanup_succeeded"')


if __name__ == "__main__":
    unittest.main()
