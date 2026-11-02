"""Mutation and reference-policy checks for session map rebuild integrity.

These tests inspect Verse source and Python policy examples, not native Verse
compilation, map allocation behavior, or Fortnite multiplayer execution.
"""
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTEXT = "verse/combat/actor_context_runtime.verse"
PARTICIPATION = "verse/bosses/encounter_participation_runtime.verse"
TARGETING = "verse/combat/targeting_runtime.verse"


def block(source: str, start: str, end: str | None = None) -> str:
    if start not in source:
        return ""
    section = source.split(start, 1)[1]
    if end and end in section:
        section = section.split(end, 1)[0]
    return section


def source_errors(sources: dict[str, str]) -> list[str]:
    errors: list[str] = []
    ctx = block(sources.get(CONTEXT, ""), "    Clear(OwnerKey:string)", "# Mutable service allocation")
    part = block(sources.get(PARTICIPATION, ""), "    RemoveRuntimeKey(RuntimeKey:string)", "# Mutable service allocation")
    tick = block(sources.get(TARGETING, ""), "    TickAll(DeltaSeconds:float)", "# Mutable service allocation")

    for name, section, map_write, write_failure, guard, final, fail_event in (
        ("context", ctx, "set Updated[StoredOwnerKey] = State", "set Valid = false",
         "if (not Valid?):", "set States = Updated", 'EventType := "context.owner_clear_failed"'),
        ("participant", part, "set UpdatedMap[EncounterId] = Updated", "set Valid = false",
         "if (not Valid?):", "set ParticipantKeysByEncounter = UpdatedMap",
         'EventType := "encounter.participant_cleanup_failed"'),
        ("target", tick, "set Updated[OwnerKey] = Next", "set Valid = false",
         "if (not Valid?):", "set Selections = Updated",
         'EventType := "target.tick_rebuild_failed"'),
    ):
        for token in ("var Valid:logic = true", map_write, write_failure,
                      guard, final, fail_event):
            if token not in section:
                errors.append(name + " missing fail-closed rebuild: " + token)
        if not (0 <= section.find(map_write) < section.find(write_failure)
                < section.find(guard) < section.find("return", section.find(guard))
                < section.find(final)):
            errors.append(name + " must reject failed replacement before replacing live map")
        if section.find(fail_event) < section.find(guard):
            errors.append(name + " failure diagnostic must require failed validation")

    for token in (
        "var Expired:[]aeonfall_target_selection = array{}",
        "set Expired += array{Selection}",
        "for (Selection : Expired):",
        'EventType := "target.expired"',
    ):
        if token not in tick:
            errors.append("target expiry deferred-notification contract missing: " + token)
    if not (0 <= tick.find("set Selections = Updated") <
            tick.find("for (Selection : Expired):") <
            tick.find('EventType := "target.expired"')):
        errors.append("expired target must not be announced before new selection map commits")
    if tick.find('EventType := "target.expired"') < tick.find("if (not Valid?):"):
        errors.append("target failure cannot emit premature expiry")
    return errors


def reference_rebuild(
    original: dict[str, object], departing_key: str, failed_insert: str | None
) -> tuple[dict[str, object], bool]:
    """A failed replacement must not truncate unrelated players' state."""
    replacement: dict[str, object] = {}
    for key, value in original.items():
        if key == departing_key:
            continue
        if key == failed_insert:
            return original.copy(), False
        replacement[key] = value
    return replacement, True


class MultiplayerMapRebuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {
            path: (ROOT / path).read_text(encoding="utf-8")
            for path in (CONTEXT, PARTICIPATION, TARGETING)
        }

    def test_committed_source(self):
        self.assertEqual(source_errors(self.sources), [])

    def mutated(self, path: str, old: str, new: str) -> None:
        self.assertIn(old, self.sources[path])
        candidate = dict(self.sources)
        candidate[path] = candidate[path].replace(old, new, 1)
        self.assertNotEqual(candidate[path], self.sources[path])
        self.assertTrue(source_errors(candidate))

    def test_context_must_track_failed_insert(self):
        self.mutated(CONTEXT, "                else:\n                    set Valid = false",
                     "                else:\n                    set Valid = Valid")

    def test_context_must_abort_failed_rebuild(self):
        self.mutated(CONTEXT, "        if (not Valid?):",
                     "        if (Valid?):")

    def test_context_must_not_drop_failure_diagnostic(self):
        self.mutated(CONTEXT, 'EventType := "context.owner_clear_failed"',
                     'EventType := "context.owner_cleared"')

    def test_participant_must_track_failed_insert(self):
        self.mutated(PARTICIPATION, "            else:\n                set Valid = false",
                     "            else:\n                set Valid = Valid")

    def test_participant_must_abort_failed_rebuild(self):
        self.mutated(PARTICIPATION, "        if (not Valid?):",
                     "        if (Valid?):")

    def test_participant_diagnostic_preserved(self):
        self.mutated(PARTICIPATION, 'EventType := "encounter.participant_cleanup_failed"',
                     'EventType := "encounter.participant_cleanup_succeeded"')

    def test_target_must_track_failed_insert(self):
        self.mutated(TARGETING, "                else:\n                    set Valid = false",
                     "                else:\n                    set Valid = Valid")

    def test_target_must_abort_failed_rebuild(self):
        self.mutated(TARGETING, "        if (not Valid?):",
                     "        if (Valid?):")

    def test_target_must_defer_expired_notifications(self):
        self.mutated(TARGETING, "        for (Selection : Expired):",
                     "        for (Selection : array{}):")

    def test_target_expiry_must_collect_then_commit(self):
        self.mutated(TARGETING, "                set Expired += array{Selection}",
                     "                set Expired = array{}")

    def test_target_failure_diagnostic_preserved(self):
        self.mutated(TARGETING, 'EventType := "target.tick_rebuild_failed"',
                     'EventType := "target.expired"')

    def test_reference_failure_preserves_unrelated_players(self):
        original = {"a": {"encounter": 2}, "b": {"encounter": 1},
                    "c": {"encounter": 1}}
        result, ok = reference_rebuild(original, "a", "c")
        self.assertFalse(ok)
        self.assertEqual(result, original)

    def test_reference_success_removes_only_departed(self):
        original = {"a": [1], "b": [2], "c": [3]}
        result, ok = reference_rebuild(original, "a", None)
        self.assertTrue(ok)
        self.assertEqual(result, {"b": [2], "c": [3]})


if __name__ == "__main__":
    unittest.main()
