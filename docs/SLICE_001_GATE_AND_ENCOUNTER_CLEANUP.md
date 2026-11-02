# SLICE-001 — checkpoint-gated encounter admission, passage and terminal cleanup

**State: source authored and source-auditable only.** UEFN Verse compilation,
physical editor binding, collision/navmesh, Fortnite Launch Session and
multiplayer gameplay remain **not_run**. No editor object paths are invented.

## Step 1: encounter admission and five physical passages

The canonical per-player policy is
`verse/progression/slice_001_gate_policy.verse`. It shares the **existing**
persistent `aeonfall_player_profile` and requires a contiguous checkpoint prefix
plus acknowledged first-clear records. A gate checks the **entering player**;
there is no global barrier that can be opened by a teammate.

| Gate index | Physical entry | Requires persisted checkpoint chain | Requires first clears | Destination / encounter |
|---|---|---|---|---|
| 0 | GATE-RED-MASON | CP1 | None | Gore-Mason BOS-005 |
| 1 | GATE-SAINTLESS | CP1–CP2 | BOS-005 | BOS-006 |
| 2 | GATE-GRAVE-MARKET | CP1–CP3 | BOS-005, BOS-006 | Grave Market Eclipse EVT-011 |
| 3 | GATE-BLACK-THRONE | CP1–CP4 | BOS-005, BOS-006, EVT-011 | King Without Pulse BOS-011 |
| 4 | GATE-EXIT | CP1–CP4 | BOS-005, BOS-006, EVT-011, BOS-011 | Post-King exit |

The physical binding contract is
`content/vertical_slice/slice_001_gate_bindings.json`. Place one
`aeonfall_slice_001_progression_gate_device` in the editor, five distinct
**Volume** devices, five distinct **Teleporter** devices, and one HUD Message
device. Bind both editable arrays in the manifest order. **Do not share**
physical devices between gate roles or make a Teleporter auto-loop on arrival.
Use the named checkpoint markers only as *design anchors*: find safe landing
points and prove them in Launch Session. Gate 3 and gate 4 share the CP4
**reference marker**; they must be physically separated to prevent overlap.

The gate runtime:
- Acquires a unique per-session owner lease after binding validation.
- Rejects missing profiles, inactive characters, NPCs, out-of-order checkpoints,
  unearned boss/event completions, duplicate devices and duplicate owners.
- Uses a per-player, per-gate transient latch, rearmed on volume exit;
  disconnect and device shutdown clear state and cancel subscriptions.
- Calls `Teleporter.Teleport(Player)` only after authorizing that player.
  A requested teleport event is **not** proof of arrival.

## Step 2: encounter ingress, failure cleanup and first-clear rewards

The **existing** `aeonfall_encounter_director_device` still owns the boss
and world-event phase machinery, hazards, adds, final phase and cleanup.
It now rejects `StartInput.TriggeredEvent` without an instigating active
player physically inside `ParticipantVolume`, an available persistent profile,
and the same per-encounter checkpoint/first-clear prerequisites used by the
passages. Bind each encounter's StartInput to a **player-instigated native
trigger chain** (for example an interaction/passage trigger that preserves the
instigator); editor scripts which call `Trigger()` without an agent will now
be refused. Do not bypass the Verse director with direct spawner activation.

On arena departure or disconnect, the director checks the remaining live
participants. Once none remain, it follows the standard `OnFail` terminal
path, disables all phase inputs and hazard damage, despawns encounter-owned
NPCs, and emits the failed output. On success, the director emits
`CompletedOutput` **only after the boss/world-event service acknowledges
completion**. The existing first-clear service resolves participation and
atomically commits completion, XP, materials and unlocks to the player's
single profile, and queues physical delivery after acknowledgment. A service
completion alone does **not** prove every participant received a reward:
profile capacity/commit refusals must be inspected in native tests.

Cleanup is not a second reward service. No new player weak_map or temporary
active-combat persistence was introduced. Rejoining players must restart any
active arena instead of inheriting an orphaned boss or hazards; persisted
checkpoint/first-clear records are the sole admission authority.

## UEFN / MCP handoff

1. Run `python tools/validate_slice_gates.py`, then
   `python -m unittest tests.test_slice_001_gates tests.test_slice_001_spatial_handoff -v`.
   CI also runs these source checks. They do not compile Verse.
2. Install the editor-created UEFN project via
   `python tools/install_uefn_sources.py PATH_TO_PROJECT.uefnproject --dry-run`
   and then a deliberate actual install. Full source installation rejects
   invalid gate contracts **before changing the target project**.
3. The installer copies the gate binding JSON to
   `AEONFALLImportPackage/content/vertical_slice/`. Generate the unplaced
   placement checklist via `tools/uefn_editor/slice_001_spatial_handoff.py`
   to obtain **12 additional gate owner/volume/teleporter/HUD roles**, separate
   from the 49-device first-playable BOS-005 rig. Editor path fields remain null.
4. Physically place and bind all 12 roles; import the Verse sources, build the
   Verse project and record exact compiler diagnostics. For each of BOS-005,
   BOS-006, EVT-011 and BOS-011, configure real NPC Character Definitions,
   native triggers, and each director's phase inputs. Ensure completion
   output and failure output are not cross-wired.
5. Test empty profile, CP3 skipped, CP1–CP4 sequential unlock, wrong player,
   two-player differing progress, non-player trigger, no-instigator trigger,
   successful reward, refused reward save, failure/leaving mid-phase, disconnect
   mid-encounter, respawn, rejoin, duplicate owner and stale phase props.
   Observe actual physical gate arrival, hazard removal, add despawn, reward
   ledger and persisted boss/event IDs, not just Verse log messages.
6. Save project- and commit-pinned screenshots, Verse compile output and Launch
   Session logs as real evidence. Leave all `native_evidence` fields
   `not_run` until authenticated evidence is captured.

**Acceptance boundary:** Python/GitHub Actions = source checks. Only the actual
UEFN editor/compiler and Fortnite session can establish playability.
