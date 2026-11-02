"""Source-only map preflight checks for position ability contexts and props.

This inspects Verse source; it is not a Verse compiler, physical collision
test, native prop disposal check or Fortnite multiplayer Launch Session.
"""
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
POSITION = "verse/combat/position_targeting_runtime.verse"
SPAWN = "verse/core/spawn_runtime.verse"


def block(source: str, start: str, end: str) -> str:
    if start not in source:
        return ""
    text = source.split(start, 1)[1]
    return text.split(end, 1)[0] if end in text else ""


def check_source(sources: dict[str, str]) -> list[str]:
    errors: list[str] = []
    position = sources.get(POSITION, "")
    spawn = sources.get(SPAWN, "")
    blocks = {
        "position_remove": block(position, "    Remove(ContextId:string)", "    ClearOwner("),
        "position_clear": block(position, "    ClearOwner(OwnerKey:string)", "    TickAll("),
        "position_tick": block(position, "    TickAll(DeltaSeconds:float)", "# Mutable service allocation"),
        "spawn_release": block(spawn, "    Release(", "    ClearOwner("),
        "spawn_clear": block(spawn, "    ClearOwner(", "    TickAll("),
        "spawn_tick": block(spawn, "    TickAll(DeltaSeconds:float)", "# Mutable service allocation"),
    }
    for name, code in blocks.items():
        dest = "set Contexts = Updated" if name.startswith("position") else "set Records = Updated"
        for token in ("var Valid:logic = true", "set Valid = false",
                      "if (not Valid?):", dest):
            if token not in code:
                errors.append(name + " missing full-rebuild preflight: " + token)
        if not (0 <= code.find("set Valid = false") <
                code.find("if (not Valid?):") <
                code.find("return", code.find("if (not Valid?):")) <
                code.find(dest)):
            errors.append(name + " must refuse failed map writes before replacement")
        diagnostic = {
            "position_remove": "target.position_remove_failed",
            "position_clear": "target.position_owner_clear_failed",
            "position_tick": "target.position_tick_rebuild_failed",
            "spawn_release": "spawn.release_rebuild_failed",
            "spawn_clear": "spawn.owner_clear_rebuild_failed",
            "spawn_tick": "spawn.tick_rebuild_failed",
        }[name]
        if 'EventType := "' + diagnostic + '"' not in code:
            errors.append(name + " missing failure diagnostic " + diagnostic)

    for name, expected_write in (
        ("position_remove", "set Updated[StoredId] = Context"),
        ("position_clear", "set Updated[ContextId] = Context"),
        ("position_tick", "set Updated[ContextId] = Next"),
        ("spawn_release", "set Updated[StoredId] = Record"),
        ("spawn_clear", "set Updated[HandleId] = Record"),
        ("spawn_tick", "set Updated[HandleId] = Next"),
    ):
        if expected_write not in blocks[name]:
            errors.append(name + " missing guarded retained-map write")

    for name, collect, release_event, dest in (
        ("position_tick", "set Expired += array{Context}",
         'EventType := "target.position_expired"', "set Contexts = Updated"),
        ("spawn_clear", "set Released += array{Record}",
         'EventType := "spawn.released"', "set Records = Updated"),
        ("spawn_tick", "set Expired += array{Record}",
         'EventType := "spawn.expired"', "set Records = Updated"),
    ):
        code = blocks[name]
        for token in (collect, release_event):
            if token not in code:
                errors.append(name + " missing deferred physical notification: " + token)
        if not (0 <= code.find(collect) < code.find("if (not Valid?):") <
                code.find(dest) < code.find(release_event)):
            errors.append(name + " cannot publish effect cleanup before state commit")

    for name, missing_branch in (
        ("position_remove", "return false"),
        ("spawn_release", "return false"),
    ):
        code = blocks[name]
        if missing_branch not in code[code.find("if (not Valid?):"):]:
            errors.append(name + " must return a refused removal on rebuild failure")
    return errors


def reference_remove(current: dict[str, int], remove: str,
                     refused: str | None) -> tuple[dict[str, int], bool]:
    next_map: dict[str, int] = {}
    for key, amount in current.items():
        if key == remove:
            continue
        if key == refused:
            return dict(current), False
        next_map[key] = amount
    return next_map, True


class PositionAndSpawnMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {p: (ROOT / p).read_text(encoding="utf-8")
                       for p in (POSITION, SPAWN)}

    def mutation(self, path: str, old: str, new: str):
        self.assertIn(old, self.sources[path])
        changed = dict(self.sources)
        changed[path] = changed[path].replace(old, new, 1)
        self.assertTrue(check_source(changed))

    def test_baseline(self):
        self.assertEqual(check_source(self.sources), [])

    def test_position_refused_remove(self):
        self.mutation(POSITION, 'EventType := "target.position_remove_failed"',
                      'EventType := "target.position_removed"')

    def test_position_refused_owner_clear(self):
        self.mutation(POSITION, 'EventType := "target.position_owner_clear_failed"',
                      'EventType := "target.position_owner_cleared"')

    def test_position_expiry_must_be_deferred(self):
        self.mutation(POSITION, "set Expired += array{Context}",
                      "set Expired = array{}")

    def test_position_tick_refusal_diagnostic(self):
        self.mutation(POSITION, 'EventType := "target.position_tick_rebuild_failed"',
                      'EventType := "target.position_expired"')

    def test_spawn_refused_release(self):
        self.mutation(SPAWN, 'EventType := "spawn.release_rebuild_failed"',
                      'EventType := "spawn.released"')

    def test_spawn_refused_owner_clear(self):
        self.mutation(SPAWN, 'EventType := "spawn.owner_clear_rebuild_failed"',
                      'EventType := "spawn.owner_cleared"')

    def test_spawn_expiry_must_be_deferred(self):
        self.mutation(SPAWN, "set Expired += array{Record}",
                      "set Expired = array{}")

    def test_spawn_release_signal_requires_commit(self):
        self.mutation(SPAWN, "set Released += array{Record}",
                      "set Released = array{}")

    def test_spawn_tick_refusal_diagnostic(self):
        self.mutation(SPAWN, 'EventType := "spawn.tick_rebuild_failed"',
                      'EventType := "spawn.tick_completed"')

    def test_reference_rejection_preserves_other_players(self):
        current = {"p1_wall": 1, "p2_stairs": 2, "p3_route": 3}
        kept, ok = reference_remove(current, "p1_wall", "p3_route")
        self.assertFalse(ok)
        self.assertEqual(kept, current)

    def test_reference_success_removes_one_context(self):
        kept, ok = reference_remove({"p1": 1, "p2": 2}, "p1", None)
        self.assertTrue(ok)
        self.assertEqual(kept, {"p2": 2})


if __name__ == "__main__":
    unittest.main()
