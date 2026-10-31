#!/usr/bin/env python3
"""Exercise migration and reject source mutations; this does not run Verse."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from migrate_session_services import (
    MANIFEST, Service, accessor, discover, migrate, plan, read_sources,
    rewrite_references, validate_sources,
)

SOURCES = {
    "verse/service.verse": """using { /Verse.org/Simulation }

aeonfall_state := class:
    var Count:int = 0

aeonfall_facade := class:
    Add():int=1

AEONFALLState:aeonfall_state = aeonfall_state{}
AEONFALLFacade:aeonfall_facade = aeonfall_facade{}
""",
    "verse/device.verse": """aeonfall_owner := class:
    Isolated:aeonfall_state = aeonfall_state{}

    Read()<transacts>:int=
        Local := aeonfall_state{}
        AEONFALLState.Count + Local.Count
""",
}


class SessionMigrationTests(unittest.TestCase):
    def setUp(self):
        self.services = discover(SOURCES)

    def test_only_mutable_module_allocation_is_discovered(self):
        self.assertEqual([s.name for s in self.services], ["AEONFALLState"])

    def test_indirect_mutable_default_is_discovered(self):
        source = SOURCES["verse/service.verse"] + """
aeonfall_indirect := class:
    Nested:aeonfall_state = aeonfall_state{}

AEONFALLIndirect:aeonfall_indirect = aeonfall_indirect{}
"""
        found = discover({"verse/test.verse": source})
        self.assertEqual({s.name for s in found}, {"AEONFALLState", "AEONFALLIndirect"})

    def test_recursive_default_dependency_is_discovered(self):
        source = """aeonfall_mutable := class:
    var Value:int = 0

aeonfall_middle := class:
    State:aeonfall_mutable = aeonfall_mutable{}

aeonfall_outer := class:
    Middle:aeonfall_middle = aeonfall_middle{}

AEONFALLOuter:aeonfall_outer = aeonfall_outer{}
"""
        self.assertEqual(discover({"verse/outer.verse": source})[0].name, "AEONFALLOuter")

    def test_constructor_and_local_instances_are_preserved(self):
        output = migrate(SOURCES, self.services)
        self.assertIn("Isolated:aeonfall_state = aeonfall_state{}", output["verse/device.verse"])
        self.assertIn("Local := aeonfall_state{}", output["verse/device.verse"])
        self.assertIn("GetAEONFALLState().Count", output["verse/device.verse"])

    def test_immutable_module_facade_is_preserved(self):
        output = migrate(SOURCES, self.services)
        self.assertIn("AEONFALLFacade:aeonfall_facade = aeonfall_facade{}", output["verse/service.verse"])

    def test_accessors_and_imports_are_checked(self):
        output = migrate(SOURCES, self.services)
        self.assertIn("using { /Verse.org/Verse }", output["verse/service.verse"])
        self.assertEqual(validate_sources(output, self.services), [])

    def test_migration_is_idempotent(self):
        output = migrate(SOURCES, self.services)
        self.assertEqual(migrate(output, self.services), output)

    def test_identifier_suffix_and_existing_getter_are_not_rewritten(self):
        source = "AEONFALLState.Count GetAEONFALLState().Count AEONFALLStateSessions"
        result = rewrite_references(source, self.services)
        self.assertEqual(result, "GetAEONFALLState().Count GetAEONFALLState().Count AEONFALLStateSessions")

    def test_failed_retention_must_be_fatal(self):
        output = migrate(SOURCES, self.services)
        output["verse/service.verse"] = output["verse/service.verse"].replace(
            'Err("AEONFALL could not retain AEONFALLState in its session")', "aeonfall_state{}"
        )
        errors = validate_sources(output, self.services)
        self.assertTrue(any("Err(" in error for error in errors))
        self.assertTrue(any("unretained fallback" in error for error in errors))

    def test_map_write_removal_is_rejected(self):
        output = migrate(SOURCES, self.services)
        output["verse/service.verse"] = output["verse/service.verse"].replace(
            "set AEONFALLStateSessions[CurrentSession] = Created", "Created.Count = 0"
        )
        self.assertTrue(any("set AEONFALLStateSessions" in e for e in validate_sources(output, self.services)))

    def test_event_bus_cannot_return_an_unretained_state(self):
        source = """GetAEONFALLBusState()<transacts>:aeonfall_event_bus_state=
    if (State := AEONFALLBusStates[GetSession()]):
        return State
    aeonfall_event_bus_state{QueueCapacity := 0}
"""
        errors = validate_sources({"verse/bus.verse": source})
        self.assertTrue(any("event bus retention failure" in error for error in errors))

    def test_stale_usage_is_rejected(self):
        output = migrate(SOURCES, self.services)
        output["verse/device.verse"] = output["verse/device.verse"].replace("GetAEONFALLState().Count", "AEONFALLState.Count")
        self.assertTrue(any("stale mutable service reference" in e for e in validate_sources(output, self.services)))

    def test_session_and_player_weak_map_roots_are_allowed(self):
        source = """var AEONFALLLease:weak_map(session, [string]string) = map{}
var AEONFALLProfiles:weak_map(player, aeonfall_player_profile) = map{}
"""
        self.assertEqual(validate_sources({"verse/maps.verse": source}), [])

    def test_native_failable_parentheses_are_rejected(self):
        source = "    Character := Agent.GetFortCharacter()\n    FitsInPlayerMap(Candidate)\n"
        errors = validate_sources({"verse/broken.verse": source})
        self.assertEqual(len(errors), 2)

    def test_transactional_class_default_is_rejected(self):
        source = """aeonfall_owner := class:
    Registry:aeonfall_state = GetAEONFALLState()
"""
        errors = validate_sources({"verse/default.verse": source})
        self.assertTrue(any("class defaults" in error for error in errors))

    def test_bare_noop_branch_is_rejected(self):
        errors = validate_sources({"verse/noop.verse": "    if (Applied?):\n        Applied = true\n"})
        self.assertTrue(any("bare no-op" in e for e in errors))

    def test_comment_and_valid_failure_context_do_not_raise_native_guard(self):
        source = "# FitsInPlayerMap(Candidate)\n    if:\n        Owner = Owner\n    then:\n        Result := true\n"
        self.assertEqual(validate_sources({"verse/comments.verse": source}), [])

    def test_planning_updates_generator_and_manifest_then_stabilizes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path, source in SOURCES.items():
                dest = root / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(source)
            (root / "tools").mkdir()
            generator = root / "tools/build_generated.py"
            generator.write_text('output = "AEONFALLState.Count"\n')
            normalized_guard = root / "tools/validate_normalized.py"
            guard_text = 'def normalized(source: str):\n    return source\nfragment = "AEONFALLState.Count"\n'
            normalized_guard.write_text(guard_text)
            (root / "tests").mkdir()
            mutation_test = root / "tests/test_real_source.py"
            mutation_test.write_text('old = "AEONFALLState.Count"\n')
            changes, services = plan(root)
            self.assertEqual(generator.read_text(), 'output = "AEONFALLState.Count"\n')
            self.assertIn('"GetAEONFALLState().Count"', changes["tools/build_generated.py"])
            self.assertIn('"GetAEONFALLState().Count"', changes["tests/test_real_source.py"])
            self.assertNotIn("tools/validate_normalized.py", changes)
            for path, source in changes.items():
                destination = root / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(source)
            self.assertEqual(plan(root)[0], {})
            self.assertEqual(validate_sources(read_sources(root), services), [])
            self.assertEqual(len(json.loads((root / MANIFEST).read_text())["services"]), 1)


if __name__ == "__main__":
    unittest.main()
