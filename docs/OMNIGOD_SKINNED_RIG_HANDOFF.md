# AEONFALL — Actual rigid-skinned Omnigod armature source

**Milestone:** advance the One True Omnigod Sovereign past independent STATIC
GLB plate meshes and animated object-node previews into a genuine
`glTF 2.0` **skinned mesh with named mechanical joints, vertex weights and
inverse-bind matrices**. This is a DCC artifact prepared for the supported
UEFN custom-NPC FBX pipeline, not a native UEFN-imported or player-controllable
actor.

## What is implemented

The original thirteen `SM_AEON_OMNI_*` modules from
`tools/build_omnigod_manifestation_assets.py` are preserved in mesh identity
and shape. The merged Cinematics source from
`tools/build_omnigod_cinematic.py` provides three actual animations with
fourteen transform channels each. The new
`tools/build_omnigod_rigid_skin.py` performs the real rig conversion:

1. Establishes one `AEON_OMNIGOD_MECHANICAL_ROOT` armature and thirteen
   `J_OMNI_*` child joints representing torso, crown, pauldrons, reactor,
   clawed gauntlets, hips, greaves, Axiom Core, eclipse, and siege blade.
2. Provides `JOINTS_0` and `WEIGHTS_0` vertex attributes for **every mesh
   primitive**, rigidly binding every vertex to its original plate's bone.
3. Bakes original mesh-world placement into source vertices, sets skinned
   mesh-node transforms to identity, and computes the inverse of every
   joint's rest translation. This preserves the original exact world
   appearance at bind pose instead of double-transforming the armor.
4. Retargets all three original cinematic animation channels to the
   corresponding mechanical joints rather than independently animated mesh
   nodes. Existing animation keyframe bytes are preserved.
5. Writes `omnigod_mechanical_rigid_skin.glb` and `rig_handoff.json` with
   hashes, unique bone names, actual per-plate vertex counts, and honest
   native-proof limits.

The skin is *genuine*: the glTF contains `skins[].joints`,
`skins[].inverseBindMatrices`, and weighted vertex attributes. That is
materially different from merely labeling a static mesh "rigged."

## Build and numerical validation

Run from repository root on Python 3.12+:

```powershell
python tools/build_omnigod_manifestation_assets.py --output dist/omnigod_manifestation
python tools/validate_omnigod_manifestation_assets.py --output dist/omnigod_manifestation
python tools/build_omnigod_cinematic.py --source dist/omnigod_manifestation/omnigod_dormant_assembly.glb --output dist/omnigod_cinematics
python tools/validate_omnigod_cinematic.py --output dist/omnigod_cinematics
python tools/build_omnigod_rigid_skin.py --source dist/omnigod_cinematics/omnigod_mechanical_motion.glb --output dist/omnigod_skeletal_handoff
python tools/validate_omnigod_rigid_skin.py --source dist/omnigod_cinematics/omnigod_mechanical_motion.glb --output dist/omnigod_skeletal_handoff
python -m unittest discover -s tests -p "test_omnigod_rigid_skin.py" -v
```

The independent validator compares every original vertex with its baked
skinned counterpart and original rest translation. It checks the exact
13-joint-to-module mapping, normalized rigid weights, inverse bind matrices,
animation target remapping, source clip preservation, and output hashes.
Mutation cases intentionally damage skin weights, bind matrices, armature
hierarchy, source pose, animation targets, native-proof fields and authority
claims. All must fail validation.

A passing [dedicated GitHub Actions workflow](../.github/workflows/omnigod-rigid-skin.yml)
uploads the generated rigged GLB and JSON manifest as a **source** artifact.
It is not a compiled Fortnite island, UE skeletal asset or FBX.

## Convert to UEFN-ready skeletal FBX (DCC step, NOT performed by CI)

If you have Blender installed on the machine with the downloaded source:

```powershell
blender --background --python tools/blender_export_omnigod_fbx.py -- --source dist/omnigod_skeletal_handoff/omnigod_mechanical_rigid_skin.glb --output dist/omnigod_skeletal_handoff/omnigod_mechanical_rigid_skin.fbx
```

This optional Blender script is provided as source and is syntax-checked.
It imports the real glTF skin, verifies the 13 intended mechanical bones and
the skinned mesh modifiers, and requests an FBX export with baked actions.

**Blender has not been run in our CI.** Inspect the resulting FBX in your
actual Blender/UEFN environment before treating this as an exported or
importable skeletal rig. The bone hierarchy consists of independent
mechanical plates, not the full humanoid locomotion chain required for a
production Fortnite NPC. Add tested hips, spine, head, legs, arms, hands,
IK/foot contacts, attack/stagger and retargeting locomotion in a DCC. In
particular, the crown, gauntlets and greaves are not weight-painted to
deforming anatomical joints; they are 100% rigid shield-like plates.

## UEFN production acceptance

Epic documentation describes importing FBX skeletal meshes and animations,
creating an Actor Blueprint with a Skeletal Mesh component, configuring a
Custom NPC Character Definition, and assigning an Animation Preset:

- [Import and Play Mesh Animations](https://dev.epicgames.com/documentation/fortnite/import-and-play-mesh-animations-in-unreal-editor-for-fortnite)
- [Animation Presets](https://dev.epicgames.com/documentation/fortnite/animation-presets-in-unreal-editor-for-fortnite)

The actual editor work must independently demonstrate:

- FBX imports as a **Skeletal Mesh** (not silently as 13 Static Meshes).
- All 13 skinned plates are correctly attached, weighted, scaled and
  material-mapped; no 100x meters/centimeters error or flipped X/Y axes.
- A correctly configured NPC Character Definition and NPC Spawner can
  animate the rig. This still requires real locomotion animations and
  a supported skeletal workflow.
- FUS-001 owner-only Armor Fusion continues to operate on the native player
  representation; no player mesh replacement or NPC possession is inferred.
- FUS-002 Titan proxy remains disabled until navigation, command/control,
  camera and collision are proven natively.
- Replaceable NPC Sequencer bindings use Everyone-visible sequence **separate**
  from owner-specific Instigator Only fusion-player sequence.
- Test both clients, a non-owner request, streaming, two complete
  fusion/separation cycles, cancellation, accessibility fallbacks, runtime
  memory, triangle LOD and visual fidelity.

## Security, scope and cost

This source pipeline creates **no classes, abilities, entitlements, weapons
or crafting grants**. It does not write to the profile, `UNI-001`, the
canonical FUS-001/FUS-002 authority, Axiom Heart or Transcendent Zero. No
new catalog entities are counted: all thirteen pieces are components of
one Omnigod.

No Codespaces, Codex, proprietary models, paid APIs, native install,
background local access, or user spend is required by this source generator.
Any native Blender/UEFN export and gameplay validation is a **separate,
explicitly unverified step**.
