"""Universe-first acceptance: ALL canonical catalog entries, zero sample ceilings."""
from __future__ import annotations

import copy
import importlib.util
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "universe_audit", ROOT / "tools/audit_universe_readiness.py")
assert SPEC and SPEC.loader
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class FullUniverseAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = audit.read_json(ROOT / audit.POLICY)
        cls.inventory = audit.read_json(ROOT / audit.INVENTORY)
        cls.current = audit.audit(ROOT)

    def modified(self, mutate):
        policy = copy.deepcopy(self.policy)
        inventory = copy.deepcopy(self.inventory)
        mutate(policy, inventory)
        return audit.audit(ROOT, policy_override=policy, inventory_override=inventory)

    def test_every_catalog_entity_is_examined_not_sampled(self):
        report = self.current
        self.assertGreaterEqual(report["catalog"]["major_entities"], 800)
        self.assertEqual(
            report["catalog"]["major_entities"],
            len(report["catalog"]["entity_rows"]),
        )
        self.assertEqual(
            report["catalog"]["major_entities"],
            len({row["id"] for row in report["catalog"]["entity_rows"]}),
        )
        self.assertEqual(report["audit_type"], "full_catalog_no_samples")

    def test_world_includes_all_thirteen_regions(self):
        self.assertGreaterEqual(self.current["world"]["region_count"], 13)
        self.assertEqual(set(self.current["world"]["required_regions"]),
                         {f"REG-{i:03d}" for i in range(1, 14)})

    def test_all_published_targets_stay_at_or_above_original_minimums(self):
        self.assertGreaterEqual(self.current["catalog"]["minimum_target"], 800)
        self.assertGreaterEqual(
            sum(self.current["catalog"]["minimums"].values()), 800)
        self.assertTrue(self.policy["no_cutdown_scope"])

    def test_catalog_specifications_are_not_a_complete_universe(self):
        empty = self.modified(lambda p, i: i.update({
            "entity_packs": [], "region_packs": [], "system_packs": []}))
        self.assertFalse(empty["source_complete"])
        self.assertFalse(empty["native_uefn_complete"])
        self.assertEqual(empty["source_delivery"]["entity_packs"]["approved"], 0)
        self.assertEqual(empty["source_delivery"]["entity_packs"]["total"],
                         empty["catalog"]["major_entities"])

    def test_all_regions_and_systems_require_distinct_source_packages(self):
        self.assertEqual(self.current["source_delivery"]["region_packs"]["total"], 13)
        self.assertGreaterEqual(self.current["source_delivery"]["system_packs"]["total"], 13)

    def test_actual_uefn_evidence_not_inferred_from_verse_files(self):
        self.assertFalse(self.current["native_uefn_complete"])
        self.assertTrue(all(
            not row["uefn_asset_bound_verified"] or row["native_evidence_recorded"]
            for row in self.current["catalog"]["entity_rows"]
        ))

    def test_user_priority_is_full_universe_not_first_playable_slice(self):
        self.assertEqual(self.policy["strategy"],
                         "full_universe_source_before_playable_prototype")
        self.assertTrue(self.current["playable_prototype_deferred"])
        self.assertTrue(self.policy["source_complete_does_not_imply_native_complete"])

    def test_missing_catalog_source_evidence_never_gets_auto_approved(self):
        def mutation(p, inv):
            inv["entity_packs"].append({
                "canonical_id": "WPN-001",
                "regions": ["REG-001"],
                "unique_visual_key": "GenuineDistinctModelID",
                "sources": {},
                "source_review": {"state": "approved_source",
                                  "reviewer": "Source QA", "evidence": "Mock"},
            })
        report = self.modified(mutation)
        self.assertNotIn("WPN-001",
                         report["source_delivery"]["entity_packs"]["approved_ids"])

    def test_unknown_catalog_id_rejected(self):
        def mutation(p, inv):
            inv["entity_packs"].append({
                "canonical_id": "WPN-9999", "sources": {},
                "regions": ["REG-001"],
            })
        report = self.modified(mutation)
        self.assertTrue(any("Unknown canonical_id" in e
                            for e in report["validation_errors"]))

    def test_duplicate_source_package_rejected(self):
        def mutation(p, inv):
            inv["region_packs"] = [
                {"region_id": "REG-001", "sources": {}},
                {"region_id": "REG-001", "sources": {}},
            ]
        report = self.modified(mutation)
        self.assertTrue(any("duplicate source package" in e
                            for e in report["validation_errors"]))

    def test_path_traversal_and_nonexistent_assets_rejected(self):
        self.assertFalse(audit.real_file(ROOT, "../../keys.txt"))
        self.assertFalse(audit.real_file(ROOT, "/etc/passwd"))
        self.assertFalse(audit.real_file(ROOT, "nonexistent.fake"))
        self.assertTrue(audit.real_file(ROOT, audit.POLICY))

    def test_unknown_region_scope_is_not_allowed(self):
        def mutation(p, inv):
            inv["entity_packs"].append({
                "canonical_id": "WPN-001",
                "regions": ["REG-999"],
                "unique_visual_key": "Test",
                "sources": {},
                "source_review": {"state": "approved_source",
                                  "reviewer": "Source QA", "evidence": "Test"},
            })
        report = self.modified(mutation)
        self.assertTrue(any("unrecognized region scope" in e
                            for e in report["validation_errors"]))

    def test_fabricated_native_proof_rejected(self):
        def mutation(p, inv):
            inv["native_complete"] = True
            inv["entity_packs"].append({
                "canonical_id": "WPN-001", "regions": ["REG-001"],
                "sources": {}, "native_uefn_verified": True,
            })
        report = self.modified(mutation)
        self.assertTrue(any("must not claim published/native completion" in e
                            for e in report["validation_errors"]))
        self.assertTrue(any("falsely claims native/playable" in e
                            for e in report["validation_errors"]))

    def test_source_review_claim_requires_evidence(self):
        def mutation(p, inv):
            inv["region_packs"].append({
                "region_id": "REG-001",
                "sources": {},
                "source_review": {"state": "approved_source"},
            })
        report = self.modified(mutation)
        self.assertTrue(any("unsubstantiated source review" in e
                            for e in report["validation_errors"]))

    def test_cannot_lower_entire_universe_minimum(self):
        report = self.modified(
            lambda p, i: p.__setitem__("minimum_major_entities", 20))
        self.assertTrue(any("Unauthorized reduction" in e
                            for e in report["validation_errors"]))

    def test_cannot_disable_codex_ban_or_scope(self):
        report = self.modified(
            lambda p, i: p.__setitem__("no_codex_in_automation", False))
        self.assertTrue(any("Codex prohibition" in e
                            for e in report["validation_errors"]))

    def test_approved_entity_visual_keys_must_be_unique_and_typed(self):
        # Synthetic fixture files are created only inside a temporary directory.
        # They never count toward the real 840-entity delivery inventory.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            categories = self.policy["entity_source_categories"]["weapon"]

            def pack(ident, visual_key):
                sources = {}
                for category in categories:
                    relative = f"{ident}/{category}.txt"
                    target = root / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(f"{ident} {category}", encoding="utf-8")
                    sources[category] = [relative]
                return {
                    "canonical_id": ident, "regions": ["REG-001"],
                    "unique_visual_key": visual_key, "sources": sources,
                    "source_review": {
                        "state": "approved_source", "reviewer": "fixture-reviewer",
                        "evidence": "synthetic unit-test evidence",
                    },
                }

            def inspect(packs):
                inventory = {
                    "schema_version": 1, "entity_packs": packs,
                    "region_packs": [], "system_packs": [],
                }
                return audit.inspect_inventory(
                    root, self.policy, inventory,
                    {"WPN-001": {"family": "weapon"},
                     "WPN-002": {"family": "weapon"}},
                    {"REG-001"}, set(),
                )

            first = pack("WPN-001", "Dread-plate-alpha")
            second = pack("WPN-002", " dread-PLATE-ALPHA ")
            approvals, errors = inspect([first, second])
            self.assertEqual(approvals["entity_packs"]["approved"], 1)
            self.assertTrue(any("duplicate unique_visual_key" in e for e in errors))

            distinct = copy.deepcopy(second)
            distinct["unique_visual_key"] = "Dread-plate-beta"
            approvals, errors = inspect([first, distinct])
            self.assertEqual(approvals["entity_packs"]["approved"], 2)
            self.assertEqual(errors, [])

            invalid = copy.deepcopy(second)
            invalid["unique_visual_key"] = ["not-a-string"]
            approvals, errors = inspect([first, invalid])
            self.assertEqual(approvals["entity_packs"]["approved"], 1)
            self.assertTrue(any("missing/invalid unique_visual_key" in e
                                for e in errors))

    def test_report_does_not_claim_imported_uefn_project(self):
        document = audit.markdown(self.current)
        self.assertIn("Source complete", document)
        self.assertIn("Native UEFN verified", document)
        self.assertIn("not a sample", document)
        self.assertNotIn("UEFN compilation passed", document)


if __name__ == "__main__":
    unittest.main()
