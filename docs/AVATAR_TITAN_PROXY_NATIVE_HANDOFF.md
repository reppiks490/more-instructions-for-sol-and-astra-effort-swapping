# AEONFALL — Sovereign Titan proxy research harness (FUS-002 remains disabled)

**Source prototype, not native-compiled UEFN gameplay.** The source in this PR
does not implement native possession, skeletal mesh substitution, an NPC-follow
camera, actual Titan damage, or verified replication. FUS-002 cannot be
activated by the Architect's authoritative phase service; the sandbox harness
may temporarily control a separate spawned NPC **only while the true creator
has an active FUS-001 Armor Fusion**. It is disabled by default.

## What has been implemented

1. `verse/sovereign/titan_proxy_command_runtime.verse` — a per-session singleton
   mailbox with a single leased proxy controller, canonical FUS-001 owner,
   active character, generation token, finite-spend attack-cue allowance and
   monotonic command and teardown epochs. Its authorization rechecks the
   Architect's `IsAuthorizedActive` plus the Avatar's current native
   character; never trusts first join, team, name or cosmetic.
2. `verse/sovereign/titan_proxy_device.verse` — disabled-by-default creative
   device with a **dedicated** NPC Spawner, four separate Input Trigger devices
   (summon / move-next-anchor / audio-cue / dismiss), eight-or-fewer placed
   waypoints, owner-facing HUD and owner-instigated cue Trigger. Invalid
   references and duplicate physical bindings reject startup. The harness
   prevents an unrelated player from driving or dismissing the NPC.
3. `verse/sovereign/titan_proxy_behavior.verse` — one native `npc_behavior`
   obtains its own NPC agent and `navigatable`, polls the command mailbox,
   and navigates to approved waypoint coordinates. Each `NavigateTo`
   invocation is bounded by a two-second `race`, then stopped; the movement
   logic never moves the owner's actual Fortnite character or camera.
   An unbound NPC behavior exits after 40 bootstrap checks.
4. `content/sovereign/titan_proxy_experiment.json` — machine-readable
   editor-binding inventory and the unchanged `not_run` native evidence
   boundaries. `tools/validate_titan_proxy.py` and
   `tests/test_titan_proxy.py` assert source guards, mutate threat surfaces
   and run an independent policy **reference model**, not Verse.

## Editor requirements (no physical proof yet)

- Build and open an actual UEFN project created by the editor. Do not invent
  `.uefnproject`, Character Definition, `.uasset` or island codes.
- Import Verse into the project through
  `python tools/install_uefn_sources.py path/to/Project.uefnproject --dry-run`
  followed by a deliberate real install, preserving the original metadata.
- Create an NPC **Character Definition** with exactly one
  `aeonfall_titan_proxy_behavior`. Use an NPC type supporting Verse custom
  behavior and navigation; verify the allowed character definition class and
  custom NPC mesh setup in the actual editor. A static GLB blockout alone is
  NOT an animated skeleton or an equipped player skin.
- Place one dedicated `npc_spawner_device`, initial state **disabled**,
  spawn-at-game-start **off**, total live NPCs **one**, automatic periodic
  spawn **off**, Despawn AIs When Disabled **on**. Bind this spawner to no
  ambient, boss, monster, horde, Titan alternative or cinematic system.
- Place one `aeonfall_titan_proxy_device` with `Enabled=false` until
  native validation. Set `AvatarController` to the unique FUS-001 controller.
  Bind the dedicated NPC spawner, four **distinct** Input Triggers, a HUD
  Message device, and one non-damaging **cue-only** Trigger. Bind one to eight
  valid, nonoverlapping creative_prop waypoints on baked navmesh, no more
  than **1600 cm** from the owner's character when used.
- The AttackCueOutput is ONLY an owner-specific audio/animation request;
  do not wire it to damageable interfaces, an unrestricted Damage Volume,
  weapon grant, global prop explosion, quest progress or encounter triggers.
  Arsenal's separate FUS-001 adapter must retain independent target/range/
  faction/LOS validation. This Titan harness currently does **no damage**.
- Owner movement and the existing FUS-001 orbit camera remain native and
  player-bound. **No Titan viewpoint** is enabled or claimed. NPC navigation
  and its resulting replication are native-engine responsibilities whose
  behavior must be demonstrated in two-client Launch Sessions.
- Keep native FUS-002 activation disabled. The harness is a test NPC, not a
  permanent player form or a second origin of Sovereign authority.

## Important outstanding race / feasibility uncertainties

Spawner events carry an agent, not a generation-bearing spawn-request
identifier. The mailbox rejects duplicate/live unsolicited agents, invalid
owners, stale commands and invalidates epoch before cleanup, but a delayed
spawn event after a rapid stop-and-resummon cannot be fully distinguished
from a new spawn using just `SpawnedEvent`. Native acceptance MUST test
spawn latency and reuse and, if this race is observed, replace event-only
binding with a generation-addressable `SpawnAt` return or a stricter native
spawn barrier before enabling production.

A timed `NavigateTo` may report partial or failed navigation, or get
canceled. Source code proves no successful pathfinding or replicated
movement. A real collision/navmesh test is required. Shutdown/despawn
calls are scoped to the dedicated spawner only, and cannot safely be used
against shared spawners.

## QA execution and evidence gates

**Source-only commands:**

```bash
python tools/validate_titan_proxy.py
python -m unittest tests.test_titan_proxy -v
python tools/validate_verse_static.py
```

**Native gate:** attach exact source commit SHA and UEFN engine version, real
Verse compiler output, Character Definition and spawner binding screenshots,
and two independent Fortnite clients' recorded Launch Sessions. Check:

- Creator-only summon, unrelated player attempt, spoofed Input Trigger and
  client reconnect; no entitlement on first join.
- Concurrent duplicate creative devices/spawners, duplicate NPC SpawnedEvent,
  missing Character Definition and delayed spawn after timeout/stop/restart.
- Navigation each anchor, blocked navmesh, command rate limit, interrupted
  NavigateTo, NPC elimination, streaming and teleport distance.
- Two players simultaneously; only the one authorized owner can issue
  commands and only the dedicated NPC is moved/despawned.
- Resource depletion, 10 rapid attack-cue presses, generation rotation,
  FUS-001 separation, permission revocation, respawn, disconnect and
  device shutdown. Verify all NPCs and per-owner cues are cleared.
- Confirm **no** real damage, grants, avatar movement suppression, owner
  camera theft or cross-client global activation. Never claim NPC possession.
- Measure platform memory, server/client network observations and lag spikes.

No test or CI workflow in this repository can substitute for these native
editor/Launch Session records.

## Workstream coordination

Architect owns authority, token and form state. Avatar owns proxy
presentation/navigation and native player restoration. Arsenal owns actual
damage and target validation, not this experimental cue. Cinematics owns
non-damaging owner-specific cue effects and reduced-flash fallback. QA owns
independent mutation review and native multiplayer evidence. Updates belong
in GitHub issue #37. No concurrent edits to PR #48 or PR #49 are required.

## Epic API references

- NPC Spawner: https://dev.epicgames.com/documentation/fortnite/verse-api/fortnitedotcom/devices/npc_spawner_device
- NPC Behavior: https://dev.epicgames.com/documentation/fortnite/verse-api/fortnitedotcom/ai/npc_behavior
- Navigatable: https://dev.epicgames.com/documentation/fortnite/verse-api/fortnitedotcom/ai/navigatable

**Evidence:** Verse compile `not_run`; NPC placement `not_run`; navigation
`not_run`; multiplayer `not_run`; possession `unproven`.
