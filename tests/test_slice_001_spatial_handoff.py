"""Mock and real-source checks. No UEFN execution is performed."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / 'tools/uefn_editor/slice_001_spatial_handoff.py'
spec = importlib.util.spec_from_file_location('slice_001_spatial_handoff', MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    markers = []
    for key, y, x in [('PLAYER-SPAWN', -2900, 0), ('CHECKPOINT-1', -1000, 0),
                      ('CHECKPOINT-2', 2900, 0), ('CHECKPOINT-3', 6500, 0),
                      ('CHECKPOINT-4', 11900, 0), ('EC_BOS_005', 9400, -3400),
                      ('EC_BOS_011', 15000, 0), ('EVT-011-MARKET', 0, 0),
                      ('GRAVE-MARKET-QUARTERMASTER', -700, -1000),
                      ('OBJ-BOS011-BREAK-TREASURY-A', 15400, -1200),
                      ('OBJ-BOS011-BREAK-TREASURY-B', 15400, 1200)]:
        markers.append({'id': key, 'location_cm': [x, y, 100], 'radius_cm': 200})
    manifest = {'schema_version': 1, 'markers': markers,
                'rooms': [{'id': 'outer_market', 'center_m': [0, 0], 'size_m': [32, 28]},
                          {'id': 'miniboss_branch', 'center_m': [-34, 94], 'size_m': [24, 24]},
                          {'id': 'black_throne', 'center_m': [0, 150], 'size_m': [44, 44]}],
                'walkable_paths': [
                    {'id': 'main_route', 'points_cm': [[0, -2900, 0], [0, 15000, 0]],
                     'required_clear_width_cm': 480, 'required_clear_height_cm': 300},
                    {'id': 'miniboss_branch', 'points_cm': [[0, 9400, 0], [-3400, 9400, 0]],
                     'required_clear_width_cm': 480, 'required_clear_height_cm': 300}],
                'modules': [{}] * 18, 'placements': [{}] * 593}
    rig = {'state': 'authored_unplaced', 'encounter_id': 'BOS-005', 'devices': [
        {'id': 'runtime_tick', 'type': 'aeonfall_runtime_tick_device', 'depends_on': []},
        {'id': 'boss_spawner', 'type': 'npc_spawner_device', 'depends_on': []},
        {'id': 'bos005_director', 'type': 'aeonfall_encounter_director_device',
         'depends_on': ['runtime_tick']}]}
    bindings = {'slice_id': 'SLICE-001', 'world_event': {'id': 'EVT-011'}}
    for category, count in module.CATEGORIES.items():
        bindings[category] = [{'id': f'{category}-{n}'} for n in range(count)]
    launch = {'slice_id': 'SLICE-001', 'tests': [{'id': 'LT-001'}]}
    return manifest, rig, bindings, launch


class SpatialHandoffTests(unittest.TestCase):
    def test_unplaced_handoff(self):
        data = module.build(*fixture())
        self.assertEqual(data['geometry']['placement_count'], 593)
        self.assertEqual(data['rig_devices'][1]['design_anchor_id'], 'EC_BOS_005')
        self.assertIsNone(data['rig_devices'][1]['actual_editor_position_cm'])
        self.assertEqual(data['playable_claim'], 'not_established')
        self.assertEqual(len(data['content_bindings']['weapons']), 12)

    def test_duplicate_marker_rejected(self):
        args = list(fixture())
        args[0]['markers'].append(copy.deepcopy(args[0]['markers'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate/malformed marker'):
            module.build(*args)

    def test_boss_outside_room_rejected(self):
        args = list(fixture())
        next(m for m in args[0]['markers'] if m['id'] == 'EC_BOS_005')['location_cm'][0] = 999999
        with self.assertRaisesRegex(ValueError, 'outside miniboss_branch'):
            module.build(*args)

    def test_checkpoint_regression_rejected(self):
        args = list(fixture())
        next(m for m in args[0]['markers'] if m['id'] == 'CHECKPOINT-3')['location_cm'][1] = 1000
        with self.assertRaisesRegex(ValueError, 'Checkpoints do not progress'):
            module.build(*args)

    def test_missing_content_binding_rejected(self):
        args = list(fixture())
        args[2]['tameables'].pop()
        with self.assertRaisesRegex(ValueError, 'Invalid tameables binding'):
            module.build(*args)

    def test_nonfinite_marker_rejected(self):
        args = list(fixture())
        args[0]['markers'][0]['location_cm'][0] = float('nan')
        with self.assertRaisesRegex(ValueError, 'Invalid marker coordinates'):
            module.build(*args)

    def test_missing_dependency_rejected(self):
        args = list(fixture())
        args[1]['devices'][-1]['depends_on'] = ['absent']
        with self.assertRaisesRegex(ValueError, 'Unresolved device dependency'):
            module.build(*args)

    def test_real_authored_contracts(self):
        docs = [json.loads(path.read_text()) for path in module.SOURCES.values()]
        result = module.build(*docs)
        self.assertEqual(len(result['rig_devices']), 49)
        self.assertEqual(len(result['launch_tests']), 24)
        self.assertEqual(result['geometry']['module_count'], 18)
        self.assertEqual(result['geometry']['placement_count'], 593)
        self.assertTrue(all(d['editor_object_path'] is None for d in result['rig_devices']))


if __name__ == '__main__':
    unittest.main()
