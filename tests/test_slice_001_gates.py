"""Fail-closed mutation tests for source-only Ossuary gate and director handoff."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_slice_gates", ROOT / "tools/validate_slice_gates.py"
)
assert SPEC and SPEC.loader
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class GateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(audit.CONTRACT.read_text(encoding="utf-8"))
        cls.checkpoints = json.loads(audit.CHECKPOINTS.read_text(encoding="utf-8"))
        cls.encounters = json.loads(audit.ENCOUNTERS.read_text(encoding="utf-8"))
        cls.policy = audit.POLICY.read_text(encoding="utf-8")
        cls.gate = audit.GATE.read_text(encoding="utf-8")
        cls.director = audit.DIRECTOR.read_text(encoding="utf-8")

    def errors(self, **changes):
        values = {
            "contract": self.contract, "checkpoints": self.checkpoints,
            "encounters": self.encounters, "policy": self.policy,
            "gate_source": self.gate, "director": self.director,
        }
        values.update(changes)
        return audit.check_contract(**values)

    def test_canonical_source_passes(self):
        self.assertEqual(self.errors(), [])

    def test_missing_gate_fails(self):
        contract = copy.deepcopy(self.contract)
        contract["gates"].pop()
        self.assertTrue(self.errors(contract=contract))

    def test_out_of_order_gate_fails(self):
        contract = copy.deepcopy(self.contract)
        contract["gates"][0], contract["gates"][1] = contract["gates"][1], contract["gates"][0]
        self.assertTrue(self.errors(contract=contract))

    def test_removed_checkpoint_prefix_fails(self):
        contract = copy.deepcopy(self.contract)
        contract["gates"][3]["required_checkpoint_ids"] = ["SLICE-001:CHECKPOINT-4"]
        self.assertTrue(self.errors(contract=contract))

    def test_missing_first_clear_dependency_fails(self):
        contract = copy.deepcopy(self.contract)
        contract["gates"][3]["required_world_event_ids"] = []
        self.assertTrue(self.errors(contract=contract))

    def test_duplicate_physical_ref_fails(self):
        contract = copy.deepcopy(self.contract)
        contract["gates"][4]["destination_ref"] = contract["gates"][0]["destination_ref"]
        self.assertTrue(self.errors(contract=contract))

    def test_invented_uefn_path_fails(self):
        contract = copy.deepcopy(self.contract)
        contract["gates"][0]["editor_entry_path"] = "/Game/Invented"
        self.assertTrue(self.errors(contract=contract))

    def test_forged_native_test_evidence_fails(self):
        contract = copy.deepcopy(self.contract)
        contract["native_evidence"]["launch_session"] = "passed"
        self.assertTrue(self.errors(contract=contract))

    def test_non_player_director_start_fails(self):
        source = self.director.replace("AdmittingPlayer := player[AdmittingAgent]", "AdmittingPlayer := AdmittingAgent")
        self.assertTrue(self.errors(director=source))

    def test_bypassed_director_prerequisites_fail(self):
        source = self.director.replace("AEONFALLSlice001CanStart(Profile, EncounterId)?", "true?")
        self.assertTrue(self.errors(director=source))

    def test_removed_arena_participation_fails(self):
        source = self.director.replace("ParticipantVolume.GetAgentsInVolume().Find[AdmittingAgent]", "true?")
        self.assertTrue(self.errors(director=source))

    def test_unchecked_completion_output_fails(self):
        source = self.director.replace("if (Success? and ServiceAcknowledged?):", "if (Success?):")
        self.assertTrue(self.errors(director=source))

    def test_disconnect_without_cleanup_fails(self):
        source = self.director.replace("PlayerRemovedEvent().Subscribe(OnPlayerRemoved)", "PlayerRemovedEvent().Subscribe(OnOther)")
        self.assertTrue(self.errors(director=source))

    def test_missing_latch_reset_fails(self):
        source = self.gate.replace("set Latched = map{}", "Print(\"leaked\")")
        self.assertTrue(self.errors(gate_source=source))

    def test_gate_without_profile_fails(self):
        source = self.gate.replace("ProfileService.GetProfile[Player]", "ProfileService.SaveProfile(Player)")
        self.assertTrue(self.errors(gate_source=source))

    def test_new_persistent_root_fails(self):
        source = self.gate + "\nvar Extra:weak_map(player, int) = map{}\n"
        self.assertTrue(self.errors(gate_source=source))

    def test_removed_reward_dependency_fails(self):
        source = self.policy.replace('Profile.CompletedBossIds.Find["BOS-011"]', "true?")
        self.assertTrue(self.errors(policy=source))


if __name__ == "__main__":
    unittest.main()
