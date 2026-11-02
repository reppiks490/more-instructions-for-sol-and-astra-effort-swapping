"""Source-mutation checks for first-playable native event ownership.

These inspect Verse text only. They do not compile Verse, bind an editor
device, execute a Fortnite Launch Session, or prove overlap behavior.
"""
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATHS = (
    "verse/combat/self_ability_input_device.verse",
    "verse/combat/targeted_ability_input_device.verse",
    "verse/combat/position_ability_input_device.verse",
)
CONTEXT = "verse/combat/encounter_context_volume_device.verse"
PARTICIPANT = "verse/bosses/encounter_participant_volume_device.verse"
PATHS = (*INPUT_PATHS, CONTEXT, PARTICIPANT)


def section(source: str, start: str, end: str | None = None) -> str:
    if start not in source:
        return ""
    found = source.split(start, 1)[1]
    return found.split(end, 1)[0] if end and end in found else found


def input_errors(source: str) -> list[str]:
    errors: list[str] = []
    begin = section(source, "    OnBegin<override>()", "    OnEnd<override>()")
    end = section(source, "    OnEnd<override>()", "    OnPressed(")
    callback = section(source, "    OnPressed(")
    for token in ("var Running:logic = false", "var InputSubscription:?cancelable = false"):
        if token not in source:
            errors.append("native input lease state missing: " + token)
    for token in ('if (AbilityId = ""):', "set Running = true",
                  "Bound := Input.PressedEvent.Subscribe(OnPressed)",
                  "set InputSubscription = option{Bound}"):
        if token not in begin:
            errors.append("native input startup guard missing: " + token)
    for token in ("set Running = false", "if (Bound := InputSubscription?):",
                  "Bound.Cancel()", "set InputSubscription = false"):
        if token not in end:
            errors.append("native input shutdown cleanup missing: " + token)
    if "if (not Running?):\n            return" not in callback:
        errors.append("native input callback must refuse after device shutdown")
    if not (0 <= begin.find('if (AbilityId = ""):') <
            begin.find("Input.PressedEvent.Subscribe(OnPressed)") <
            begin.find("set InputSubscription = option{Bound}")):
        errors.append("native input must reject bad binding before subscribing")
    if not (0 <= end.find("set Running = false") <
            end.find("Bound.Cancel()") <
            end.find("set InputSubscription = false")):
        errors.append("native input must stop callbacks before releasing native subscription")
    return errors


def context_errors(source: str) -> list[str]:
    errors: list[str] = []
    begin = section(source, "    OnBegin<override>()", "    OnEnd<override>()")
    end = section(source, "    OnEnd<override>()", "    CommitEnter(")
    enter = section(source, "    CommitEnter(", "    OnEnter(")
    exit_ = section(source, "    CommitExit(", "    OnExit(")
    enter_callback = section(source, "    OnEnter(", "    CommitExit(")
    exit_callback = section(source, "    OnExit(")
    for token in (
        "var Running:logic = false",
        "var Subscriptions:[]cancelable = array{}",
        "var TrackedAgents:[agent]logic = map{}",
    ):
        if token not in source:
            errors.append("context ownership state missing: " + token)
    for token in (
        'if (EncounterId = ""):',
        "Volume.AgentEntersEvent.Subscribe(OnEnter)",
        "Volume.AgentExitsEvent.Subscribe(OnExit)",
        "Volume.GetAgentsInVolume()",
        "OnEnter(Agent)",
    ):
        if token not in begin:
            errors.append("context volume startup reconciliation missing: " + token)
    for token in (
        "set Running = false",
        "Subscription.Cancel()",
        "for (TrackedAgent -> Admitted : TrackedAgents):",
        "ExitEncounter(",
        "set TrackedAgents = map{}",
    ):
        if token not in end:
            errors.append("context device shutdown must release own depth: " + token)
    if not (0 <= end.find("Subscription.Cancel()") <
            end.find("ExitEncounter(") <
            end.find("set TrackedAgents = map{}")):
        errors.append("context volume must cancel callbacks before balancing depth")
    for token in (
        ")<decides><transacts>:void=",
        "not TrackedAgents[Agent]",
        "EnterEncounter(Agent, EncounterId)?",
        "set TrackedAgents[Agent] = true",
    ):
        if token not in enter:
            errors.append("context increment must commit with unique ownership: " + token)
    if not (0 <= enter.find("not TrackedAgents[Agent]") <
            enter.find("EnterEncounter(Agent, EncounterId)?") <
            enter.find("set TrackedAgents[Agent] = true")):
        errors.append("context admission order permits phantom or duplicate depth")
    for token in (
        ")<decides><transacts>:void=",
        "TrackedAgents[Agent]?",
        "ExitEncounter(Agent, EncounterId)?",
        "set Remaining[Stored] = Admitted",
        "set TrackedAgents = Remaining",
    ):
        if token not in exit_:
            errors.append("context decrement must commit with tracked ownership: " + token)
    if "if (not Running?):\n            return" not in enter_callback:
        errors.append("context stopped-enter callback must refuse action")
    if "if (not Running?):\n            return" not in exit_callback:
        errors.append("context stopped-exit callback must refuse action")
    return errors


def participant_errors(source: str) -> list[str]:
    errors: list[str] = []
    begin = section(source, "    OnBegin<override>()", "    OnEnd<override>()")
    end = section(source, "    OnEnd<override>()", "    OnEntered(")
    entered = section(source, "    OnEntered(", "    OnExited(")
    exited = section(source, "    OnExited(")
    for token in (
        "var Running:logic = false", "var Subscriptions:[]cancelable = array{}",
    ):
        if token not in source:
            errors.append("participant lifecycle state missing: " + token)
    for token in (
        'if (EncounterId = ""):',
        "Volume.AgentEntersEvent.Subscribe(OnEntered)",
        "Volume.AgentExitsEvent.Subscribe(OnExited)",
        "Volume.GetAgentsInVolume()",
    ):
        if token not in begin:
            errors.append("participant startup guard missing: " + token)
    for token in (
        "set Running = false", "Subscription.Cancel()",
        "set Subscriptions = array{}",
    ):
        if token not in end:
            errors.append("participant subscription cleanup missing: " + token)
    if "ClearEncounter(" in end:
        errors.append("participant shutdown must not erase another director's players")
    for part in (entered, exited):
        if "if (not Running?):\n            return" not in part:
            errors.append("participant callbacks require active native owner")
    return errors


def violations(sources: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for path in INPUT_PATHS:
        errors.extend(f"{path}: {e}" for e in input_errors(sources.get(path, "")))
    errors.extend(f"{CONTEXT}: {e}" for e in context_errors(sources.get(CONTEXT, "")))
    errors.extend(f"{PARTICIPANT}: {e}" for e in participant_errors(sources.get(PARTICIPANT, "")))
    return errors


class NativeInputVolumeLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {p: (ROOT / p).read_text(encoding="utf-8") for p in PATHS}

    def mutate(self, path: str, before: str, after: str) -> None:
        self.assertIn(before, self.sources[path])
        changed = dict(self.sources)
        changed[path] = changed[path].replace(before, after, 1)
        self.assertTrue(violations(changed))

    def test_baseline(self):
        self.assertEqual(violations(self.sources), [])

    def test_each_input_cancels_owned_subscription(self):
        for path in INPUT_PATHS:
            with self.subTest(path=path):
                self.mutate(path, "            Bound.Cancel()", "            Print(\"callback leaked\")")

    def test_each_input_blocks_callbacks_after_end(self):
        for path in INPUT_PATHS:
            with self.subTest(path=path):
                self.mutate(path, "        if (not Running?):\n            return", "        if (Running?):\n            return")

    def test_each_input_requires_canonical_ability_id(self):
        for path in INPUT_PATHS:
            with self.subTest(path=path):
                self.mutate(path, '        if (AbilityId = ""):', '        if (AbilityId <> ""):')

    def test_context_rejects_repeat_enters(self):
        self.mutate(CONTEXT, "        not TrackedAgents[Agent]", "        TrackedAgents[Agent]?")

    def test_context_cannot_lose_atomic_enter(self):
        self.mutate(CONTEXT, "EnterEncounter(Agent, EncounterId)?", "EnterEncounter(Agent, EncounterId)")

    def test_context_cannot_lose_atomic_exit(self):
        self.mutate(CONTEXT, "ExitEncounter(Agent, EncounterId)?", "ExitEncounter(Agent, EncounterId)")

    def test_context_reconciles_starting_occupants(self):
        self.mutate(CONTEXT, "        for (Agent : Volume.GetAgentsInVolume()):",
                    "        for (Agent : array{}):")

    def test_context_balances_shutdown_depth(self):
        self.mutate(CONTEXT, "                Released := GetAEONFALLActorContextRuntime().ExitEncounter(",
                    "                Released := GetAEONFALLActorContextRuntime().EnterEncounter(")

    def test_context_cancels_enter_exit_subscriptions(self):
        self.mutate(CONTEXT, "            Subscription.Cancel()", "            Print(\"listener retained\")")

    def test_participant_requires_cleanup(self):
        self.mutate(PARTICIPANT, "            Subscription.Cancel()", "            Print(\"listener retained\")")

    def test_participant_must_not_clear_another_director(self):
        self.mutate(PARTICIPANT, "        set Subscriptions = array{}",
                    "        set Subscriptions = array{}\n        GetAEONFALLEncounterParticipation().ClearEncounter(EncounterId)")

    def test_participant_refuses_blank_id(self):
        self.mutate(PARTICIPANT, '        if (EncounterId = ""):', '        if (EncounterId <> ""):')


if __name__ == "__main__":
    unittest.main()
