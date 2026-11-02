# AEONFALL — ALL 13 original region landscape source sets

**Delivery:** full-universe terrain-source generation for **every canonical**
region in `content/world/world_topology.json`, rather than only building the
Ossuary starter. This is an original `R16 + PNG16` source output for each
region. **It does not mean the region contains its buildings, NPCs, encounters,
quests, runtime NavMesh or actual World Partition map.** The creator
prioritizes full-universe source production before a playable prototype.

## Real authored terrain source

`tools/build_all_region_terrain.py` produces exactly 13 complete 253×253
sample landscapes (one existing source reused, twelve new terrain profiles):

| ID | Region | Source landscape character |
|---|---|---|
| REG-001 | The Ossuary March | Original Ossuary Marsh terrain reused byte-for-byte |
| REG-002 | Black Sun Meridian | Solar dunes and eclipse depression |
| REG-003 | Crownless Tempest | Sawtooth mountains and a storm pass |
| REG-004 | Leviathan Red Coast | Coastal shelf, shallow/deep channels |
| REG-005 | Worldroot Cathedral | Root-lattice hills around forest court |
| REG-006 | Court of Broken Hours | Concentric repeat-city terraces |
| REG-007 | Infernal Ledgerlands | Basalt mesas, fissures and fort flats |
| REG-008 | Glass Wyrm Expanse | Crystal spines and migration trench |
| REG-009 | Hollow Astral Synod | Observatory crater and impact rim |
| REG-010 | Null Cartography | Fractured checkerfields and void seam |
| REG-011 | Titan's Last Orchard | Colossus burial mounds and grooves |
| REG-012 | The Axiom Scar | Large fracture valley and offset faults |
| REG-013 | Threshold of Zero | Quiet symmetric ascension terraces |

The entire original Ossuary `r16` and grayscale `PNG` are copied from
`assets/source/ossuary_starter/landscape/` without replacement, preserving
previous source work. The other twelve landscapes are deterministic,
independent mathematical terrain profiles with distinct sample hashes.

Each landscape includes all **64,009** sixteen-bit integer elevation values.
The bundle contains **832,117** actual source height samples total, not a
small example or random screenshot. Each pair includes exact headerless
16-bit little-endian R16 and corresponding 16-bit grayscale PNG values.

The generated `manifest.json` enumerates all thirteen regional IDs, names,
themes, canonical neighbors, region-specific terrain motifs, SHA-256 file
inventory, height bounds, XY scale, vertical scaling, safe planning-only
region offsets and explicit UEFN proof limitations.

## Generate and validate all 13 now

At the cloned repository root:

```powershell
python tools/build_all_region_terrain.py --output dist/full_universe_13_region_terrain
python tools/validate_all_region_terrain.py --output dist/full_universe_13_region_terrain
python -m unittest discover -s tests -p "test_all_region_terrain.py" -v
```

The dedicated [13 Region Terrain Sources workflow](../.github/workflows/full-universe-terrain.yml)
produces a downloadable GitHub Actions artifact with the manifest and all
26 source heightmaps. The validator processes every pixel in every pair,
checks CRCs and full PNG/R16 equality, proves region-hash uniqueness,
catches removed files, and verifies the original Ossuary remains unchanged.
It also rejects false editor/mobile/playtest status.

This standalone source pipeline uses Python's standard library. It does not
use Codex, paid generators, external assets, or custom private APIs.

## Source coordinates and actual UEFN import

The 253×253 resolution supports 4×4 Unreal Landscape components with 63
quads per section. The recommended source scales are X=200cm, Y=200cm,
Z=20cm, and sample height is `(sample - 32768) * 20 / 128` centimeters.
Each local region footprint covers 504m × 504m.

The manifest's region placement offsets form a **planning grid only** to
avoid overlap while reviewing. They do NOT claim World Partition Streaming
Sources or physically traversable canonical region connectors. Canonical
neighbor links may need supported portals/travel transitions, separate
World Partition cells or a carefully authored island topology. In
particular, portal/neighbor entries are not proof that a player can travel.

When UEFN becomes available again:

1. Import the landscapes into the **actual** UEFN project and confirm
   elevation direction, scaling, height clamping, component count and
   named region ownership without overwriting the earlier Ossuary layout.
2. Author and bind full region architecture, roads, roads and traversal,
   cities, ecologies, 840-entity spawn/availability relationships, quests,
   world event sites, boss spaces, materials, lore, lighting, audio and VFX.
3. Implement regional streaming/HLOD and dynamically capped NPC/VFX
   concurrency; design actual traversal and navigation beyond the heightmap.
4. Capture real **cooked** memory against Epic's current 300 MiB publishing
   budget and runtime performance on the intended Fortnite mobile platform.
5. Verify region-specific gameplay, unique creatures, quests, travel,
   low-end presentation, accessibility and multiplayer state transitions.

These are later native acceptance requirements, not steps performed by the
heightmap generator. Epic [Memory Management in UEFN](https://dev.epicgames.com/documentation/fortnite/memory-management-in-unreal-editor-for-fortnite)
distinguishes cooked publishing memory from platform/runtime memory. A
source heightmap byte count cannot replace either measurement.

## Full universe coverage status remains separate

The new source terrain bundle addresses **only the terrain category** in
each of the thirteen region source packages. The universe-readiness
policy still requires per-region landscapes/landmarks, encounters, ecology,
quests, navigation, streaming, VFX/audio, and mobile LOD. No region may be
marked `approved_source` solely because it has a heightmap. Terrain
source path references from Actions must be imported into durable source
storage or otherwise properly captured before populating the reviewed
`universe_source_delivery_inventory.json` registry. No fake file paths.

The creator's complete-universe-first directive and no-Codex restriction
remain in force. The project is not labeled playable, complete or published
by this work.
