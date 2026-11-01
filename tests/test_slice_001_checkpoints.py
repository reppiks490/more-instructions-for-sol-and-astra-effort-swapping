"""Mutation tests for the source-only Ossuary checkpoint/respawn contract."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_slice_checkpoints", ROOT / "tools/validate_slice_checkpoints.py"
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class CheckpointContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(module.MANIFEST.read_text(encoding="utf-8"))
        cls.contract = json.loads(module.CONTRACT.read_text(encoding="utf-8"))
        cls.source = module.VERSE.read_text(encoding="utf-8")

    def errors(self, manifest=None, contract=None, source=None):
        return module.check_contract(
            self.manifest if manifest is None else manifest,
            self.contract if contract is None else contract,
            self.source if source is None else source,
        )

    def test_authored_contract_passes(self):
        self.assertEqual(self.errors(), [])

    def test_missing_geometry_checkpoint_fails(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["markers"] = [m for m in manifest["markers"] if m.get("id") != "CHECKPOINT-4"]
        self.assertTrue(self.errors(manifest=manifest))

    def test_reordered_checkpoint_fails(self):
        contract = copy.deepcopy(self.contract)
        contract["checkpoints"][1], contract["checkpoints"][2] = (
            contract["checkpoints"][2], contract["checkpoints"][1]
        )
        self.assertTrue(self.errors(contract=contract))

    def test_spatial_drift_fails(self):
        contract = copy.deepcopy(self.contract)
        contract["checkpoints"][0]["design_anchor_location_cm"][0] += 500
        self.assertTrue(self.errors(contract=contract))

    def test_duplicate_physical_reference_fails(self):
        contract = copy.deepcopy(self.contract)
        contract["checkpoints"][1]["teleporter_ref"] = contract["checkpoints"][0]["teleporter_ref"]
        self.assertTrue(self.errors(contract=contract))

    def test_wrong_device_class_fails(self):
        contract = copy.deepcopy(self.contract)
        contract["checkpoints"][0]["volume_type"] = "trigger_device"
        self.assertTrue(self.errors(contract=contract))

    def test_unverified_editor_path_fails(self):
        contract = copy.deepcopy(self.contract)
        contract["checkpoints"][0]["editor_teleporter_path"] = "/Game/Invented"
        self.assertTrue(self.errors(contract=contract))

    def test_forged_native_evidence_fails(self):
        contract = copy.deepcopy(self.contract)
        contract["execution_evidence"]["uefn_compile"] = "passed"
        self.assertTrue(self.errors(contract=contract))

    def test_nonsequential_policy_fails(self):
        contract = copy.deepcopy(self.contract)
        contract["rules"]["progression"] = "any_order"
        self.assertTrue(self.errors(contract=contract))

    def test_unchecked_profile_write_fails(self):
        source = self.source.replace(
            "ProfileService.TrySaveProfile(Player, Candidate)",
            "ProfileService.SaveProfile(Player, Candidate)"
        )
        self.assertTrue(self.errors(source=source))

    def test_removed_predecessor_guard_fails(self):
        source = self.source.replace("Old.DiscoveredPoiIds.Find[PreviousId]", "true?")
        self.assertTrue(self.errors(source=source))

    def test_removed_teleport_fails(self):
        source = self.source.replace("Destination.Teleport(Player)", "Print(\"no teleport\")")
        self.assertTrue(self.errors(source=source))

    def test_missing_cleanup_fails(self):
        source = self.source.replace("Subscription.Cancel()", "Print(\"leak\")")
        self.assertTrue(self.errors(source=source))


if __name__ == "__main__":
    unittest.main()
