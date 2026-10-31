#!/usr/bin/env python3
"""Check authored bindings, role isolation and readiness dependencies; no UEFN execution."""
from __future__ import annotations

import json
import re
from pathlib import Path

from build_first_playable_rig import OUT, ROOT, render


def validate_rig(rig: dict, *, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    if rig.get('schema_version') != 1 or rig.get('state') != 'authored_unplaced':
        errors.append('rig schema/state must describe authored, unplaced intent')
    if rig.get('encounter_id') != 'BOS-005':
        errors.append('first playable rig must bind BOS-005')
    if rig.get('execution_evidence') != {'uefn_compile': 'not_run', 'device_placement': 'not_run', 'launch_session': 'not_run'}:
        errors.append('unplaced rig cannot claim editor execution evidence')
    records = rig.get('devices', [])
    if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
        return errors + ['devices must be a list of records']
    ids = [item.get('id') for item in records]
    if any(not isinstance(key, str) or not key for key in ids) or len(ids) != len(set(ids)):
        return errors + ['device IDs must be unique nonempty strings']
    by_id = {item['id']: item for item in records}
    resolved_paths = [item['resolved_editor_object_path'] for item in records if item.get('resolved_editor_object_path')]
    if len(resolved_paths) != len(set(resolved_paths)):
        errors.append('different device IDs alias the same physical editor object')
    graph = {}
    for item in records:
        key = item['id']
        dependencies = item.get('depends_on', [])
        if not isinstance(dependencies, list) or any(not isinstance(dep, str) for dep in dependencies):
            errors.append(f'{key}: dependencies must be string references')
            dependencies = []
        if len(dependencies) != len(set(dependencies)):
            errors.append(f'{key}: duplicate readiness dependency')
        for dep in dependencies:
            if dep not in by_id:
                errors.append(f'{key}: unresolved dependency {dep}')
        graph[key] = dependencies
        path = item.get('source_path')
        if path:
            source = (root / path).resolve()
            if not source.is_relative_to(root.resolve()) or not source.is_file():
                errors.append(f'{key}: invalid source path')
            elif not re.search(rf'\b{re.escape(item.get("type", ""))}\s*:=\s*class\(creative_device\)', source.read_text()):
                errors.append(f'{key}: device class absent from source')
    visiting, visited = set(), set()

    def visit(key):
        if key in visiting:
            errors.append('readiness dependency cycle')
            return
        if key in visited:
            return
        visiting.add(key)
        for dep in graph.get(key, []):
            if dep in graph:
                visit(dep)
        visiting.remove(key)
        visited.add(key)
    for key in graph:
        visit(key)

    directors = [item for item in records if item.get('type') == 'aeonfall_encounter_director_device']
    if len(directors) != 1:
        return errors + ['rig requires exactly one canonical encounter director']
    director = directors[0]
    required_dependencies = {'runtime_tick', 'player_identity', 'player_profile', 'combat_definitions', 'class_definitions', 'encounter_rewards'}
    if not required_dependencies <= set(director.get('depends_on', [])):
        errors.append('director is missing a required runtime readiness dependency')
    if director.get('editable_values', {}).get('EncounterId') != 'BOS-005':
        errors.append('director editable encounter ID mismatch')
    bindings = director.get('bindings', {})
    claimed = {}

    def claim(ref, kind, role):
        if not isinstance(ref, str) or ref not in by_id:
            errors.append(f'{role}: unresolved physical reference {ref!r}')
            return
        if by_id[ref].get('type') != kind:
            errors.append(f'{role}: expected {kind}')
        if ref in claimed:
            errors.append(f'{role}: device also owns {claimed[ref]}')
        claimed[ref] = role
    for field, kind in (('StartInput', 'trigger_device'), ('FailInput', 'trigger_device'),
                        ('ParticipantVolume', 'volume_device'), ('CompletedOutput', 'trigger_device'), ('FailedOutput', 'trigger_device')):
        claim(bindings.get(field), kind, field)
    bosses = bindings.get('BossSpawners', [])
    if len(bosses) != 1:
        errors.append('rig requires exactly one boss spawner')
    for ref in bosses:
        claim(ref, 'npc_spawner_device', 'boss')
    source = json.loads((root / 'content/vertical_slice/slice_001_encounters.json').read_text())
    canonical = next(b for b in source['boss_encounters'] if b['boss_id'] == 'BOS-005')
    phases = bindings.get('Phases', [])
    if [phase.get('phase_id') for phase in phases] != [phase['id'] for phase in canonical['phases']]:
        return errors + ['phase IDs/order mismatch canonical BOS-005']
    for phase, authored in zip(phases, canonical['phases'], strict=True):
        label = phase['phase_id']
        claim(phase.get('enter_ref'), 'trigger_device', f'{label}/enter')
        claim(phase.get('cleanup_ref'), 'trigger_device', f'{label}/cleanup')
        inputs = phase.get('inputs', [])
        actual = [(item.get('kind'), item.get('canonical_id')) for item in inputs]
        expected = [('Objective', key) for key in authored['objectives']] + [('WeakPoint', key) for key in authored['weak_points']]
        if len(actual) != len(set(actual)) or set(actual) != set(expected):
            errors.append(f'{label}: canonical objective/weak-point inputs mismatch')
        for item in inputs:
            key = item.get('canonical_id')
            mode = item.get('source')
            ref = item.get('device_ref')
            if mode == 'PropDestroyed':
                claim(ref, 'prop_manipulator_device', f'{label}/{key}')
                record = by_id.get(ref, {})
                if record.get('native_event') != 'DestroyedEvent' or record.get('affected_prop_count') != 1:
                    errors.append(f'{label}/{key}: native objective requires exactly one destructible prop')
            elif mode == 'TriggerGraph':
                claim(ref, 'trigger_device', f'{label}/{key}')
            else:
                errors.append(f'{label}/{key}: unsupported input source')
            if isinstance(key, str) and key.startswith('OBJ-BOS005-BREAK-STAIR-') and mode != 'PropDestroyed':
                errors.append(f'{label}/{key}: stair must be credited by native destruction')
        hazards = phase.get('hazards', [])
        if [item.get('canonical_id') for item in hazards] != authored['hazards']:
            errors.append(f'{label}: canonical hazard mismatch')
        for hazard in hazards:
            name = hazard.get('canonical_id')
            claim(hazard.get('enable_ref'), 'trigger_device', f'{label}/{name}/enable')
            claim(hazard.get('disable_ref'), 'trigger_device', f'{label}/{name}/disable')
            for ref in hazard.get('damage_volume_refs', []):
                claim(ref, 'damage_volume_device', f'{label}/{name}/damage')
        groups = phase.get('spawn_groups', [])
        if [item.get('canonical_id') for item in groups] != authored['spawn_groups']:
            errors.append(f'{label}: canonical spawn group mismatch')
        live_cap = 0
        for group in groups:
            count = group.get('maximum_live', 0)
            if type(count) is not int or count < 1:
                errors.append(f'{label}: spawn cap must be positive integer')
            else:
                live_cap += count
            refs = group.get('spawner_refs', [])
            if not refs:
                errors.append(f'{label}: spawn group needs a physical spawner')
            for ref in refs:
                claim(ref, 'npc_spawner_device', f'{label}/{group.get("canonical_id")}/adds')
        if live_cap > canonical['candidate_add_cap']:
            errors.append(f'{label}: aggregate adds exceed authored live cap')
    if rig.get('native_completion') != {'health_source': 'owned_fort_character', 'defeat_source': 'owned_fort_character.EliminatedEvent',
                                       'stair_source': 'three_distinct_prop_manipulator_device.DestroyedEvent'}:
        errors.append('boss health/elimination cannot be substituted by manual triggers')
    return errors


def main() -> int:
    errors = validate_rig(json.loads(OUT.read_text()))
    if OUT.read_text() != render():
        errors.append('rig manifest drift; run tools/build_first_playable_rig.py')
    if errors:
        print('First playable rig validation FAILED\n' + '\n'.join(f'- {error}' for error in errors))
        return 1
    print('First playable rig source validation PASSED; placement, Verse compilation and session acceptance remain not_run.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
