# AEONFALL Verse

This directory contains the gameplay-runtime source intended for the UEFN project.

## Current State
The repository can author and review Verse, but final correctness requires the actual UEFN project because Epic's generated digests, assets, Character Definitions, Scene Graph prefabs, and editor references are project-specific.

## Rules
1. Prefer small services/components over monolithic devices.
2. Keep persistent data in versioned append-friendly classes.
3. Keep content identity in canonical IDs.
4. Do not hardcode hundreds of entity behaviors into one switch.
5. Separate gameplay authority from VFX presentation.
6. Every async loop needs an exit/cleanup condition.
7. Every spawned or temporary effect needs deterministic cleanup.
8. Compile in UEFN before moving a module from `prototype` to `implemented`.

## First Runtime Modules
- persistence/player_profile.verse
- persistence/profile_bootstrap_device.verse

## Planned Modules
- core/event_bus
- core/content_registry
- combat/status_runtime
- combat/ability_runtime
- progression/level_service
- progression/mastery_service
- crafting/material_ledger
- crafting/recipe_graph
- factions/reputation_service
- npcs/hireable_runtime
- npcs/taming_runtime
- bosses/encounter_brain
- events/world_event_director
- transcendent/zero_candidate_manager
- transcendent/authority_runtime
