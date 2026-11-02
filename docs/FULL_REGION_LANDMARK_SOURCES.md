# AEONFALL ∞ — 13-region original landmark source kit

**Status:** Original code-generated **static architectural source meshes**, not production-finished Fortnite environments. This package covers *every region* in the canonical topology and builds on the earlier 13-region landscape source package, without replacing or downgrading the Ossuary Exchange.

## Delivered 3D models, not just world descriptions

The generator `tools/build_all_region_landmarks.py` creates **39 individually modeled static meshes**:

- One `Sanctum` architectural identity / altar / large monument per region.
- One `ThresholdGate` structural gateway shell per region, with wide ground-level passage. These are visual modules, **not actual teleport/navigation devices**.
- One `EventBeacon` regional event-locator landmark per region. These are *not bound to gameplay or world events*.

Every region gets a dedicated material palette, an authored geometric signature and a real three-mesh assembly GLB. No region is omitted or replaced with the Ossuary building model. There are **130 physical source files** in the generated pack: 39 GLB meshes, 39 OBJ models, 39 MTL material definitions, and 13 assembled GLB previews. All geometry is programmatically original. An additional manifest documents hashes, quantities and terrain placement planning.

| Region | Architectural identity |
|---|---|
| REG-001 — The Ossuary March | Blackwater ossuary bones and necrotic reliquary |
| REG-002 — Black Sun Meridian | Solar discs and eclipse obelisks |
| REG-003 — Crownless Tempest | Lightning-fork towers and storm conductors |
| REG-004 — Leviathan Red Coast | Colossal fossilized sea-monster ribs |
| REG-005 — Worldroot Cathedral | Worldroot branches and canopy ring |
| REG-006 — Court of Broken Hours | Fractured clockwork time wheels |
| REG-007 — Infernal Ledgerlands | Furnace shafts and hellforge chimneys |
| REG-008 — Glass Wyrm Expanse | Crystalline teeth and faceted spires |
| REG-009 — Hollow Astral Synod | Observatory rings and lunar orrery |
| REG-010 — Null Cartography | Dislocated dimensional plates |
| REG-011 — Titan's Last Orchard | Giant fossil spines and grave-garden remains |
| REG-012 — The Axiom Scar | Physically sheared axiom monuments |
| REG-013 — Threshold of Zero | Minimal void monoliths, white threshold, zero corona |

These geometries are **blockouts and reusable landmarks**, not complete settlements or polished environment art. The mesh exporter checks closed original source solids; the independent validator inspects actual glTF triangles and OBJ face counts, not just file existence.

### Source terrain-aware placement

The previous `tools/build_all_region_terrain.py` produces 253×253 16-bit source landscapes for all 13 regions. This landmark generator samples those actual R16-equivalent heights to choose proposed `Sanctum`, `ThresholdGate` and `EventBeacon` locations. For REG-001, it samples the preserved original Ossuary terrain, with a special event-beacon offset designed to avoid the existing throne plan.

Landmarks are placed relative to each region's **local** source coordinates. The manifest records local XY in meters, the sampled ground height, 65 cm source foundation clearance, surrounding terrain relief and a `requires_editor_grading` flag. High-relief sites need real landscape preparation rather than pretending the source mesh automatically conforms to the terrain. The locations are **planning proposals**, not verified safe multiplayer/navigation/collision placements.

- Local source axes: X east, Y north, Z up, in **meters**.
- OBJ vertices: **centimeters**, with no second 100× scale to apply.
- GLB: glTF Y-up **meters**, using the verified Ossuary geometry exporter.
- Location/placement manifest: **Unreal centimeters**, source-local, with neutral rotations/unit scale.
- Visual emissive material parameters: source preview only, not a Niagara emitter, dynamic light or editor-authored shader.
- Portal aperture: visually open; the validator does not claim actual native NavMesh or UEFN travel functionality.

### Generate and inspect the real source assets

From the repository root, Python 3.12 or newer:

```bash
python tools/build_all_region_landmarks.py --output dist/full_universe_region_landmarks
python tools/validate_all_region_landmarks.py --output dist/full_universe_region_landmarks
python -m unittest discover -s tests -p 'test_all_region_landmarks.py' -v
```

The [All 13 Region Landmark Geometry workflow](../.github/workflows/full-universe-landmarks.yml) builds and independently validates the output before uploading a downloadable source package. Generated GLB/OBJ/MTL files are deterministic and regenerable from the committed code. The workflow's downloadable ZIP expires after GitHub artifact retention; **the committed source generator is durable**.

The independent validator checks the actual material palette for each region, the three per-region mesh roles, 39 unique GLB meshes, all binary triangles/normals, per-file hashes, the thirteen full source assembly GLBs, 130-file completeness, canonical adjacency, terrain position consistency, material/source provenance, and negative mutation tests for edited IDs, false UEFN claims, deleted meshes or corrupted geometry.

**Neither this model generator nor the prior terrain generator can make a UEFN island ready to play.**

## Full-universe source completion

This source pack advances the `landmarks` category for every region; the other eight categories in `content/implementation/universe_first_policy.json` remain necessary: terrain, encounters, ecology, quests, navigation, streaming, VFX/audio and mobile LOD. It does not approve any `region_packs` registry entry because all required categories and independent human source review have not yet been completed. The master [universe-first completion plan](UNIVERSE_FIRST_COMPLETION.md) remains the authority for scope.

The creator chose to **finish the whole planned universe source before first playable prototyping**. Native UEFN import, actual World Partition, editor collision/nav, quest devices, real landscape sculpt alignment, combat/spawning, platform performance, cooked memory and Fortnite mobile Launch Session remain separate later gates. Source validation passing is meaningful but **is not evidence of native UEFN execution**.

Other AEONFALL Fusion hourly loops and their zero-Codex restriction are untouched. No new spend, owner entitlement, public island publication, branch deletion or force push is involved.
