# AEONFALL — Omnigod original VFX texture and telegraph source

**Artifact class:** deterministic original PNG textures and original PCM WAV cues for the One True Omnigod Sovereign. **Not:** a Niagara system, Unreal material, UEFN-imported asset, cinematic sequence, working NPC, owner fusion activation or proven gameplay attack. No new player grants, paid assets, Codex, model calls or editor access are used.

## Reproduce the actual visual/audio assets

From the repository root with Python 3.12 or newer:

```sh
python tools/build_omnigod_vfx_textures.py --output dist/omnigod_vfx_textures
python tools/validate_omnigod_vfx_textures.py --output dist/omnigod_vfx_textures
python -m unittest discover -s tests -p 'test_omnigod_vfx_textures.py' -v
```

The source-only workflow `omnigod-vfx-source.yml` runs the same checks and publishes the generated files as an Actions artifact. `manifest.json` records SHA-256 and byte lengths of **six original 256×256 straight-alpha RGBA PNGs** and **three original 22,050 Hz mono 16-bit PCM WAV cues**. PNG pixels are generated algorithmically with Python's standard library, with valid PNG CRCs; WAV samples are synthesized, not licensed or downloaded. Output is byte-for-byte deterministic for the same source. No generated binary is committed; reproduce or obtain the source-only workflow artifact.

| Actual generated texture | Design purpose | Shape-independent-of-color cue |
| --- | --- | --- |
| `textures/armor_crimson_fissures.png` | Crimson branching armor seams | Interlaced, narrow fissures |
| `textures/reactor_violet_veins.png` | Violet core and energy tendrils | Radial veins and core ring |
| `textures/eclipse_occlusion.png` | Black occulting disc with segmented rim | Disc and 16 half-wave corona segments |
| `textures/telegraph_reaver_chevrons.png` | Reaver strike warning | Three forward chevrons |
| `textures/telegraph_cataclysm_broken_ring.png` | Cataclysm siege AoE warning | Interrupted annular sectors |
| `textures/telegraph_aegis_shield.png` | Aegis guard warning | Outlined shield and inset mark |

Actual WAVs: `audio/reaver_blade_warning.wav` (0.55 s, three short attacks), `audio/cataclysm_siege_warning.wav` (0.90 s, four low pulses), and `audio/aegis_guard_warning.wav` (0.70 s, three high chimes). Audio is intentionally conservative, with no reliance on audio alone for combat signaling. All six PNGs are static; the pipeline creates **no screen flashes, rapid strobes or forced camera shake**. Texture alpha silhouettes remain recognizable in grayscale and muted-audio play.

## Native UEFN assembly plan — actions not yet performed

1. Import each actual PNG into the project as a Texture2D and each WAV as an audio asset. Check alpha orientation, sRGB treatment, mip filtering, UV wrap/clamp, memory compression, and actual import logs. Do not infer Unreal material assets from a PNG. Author tested unlit/emissive material instances for armor fissures and reactor veins; use the eclipse mask for an occulting-disc/corona material, with controlled intensity rather than frame-wide brightness.
2. Attach materials to the **existing original 13-module skinned source** described in `OMNIGOD_SKINNED_RIG_HANDOFF.md`; use the Avatar loop's approved socket/mesh contract, not a second NPC controller. Native FBX conversion, skeletal mesh import, NPC Character Definition, and five-way locomotion remain independent UEFN acceptance gates. Do not promote FUS-002 Titan proxy based on this source.
3. Author **real Niagara** emitters in UEFN for fusion lock, eclipse sweep, shards, and attack telegraph sprites. Use the three telegraph alpha shapes on mesh decals or supported particle renderers; texture availability is not an emitter graph. Treat the following as *design ceilings to test*, not measured performance: near ≤25 m: 2 systems/80 particles; mid 25–60 m: 1/24; far 60–120 m: 0/0; beyond 120 m: culled. Persistent armor seams should be material-only where practical. Disable cosmetic mesh collision, GPU-heavy lights and shadow casting on transient particles; validate actual LOD transitions on Fortnite mobile and desktop.
4. Keep **two different Cinematic Sequence devices**: an Everyone-visible NPC sequence if using replaceable NPC binding, and an Instigator-Only player-camera sequence **without** replaceable NPC binding. Align fusion (4 s) and separation (3 s) against `tools/build_omnigod_cinematic.py` source clip durations; bind the PNGs/WAVs only after native editor review. A source manifest is not a Sequencer track.
5. Use the Architect's existing `aeonfall_fusion_state_runtime` as the sole owner of `Dormant → Activating → Active → Separating → Dormant`. An adapter must check trusted owner authority and generation lease before playing any cue; keep all spawned effects, audio, camera and timers under one lease. **Stop and clean up owned presentation before canonical Abort/CompleteSeparation**, including disconnect, respawn, revoke, repeated input and sequence interruption. Do not authorize damage, consume attack receipts, or mutate the player profile from telegraph playback. Arsenal owns Reaver/Cataclysm/Aegis admission; a rejected or stale attack must not display a valid-hit cue.
6. Offer reduced-intensity mode with material-only silhouettes, zero Niagara transients, no screen flash or shake, HUD/subtitle warnings and visible telegraph shape independent of crimson/violet. Verify muted-audio, color-blind, mobile-touch, low-end, two-client and photosensitivity cases in native Launch Session.

## Evidence and blockers

The validator inspects PNG structure/CRC, exact RGBA palette, distinct alpha silhouettes, audio encoding/duration/peak/discontinuity, SHA-256 inventory, conservative LOD caps, separate Sequencer visibility, creator-only/generation cleanup contracts, and truthful native-evidence fields. Mutation tests deliberately corrupt source bytes and spoof owner/native claims. **Python checks do not compile Verse or execute UEFN.** Native texture/WAV import, material graphs, Niagara emitters, Sequencer bindings, skeletal FBX, device binding, 2-client session, cooked map memory and runtime performance are **not run**. Record editor version, source commit, screenshots/logs, cooked Memory Calculation and Spatial Profiler measurements before declaring production-ready.

**Ownership:** Cinematics owns this source pack; Architect owns authority/generation, Avatar owns character presentation/rig, Arsenal owns attack validation, QA owns independent native acceptance. Related tracking: #37, #84, #89. No shared state-machine, Avatar, Arsenal, persistent-profile or catalog quota files are modified.
