#!/usr/bin/env python3
"""Author editor-independent placement/binding intent, never a placed UEFN map."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'content/vertical_slice/first_playable_rig.json'


def build() -> dict:
    source = json.loads((ROOT / 'content/vertical_slice/slice_001_encounters.json').read_text())
    boss = next(b for b in source['boss_encounters'] if b['boss_id'] == 'BOS-005')
    devices: list[dict] = []

    def add(device_id, device_type, *, source_path=None, dependencies=(), **fields):
        record = {'id': device_id, 'type': device_type, 'depends_on': list(dependencies), **fields}
        if source_path:
            record['source_path'] = source_path
        devices.append(record)
        return device_id

    bootstrap = {
        'runtime_tick': ('aeonfall_runtime_tick_device', 'verse/core/runtime_tick_device.verse'),
        'player_identity': ('aeonfall_actor_registry_bootstrap_device', 'verse/core/actor_registry_bootstrap_device.verse'),
        'player_profile': ('aeonfall_profile_bootstrap_device', 'verse/persistence/profile_bootstrap_device.verse'),
        'combat_definitions': ('aeonfall_slice_001_combat_bootstrap_device', 'verse/generated/slice_001_combat_bootstrap.verse'),
        'class_definitions': ('aeonfall_slice_001_class_bootstrap_device', 'verse/generated/slice_001_class_bootstrap.verse'),
        'encounter_rewards': ('aeonfall_slice_001_reward_bootstrap_device', 'verse/generated/slice_001_reward_bootstrap.verse'),
    }
    for key, (kind, path) in bootstrap.items():
        add(key, kind, source_path=path)
    for key, kind in (('arena_volume', 'volume_device'), ('encounter_start', 'trigger_device'),
                      ('encounter_fail', 'trigger_device'), ('encounter_complete', 'trigger_device'),
                      ('encounter_failed', 'trigger_device')):
        add(key, kind)
    add('boss_spawner', 'npc_spawner_device',
        editor_requirements=['One boss NPC maximum; no game-start or timer spawn; initially disabled.',
                             'Bind a real Character Definition with supported NPC combat/navigation behavior.'])
    phases = []
    for index, phase in enumerate(boss['phases']):
        prefix = f'bos005_p{index + 1}'
        enter = add(f'{prefix}_enter', 'trigger_device')
        cleanup = add(f'{prefix}_cleanup', 'trigger_device')
        inputs = []
        for kind, ids in (('Objective', phase['objectives']), ('WeakPoint', phase['weak_points'])):
            for number, canonical_id in enumerate(ids):
                native = canonical_id.startswith('OBJ-BOS005-BREAK-STAIR-') or kind == 'WeakPoint'
                device_id = f'{prefix}_{kind.lower()}_{number + 1}'
                if native:
                    add(device_id, 'prop_manipulator_device', editor_requirements=[
                        'Affect exactly one authored destructible prop; manipulator regions must not overlap.',
                        'Recreate destroyed props from the phase EnterOutput graph before a repeated run.',
                        'No resource-node substitution; use the actual DestroyedEvent.'],
                        native_event='DestroyedEvent', affected_prop_count=1)
                    inputs.append({'kind': kind, 'canonical_id': canonical_id,
                                   'source': 'PropDestroyed', 'device_ref': device_id})
                else:
                    add(device_id, 'trigger_device', editor_requirements=[
                        'Unlimited activations, zero transmit delay, never driven by a phase-enter output.',
                        'Requires its authored mechanic producer; optional to the native-health victory path.'])
                    inputs.append({'kind': kind, 'canonical_id': canonical_id,
                                   'source': 'TriggerGraph', 'device_ref': device_id})
        hazards = []
        for number, canonical_id in enumerate(phase['hazards']):
            key = f'{prefix}_hazard_{number + 1}'
            enable = add(f'{key}_enable', 'trigger_device')
            disable = add(f'{key}_disable', 'trigger_device')
            volume = add(f'{key}_damage', 'damage_volume_device',
                         editor_requirements=['Encounter-owned volume; initial state disabled; finite authored damage.'])
            hazards.append({'canonical_id': canonical_id, 'damage_volume_refs': [volume],
                            'enable_ref': enable, 'disable_ref': disable})
        groups = []
        for number, canonical_id in enumerate(phase['spawn_groups']):
            key = add(f'{prefix}_adds_{number + 1}', 'npc_spawner_device',
                      editor_requirements=['Separate from the boss and every ambient/invasion spawner.',
                                           'Initially disabled; finite timer-driven spawn batch; phase cleanup despawns owned adds.'])
            groups.append({'canonical_id': canonical_id, 'spawner_refs': [key], 'maximum_live': boss['candidate_add_cap']})
        phases.append({'phase_id': phase['id'], 'inputs': inputs, 'hazards': hazards,
                       'spawn_groups': groups, 'enter_ref': enter, 'cleanup_ref': cleanup})
    add('bos005_director', 'aeonfall_encounter_director_device',
        source_path='verse/bosses/encounter_director_device.verse',
        dependencies=tuple(bootstrap),
        editable_values={'EncounterId': 'BOS-005', 'BossSpawnTimeoutSeconds': 5.0},
        bindings={'StartInput': 'encounter_start', 'FailInput': 'encounter_fail',
                  'ParticipantVolume': 'arena_volume', 'BossSpawners': ['boss_spawner'],
                  'CompletedOutput': 'encounter_complete', 'FailedOutput': 'encounter_failed', 'Phases': phases})
    return {'schema_version': 1, 'rig_id': 'AEONFALL-FIRST-PLAYABLE-BOS005',
            'state': 'authored_unplaced', 'encounter_id': 'BOS-005',
            'startup_contract': 'Dependencies describe readiness requirements, not guaranteed OnBegin ordering. Reward readiness is checked at start.',
            'native_completion': {'health_source': 'owned_fort_character', 'defeat_source': 'owned_fort_character.EliminatedEvent',
                                  'stair_source': 'three_distinct_prop_manipulator_device.DestroyedEvent'},
            'devices': devices,
            'pending_editor_requirements': ['Create/open an actual Windows UEFN project.',
                                           'Place these devices using their live editor schemas and bind real references.',
                                           'Create Character Definitions, authored destructible props, HUD/telegraph graphs and finite arena failure rule.',
                                           'Bound optional trigger mechanics require real producer graphs; no fake boss-health or defeat inputs.',
                                           'Compile Verse, save the placed map, Launch Session and record native health/three-anchor/elimination acceptance.'],
            'execution_evidence': {'uefn_compile': 'not_run', 'device_placement': 'not_run', 'launch_session': 'not_run'}}


def render() -> str:
    return json.dumps(build(), indent=2) + '\n'


if __name__ == '__main__':
    OUT.write_text(render())
    print(f'Authored rig intent: {OUT.relative_to(ROOT)} (no editor devices placed).')
