# AEONFALL — One True Omnigod Sovereign telegraph animation source

**Artifact class:** three original 16-frame 4×4 PNG RGBA8 sprite sheets derived from validated, original Reaver, Cataclysm and Aegis shape textures. They are *genuine animated visual source frames*, not imported UEFN Texture2D assets, material graphs, Niagara emitters, Sequencer tracks, physical damage, native Verse code or a playable NPC. This is a **universe-first** content integration; the source cannot enable FUS-001 or FUS-002. No Codex, proprietary assets, GPU or paid services.

## Reproducible pipeline

Run in a checked-out repository with Python 3.12, no third-party dependencies:

```sh
python tools/build_omnigod_vfx_textures.py --output dist/omnigod_vfx_textures
python tools/validate_omnigod_vfx_textures.py --output dist/omnigod_vfx_textures
python tools/build_omnigod_vfx_flipbooks.py --source dist/omnigod_vfx_textures --output dist/omnigod_vfx_flipbooks
python tools/validate_omnigod_vfx_flipbooks.py --source dist/omnigod_vfx_textures --output dist/omnigod_vfx_flipbooks
python -m unittest discover -s tests -p 'test_omnigod_vfx_flipbooks.py' -v
```

The dedicated **AEONFALL Omnigod Telegraph Motion Source** GitHub Actions workflow generates and verifies an exact source package with three `atlases/*_reveal_4x4.png` files and `flipbook_manifest.json`. Each PNG contains 16 individually rendered RGBA8 frames in four columns and four rows, each tile 128×128 px, giving a 512×512 px image. All frame alpha changes are nondecreasing, so the reveal does not contain intensity flashes or reversals. The first frame is transparent, the last frame matches the downsampled approved source silhouette, and intermediate masks preserve the original non-color silhouettes.

The source audio and effect timings match the generated attack warnings:

| Telegraph | Reveal shape | Single-shot duration | Frames |
| --- | --- | ---: | ---: |
| Reaver | Three directional chevrons, top-to-bottom reveal | 550 ms | 16 |
| Cataclysm | Broken AoE sectors, center-outward wave | 900 ms | 16 |
| Aegis | Shield silhouette, center-to-edge reveal | 700 ms | 16 |

The machine-readable `frame_times_ms` are explicit, starting at zero and ending at the WAV duration. The frame order is row-major 0–15; **never loop** the animation or reverse it on a cancel. On cancellation or owner-generation invalidation, remove all its visual/audio presentation instead. Each atlas occupies 512×512×4 = 1,048,576 bytes before texture compression or mipmaps; three would occupy 3,145,728 raw bytes. Those are **source byte-size arithmetic**, not UEFN GPU/resident memory measurements. Runtime platform formats and streaming must be profiled in the real editor.

## Native UEFN authoring handoff — pending

1. Inspect UEFN's current available Texture2D importer and supported Niagara sprite SubUV/flipbook material workflow on the installed UEFN release. Import the original PNGs and newly generated atlases, check alpha, gamma/sRGB, mipmaps, frame slicing and compression on desktop and mobile. Do not imply that a PNG or manifest is a material or Niagara system.
2. Create a **separate owner-visible presentation** for each admitted attack shape, using the atlas 4×4 grid and manifest frame timing; set non-looping playback and automatic stop. Use the approved HUD message/subtitle fallbacks for muted audio and restricted effects. A visible telegraph requires shape or text cues even when red/violet colors cannot be distinguished.
3. Keep persistent crimson armor fissures and violet core veins primarily in emissive materials on the Avatar-owned 13-joint model; use the eclipse occlusion geometry and short pulse cues from the existing Cinematics pack. Add no duplicate authority or independent player/proxy state machine.
4. Respect the source-design hard caps **per active owner presentation budget**, not separately for every particle emitter: near (≤25m): ≤2 concurrent Niagara systems and ≤80 simultaneous particles; mid (25–60m): ≤1 system and ≤24 particles; far (60–120m): zero; beyond 120m: culled. Avoid heavy per-particle collision, shadows, repeated light updates and frame-wide flashes. **Not measured**: actual mobile frame time, GPU cost, cooked map memory, network replication or HLOD behavior.
5. Bind owner-camera/audio cues to the **Instigator Only** sequence with **no replaceable NPC binding**. NPC visuals with replaceable bindings, if present, must run in a separate **Everyone** sequence. Use only Editor-supported device APIs verified against the actual project.
6. Check the canonical Architect FUS-001 owner, generation and phase before *every* presentation start and delayed callback. Arsenal alone owns authoritative attack admission, receipt/cost validation and physical damage. **A rendered warning is never a valid-hit receipt** and must not be displayed as evidence an attack succeeded. Cancel and dispose owned timers, Niagara instances, camera/audio, HUD and sprites before canonical Abort or CompleteSeparation. Reject duplicate starts, stale generations, owner revocation, disconnect, respawn and wrong-player triggers.
7. Capture actual editor-version/source-SHA evidence: texture import logs; native Verse compilation; a two-client owner/observer visibility and cancellation matrix; audio-disabled and color-vision-safe cases; performance on target mobile hardware; cooked Memory Calculation and Spatial Profiler results. Until verified, FUS-001 and FUS-002 remain native-disabled.

## Integrity and ownership

The independent validator checks actual PNG chunk structure, CRC and zlib integrity, strict pixels and source palette, 48 individual frame masks, monotonic alpha, real WAV durations, exact frame timing and order, SHA-256 for all original and generated files, truthful native-disabled fields, cleanup and owner-only rules, and LOD design caps. Mutation tests include a *rehash-consistent deliberately flashing frame*: rehashing cannot conceal a nonmonotonic alpha regression.

**Cross-loop ownership:** Cinematics controls these source/CI/docs files; Architect controls canonical generation and owner identity; Avatar supplies skeletal/rigged NPC import and presentation device wiring; Arsenal provides true server-authorized Reaver/Cataclysm/Aegis attack admissions; QA runs native two-client and performance acceptance. Coordinate through [Fusion Architect issue #37](https://github.com/reppiks490/more-instructions-for-sol-and-astra-effort-swapping/issues/37). Native bindings have **not** been performed. Do not open a PR while repository PR events can automatically request Codex reviews: the user has prohibited all Codex token consumption by scheduled agents.
