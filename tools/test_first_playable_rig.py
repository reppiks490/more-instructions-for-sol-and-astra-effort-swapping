#!/usr/bin/env python3
"""Mutation evidence for authored rig safety, not engine/device execution."""
import copy
import unittest

from build_first_playable_rig import build
from validate_first_playable_rig import validate_rig


class RigTests(unittest.TestCase):
    def setUp(self):
        self.rig = build()
        self.director = self.rig['devices'][-1]
        self.phases = self.director['bindings']['Phases']

    def rejects(self):
        self.assertTrue(validate_rig(self.rig))

    def test_authored_intent_valid(self):
        self.assertEqual(validate_rig(self.rig), [])

    def test_duplicate_device_id_rejected(self):
        self.rig['devices'].append(copy.deepcopy(self.rig['devices'][0]))
        self.rejects()

    def test_same_physical_stair_source_cannot_credit_three_anchors(self):
        stairs = [item for item in self.phases[1]['inputs'] if item['kind'] == 'Objective']
        stairs[1]['device_ref'] = stairs[0]['device_ref']
        stairs[2]['device_ref'] = stairs[0]['device_ref']
        self.rejects()

    def test_boss_spawner_cannot_be_cleaned_up_as_add_group(self):
        self.phases[0]['spawn_groups'][0]['spawner_refs'] = ['boss_spawner']
        self.rejects()

    def test_input_output_feedback_rejected(self):
        self.phases[0]['inputs'][0]['device_ref'] = self.phases[0]['enter_ref']
        self.rejects()

    def test_unresolved_binding_rejected(self):
        self.director['bindings']['ParticipantVolume'] = 'not_placed'
        self.rejects()

    def test_resolved_objects_cannot_alias(self):
        self.rig['devices'][0]['resolved_editor_object_path'] = '/same/editor/object'
        self.rig['devices'][1]['resolved_editor_object_path'] = '/same/editor/object'
        self.rejects()

    def test_dependency_cycle_rejected(self):
        self.rig['devices'][0]['depends_on'] = ['bos005_director']
        self.rejects()

    def test_unresolved_dependency_rejected(self):
        self.director['depends_on'].append('missing_bootstrap')
        self.rejects()

    def test_required_bootstrap_cannot_be_dropped(self):
        self.director['depends_on'].remove('player_profile')
        self.rejects()

    def test_native_anchor_cannot_be_replaced_with_manual_credit(self):
        self.phases[1]['inputs'][0]['source'] = 'TriggerGraph'
        self.rejects()

    def test_one_destruction_source_cannot_cover_multiple_props(self):
        target = self.phases[1]['inputs'][0]['device_ref']
        next(item for item in self.rig['devices'] if item['id'] == target)['affected_prop_count'] = 3
        self.rejects()

    def test_fake_boss_defeat_evidence_rejected(self):
        self.rig['native_completion']['defeat_source'] = 'manual_trigger'
        self.rejects()

    def test_phase_order_mismatch_rejected(self):
        self.phases.reverse()
        self.rejects()

    def test_unplaced_manifest_cannot_claim_completed_session(self):
        self.rig['execution_evidence']['launch_session'] = 'passed'
        self.rejects()

    def test_spawn_cap_cannot_exceed_canonical(self):
        self.phases[0]['spawn_groups'][0]['maximum_live'] = 13
        self.rejects()


if __name__ == '__main__':
    unittest.main()
