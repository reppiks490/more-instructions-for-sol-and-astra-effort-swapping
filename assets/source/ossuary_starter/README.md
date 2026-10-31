# AEONFALL Ossuary starter assets

This is an original geometric blockout for The Ossuary March and The Ossuary
Exchange. It contains **18 reusable meshes, 593 placed objects, and 19,584
placed triangles**. It is ready for editor import and assembly; it does not
contain a UEFN project, saved map, cooked assets, or a verified Fortnite session.

Every shape was authored by the deterministic Python generator in this
repository. No third-party geometry, textures, stock models, or generated
images are used. The visual vocabulary is faceted ledger stone, pointed crypt
arches, octagonal rib supports, copper seams, jade treasury cores and a
seven-rib Black Throne.

## Files

| File | Purpose |
| --- | --- |
| [manifest.json](manifest.json) | Module files, hull recipes, Unreal transforms, checkpoints, objective locations, terrain settings and SHA-256 inventory |
| [preview.html](preview.html) | Self-contained browser viewer; orbit, zoom, open a GLB and inspect the kit |
| [ossuary_exchange_preview.glb](ossuary_exchange_preview.glb) | Complete assembled dungeon preview with shared mesh references |
| [ossuary_module_gallery.glb](ossuary_module_gallery.glb) | All 18 reusable meshes laid out separately |
| [layout_plan.svg](layout_plan.svg) | Labeled room, route, prop and objective plan |
| `meshes/*.glb` | Individual glTF 2.0 meshes, embedded geometry/materials, meter units |
| `meshes/*.obj` and matching `*.mtl` | Individual centimeter-scale geometry with material fallback |
| `landscape/ossuary_march_253.png` | Standard 253 × 253, 16-bit grayscale landscape heightmap |
| `landscape/ossuary_march_253.r16` | Identical unsigned 16-bit elevations, little-endian, without a header |

Open `preview.html` locally, click **Open GLB**, then select the dungeon or
gallery GLB. A browser may block automatic local-file loading; the file picker
avoids that restriction. The viewer uses WebGL and never uploads a file. The
viewer has a JavaScript syntax check, but browser rendering has not been
verified in this restricted environment. The SVG plan can be viewed without
WebGL.

## Import and scale

Source geometry uses X east, Y north, Z up. GLB converts each source point
`(x, y, z)` to glTF `(x, z, -y)`, in meters. OBJ retains source axes and expresses
every vertex in centimeters. Placement locations are Unreal centimeters;
`rotation_deg` is `[pitch, yaw, roll]`. An OBJ imports at scale **1**, and the
GLB importer should perform its normal meter-to-centimeter conversion.

Import the individual meshes and assemble `manifest.json` placements. The
assembled preview GLB is for reviewing composition; individual modules are
the intended level-building units. The repository's editor automation is
documented in [UEFN_STARTER.md](../../../docs/UEFN_STARTER.md).

Before accepting an import, inspect `SM_AEON_Floor_4m`: its upper surface is
400 × 400cm at local Z=0, with its lower face at Z=-30cm. The basis marker has
2m X, Y and Z arms: crimson X, jade Y, limestone Z. The stairs rise toward
local +Y; the throne faces local -Y. Confirm those directions before placing
the scene. Importing OBJ with an unwanted automatic axis conversion must be
corrected in the importer, not hidden by rescaling the placement manifest.

## Collision and navigation

Each module's `collision.hulls` lists independent closed convex components in
both local meters (`vertices_m`) and local centimeters (`vertices_cm`). Hulls
are source recipes; GLB and OBJ files do not claim to embed Unreal collision
assets. The editor assembly workflow must create collision or apply its
documented fallback, then verify the result in UEFN.

Keep the components separate. One convex hull around an arch, open market
stall or throne would fill the empty space. Components may intentionally
touch or overlap; the source meshes are solids suitable for blockout geometry,
not boolean-unioned surfaces. This matters if the pack is later used for
manufacturing, watertight mesh processing or final texture baking.

Floors and ramps should support navigation. Cover, wall and objective props
should be obstacles. The basis marker is calibration geometry and should have
no collision or navigation influence. Static emissive materials do not create
gameplay lighting: add lights and hazard cues in the editor.

The main route and miniboss branch are flat. Portal floor clearance is 5m,
with a 6m central apex. Static validation checks a **4.8m wide × 3m high** route
envelope and samples full floor support every 0.5m along its center and sides.
Those checks cover the authored route through the starter; they do not prove
every possible room traversal or replace companion navmesh/session tests.

## Layout and bindings

The five dungeon acts follow the existing slice specification:

1. Outer Market: 32 × 28m, faction choice, quartermaster and event props.
2. Corpse-economy disruption: 24 × 24m, paired sarcophagus lots.
3. Necromancer construction gauntlet: 20 × 36m, edge cover and branch access.
4. Red Mason miniboss branch: 24 × 24m, connected by an 8m-wide flat passage.
5. Throne approach: 16 × 16m, opening onto the 44 × 44m Black Throne arena.

Four checkpoint markers, the player spawn, BOS-005/BOS-011 controller
locators, two BOS-011 treasury anchors and candidate add-spawn groups are
listed in the manifest. They are device-binding locations, not operational
Verse devices or NPCs. The remaining encounter objectives require editor
actors and gameplay bindings. Stairs, ramps and the causeway bridge are in
the reusable kit; the initial dungeon route uses level slabs.

## Landscape

Use either PNG or r16, resolution **253 × 253**, 63 quads per section, one
section per component and a **4 × 4** component grid. Landscape scale is
`[200, 200, 20]`: samples are 2m apart, covering 504 × 504m.

The intended southwest sample is world `[-25200, -15200, 0]` cm. An editor
that centers the imported grid should place the landscape actor at
`[0, 10000, 0]` cm; an importer that uses a corner origin must place that
corner at the southwest coordinates. Verify sample orientation and bounds
against the floor plan because importer conventions vary.

Elevation is encoded as `height_cm = (sample - 32768) * 20 / 128`. The dungeon
footprint and approach are blended flat at -32cm, just below the slab bottoms.
The surrounding original terrain forms gentle marsh depressions and ridges.
Do not use 8-bit grayscale conversion: it destroys the supplied elevations.

## Regenerate and verify

Run from the repository root; Python's standard library is sufficient:

```sh
python tools/build_ossuary_starter_assets.py
python tools/validate_ossuary_starter_assets.py
python tools/test_ossuary_starter_assets.py
```

The generator is deterministic and has no network dependency. Validation
parses the actual GLB/OBJ files, verifies buffer ranges, indices, normals,
bounds, counts, unit conversions, preview transforms and file hashes, compares
PNG/r16 elevations, checks required markers, and checks route floor support
and collision clearance. Generator validation checks every convex component
for consistent winding, closed edges, positive volume and finite geometry.
Regression tests reject invalid indices, inconsistent winding, missing floors
and an inserted route blocker, and verify deterministic regeneration.

UEFN import, collision creation, navmesh, companion traversal, HLOD, memory
calculation, lighting, audio and Launch Session tests remain editor work. UV0
contains simple planar tiling coordinates; production texture unwraps and
lightmap UV1 are not authored.
