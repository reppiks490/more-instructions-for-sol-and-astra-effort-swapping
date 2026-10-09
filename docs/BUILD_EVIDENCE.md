# AEONFALL starter build evidence — 2026-10-08

This build delivers source and importable assets. It does not claim a compiled
Fortnite island. The actual Windows UEFN editor is not available in this Linux
workspace.

## Delivered

- Original Ossuary Exchange blockout: 18 reusable GLB/OBJ modules, 593 placements,
  19,584 placed triangles, a labeled plan and an offline WebGL viewer.
- Matching 253 × 253, 16-bit PNG/r16 landscape samples, module hull recipes and
  a placement/marker manifest with 59 verified artifact hashes.
- Windows launcher and existing-project source installer, with backups,
  idempotent installation, stale-file checks and project-metadata protection.
- UEFN Python import/assembly script using documented editor operations and
  the actual project content mount. Local MCP configuration and editor mission.
- Five-tier horde ecology, canonical directors for three bosses and one event,
  typed transactional event queues, guarded activation identity and dispatch,
  instant/managed lifetimes, atomic status/taming application, saturation
  handling and physical status cleanup reconciliation.

## Executed checks

All **55 Python validation/generation/test commands** in the catalog workflow
passed in the final integrated local run. Their raw command output is supplied
as `SOURCE_VERIFICATION.json` in the downloadable package. `git diff --check`
and Python compilation of the installer/editor script also passed.

The test commands executed **89 Python tests**: 36 installer/editor contract
tests, 21 event/status source mutation tests, 12 activation mutation tests,
13 encounter-policy tests and seven actual geometry/regeneration regressions.
Installer tests make real isolated file-system changes; editor tests use a fake
API to check calls and decisions. Mutation guards inspect source, not Verse
execution. Geometry validation parses the actual assets and checks 1,296 route
samples and 64,009 matching elevation samples. Viewer JavaScript syntax passed;
browser rendering was not verified.

## Editor checks still required

Create the Blank project through Epic's Windows UEFN editor and follow
[UEFN_STARTER.md](UEFN_STARTER.md). Real project metadata, `.uasset` imports and
the `.umap` level must come from that editor. The assembly script creates only
architecture; Creative devices, Character Definitions, effect graphs, lighting
and navigation still require editor configuration.

Compile all 118 Verse source files against the installed Fortnite release.
Run the disabled development devices in a private test map and record the
actual `HORDE RESULT`, `ACTIVATION RESULT`, `ENCOUNTER DIRECTOR RESULT`,
`BUS TEST` and `STATUS SATURATION TEST` totals. Then validate physical effects,
multiplayer/AI behavior, persistence/rejoin, collision, navigation, memory and
Spatial Profiler results. None of those checks was executed by Python here.

The review branch remains a draft. No island was published.
