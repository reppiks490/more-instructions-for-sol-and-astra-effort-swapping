"""Actor identity guard regression tests.

These are source-mutation checks only. They do not execute Verse or establish
UEFN compilation or NPC lifecycle behavior in a Launch Session.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "verse/core/actor_registry.verse"


def check_actor_identity_source(source: str) -> list[str]:
    code = "\n".join(line.split("#", 1)[0] for line in source.splitlines())
    register = code.partition("    Register(")[2].partition("    GetAgent(")[0]
    unregister = code.partition("    Unregister(")[2].partition(
        "# Mutable service allocation"
    )[0]
    errors: list[str] = []

    # Validate the identity before any registration map mutation.
    first_write = register.find("set NextActorNumber += 1")
    canonical_guard = register.find('CanonicalId <> ""')
    if first_write < 0 or canonical_guard < 0 or canonical_guard > first_write:
        errors.append("registration must reject blank canonical identities before mutation")

    # Idempotent registration must verify both directions and canonical ID.
    for token in (
        "ExistingAgent := AgentByKey[Existing]",
        "ExistingAgent = Agent",
        "ExistingCanonical := CanonicalByKey[Existing]",
        "ExistingCanonical = CanonicalId",
    ):
        at = register.find(token)
        if at < 0 or first_write < 0 or at > first_write:
            errors.append(f"registration missing existing-identity guard: {token}")

    # A corrupt/stale key must not tear down another actor's live state.
    first_cleanup = unregister.find(
        "GetAEONFALLActivationCoordinator().ClearOwnerPending(RuntimeKey)"
    )
    for token in (
        "ReverseKey := KeyByAgent[Agent]",
        "ReverseKey = RuntimeKey",
        "CanonicalId := CanonicalByKey[RuntimeKey]",
        'CanonicalId <> ""',
    ):
        at = unregister.find(token)
        if at < 0 or first_cleanup < 0 or at > first_cleanup:
            errors.append(f"unregister must verify identity before cleanup: {token}")
    return errors


class ActorIdentitySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = REGISTRY.read_text(encoding="utf-8")

    def test_baseline_guards(self):
        self.assertEqual(check_actor_identity_source(self.source), [])

    def assert_mutation_rejected(self, old: str, new: str = ""):
        self.assertIn(old, self.source)
        mutated = self.source.replace(old, new, 1)
        self.assertNotEqual(mutated, self.source)
        self.assertTrue(check_actor_identity_source(mutated))

    def test_blank_canonical_guard_required(self):
        self.assert_mutation_rejected('        CanonicalId <> ""\n', "")

    def test_forward_identity_guard_required(self):
        self.assert_mutation_rejected("            ExistingAgent = Agent\n")

    def test_canonical_identity_guard_required(self):
        self.assert_mutation_rejected("            ExistingCanonical = CanonicalId\n")

    def test_reverse_index_guard_required_on_cleanup(self):
        self.assert_mutation_rejected("            ReverseKey = RuntimeKey\n")

    def test_canonical_index_required_on_cleanup(self):
        self.assert_mutation_rejected(
            "            CanonicalId := CanonicalByKey[RuntimeKey]\n"
        )


if __name__ == "__main__":
    unittest.main()
