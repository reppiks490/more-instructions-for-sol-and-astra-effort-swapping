# Omnigod Sovereign — 12-ability audiovisual source package

This source-first package addresses universe program #84, visual issue #88 and
Arsenal handoff #83. It is **not** a native UEFN asset or early playable prototype.
It contributes **zero approved 840-entity packages** to the reviewed inventory.

## Generate and verify

```bash
python tools/build_omnigod_arsenal_presentation.py --output dist/omnigod_arsenal_presentation
python tools/build_omnigod_arsenal_presentation.py --output dist/omnigod_arsenal_presentation --validate-only
python -m unittest discover -s tests -p 'test_omnigod_arsenal_presentation.py' -v
```

The deterministic Python 3.12 standard-library source compiler emits **12
original RGBA8 256x256 PNG telegraph masks**, **14 original mono PCM16 16 kHz
WAV cues**, **12 WebVTT caption files**, and a file-hash/provenance manifest.
Each SFA-001–SFA-012 signature has a distinct noncolor silhouette and a
corresponding audio/caption cue. SFA-002 adds an *optional* CLS-006-mark
accent (never a class grant); SFA-005 has two separately timed audio events.
SFA-008's proposed 3000 ms shield hold is visual only. All timings are
**editor presentation suggestions**, never server hit-pulse deadlines.

Optional integration against the Arsenal team's unmerged 12-ability contract:

```bash
python tools/build_omnigod_arsenal_presentation.py \
  --arsenal-contract content/sovereign/sovereign_arsenal_universe_contract.json \
  --output dist/omnigod_arsenal_presentation
```

Only use this flag when the contract file actually exists in the checked-out
branch. It rejects name/ID drift, a non-FUS-001 contract, or enabled native
activation. This package deliberately does not copy Arsenal-owned files.

## Native editor handoff (NOT DONE)

1. Import PNGs as appropriate textures; create Niagara material instances and
   per-ability systems in the actual UEFN editor. These PNGs are *not* Niagara
   systems. Preserve all 12 different silhouettes in reduced-color settings.
2. Create owner-only audio/subtitle cues and optional world-readable telegraph
   silhouettes separately. Bind to trusted canonical FUS-001 owner and current
   generation; no broadcast owner camera, no NPC-possession assumption.
3. On cancel, revocation, logout, separation, actor despawn, generation change,
   or region unload, stop **all** presentation before canonical abort. Never
   use these VFX events to authorize damage, shield, LOS, cooldown, a paid
   receipt, or an NPC entitlement. FUS-002 remains disabled.
4. Proposed per-effect LOD caps: near <=2500 cm, <=80 particles/2 systems;
   mid <=6000 cm, <=24/1; far <=12000 cm, **0/0**. Proposed per-region
   concurrency: 2 near, 1 mid, 0 far. These are **unmeasured design caps**;
   authored texture dimensions and WAV bytes are not cooked memory proof.
5. Non-color cues, mute-safe HUD text, subtitles, no screen flashes or shake,
   and touch-safe warning sizing are mandatory. Mobile needs native frame-time,
   memory, visibility and two-client testing across **all 13 regions**.
6. UEFN import, Niagara and Sequencer binding, Verse compile, native character
   definitions, multiplayer Launch Session, Fortnite mobile profile, and
   actual **300 MiB cooked publishing memory** measurement remain NOT RUN.

Coordinate with Avatar #87 for owner lease/camera, Architect #37 for canonical
state, Arsenal #83 for conditional events, World #86 for regional streaming,
Content #85 for full catalog, and independent QA #89 for native evidence.
The 840+ entities, 13 regions and 13 systems remain the full source priority.
