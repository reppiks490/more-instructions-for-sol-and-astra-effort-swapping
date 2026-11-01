"""Mock-only regression tests for the SLICE-001 physical binding audit."""
import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools/uefn_editor/slice_001_binding_audit.py"
spec = importlib.util.spec_from_file_location("slice_001_binding_audit", MODULE)
audit_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_module)


class BindingAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.paths = [self.root / x for x in ("rig.json", "bindings.json", "launch.json")]
        rig = {"state": "authored_unplaced", "encounter_id": "BOS-005", "devices": [
            {"id": "start", "type": "trigger_device"},
            {"id": "arena", "type": "volume_device"},
            {"id": "director", "type": "aeonfall_encounter_director_device",
             "bindings": {"StartInput": "start", "ParticipantVolume": "arena"}}]}
        for path, value in zip(self.paths, (rig, {"slice_id": "SLICE-001"},
                                             {"slice_id": "SLICE-001", "tests": [{"id": "LT-001"}]})):
            path.write_text(json.dumps(value))
        self.spec = audit_module.contracts(*self.paths)
        self.inventory = audit_module.template(self.spec)
        for item in self.inventory["observations"]:
            item["observed_class"] = next(d["type"] for d in self.spec["devices"] if d["id"] == item["device_id"])
            item["object_path"] = "/Game/Test." + item["device_id"]
        self.inventory["director_observed_links"] = {"start": "/Game/Test.start", "arena": "/Game/Test.arena"}
        self.inventory["editor_project"] = "AEONFALL"
        self.inventory["editor_level"] = "/Game/Test"

    def verify(self, inventory=None):
        return audit_module.audit(self.spec, inventory if inventory is not None else self.inventory,
                                  evidence_root=self.root)

    def test_authored_source_contract_counts(self):
        actual = audit_module.contracts()
        self.assertEqual(len(actual["devices"]), 49)
        self.assertEqual(len(actual["refs"]), 42)
        self.assertEqual(len(actual["test_ids"]), 24)
        bindings = json.loads(audit_module.BINDINGS.read_text())
        for kind, count in (("weapons", 12), ("monsters", 12), ("tameables", 6),
                            ("hireables", 8), ("encounters", 3), ("vehicles", 3)):
            self.assertEqual(len(bindings[kind]), count, kind)

    def test_valid_inventory_does_not_claim_native_acceptance(self):
        result = self.verify()
        self.assertTrue(result["inventory_consistent"])
        self.assertEqual(result["matching_role_count"], 2)
        self.assertEqual(result["native_verse_compile"], "not_assessed")
        self.assertEqual(result["playable_claim"], "not_established")

    def test_blank_template_fails_closed(self):
        result = self.verify(audit_module.template(self.spec))
        self.assertFalse(result["inventory_consistent"])
        self.assertEqual(result["observed_device_count"], 0)

    def test_duplicate_physical_path_rejected(self):
        self.inventory["observations"][1]["object_path"] = "/Game/Test.start"
        self.assertTrue(any("aliased" in e for e in self.verify()["errors"]))

    def test_wrong_class_rejected(self):
        self.inventory["observations"][0]["observed_class"] = "npc_spawner_device"
        self.assertTrue(any("class mismatch" in e for e in self.verify()["errors"]))

    def test_missing_and_duplicate_observations_rejected(self):
        self.inventory["observations"].pop()
        self.inventory["observations"].append(copy.deepcopy(self.inventory["observations"][0]))
        errors = self.verify()["errors"]
        self.assertTrue(any("Duplicate device" in e for e in errors))
        self.assertTrue(any("no editor observation" in e for e in errors))

    def test_misdirected_link_rejected(self):
        self.inventory["director_observed_links"]["start"] = "/Game/Test.arena"
        self.assertTrue(any("mismatched observed director link" in e for e in self.verify()["errors"]))

    def test_unknown_link_rejected(self):
        self.inventory["director_observed_links"]["invented"] = "/Game/Test.fake"
        self.assertTrue(any("Unexpected director" in e for e in self.verify()["errors"]))

    def test_stale_contract_rejected(self):
        self.inventory["contract_sha256"]["rig"] = "0" * 64
        self.assertTrue(any("contracts changed" in e for e in self.verify()["errors"]))

    def test_capture_hash_and_boundary(self):
        path = self.root / "editor-capture.log"
        path.write_text("local editor capture\n")
        self.inventory["editor_capture"] = {
            "path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        self.assertTrue(self.verify()["editor_capture_integrity_checked"])
        self.inventory["editor_capture"]["sha256"] = "0" * 64
        self.assertTrue(any("SHA-256 mismatch" in e for e in self.verify()["errors"]))
        self.inventory["editor_capture"]["path"] = "../escape.log"
        self.assertTrue(any("outside evidence root" in e for e in self.verify()["errors"]))

    def test_claimed_launch_pass_does_not_establish_playability(self):
        self.inventory["launch_test_status"]["LT-001"] = "passed"
        result = self.verify()
        self.assertEqual(result["launch_tests_claimed_passed"], 1)
        self.assertEqual(result["fortnite_launch_session"], "not_assessed")

    def test_missing_test_status_rejected(self):
        self.inventory["launch_test_status"].clear()
        self.assertTrue(any("exact canonical IDs" in e for e in self.verify()["errors"]))

    def test_duplicate_source_reference_rejected(self):
        self.paths[0].write_text(json.dumps({
            "state": "authored_unplaced", "encounter_id": "BOS-005",
            "devices": [{"id": "start", "type": "trigger_device"},
                        {"id": "director", "type": "aeonfall_encounter_director_device",
                         "bindings": {"StartInput": "start", "FailInput": "start"}}]}))
        with self.assertRaisesRegex(ValueError, "multiple roles"):
            audit_module.contracts(*self.paths)


if __name__ == "__main__":
    unittest.main()
