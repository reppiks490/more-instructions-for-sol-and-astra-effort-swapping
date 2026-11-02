# AEONFALL — Sovereign Titan proxy research harness (FUS-002 remains disabled)

**Source prototype, not native-compiled UEFN gameplay.** The source in this PR
does not implement native possession, skeletal mesh substitution, actual
Titan damage, or verified replication. An optional fixed-point camera follow
experiment is authored but **not native-tested or enabled by default**. FUS-002 cannot be
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
5. **Optional camera research:** a dedicated `gameplay_camera_fixed_point_device`
   can be added to the single verified owner's camera stack only **after**
   successful NPC behavior acknowledgement. A bounded coroutine repositions
   that camera every 0.15 seconds to the NPC position plus an editable
   **world-space** offset, while preserving the editor-authored camera rotation.
   The initial camera relocation must succeed **before** it is added to
   the owner's stack; no unpositioned camera is presented. Subsequent
   invalidation or teleport failure removes it **from that owner only**.
   This is not a native NPC viewpoint, facing-relative chase camera, camera
   proof, character swap or possession.

## Native spawn and behavior-readiness safety upgrade

**2026-11-01 in-flight inventory reconciliation:** Epic documents
`npc_spawner_device.SpawnAt` as suspending while the NPC loads. A native
`GetAgents()` poll can therefore observe the eventual NPC **before** the
`SpawnAt` call returns its agent. Previously the monitor unconditionally
destroyed that legitimate single in-flight candidate as "unexpected," making
otherwise valid summons nondeterministically fail under load.

The monitor now tolerates **at most one untrusted candidate** only while the
current session's exact epoch holds the outstanding `SpawnAt` lease. It does
not mark the candidate owned or behavior-ready and it cannot navigate, emit
attack cues, grant any entitlement, or receive gameplay commands. Two or more
agents still trigger immediate teardown. When `SpawnAt` returns, the existing
`CompleteSpawn` epoch/authority checks and `GetAgents` exact-identity match
must succeed or the spawner is cleared. A failed/slow `SpawnAt` still hits
the five-second timeout and is invalidated, with an outstanding lease kept
until the actual asynchronous return. This trades a bounded observation
window for correct asynchronous identity reconciliation; it is **not**
evidence of native spawn success, race ordering, or possession. In Launch
Session, explicitly instrument the relative timing of SpawnedEvent,
GetAgents visibility, SpawnAt return and owner revocation.

**2026-11-01 preflight correction:** A populated dedicated spawner must be
rejected and cleared **before** the mailbox's `Begin` reserves its
`SpawnInFlight` lease. The previous order reserved the lease, detected an
existing NPC, then called `End` without issuing `SpawnAt`. Because no
asynchronous return could clear the lease, subsequent summons were blocked
for the entire session. Source guards and a mutation regression now require
inventory preflight and dedicated-spawner cleanup before reservation.
This does not make the NPC natively validated.

Epic's `npc_spawner_device.Enable()` states that characters **will start to
spawn**. Therefore the old assumption that `Enable(); SpawnAt(...)`
necessarily creates exactly one NPC was unsafe. The revised harness now
cross-checks the returned `SpawnAt` agent against the complete
`TitanSpawner.GetAgents()` inventory, rejects a preexisting or additional
spawn, and monitors the inventory thereafter. It fails closed and cleans the
**dedicated** spawner if the inventory differs from the authorized agent.
The installer cannot verify physical editor settings: configure spawn-on-enable
and periodic spawn behavior to avoid unsolicited agents, and verify actual
Native NPC Spawner operation before activation.

`SpawnAt` returning an agent **does not prove its custom Verse `npc_behavior`
is running**. The NPC behavior now calls `AcknowledgeBehavior(Agent)`
after `GetNavigatable[]` succeeds and its authorized identity matches the
same agent. Both waypoint movement and the non-damaging attack cue require
`BehaviorReady`; if no acknowledgment arrives within five seconds, the
harness invalidates the session and despawns the dedicated NPC. The UI
distinguishes *summon requested* from *behavior online*. A creator's input
cannot make an unacknowledged or unrelated NPC ready.

These safeguards detect several source-level failure modes; they **do not**
prove native NPC Spawner and Verse timing, collision, replication or editor
configuration. The source intentionally remains disabled. `GetAgents` may
include engine-owned or expired agents depending on editor behavior; test the
actual UEFN device under elimination and repeated summon cycles.

Reference: Epic's public NPC Spawner
`Enable`, `GetAgents` and `SpawnAt` APIs:
https://dev.epicgames.com/documentation/fortnite/verse-api/fortnitedotcom/devices/npc_spawner_device

## Owner-only Input Trigger lifecycle (source, not native verified)

**NPC behavior end:** A behavior may stop without its agent being eliminated.
The NPC records the exact acknowledged epoch and calls an epoch/agent-scoped
readiness withdrawal in `OnEnd`. Pending navigation is invalidated and the
0.25s owner monitor tears down camera, command HUD and the dedicated NPC if
its behavior is no longer ready. Stale `OnEnd` from an older epoch cannot
revoke a newer generation. This is a source-level safety path, **not** native
proof that engine callbacks always arrive in every shutdown scenario.

**Behavior-readiness UI gate:** Summon is registered only while the exact
FUS-001 owner is eligible and no proxy is pending/active. Once a summon is
admitted, Summon is immediately unregistered and all three command actions
(move, cue, dismiss) remain disabled and unregistered. Only the current
NPC's exact `AcknowledgeBehavior` handshake, current epoch and renewed
canonical owner/character authorization permit the command input registration.
A wrong NPC, failed spawn, revocation, timeout or disconnect cannot expose
command controls. After teardown, the eligible owner may regain Summon on the
next monitor reconciliation. This limits false touch controls and duplicate
requests; it is **not** proof of mobile HUD rendering or network latency.

Epic's `input_trigger_device.Register(Agent)` and
`Unregister(Agent)` methods are supported, but the UEFN device setting
**Registered Player Behavior** determines whether registration actually
filters the HUD/input. This Titan harness now uses **individual** registration
only after the existing FUS-001 Architect controller acknowledges a live
native creator-owner/character/generation. It never uses RegisterAll,
GetPlayers()[0], a display name or team as authority.

**Required editor setup for all four dedicated Titan Input Triggers:**

- `Registered Player Behavior = Require Registered`. If set to `Add
  Registered` or `Ignore Registered`, registration does not provide the
  intended owner-only input visibility. **Server Verse authorization remains
  mandatory even when the HUD appears owner-only.**
- `Enabled At Game Start = Off`. `SummonInput` becomes enabled only for
  the current verified FUS-001 owner, reconciled every 0.25 seconds.
  Movement, attack-cue and dismissal inputs remain disabled until the exact
  NPC behavior acknowledgement and renewed owner authorization, not merely
  `SpawnAt` return. They are registered only to that player.
- Never share these four physical Input Trigger instances with Arsenal,
  normal ability inputs, other islands, Titan spawners or Cinematics. Changing
  their enablement/registration would otherwise disrupt another system.
- On owner change, FUS-001 separation, revocation, device end, death,
  disconnect or proxy dismissal, unregister the relevant owner and disable
  command inputs. Do not use `UnregisterAll` to destroy another component's
  registrations.

Owner registration alone cannot prove that a press, native HUD display or
multiplayer delivery occurs. Test with two live Fortnite clients and capture
the device option screenshots; the input trigger's network response can be
affected by client round-trip latency.

Epic official references:
https://dev.epicgames.com/documentation/fortnite/verse-api/fortnitedotcom/devices/input_trigger_device
https://dev.epicgames.com/documentation/fortnite/using-input-trigger-devices-in-fortnite-creative

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
  player-bound. The experimental Titan fixed-point tracking camera is **off
  by default**. If explicitly enabled for controlled editor testing, dedicate
  one Fixed Point Camera device, disable **Add to Players on Start**, wire
  `ProxyCamera` and set `ExperimentalCameraEnabled=true` only after all
  native bindings and authority are proven. The device is added only to the
  verified owner's stack after NPC behavior readiness and removed on dismissal,
  NPC elimination, owner revocation, disconnect or device shutdown. Its
  world-space camera offset and editor-authored rotation do **not** guarantee
  Titan framing, occlusion safety, smoothness, target tracking or input
  redirection. Native NPC navigation, camera behavior and replication must
  be demonstrated in two-client Launch Sessions.
- Keep native FUS-002 activation disabled. The harness is a test NPC, not a
  permanent player form or a second origin of Sovereign authority.

## Important outstanding race / feasibility uncertainties

The harness now uses the documented asynchronous `SpawnAt(Position, false)`
return value rather than associating an untagged `SpawnedEvent`. It permits
**one in-flight SpawnAt request per session**, and binds the returned NPC only
if the request epoch is still active and the exact FUS-001 owner/character/
generation remains authorized. Stop invalidates the epoch *without resetting*
the pending-spawn flag, so a new summon is rejected until the old SpawnAt
returns. A late/failed return triggers a dedicated-spawner cleanup. Native
acceptance must nevertheless verify SpawnAt timing and delayed callbacks,
especially after respawn, shutdown and island reload. A permanently stalled
SpawnAt intentionally fails closed rather than risking cross-generation NPC
ownership.

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
- Confirm **Require Registered** on all four dedicated inputs. Owner sees the
  summon action only during authorized FUS-001; nonowner sees no Titan
  movement/cue/dismiss UI, even when both clients use the same team.
- During an in-flight summon, confirm **no player** sees move/cue/dismiss or
  a repeat Summon action. After the exact NPC behavior acknowledgement,
  confirm only the owner gains move/cue/dismiss inputs. Test on Fortnite
  mobile touch UI and with two live clients; do not assume registration
  automatically proves native HUD visibility. On owner revocation, character replacement, disconnect and
  teardown, verify native input unregister/disable on both clients.
  Delayed input callbacks must still fail the server authorization gate.
- Concurrent duplicate creative devices/spawners, duplicate NPC SpawnedEvent,
  missing Character Definition and delayed spawn after timeout/stop/restart.
- Navigation each anchor, blocked navmesh, command rate limit, interrupted
  NavigateTo, NPC elimination, streaming and teleport distance.
- Enable a deliberately misconfigured spawner that auto-spawns while
  `SpawnAt` is in flight. Confirm two visible agents immediately force
  shutdown. A single unbound candidate is only temporarily tolerated
  during the exact in-flight epoch, cannot issue commands, and must match
  the eventual `SpawnAt` return identity or force teardown. Record the
  order of GetAgents visibility, async return, and monitor ticks; confirm
  no unsolicited NPC survives and the player never receives the
  *behavior online* cue for an unacknowledged NPC.
- Delay Character Definition startup; confirm movement and attack input
  are rejected before NPC-behavior acknowledgment, and verify cleanup
  after the five-second timeout. Test acknowledgment from the wrong agent.
- Interrupt summoning before the owner field is established and confirm
  pre-owner cleanup does not leave the device or NPC enabled.
- Two players simultaneously; only the one authorized owner can issue
  commands and only the dedicated NPC is moved/despawned.
- Kill the bound Titan NPC and also simulate an unrelated NPC death. Only the
  exact bound-agent elimination must invalidate the proxy; duplicated death
  callbacks must be harmless. Stop the NPC behavior while its agent remains
  alive and verify command HUD/camera/paid cue admission are withdrawn; a
  late OnEnd from an old epoch must not stop a new proxy.
- Resource depletion, 10 rapid attack-cue presses, generation rotation,
  FUS-001 separation, permission revocation, respawn, disconnect and
  device shutdown. Verify all NPCs and per-owner cues are cleared.
- With the optional camera **off**, confirm the owner's FUS-001 orbit camera
  remains unmodified. With it on in a private editor session, verify only
  the verified owner gets a fixed-point stack addition; observe camera
  tracking on multiple waypoints and its world-offset/rotation limits. Dismiss,
  revoke authority, kill the NPC, disconnect and force failed TeleportTo;
  confirm only the owner camera is removed, returning to FUS-001 without
  changing the second client's view or trapping the first client.
- Confirm **no** real damage, grants, avatar movement suppression, inherited
  owner camera, or cross-client global activation. Never claim NPC possession.
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
- Fixed Point Camera: https://dev.epicgames.com/documentation/fortnite/using-fixed-point-camera-devices-in-fortnite-creative
- Camera Stack API: https://dev.epicgames.com/documentation/fortnite/verse-api/fortnitedotcom/devices/gameplay_camera_device

**Evidence:** Verse compile `not_run`; NPC placement `not_run`; navigation
`not_run`; multiplayer `not_run`; possession `unproven`.
