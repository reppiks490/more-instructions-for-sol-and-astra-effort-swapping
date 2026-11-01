"""Fail-closed actor teardown preflight source regression guards.

Structural checks only; native Verse compilation and NPC Launch Session
behavior must be verified in UEFN separately.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "verse/core/actor_registry.verse"


def check_preflight(source: str) -> list[str]:
    code = "\n".join(line.split("#", 1)[0] for line in source.splitlines())
    registered = code.partition("    IsRegistered(")[2].partition("    Unregister(")[0]
    teardown = code.partition("    Unregister(")[2].partition(
        "# Mutable service allocation"
    )[0]
    errors = []
    for token in ("AgentByKey[RuntimeKey]", "KeyByAgent[Agent]",
                  "ReverseKey = RuntimeKey", "CanonicalByKey[RuntimeKey]"):
        if token not in registered:
            errors.append("IsRegistered missing bidirectional identity check: " + token)

    preflight = teardown.find("var UpdatedAgents:[string]agent = map{}")
    guard = teardown.find("if (not Valid?):")
    failure_return = teardown.find("return false", guard)
    cleanup = teardown.find(
        "GetAEONFALLActivationCoordinator().ClearOwnerPending(RuntimeKey)"
    )
    commit = teardown.find("set AgentByKey = UpdatedAgents")
    for token in ("var UpdatedKeys:[agent]string = map{}",
                  "var UpdatedCanonical:[string]string = map{}",
                  "for (Key -> StoredAgent : AgentByKey):",
                  "for (StoredAgent -> Key : KeyByAgent):",
                  "for (Key -> CanonicalId : CanonicalByKey):",
                  "set Valid = false"):
        at = teardown.find(token)
        if at < 0 or guard < 0 or at > guard:
            errors.append("missing teardown map preflight: " + token)
    if min(preflight, guard, failure_return, cleanup, commit) < 0 or not (
        preflight < guard < failure_return < cleanup < commit
    ):
        errors.append("teardown must preflight and reject failed map rebuild before cleanup")
    if "set KeyByAgent = UpdatedKeys" not in teardown or (
        "set CanonicalByKey = UpdatedCanonical" not in teardown
    ):
        errors.append("teardown must commit all three identity maps")
    return errors


class ActorTeardownPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_preflight_baseline(self):
        self.assertEqual(check_preflight(self.source), [])

    def assert_mutation_rejected(self, old, new=""):
        self.assertIn(old, self.source)
        mutated = self.source.replace(old, new, 1)
        self.assertTrue(check_preflight(mutated))

    def test_registered_reverse_lookup_required(self):
        self.assert_mutation_rejected("        ReverseKey = RuntimeKey\n")

    def test_failed_rebuild_must_abort_before_cleanup(self):
        self.assert_mutation_rejected("            if (not Valid?):\n")

    def test_preflight_must_precede_cleanup(self):
        self.assert_mutation_rejected(
            "            var UpdatedAgents:[string]agent = map{}\n"
        )

    def test_all_three_maps_must_commit(self):
        self.assert_mutation_rejected("            set KeyByAgent = UpdatedKeys\n")


if __name__ == "__main__":
    unittest.main()
