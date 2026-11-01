#!/usr/bin/env python3
"""Source-pinned UNPLACED spatial handoff; does not call UEFN/editor APIs."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    'geometry': ROOT / 'assets/source/ossuary_starter/manifest.json',
    'rig': ROOT / 'content/vertical_slice/first_playable_rig.json',
    'bindings': ROOT / 'content/vertical_slice/slice_001_uefn_bindings.json',
    'launch_tests': ROOT / 'content/vertical_slice/slice_001_launch_tests.json',
}
REQUIRED_MARKERS = (
    'PLAYER-SPAWN', 'CHECKPOINT-1', 'CHECKPOINT-2', 'CHECKPOINT-3', 'CHECKPOINT-4',
    'EC_BOS_005', 'EC_BOS_011', 'EVT-011-MARKET', 'GRAVE-MARKET-QUARTERMASTER',
    'OBJ-BOS011-BREAK-TREASURY-A', 'OBJ-BOS011-BREAK-TREASURY-B',
)
CATEGORIES = {'weapons': 12, 'monsters': 12, 'tameables': 6,
              'hireables': 8, 'encounters': 3, 'vehicles': 3}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def vector3(value):
    return (isinstance(value, list) and len(value) == 3
            and all(type(n) in (int, float) and math.isfinite(n) for n in value))


def build(manifest, rig, bindings, launch, *, hashes=None):
    require(manifest.get('schema_version') == 1, 'Unsupported geometry manifest')
    require(rig.get('state') == 'authored_unplaced' and rig.get('encounter_id') == 'BOS-005',
            'Expected unplaced BOS-005 rig')
    require(bindings.get('slice_id') == launch.get('slice_id') == 'SLICE-001',
            'Inconsistent SLICE-001 contracts')
    markers = manifest.get('markers')
    require(isinstance(markers, list), 'Geometry markers missing')
    ids = [m.get('id') for m in markers if isinstance(m, dict)]
    require(len(ids) == len(markers) and len(set(ids)) == len(ids)
            and all(isinstance(i, str) and i for i in ids), 'Duplicate/malformed marker IDs')
    by_marker = {m['id']: m for m in markers}
    require(set(REQUIRED_MARKERS) <= set(by_marker), 'Required player/encounter/shop marker missing')
    for marker in markers:
        require(vector3(marker.get('location_cm'))
                and type(marker.get('radius_cm')) in (int, float)
                and math.isfinite(marker['radius_cm']) and marker['radius_cm'] > 0,
                f"Invalid marker coordinates/radius: {marker['id']}")
    rooms = manifest.get('rooms')
    require(isinstance(rooms, list) and all(isinstance(r, dict) for r in rooms)
            and len({r.get('id') for r in rooms}) == len(rooms),
            'Missing/duplicate geometry rooms')
    by_room = {r['id']: r for r in rooms}
    for marker_id, room_id in (('EC_BOS_005', 'miniboss_branch'),
                               ('EC_BOS_011', 'black_throne'),
                               ('EVT-011-MARKET', 'outer_market')):
        require(room_id in by_room, f'Missing geometry room: {room_id}')
        marker, room = by_marker[marker_id], by_room[room_id]
        center, size = room.get('center_m'), room.get('size_m')
        require(isinstance(center, list) and len(center) == 2
                and isinstance(size, list) and len(size) == 2
                and all(type(x) in (int, float) and math.isfinite(x) for x in center + size)
                and all(x > 0 for x in size), f'Invalid room footprint: {room_id}')
        x, y = marker['location_cm'][:2]
        require(abs(x / 100 - center[0]) <= size[0] / 2
                and abs(y / 100 - center[1]) <= size[1] / 2,
                f'{marker_id} outside {room_id}')
    paths = manifest.get('walkable_paths')
    require(isinstance(paths, list) and all(isinstance(p, dict) for p in paths),
            'Walkable paths missing')
    by_path = {p['id']: p for p in paths}
    require('main_route' in by_path and 'miniboss_branch' in by_path
            and len(by_path) == len(paths), 'Missing/duplicate required walkable routes')
    for path in paths:
        require(len(path.get('points_cm', [])) >= 2
                and all(vector3(v) for v in path['points_cm'])
                and type(path.get('required_clear_width_cm')) in (int, float)
                and path['required_clear_width_cm'] > 0
                and type(path.get('required_clear_height_cm')) in (int, float)
                and path['required_clear_height_cm'] > 0,
                f"Invalid authored walkable route: {path['id']}")
    route = by_path['main_route']['points_cm']
    require(route[0][1] <= by_marker['PLAYER-SPAWN']['location_cm'][1]
            and route[-1][1] >= by_marker['EC_BOS_011']['location_cm'][1]
            and all(a[1] < b[1] for a, b in zip(route, route[1:])),
            'Main route does not progress from spawn toward throne')
    checkpoint_y = [by_marker[f'CHECKPOINT-{n}']['location_cm'][1] for n in range(1, 5)]
    require(by_marker['PLAYER-SPAWN']['location_cm'][1] < checkpoint_y[0]
            and all(a < b for a, b in zip(checkpoint_y, checkpoint_y[1:]))
            and checkpoint_y[-1] < by_marker['EC_BOS_011']['location_cm'][1],
            'Checkpoints do not progress from spawn to final boss')
    devices = rig.get('devices')
    require(isinstance(devices, list) and devices and all(isinstance(d, dict) for d in devices),
            'No valid rig devices')
    device_ids = [d.get('id') for d in devices]
    require(len(set(device_ids)) == len(device_ids)
            and all(isinstance(x, str) and x for x in device_ids), 'Invalid rig device IDs')
    require(len([d for d in devices if d.get('type') == 'aeonfall_encounter_director_device']) == 1,
            'Expected exactly one encounter director')
    for device in devices:
        require(isinstance(device.get('type'), str) and device['type'],
                f"Missing device type: {device['id']}")
        require(isinstance(device.get('depends_on'), list)
                and all(dep in device_ids and dep != device['id'] for dep in device['depends_on']),
                f"Unresolved device dependency: {device['id']}")
    content = {}
    for category, count in CATEGORIES.items():
        items = bindings.get(category)
        require(isinstance(items, list) and len(items) == count
                and all(isinstance(item, dict) for item in items)
                and len({item.get('id') for item in items}) == count,
                f'Invalid {category} binding coverage')
        content[category] = [
            {'canonical_id': item['id'], 'source_binding': item,
             'editor_asset_path': None, 'native_validation': 'not_run'} for item in items
        ]
    require(bindings.get('world_event', {}).get('id') == 'EVT-011',
            'Grave Market Eclipse binding missing')
    tests = launch.get('tests')
    require(isinstance(tests, list) and tests and all(isinstance(t, dict) for t in tests)
            and len({t.get('id') for t in tests}) == len(tests),
            'Invalid Launch Session test IDs')
    placements = []
    for device in devices:
        name = device['id']
        anchor = 'EC_BOS_005' if (name.startswith('bos005_') or name in (
            'arena_volume', 'boss_spawner', 'encounter_start', 'encounter_fail',
            'encounter_complete', 'encounter_failed')) else 'PLAYER-SPAWN'
        placements.append({
            'device_id': name, 'expected_class': device['type'],
            'design_anchor_id': anchor,
            'design_anchor_location_cm': by_marker[anchor]['location_cm'],
            'design_anchor_radius_cm': by_marker[anchor]['radius_cm'],
            'depends_on': device['depends_on'],
            'placement_instruction': 'manual_editor_layout_and_wiring_required',
            'actual_editor_position_cm': None, 'editor_object_path': None,
            'placement_status': 'unplaced',
        })
    return {
        'schema_version': 1, 'slice_id': 'SLICE-001',
        'state': 'authored_unplaced_not_editor_evidence',
        'source_sha256': hashes or {},
        'geometry': {'module_count': len(manifest.get('modules', [])),
                     'placement_count': len(manifest.get('placements', [])),
                     'walkable_routes': paths, 'markers': [by_marker[k] for k in REQUIRED_MARKERS]},
        'rig_devices': placements, 'content_bindings': content,
        'world_event': {'canonical_id': 'EVT-011', 'design_anchor_id': 'EVT-011-MARKET',
                        'editor_director_path': None, 'state': 'unplaced'},
        'king_without_pulse': {'canonical_id': 'BOS-011', 'design_anchor_id': 'EC_BOS_011',
                               'editor_controller_path': None, 'state': 'unplaced'},
        'shop': {'design_anchor_id': 'GRAVE-MARKET-QUARTERMASTER',
                 'editor_object_path': None, 'state': 'unplaced'},
        'checkpoints': [{'marker_id': f'CHECKPOINT-{n}', 'editor_object_path': None,
                         'respawn_rejoin_validation': 'not_run'} for n in range(1, 5)],
        'launch_tests': [{'id': test['id'], 'status': 'not_run', 'evidence': None} for test in tests],
        'uefn_compile': 'not_run', 'fortnite_launch_session': 'not_run',
        'playable_claim': 'not_established',
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name, default in SOURCES.items():
        parser.add_argument('--' + name.replace('_', '-'), type=Path, default=default)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    paths = {name: getattr(args, name) for name in SOURCES}
    try:
        if args.out.exists():
            raise ValueError('Refusing to overwrite an existing editor handoff or evidence file')
        docs = {key: json.loads(path.read_text(encoding='utf-8')) for key, path in paths.items()}
        hashes = {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in paths.items()}
        result = build(docs['geometry'], docs['rig'], docs['bindings'], docs['launch_tests'],
                       hashes=hashes)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(f"Wrote {len(result['rig_devices'])} unplaced device checklist entries to {args.out}")
        return 0
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.exit(1, f'Spatial handoff failed: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
