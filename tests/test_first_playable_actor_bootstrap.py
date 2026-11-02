"""Static mutation guards for actor-bootstrap exclusivity.

These tests inspect authored Verse source; they do not compile Verse or launch
a Fortnite session.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ACTOR_SOURCE = ROOT / "verse/core/actor_registry_bootstrap_device.verse"


def part(source: str, start: str, end: str | None = None) -> str:
    if start not in source:
        return ""
    value = source.split(start, 1)[1]
    return value.split(end, 1)[0] if end and end in value else value


def violations(source: str) -> list[str]:
    errors: list[str] = []
    if "AEONFALLActorBootstrapOwners:weak_map(session," not in source:
        errors.append("no session-scoped actor bootstrap lease")
    begin = part(source, "    OnBegin<override>()", "    OnEnd<override>()")
    end = part(source, "    OnEnd<override>()", "    RegisterPlayer(")
    register = part(source, "    RegisterPlayer(", "    UnregisterPlayer(")
    unregister = part(source, "    UnregisterPlayer(")

    lease = "set AEONFALLActorBootstrapOwners[GetSession()] = option{Self}"
    subscribe = "PlayerAddedEvent().Subscribe(RegisterPlayer)"
    for fragment in ("Owner <> Self", lease, "set OwnsLease = true",
                     "if (not OwnsLease?):", "set Running = true"):
        if fragment not in begin:
            errors.append("bootstrap must acquire and own exclusive lease: " + fragment)
    if begin.find(lease) < 0 or begin.find(subscribe) < 0 or begin.find(lease) > begin.find(subscribe):
        errors.append("bootstrap must lease before subscribing")
    if "RegisterPlayer(Player)" not in begin or begin.find(lease) > begin.find("RegisterPlayer(Player)"):
        errors.append("bootstrap must lease before enumerating existing players")
    for fragment in ("set Running = false", "Subscription.Cancel()",
                     "Owner = Self", "set AEONFALLActorBootstrapOwners[GetSession()] = false",
                     "set OwnsLease = false"):
        if fragment not in end:
            errors.append("bootstrap must cancel and release only owner lease: " + fragment)
    if (end.find("Subscription.Cancel()") < 0
        or end.find("set AEONFALLActorBootstrapOwners[GetSession()] = false") < 0
        or end.find("Subscription.Cancel()") > end.find("set AEONFALLActorBootstrapOwners[GetSession()] = false")):
        errors.append("bootstrap must cancel callbacks before releasing lease")
    if "Running?" not in register:
        errors.append("no running guard on identity ready callback")
    if "if (not Running?):" not in unregister:
        errors.append("no running guard on identity cleanup callback")
    return errors


class ActorBootstrapLeaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = ACTOR_SOURCE.read_text(encoding="utf-8")

    def test_authoritative_source(self):
        self.assertEqual(violations(self.source), [])

    def check_mutation(self, old: str, new: str):
        self.assertIn(old, self.source)
        mutant = self.source.replace(old, new, 1)
        self.assertTrue(violations(mutant))

    def test_missing_lease_rejected(self):
        self.check_mutation(
            "var AEONFALLActorBootstrapOwners:weak_map(session,",
            "var AEONFALLActorBootstrapOwners:weak_map(player,",
        )

    def test_missing_duplicate_owner_check_rejected(self):
        self.check_mutation("            Owner <> Self", "            Owner = Self")

    def test_subscription_before_lease_rejected(self):
        old = "        Added := GetPlayspace().PlayerAddedEvent().Subscribe(RegisterPlayer)"
        self.check_mutation(
            old, "        Added := GetPlayspace().PlayerAddedEvent().Subscribe(RegisterPlayer)\n"
                 "        Print(\"subscription before ownership\")",
        ) if False else None
        self.assertIn(old, self.source)
        mutant = self.source.replace(
            "        if (set AEONFALLActorBootstrapOwners[GetSession()] = option{Self}):",
            old + "\n        if (set AEONFALLActorBootstrapOwners[GetSession()] = option{Self}):",
            1,
        )
        self.assertTrue(violations(mutant))

    def test_early_release_rejected(self):
        self.check_mutation(
            "        set Subscriptions = array{}\n        if:",
            "        set Subscriptions = array{}\n"
            "        if (set AEONFALLActorBootstrapOwners[GetSession()] = false) {}\n        if:",
        )

    def test_missing_running_guard_rejected(self):
        self.check_mutation(
            "    UnregisterPlayer(Player:player)<transacts>:void=\n        if (not Running?):",
            "    UnregisterPlayer(Player:player)<transacts>:void=\n        if (Running?):",
        )


if __name__ == "__main__":
    unittest.main()
