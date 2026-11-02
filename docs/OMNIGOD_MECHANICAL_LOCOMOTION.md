# AEONFALL Omnigod — Five keyed mechanical skeletal locomotion source clips

This stage advances the merged [original Omnigod skeletal skin](OMNIGOD_SKINNED_RIG_HANDOFF.md)
by adding five distinct **keyed bone-animation clips** corresponding to
Epic's [Basic Locomotion](https://dev.epicgames.com/documentation/fortnite/animation-presets-in-unreal-editor-for-fortnite)
roles. The output is still an original DCC source GLB, **not** an imported UEFN
Animation Preset or a verified moving NPC.

## Actual source animations

The generator `tools/build_omnigod_mechanical_locomotion.py` reuses the
existing 13-joint rigid plate skin and preserves the three merged Cinematics
clips. It adds five new named skeletal animations:

| Basic Locomotion slot | Actual glTF clip name | Mechanism |
| --- | --- | --- |
| Idle | `AEON_NPC_Idle_Mechanical` | Heart/spinal idle breathing, subtle crown/armor stabilization |
| Move Forward | `AEON_NPC_MoveForward_Mechanical` | Opposed tank-greave advance and counter-swinging gauntlets |
| Move Backward | `AEON_NPC_MoveBackward_Mechanical` | Shorter backward stride with opposite thrust |
| Move Left | `AEON_NPC_MoveLeft_Mechanical` | Lateral steps with hip/crown load compensation |
| Move Right | `AEON_NPC_MoveRight_Mechanical` | Mirrored lateral steps and separate shoulder stabilizers |

Every new clip has 17 monotonic time samples over 1.6 seconds.
Every clip has 13 joint translations, one bounded Axiom Core scale pulse and
one bounded eclipse rotation channel. Original armor-mesh geometry, bind
positions, inverse bind matrices, vertex weights and original three source
cinematics remain unchanged.

The movement is **in place**. It does not force the actor transform, change
root position, move other players, teleport, inflict damage, or grant ownership.
Per-joint displacement is source-limited to at most 0.28 m per component;
Core visual scale is at most 1.07; the eclipse has a small non-flashing
two-degree sway. Every clip returns to the exact original rest pose so
looping does not accumulate world drift. The two legs' forward/back and
left/right translations are demonstrably different, not mere renamed
duplicates.

## Reproduce and verify (no paid dependencies)

From repository root:

```powershell
python tools/build_omnigod_manifestation_assets.py --output dist/omnigod_manifestation
python tools/build_omnigod_cinematic.py --source dist/omnigod_manifestation/omnigod_dormant_assembly.glb --output dist/omnigod_cinematics
python tools/build_omnigod_rigid_skin.py --source dist/omnigod_cinematics/omnigod_mechanical_motion.glb --output dist/omnigod_skeletal_handoff
python tools/validate_omnigod_rigid_skin.py --source dist/omnigod_cinematics/omnigod_mechanical_motion.glb --output dist/omnigod_skeletal_handoff
python tools/build_omnigod_mechanical_locomotion.py --source dist/omnigod_skeletal_handoff/omnigod_mechanical_rigid_skin.glb --output dist/omnigod_npc_locomotion
python tools/validate_omnigod_mechanical_locomotion.py --source dist/omnigod_skeletal_handoff/omnigod_mechanical_rigid_skin.glb --output dist/omnigod_npc_locomotion
python -m unittest discover -s tests -p "test_omnigod_mechanical_locomotion.py" -v
```

This produces:

- `omnigod_mechanical_five_way_locomotion.glb`: the original three cinematic
  bone clips plus the five new keyed in-place motion clips on real skin.
- `locomotion_handoff.json`: exact output/source hashes, clip-role mapping,
  joint bounds, recommended foot-sync cue times, native-proof disclaimers.

The [dedicated source workflow](../.github/workflows/omnigod-skeletal-locomotion.yml)
builds, validates and uploads these files. Source validation numerically
checks all new keyframes, quaternion lengths, leg-direction differences,
rest-pose closure and honest engine-evidence fields. Deliberate negative
mutations must fail. These are **not** native gameplay tests.

## Supported UEFN production handoff

Epic Basic Locomotion requires Idle; Forward, Backward, Left and Right
are additional role inputs. A source GLB with clips is not an editor-created
Animation Preset. The supported project route still requires:

1. In Blender, inspect the real joint rig and generated skin; add a usable
   locomotion hierarchy with hips, spine, feet/ankles, IK anchors and proper
   mechanical linkages. The current detached-plate bones are a DCC blockout.
2. Retarget or bake the five source actions onto that skeleton and export FBX
   using the optional `tools/blender_export_omnigod_fbx.py` helper as a
   starting point. Verify that separate named animations are actually
   exported and the hand/foot pivots do not explode in scale/orientation.
3. Import the FBX skeletal mesh and animations in the actual UEFN editor;
   create Actor Blueprint with Skeletal Mesh, Custom NPC Character Definition,
   and Animation Preset with five mapped slots. Verify if a directional
   navigation blend is supported on the current NPC preset/settings.
4. Launch a Fortnite session, spawn the custom NPC, check collision/navmesh,
   forward/back/strafe behavior, footstep timing, turning, combat reactions,
   multiplayer replication, HLOD, audio, memory and visibility.
5. Keep FUS-001 creator-only player presentation independent from the
   dormant NPC and keep FUS-002 proxy disabled until genuine controlled-NPC
   movement/camera/cleanup evidence exists.

**Do not confuse source animation with a controllable Omnigod NPC.** Native
UEFN imports, FBX export, custom NPC Spawner binding, physics,
movement/animation blending and two-client Launch Session remain
`not_run`. No existing `UNI-001`, FUS-001/FUS-002, Axiom Heart,
Transcendent Zero or player profile authority is modified by this work.
