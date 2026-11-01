# SLICE-001 Ossuary editor rerun reconciliation

The source assembly entry point is `tools/uefn_editor/build_ossuary_level.py`.
Its `build(apply=False)` path only reads the manifest. The `apply=True`
path must run **inside the real UEFN editor** after the project source
installer has copied the source kit.

## Why reruns need a guard

The initial editor builder skipped an existing actor when its **label**
matched a placement. A creator-modified, incorrectly imported or duplicated
actor could therefore be treated as assembled geometry. This risks blocking
the dungeon route, displacing objectives, and corrupting encounter acceptance
while the script reports a successful rerun.

The editor now calls `preflight_existing_placements` after loading its
AEONFALL-owned map and before placing missing actors. For every manifest-owned
label already in the map it checks:

- Exactly one actor with that label; unrelated creator actors are untouched.
- A static mesh component with the exact expected imported asset path.
- World position within 0.1 cm, rotation within 0.1 degree (modulo full turns),
  and scale within 0.001 of the authored manifest.
- All checks must pass before **any new actor is spawned**. On failure, the
  builder raises an explicit error and does not silently overwrite the actor.

This is intentionally fail-closed. A creator who deliberately moved a module
must manually reconcile it with the manifest, or work in a separate level.
A successful rerun reports both `created_actors` and `reused_actors`.
The script does **not** delete unrelated actors, repair intentional edits,
or certify navigation, collision, UEFN compatibility or runtime gameplay.

## Evidence and handoff

Run `python tools/test_ossuary_editor_preflight.py` in ordinary Python
to execute the 11 mock-object regressions: empty map, exact rerun, unrelated
actor, duplicate labels, nonmesh label collision, wrong mesh, drifted position,
rotation and scale, full-turn equivalence, and duplicate manifest identity.
These are **source-policy tests**, not UEFN editor tests.

For a real editor handoff, preserve the emitted `editor_build_report.json`,
the native UEFN import/validation diagnostics, Verse compiler output, and
Fortnite Launch Session evidence. Verify the 593 placement manifest against
actual level actor counts, inspect arch/stair clearance and collision, then
bind the first playable rig and encounter devices. Do not mark SLICE-001
playable until native editor/session evidence exists.
