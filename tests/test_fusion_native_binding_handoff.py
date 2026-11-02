"""Source and adversarial inventory tests; no actual UEFN editor is launched."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "tools/uefn_editor/fusion_native_binding_handoff.py"
SPEC = importlib.util.spec_from_file_location("fusion_native_binding_handoff", MODULE)
assert SPEC and SPEC.loader
handoff = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(handoff)


class FusionBindingSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = handoff.read_contract(ROOT)
        cls.original = handoff.inventory_template(ROOT, cls.doc)

    def test_current_sources_have_the_exact_physical_editables(self):
        self.assertEqual(handoff.validate_contract(ROOT, self.doc), [])
        self.assertEqual(len(self.doc["components"]), 5)
        self.assertEqual(len(self.original["shared_editor_links"]), 5)
        self.assertGreater(len(self.original["objects"]), 20)

    def test_owner_reference_provisioning_must_remain_trusted(self):
        doc = copy.deepcopy(self.doc)
        doc["components"][0]["bindings"]["OwnerReference"]["restriction"] = "first_join"
        self.assertTrue(handoff.validate_contract(ROOT, doc))

    def test_armor_and_arsenal_must_share_exact_trigger(self):
        doc = copy.deepcopy(self.doc)
        doc["components"][2]["bindings"]["RendRequest"]["alias"] = "arsenal.Feedback"
        self.assertTrue(handoff.validate_contract(ROOT, doc))

    def test_controllers_cannot_be_deleted_or_duplicated(self):
        doc = copy.deepcopy(self.doc)
        doc["components"].pop()
        self.assertTrue(handoff.validate_contract(ROOT, doc))
        doc = copy.deepcopy(self.doc)
        doc["components"][0]["id"] = "armor"
        self.assertTrue(handoff.validate_contract(ROOT, doc))

    def test_enablement_cannot_be_forged_in_authored_contract(self):
        doc = copy.deepcopy(self.doc)
        doc["editor_guardrails"]["titan_enabled"] = True
        self.assertTrue(handoff.validate_contract(ROOT, doc))
        doc = copy.deepcopy(self.doc)
        doc["native_evidence"]["uefn_compile"] = "passed"
        self.assertTrue(handoff.validate_contract(ROOT, doc))

    def test_titan_audio_only_and_waypoint_limits(self):
        doc = copy.deepcopy(self.doc)
        doc["components"][-1]["bindings"]["AttackCueOutput"]["restriction"] = "direct_damage"
        self.assertTrue(handoff.validate_contract(ROOT, doc))
        doc = copy.deepcopy(self.doc)
        doc["components"][-1]["bindings"]["Waypoints"]["max_items"] = 500
        self.assertTrue(handoff.validate_contract(ROOT, doc))

    def test_source_change_requires_manifest_update_and_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for component in self.doc["components"]:
                p = root / component["source"]
                p.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / component["source"], p)
            code = root / self.doc["components"][1]["source"]
            data = code.read_text()
            self.assertIn("Enabled:logic = false", data)
            code.write_text(data.replace("Enabled:logic = false", "Enabled:logic = true", 1))
            self.assertTrue(handoff.validate_contract(root, self.doc))
            code.write_text(data.replace(
                "    @editable\n    AttackOutput:trigger_device",
                "    @editable\n    ExtraInput:input_trigger_device = input_trigger_device{}\n    @editable\n    AttackOutput:trigger_device",
                1
            ))
            self.assertTrue(handoff.validate_contract(root, self.doc))

    def test_unexpected_manifest_role_properties_fail_closed(self):
        doc = copy.deepcopy(self.doc)
        doc["components"][1]["bindings"]["FuseInput"]["editor_verified"] = True
        self.assertTrue(handoff.validate_contract(ROOT, doc))

    def test_duplicate_editable_declarations_are_rejected(self):
        source = (
            "    @editable\n    Input:input_trigger_device = input_trigger_device{}\n"
            "    @editable\n    Input:input_trigger_device = input_trigger_device{}\n"
        )
        with self.assertRaisesRegex(ValueError, "Duplicate @editable"):
            handoff.source_device_editables(source)

    def test_source_hashes_and_never_native_evidence_template(self):
        doc = self.original
        self.assertEqual(doc["native_evidence"], handoff.EVIDENCE_STATE)
        self.assertEqual(doc["claim_boundary"], "operator_binding_report_only_not_native_acceptance")
        self.assertIsNone(doc["editor_capture"])
        self.assertTrue(all(item.get("object_path") is None or
                            item.get("object_paths") == [] for item in doc["objects"]))


class FusionBindingReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = handoff.read_contract(ROOT)
        cls.template = handoff.inventory_template(ROOT, cls.doc)

    def report(self, inventory=None, **kwargs):
        return handoff.audit(ROOT, self.doc, inventory or copy.deepcopy(self.template), **kwargs)

    def test_unbound_checklist_is_consistent_but_not_playable(self):
        result = self.report()
        self.assertTrue(result["binding_consistent"], result["errors"])
        self.assertFalse(result["core_binding_report_complete"])
        self.assertEqual(result["native_playability"], "not_established")
        self.assertIn("authority.OwnerReference", result["unbound_core_roles"])

    def test_duplicate_editor_object_assignment_fails(self):
        inventory = copy.deepcopy(self.template)
        for role in ("authority", "armor"):
            record = next(item for item in inventory["objects"] if item["role_id"] == role)
            record["object_path"] = "/AEONFALL/Tests/Duplicate_123"
            record["observed_type"] = record["expected_type"]
        self.assertFalse(self.report(inventory)["binding_consistent"])

    def test_duplicate_role_record_fails(self):
        inventory = copy.deepcopy(self.template)
        inventory["objects"].append(copy.deepcopy(inventory["objects"][0]))
        self.assertFalse(self.report(inventory)["binding_consistent"])

    def test_unknown_role_or_wrong_native_class_fails(self):
        inventory = copy.deepcopy(self.template)
        inventory["objects"][0]["role_id"] = "unknown"
        self.assertFalse(self.report(inventory)["binding_consistent"])
        inventory = copy.deepcopy(self.template)
        obj = inventory["objects"][0]
        obj["object_path"] = "/AEONFALL/Editor/Actor0"
        obj["observed_type"] = "npc_spawner_device"
        self.assertFalse(self.report(inventory)["binding_consistent"])

    def test_report_cannot_claim_native_compilation(self):
        inventory = copy.deepcopy(self.template)
        inventory["native_evidence"]["uefn_compile"] = "passed"
        self.assertFalse(self.report(inventory)["binding_consistent"])

    def test_unrecognized_editor_proof_property_is_rejected(self):
        inventory = copy.deepcopy(self.template)
        inventory["native_verified"] = True
        self.assertFalse(self.report(inventory)["binding_consistent"])
        inventory = copy.deepcopy(self.template)
        inventory["objects"][0]["compiled"] = True
        self.assertFalse(self.report(inventory)["binding_consistent"])

    def test_claimed_class_without_object_path_is_rejected(self):
        inventory = copy.deepcopy(self.template)
        inventory["objects"][0]["observed_type"] = inventory["objects"][0]["expected_type"]
        self.assertFalse(self.report(inventory)["binding_consistent"])

    def test_stale_source_digest_fails(self):
        inventory = copy.deepcopy(self.template)
        first = next(iter(inventory["verse_source_sha256"]))
        inventory["verse_source_sha256"][first] = "0" * 64
        self.assertFalse(self.report(inventory)["binding_consistent"])

    def test_alias_target_mismatch_and_forged_link_fail(self):
        inventory = copy.deepcopy(self.template)
        armor_output = next(i for i in inventory["objects"] if i["role_id"] == "armor.AttackOutput")
        armor_output["object_path"] = "/AEONFALL/Editor/RealAttack"
        armor_output["observed_type"] = "trigger_device"
        inventory["shared_editor_links"]["arsenal.RendRequest"]["observed_object_path"] = "/AEONFALL/Editor/WrongAttack"
        self.assertFalse(self.report(inventory)["binding_consistent"])
        inventory["shared_editor_links"]["arsenal.RendRequest"]["target_role"] = "arsenal.Feedback"
        self.assertFalse(self.report(inventory)["binding_consistent"])

    def test_editor_path_traversal_and_placeholder_fails(self):
        for path in ("/AEONFALL/../Actor", "/Game/<placeholder>", "/Game/Bad Path", "../Game/Actor"):
            with self.subTest(path=path):
                self.assertFalse(handoff.valid_editor_path(path))

    def test_optional_waypoint_count_limit_and_path_uniqueness(self):
        inventory = copy.deepcopy(self.template)
        waypoint = next(i for i in inventory["objects"] if i["role_id"] == "titan.Waypoints")
        waypoint["object_paths"] = [f"/AEONFALL/Waypoints/Waypoint{i}" for i in range(9)]
        waypoint["observed_types"] = ["creative_prop"] * 9
        self.assertFalse(self.report(inventory)["binding_consistent"])
        waypoint["object_paths"] = ["/AEONFALL/Waypoints/Same"] * 2
        waypoint["observed_types"] = ["creative_prop"] * 2
        self.assertFalse(self.report(inventory)["binding_consistent"])

    def test_operator_reported_full_core_is_not_native_proof(self):
        inventory = copy.deepcopy(self.template)
        paths = {}
        for index, record in enumerate(inventory["objects"]):
            if record["role_id"].split(".", 1)[0] not in {"authority", "armor", "arsenal"}:
                continue
            record["object_path"] = f"/AEONFALL/Editor/UniqueAsset{index}"
            record["observed_type"] = record["expected_type"]
            paths[record["role_id"]] = record["object_path"]
        for alias, value in inventory["shared_editor_links"].items():
            if alias.split(".", 1)[0] in {"authority", "armor", "arsenal"}:
                value["observed_object_path"] = paths[value["target_role"]]
        # Even an operator-reported complete core inventory cannot be
        # considered complete without a project, level, and checked capture.
        self.assertFalse(self.report(inventory)["core_binding_report_complete"])
        inventory["editor_project"] = "AEONFALL-Editor-Project-From-Operator"
        inventory["editor_level"] = "/AEONFALL/Maps/ActualEditorLevel"
        with tempfile.TemporaryDirectory() as directory:
            capture = Path(directory) / "editor_capture.txt"
            capture.write_bytes(b"untrusted-operator-evidence-not-fortnite")
            inventory["editor_capture"] = {
                "path": capture.name,
                "sha256": hashlib.sha256(capture.read_bytes()).hexdigest(),
            }
            result = self.report(inventory, evidence_root=directory)
        self.assertTrue(result["binding_consistent"], result["errors"])
        self.assertTrue(result["core_binding_report_complete"])
        self.assertEqual(result["native_verse_compile"], "not_assessed")
        self.assertEqual(result["native_multiplayer"], "not_assessed")
        self.assertEqual(result["native_playability"], "not_established")

    def test_missing_source_alias_or_broken_report_fails_closed(self):
        inventory = copy.deepcopy(self.template)
        inventory["shared_editor_links"].pop("arsenal.RendRequest")
        self.assertFalse(self.report(inventory)["binding_consistent"])
        inventory = copy.deepcopy(self.template)
        inventory["objects"].pop()
        self.assertFalse(self.report(inventory)["binding_consistent"])

    def test_evidence_capture_hash_checked_without_native_claim(self):
        inventory = copy.deepcopy(self.template)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            blob = root / "editor_capture.txt"
            blob.write_bytes(b"operator-supplied-file-not-validated-uefn")
            inventory["editor_capture"] = {
                "path": blob.name, "sha256": hashlib.sha256(blob.read_bytes()).hexdigest()
            }
            result = self.report(inventory, evidence_root=root)
            self.assertTrue(result["binding_consistent"], result["errors"])
            self.assertTrue(result["editor_capture_integrity_checked"])
            self.assertEqual(result["native_playability"], "not_established")
            inventory["editor_capture"]["sha256"] = "0" * 64
            self.assertFalse(self.report(inventory, evidence_root=root)["binding_consistent"])

    def test_evidence_root_traversal_rejected(self):
        inventory = copy.deepcopy(self.template)
        inventory["editor_capture"] = {"path": "../outside.txt", "sha256": "0" * 64}
        with tempfile.TemporaryDirectory() as directory:
            self.assertFalse(self.report(inventory, evidence_root=directory)["binding_consistent"])


if __name__ == "__main__":
    unittest.main()
