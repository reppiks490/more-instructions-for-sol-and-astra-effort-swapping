# AEONFALL — Omnigod cinematic source implementation

**Deliverable:** deterministic animated **glTF 2.0 GLB** and three original, playable mono PCM WAV sound cues, generated from the existing 13-module original machine-demon source assembly. The output is an **independent static-module DCC preview**, not a skinned NPC, native Fortnite animation, imported Niagara effect, Verse runtime binding, actual player transformation or published UEFN island.

## Reproduce the executable source

From repository root, with Python 3.12 and no paid dependencies:

```sh
python tools/build_omnigod_manifestation_assets.py --output dist/omnigod_manifestation
python tools/build_omnigod_cinematic.py --source dist/omnigod_manifestation/omnigod_dormant_assembly.glb --output dist/omnigod_cinematics
python tools/validate_omnigod_cinematic.py --output dist/omnigod_cinematics
python -m unittest discover -s tests -p "test_omnigod_cinematic.py" -v
```

The new workflow `.github/workflows/omnigod-cinematic-source.yml` builds and uploads the source pack. `omnigod_mechanical_motion.glb` contains three named glTF animations with 14 channels each: 13 plate translations and a separate eclipse rotation. They are `AEON_FUS001_Fusion_Preview` (4 s), `AEON_FUS001_Separation_Preview` (3 s) and `AEON_OMNI_DormantBreath_Preview` (6 s). The original source meshes and material geometry are preserved. Fusion opens the armored silhouette, then locks the modules back together. Separation expands modules outward for subsequent despawn; the preview itself does **not** hide, detach or destroy a gameplay actor. Dormant breathing is deliberately subtle.

`audio/eclipse_subpulse.wav`, `audio/iron_plate_lock.wav` and `audio/void_separation.wav` are deterministic, original synthesized 16-kHz mono 16-bit PCM source cues with bounded amplitude. These are actual audio files, not descriptions or claims of imported Fortnite sound assets. `cue_sheet.json` records cue timing, accessible non-color shape language, distance tiers, budget ceilings, authoritative binding requirements and SHA-256 hashes of every generated file. The cue sheet is not interpreted by the existing Verse runtime.

## Native production handoff — UEFN editor actions required

1. **DCC preparation.** Import the 13 original meshes/assembled GLB into a DCC tool and inspect axis orientation, pivots, normal direction, UVs and 100-cm/m conversions. glTF animations are independent rigid node transforms, not skeletal clips. Build and weight an actual skeletal rig for the NPC, then retarget/bake the module motions to bones and export FBX skeletal mesh and animation assets. Preview the root motion, joint penetration and animation blend; do not label the static GLB as an imported playable character.
2. **NPC and Sequencer.** Import and validate the rigged FBX in the real UEFN project. Build a Custom NPC Character Definition and supported Animation Preset, then configure NPC Spawner and native locomotion. Use a dedicated **Everyone-visible** Cinematic Sequence device for a sequence containing **replaceable NPC bindings**. Use a different **Instigator Only** Cinematic Sequence device for the owner-player fusion camera and cues; that sequence must **not** contain a replaceable NPC binding. Never reveal owner-only effects to a second player merely to work around NPC binding visibility.
3. **Niagara.** Author real Niagara emitters in the editor using crimson rim, violet reactor veins, eclipse silhouette, directional shards and lock pulses. The source pack does not create Niagara graphs. Prefer emissive material modulation for persistent seams and event-triggered emitters for transients. Disable mesh collision on cosmetic plates and corona. Use a tested NPC capsule/navmesh, not 13 animated collision hulls.
4. **Verse lifecycle adapter.** Bind native devices only after verifying their actual editor-exposed APIs and a trusted owner Player Reference. Canonical `aeonfall_fusion_state_runtime` owns `Dormant → Activating → Active → Separating → Dormant` and generation tokens. Cinematics must **not** create a competing owner authority or phase service. On successful `BeginActivation`, stage a token-scoped visual request; only the physical controller may confirm `Active` after every required adapter acknowledges real success. If a cue cannot be started, do not fake an acknowledgement. On stale generation, abort, death, disconnect, authority revocation, respawn or shutdown, stop/disable **all** owned VFX/audio/camera/sequence devices, restore the original character and cancel delayed callbacks **before** canonical `Abort` or `CompleteSeparation`. Avoid global `Play()` for owner-only cinematics; use the verified instigator-specific device overload and native visibility configuration. Trigger input is never proof of a hit or damage receipt.
5. **Arsenal telegraphs.** Consume Avatar's proposed `AttackOutput` only after Architect and Arsenal confirm token/cost/damage-receipt contracts. Shape + audio must distinguish Reaver, Cataclysm and Aegis, without using crimson versus violet as the sole differentiator. Telegraphs are client presentation, not damage authorization; disable on stale token, cooldown rejection and target denial.
6. **Capture proof.** Record exact UEFN version and commit, native Verse compile, import logs, actual device property screenshots, one-owner/two-client Launch Session with second-player denial, interrupted fusion at every phase, 20 consecutive start/cancel cycles, rejoin/respawn, asset streaming/HLOD transitions, source-versus-import orientation, and cooked/runtime memory profiles. Until those are captured, all native integration gates remain **not run**.

## Source planning budgets — not measured Fortnite runtime costs

| Distance | Cosmetic plate motion | Eclipse | Simultaneous particles (design cap) | Niagara systems (design cap) |
| --- | --- | --- | ---: | ---: |
| Near, up to 25 m | On | On | 80 | 2 |
| Mid, 25–60 m | Off | On | 24 | 1 |
| Far, 60–120 m | Off | Off | 0 | 0 |
| Beyond 120 m | Culled | Culled | 0 | 0 |

Only **one** owner-fusion sequence may run at a time. Do not overlap repeated requests or stack separate eclipse, aura, shard and smoke systems outside these caps. Niagara particle counts are authored limits to validate in the editor, not GPU measurements. Native effect memory, cooked island memory, frame times and network replication are unmeasured. Provide a low-effects mode with **zero screen flashes**, no forced camera shake, no seizure-inducing strobes and distinct shape/audio cues. Provide subtitles or HUD text for users with audio disabled. Avoid 3D spatial audio cues that are the only indication of danger.

## Coordination and merge boundaries

- **Architect:** canonical generation lease, owner identity and activation receipts; this source pipeline never changes `fusion_state_runtime.verse`.
- **Avatar:** owns NPC rig, controller and physical camera/armor attachment; consume GLB as a reference, not an automatic character import.
- **Arsenal:** attack receipts and validated damage; no combat state is modified by these cues.
- **QA:** independent mutation tests, editor compile, two-client owner spoof, teardown and runtime budget verification.
- **Cinematics:** owns this generator, test, workflow, source cue sheet and this handoff. No other loop's files were modified.

**Hard blockers:** verified owner provisioning, skeletal FBX rig/retargeting, actual NPC Character Definition, native Sequencer/Niagara/audio devices and Verse bindings, two-client Launch Session, platform profiling and memory calculation. FUS-002 Titan proxy remains experimental and disabled. FUS-001 is also native-disabled until acceptance. No unapproved spend or imported asset claims.

Epic references: [Import and Play Mesh Animations](https://dev.epicgames.com/documentation/fortnite/import-and-play-mesh-animations-in-unreal-editor-for-fortnite), [Animation Presets](https://dev.epicgames.com/documentation/fortnite/animation-presets-in-unreal-editor-for-fortnite), [NPC Spawner with Animations](https://dev.epicgames.com/documentation/en-us/fortnite/using-the-npc-spawner-with-animations-in-unreal-editor-for-fortnite).
