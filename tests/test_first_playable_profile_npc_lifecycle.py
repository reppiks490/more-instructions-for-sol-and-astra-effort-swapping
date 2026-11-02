"""Source-level profile bootstrap and NPC lifecycle regression tests.

Structural checks and mutation tests only; neither Verse compilation nor
Fortnite Launch Session behavior can be inferred from these tests.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "verse/persistence/profile_bootstrap_device.verse"
NPC = ROOT / "verse/npcs/npc_lifecycle_behavior.verse"


def section(source: str, first: str, next_start: str | None = None) -> str:
    if first not in source:
        return ""
    body = source.split(first, 1)[1]
    if next_start and next_start in body:
        return body.split(next_start, 1)[0]
    return body


def profile_errors(source: str) -> list[str]:
    errors: list[str] = []
    begin = section(source, "    OnBegin<override>()", "    OnEnd<override>()")
    end = section(source, "    OnEnd<override>()", "    OnPlayerAdded(")
    added = section(source, "    OnPlayerAdded(", "    EnsureProfile(")
    ensure = section(source, "    EnsureProfile(")
    lease = "set AEONFALLProfileBootstrapOwners[GetSession()] = option{Self}"
    release = "set AEONFALLProfileBootstrapOwners[GetSession()] = false"
    subscription = "PlayerAddedEvent().Subscribe(OnPlayerAdded)"
    if "AEONFALLProfileBootstrapOwners:weak_map(session, ?aeonfall_profile_bootstrap_device)" not in source:
        errors.append("profile owner lease must be session scoped")
    for token in ("Owner <> Self", lease, "set OwnsLease = true",
                  "if (not OwnsLease?):", "set Running = true"):
        if token not in begin:
            errors.append("bootstrap owner acquisition missing: " + token)
    if min(begin.find(lease), begin.find(subscription),
           begin.find("EnsureProfile(Player)")) < 0 or not (
        begin.find(lease) < begin.find(subscription) < begin.find("EnsureProfile(Player)")
    ):
        errors.append("bootstrap must lease before any subscription or profile initialization")
    for token in ("set Running = false", "Subscription.Cancel()",
                  "OwnsLease?", "Owner = Self", release, "set OwnsLease = false"):
        if token not in end:
            errors.append("bootstrap release guard missing: " + token)
    if end.count(release) != 1 or not (
        0 <= end.find("Subscription.Cancel()") < end.find(release)
    ) or not (0 <= end.find("Owner = Self") < end.find(release)):
        errors.append("profile owner must cancel callbacks and verify owner before release")
    if "if (Running?):" not in added:
        errors.append("join callback must require running lease")
    if "if (not Running?):" not in ensure or "if (not Player.IsActive[]):" not in ensure:
        errors.append("profile persistence must require running owner and active player")
    if "ProfileService.TrySaveProfile" not in ensure:
        errors.append("profile initialization must use acknowledged save")
    return errors


def npc_errors(source: str) -> list[str]:
    errors: list[str] = []
    end = section(source, "    OnEnd<override>()")
    blank = end.find('if (RuntimeKey = ""):')
    blank_return = end.find("return", blank)
    unregister = end.find("Removed := GetAEONFALLActorRegistry().Unregister(RuntimeKey)")
    success = end.find("if (Removed?):", unregister)
    removed = end.find('EventType := "npc.removed"')
    failure = end.find('EventType := "npc.runtime_identity_cleanup_failed"')
    branch = end.find("        else:", success)
    if min(blank, blank_return, unregister, success, removed, failure, branch) < 0 or not (
        blank < blank_return < unregister < success < removed < branch < failure
    ):
        errors.append("NPC removal must follow successful unregister, not a blank/failed key")
    # Ensure a removed event is indented inside the successful branch.
    lines = end.splitlines()
    success_line = next((i for i, line in enumerate(lines) if "if (Removed?):" in line), -1)
    removed_line = next((i for i, line in enumerate(lines) if 'EventType := "npc.removed"' in line), -1)
    if success_line < 0 or removed_line < 0:
        errors.append("NPC success/removal event missing")
    else:
        level = len(lines[success_line]) - len(lines[success_line].lstrip())
        emit_line = next((line for line in lines[success_line+1:removed_line]
                          if "AEONFALLRuntimeBus.Emit(" in line), "")
        if not emit_line or len(emit_line)-len(emit_line.lstrip()) <= level:
            errors.append("NPC removal event must be scoped to successful unregister")
    return errors


class FirstPlayableLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = PROFILE.read_text(encoding="utf-8")
        cls.npc = NPC.read_text(encoding="utf-8")

    def test_baseline(self):
        self.assertEqual(profile_errors(self.profile), [])
        self.assertEqual(npc_errors(self.npc), [])

    def mutation(self, source: str, old: str, new: str, checker):
        self.assertIn(old, source)
        changed = source.replace(old, new, 1)
        self.assertTrue(checker(changed))

    def test_session_lease_required(self):
        self.mutation(self.profile,
                      "AEONFALLProfileBootstrapOwners:weak_map(session,",
                      "AEONFALLProfileBootstrapOwners:weak_map(player,",
                      profile_errors)

    def test_duplicate_profile_owner_refused(self):
        self.mutation(self.profile, "            Owner <> Self",
                      "            Owner = Self", profile_errors)

    def test_owner_must_be_acquired_before_subscribing(self):
        altered = self.profile.replace(
            "        if (set AEONFALLProfileBootstrapOwners[GetSession()] = option{Self}):",
            "        Added := GetPlayspace().PlayerAddedEvent().Subscribe(OnPlayerAdded)\n"
            "        if (set AEONFALLProfileBootstrapOwners[GetSession()] = option{Self}):", 1)
        self.assertTrue(profile_errors(altered))

    def test_release_only_after_cancellation(self):
        self.mutation(self.profile,
                      "        set Subscriptions = array{}\n        if:",
                      "        set Subscriptions = array{}\n"
                      "        if (set AEONFALLProfileBootstrapOwners[GetSession()] = false) {}\n"
                      "        if:", profile_errors)

    def test_profile_join_requires_running(self):
        self.mutation(self.profile, "        if (Running?):\n            EnsureProfile(Player)",
                      "        EnsureProfile(Player)", profile_errors)

    def test_profile_save_requires_running(self):
        self.mutation(self.profile, "        if (not Running?):\n            return",
                      "        Print(\"no running guard\")", profile_errors)

    def test_npc_must_not_remove_unregistered(self):
        self.mutation(self.npc, '        if (RuntimeKey = ""):\n            return',
                      '        Print(\"ignore empty key\")', npc_errors)

    def test_npc_must_not_emit_unsupported_removal(self):
        self.mutation(self.npc,
                      '        if (Removed?):\n            AEONFALLRuntimeBus.Emit(',
                      '        if (not Removed?):\n            AEONFALLRuntimeBus.Emit(', npc_errors)

    def test_npc_teardown_failure_event_required(self):
        self.mutation(self.npc,
                      'EventType := "npc.runtime_identity_cleanup_failed"',
                      'EventType := "npc.removed"', npc_errors)


if __name__ == "__main__":
    unittest.main()
