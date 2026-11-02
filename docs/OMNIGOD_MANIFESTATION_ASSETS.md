# AEONFALL — One True Omnigod Sovereign: original 3D manifestation source

**Scope:** original *static* prototype geometry for a colossal crimson-violet machine-demon. The new source kit contains 13 independent mesh components, a blood-red Axiom Core, enormous armored pauldron sets, diabolical horned crown, 16-section eclipse corona, oversized gauntlet claws and an ornamental siege greatsword. This is original programmatic geometry, **not** an imported rig, playable outfit, complete NPC, transformed player, or finished cinematic.

## What is real

`tools/build_omnigod_manifestation_assets.py` produces actual geometry in the following formats:

- 13 independent `SM_AEON_OMNI_*.glb` files, using glTF 2.0 embedded geometry and material parameters in meters.
- 13 independent `SM_AEON_OMNI_*.obj` files with matching MTL fallback materials, in Unreal centimeters.
- `omnigod_dormant_assembly.glb`, a full assembled still composition for external review.
- `manifest.json`, original-source provenance, per-part sizes/triangle counts, intended skeletal socket roles, Unreal-centimeter assembly locations, material presets, SHA-256 inventory and explicit test limitations.

The generator reuses the existing Ossuary source-geometry encoder and watertight closed-solid checks. No stock or licensed third-party mesh is downloaded. The pack is strictly separate from the canonical content quotas and creator account entitlement. Its 13 pieces are **components of one character design**, not 13 new catalog creatures or classes.

## Generate and obtain the assets

At repository root:

```powershell
python tools/build_omnigod_manifestation_assets.py --output dist/omnigod_manifestation
python tools/validate_omnigod_manifestation_assets.py --output dist/omnigod_manifestation
python -m unittest discover -s tests -p "test_omnigod_manifestation_assets.py" -v
```

The dedicated [AEONFALL Omnigod Source Geometry workflow](../.github/workflows/omnigod-manifestation.yml) runs these checks and uploads a downloadable source-artifact ZIP on successful source validation. Download the `AEONFALL-Omnigod-static-source-<commit>` artifact from GitHub Actions for your source import. An Actions artifact is not a compiled UEFN package.

## Asset pivots and scale

All source geometry uses local `X east / Y north / Z up` coordinates in **meters**. OBJ vertices are multiplied by 100 so they import in **centimeters**. GLB uses glTF Y-up meters; the encoder maps source `(x,y,z)` to `(x,z,-y)`. The manifest's 13 placements are in Unreal centimeters; all are explicit neutral rotations and unit scale. Parts have local pivots and suggested **planning** socket names (chest_core, head, shoulder_l/r, spine, hand_l/r, pelvis, foot_l/r, back_vfx, weapon_r). They are *not* existing bones or Unreal asset paths.

Before doing any editor placement, verify the imported Torso dimensions, Crown orientation, eclipse behind the body (+Y), and sword offset. Do not silently compensate for axis/scale mismatch with arbitrary on-import transforms. The material palette defines Obsidian, Black Iron, Blood Crimson, Axiom Violet, Solar Rift, Bone Chrome, Void Veins and Ancient Gold. Their emissive values are preview colors; they do not produce a native Niagara effect, gameplay lighting, audio or accessibility cue.

### Polygon and collision discipline

The source kit is capped at 16 modules and 9,000 total original triangles. Source tests validate individual glTF triangles, index bounds, nondegenerate faces, coordinates, asset hashes and the assembled 13-part scene. These are **source** validation budgets, not UEFN device memory, runtime VFX, or Fortnite triangle/LOD approvals. For decorative NPC parts, disable static collision; use an appropriately tested character capsule, navigation and encounter bounds rather than a giant composite collision hull. The corona's central hole must remain visually open and nonblocking.

## Animated source preview: FUS-001 mechanical fusion

The separate deterministic `tools/build_omnigod_fusion_animation.py` takes
the existing 13-part assembly and adds a real glTF 2.0 node animation named
`Omnigod_Armor_Fusion_Beats`. It produces two additional source files:

- `omnigod_mechanical_fusion_preview.glb`: eight-second animated GLB containing
  source component movement, pauldron/gauntlet separation, reactor translation,
  forward Axiom Core pulse, eclipse expansion and a complete eclipse revolution.
  Components return to their original static rest transforms at the end.
- `omnigod_mechanical_fusion_timeline.json`: seven named beats with matching
  timestamps and **authored VFX/audio descriptions** for future production.
  This JSON is not an audio asset, particle system or Fortnite cutscene.

The source geometry remains unchanged. Animation targets are bounded and
nonnegative, with a single channel for each node/path, finite keyframes,
rest-pose closure and a verified checksum. The `tools/validate_omnigod_fusion_animation.py`
inspects actual glTF animation bytes, channel names, time arrays, sample vectors,
quaternions, source geometry topology and native-proof claims. Tampered channel
targets, inflated scale, fabricated UEFN results and checksum corruption fail.

Run after generating the static pack:

```powershell
python tools/build_omnigod_fusion_animation.py --output dist/omnigod_manifestation
python tools/validate_omnigod_fusion_animation.py --output dist/omnigod_manifestation
python -m unittest discover -s tests -p "test_omnigod_fusion_animation.py" -v
```

A successful dedicated Actions run includes these animated source files in
the same downloadable import-geometry artifact.

**Rigging boundary:** The glTF preview animates **mesh nodes**, not skin
weights or a bone-driven Character Definition. Bring this clip into a DCC,
attach individual plates to real skeleton bones, and export actual skeletal
FBX plus animations for the supported UEFN NPC workflow. Do not interpret
the working animated GLB as native playable armor fusion, NPC possession,
Niagara effects, or finished soundtrack. The owner-only player fusion
cinematic must remain separate from an Everyone-visible replaceable NPC
Sequencer binding.

## Native UEFN production path

The supported workflow is to promote this static original blockout into a **DCC-rigged** skeletal character with real animations, then import FBX into UEFN:

1. In Blender, Maya or another DCC, import the individual modules. Verify scale, UVs, normals and relative pivots. Rig a coherent skeleton, skin or parent plates to bones, design the mechanical plate separation motion and animate five-direction locomotion plus idle, attack, stagger, fusion and breakup. Export a tested character skeletal FBX and corresponding animation FBX. Do not assume static OBJ/GLB files automatically become controllable NPC skeletal meshes.
2. In the actual UEFN project, import the FBX skeletal mesh and animations; create an Actor Blueprint with a Skeletal Mesh component. Create a **Custom** NPC Character Definition with custom cosmetic and a supported Animation Preset; connect to an NPC Spawner device. Retarget and measure navmesh/capsule/collision in Launch Session. Epic references: [Import and Play Mesh Animations](https://dev.epicgames.com/documentation/fortnite/import-and-play-mesh-animations-in-unreal-editor-for-fortnite), [Animation Presets](https://dev.epicgames.com/documentation/fortnite/animation-presets-in-unreal-editor-for-fortnite).
3. Keep the bound Sovereign NPC independent of the real owner-player character. FUS-001 uses the already authored owner-gated camera/visual adapter and native player character. FUS-002 NPC Titan proxy is experimental, **not** automatic NPC possession. No custom skeletal rig, importer binding or controller has been verified yet.
4. **Sequencer visibility constraint:** If a level sequence uses a *replaceable NPC binding*, Epic requires its Cinematic Sequence device visibility to be **Everyone**. The currently authored **instigator-only** fusion-player cinematic must **not** include a replaceable NPC binding. Use two different sequences, or use a supported non-replaceable approach verified in the editor. Epic: [NPC Spawner with Animations](https://dev.epicgames.com/documentation/en-us/fortnite/using-the-npc-spawner-with-animations-in-unreal-editor-for-fortnite).
5. Bind authored crimson and violet Niagara VFX, lighting and a layered audio signature to the rig's actual sockets. Provide reduced-intensity effects and non-color cues for photosensitivity and colorblind accessibility. Capture real editor FPS/memory and multiplayer replication evidence before enabling the experience.
6. Creator-only ownership remains the existing trusted disabled-by-default authority device. Geometry or proximity to a mesh is never proof of creator eligibility. Do not grant any player `FUS-001`, `FUS-002`, or `UNI-001` based on asset presence.

## Honest acceptance criteria

- `python tools/validate_omnigod_manifestation_assets.py` returns success for the generated pack; tests detect corrupt/missing meshes and unverified native claims.
- UEFN actually imports all relevant static meshes with correct origin/scale; a skeletal FBX and animation sequence is independently built and compiled in the editor.
- The NPC spawns as an authentic Character Definition with correct hitboxes and actual basic locomotion. This is not demonstrated by this source pack.
- Two Fortnite clients observe the same NPC and owner-only fusion cinematic, with no duplicate attachment, leaked camera or cross-player effect.
- Profiling captures full crimson/violet VFX stack, camera, NPC model and a realistic late-join/respawn cycle.

This kit is the geometry handoff for the **Omnigod Avatar and Fusion Cinematics** loops. Its source validation is real; its engine import, physical rigging, advanced behavior, actual owner fusion and public release remain unverified.
