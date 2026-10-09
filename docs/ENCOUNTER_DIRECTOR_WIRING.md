# First-slice encounter execution

`aeonfall_encounter_director_device` now connects the existing boss/world-event
services to physical Creative devices. It supports BOS-005, BOS-006, BOS-011,
and EVT-011 through generated canonical contracts and explicit progression gates.
The new code has passed repository static validation. It has **not** compiled or
run in UEFN; no Character Definitions, arenas, or editor device references are
created by these source files.

The director owns one service instance for its encounter. Place exactly one
director for each canonical ID. Do not place the legacy participant-volume
device for the same encounter: the director owns participation and snapshots
registered live players in its volume immediately before reward resolution.

## BOS-005: playable integration path

1. Import the new files under `verse/bosses` into the UEFN project alongside the
   existing AEONFALL runtime. Build Verse. Place the actor/profile bootstrap and
   `aeonfall_slice_001_reward_bootstrap_device`, then one encounter director.
   Set `EncounterId = BOS-005` and name it `EC_BOS_005`.
2. Bind a volume around the arena to `ParticipantVolume`. Bind separate start,
   failure, completion-output, and failure-output Trigger devices. Configure
   failure input to the arena's explicit team-wipe/timeout/abandon rule.
   Missing/wrong reward registration rejects start with
   `encounter.director_reward_not_ready`; it does not consume the start input.
3. Add **one** boss NPC Spawner to `BossSpawners`. Bind
   `CD_BOS_005_GoreMasonRedHand`; retain supported native or authored NPC combat
   behavior. Configure Spawn Count **1**, Total Spawn Limit **1**, Allow Infinite
   Spawn **False**, Spawn Character at Game Start **False**, Spawn On Timer
   **False**. The director calls Reset, Enable, and Spawn once per run. It fails
   if no live `fort_character` arrives within `BossSpawnTimeoutSeconds` (default
   five seconds), or if a second distinct boss body arrives.
4. Add three `Phases` entries in exactly the order below. Each `Inputs` entry
   has a `Kind`, canonical ID, and distinct physical source. Set `Source` to
   `PropDestroyed` and bind `DestructionSource` for native destructible targets;
   set `Source` to `TriggerGraph` and bind `Input` for authored mechanic graphs.
   Drive these inputs from actual objectives/destructibles/trackers; no objective completes merely
   because its phase starts. Every listed objective and weak point must have
   one input binding, even when it is an optional mechanic.

| Phase ID | Objective inputs | WeakPoint inputs | Progression inputs |
| --- | --- | --- | --- |
| BOS005-P1-FRESH-MORTAR | OBJ-BOS005-DENY-CORPSES | WP-BOS005-RED-HAND | None: health is observed automatically |
| BOS005-P2-DEADMANS-STAIR | OBJ-BOS005-BREAK-STAIR-A, OBJ-BOS005-BREAK-STAIR-B, OBJ-BOS005-BREAK-STAIR-C | WP-BOS005-TOOL-ARMS | None |
| BOS005-P3-LAST-WALL | OBJ-BOS005-PUNISH-WHISTLE | WP-BOS005-RED-HAND, WP-BOS005-WHISTLE | None: elimination is observed automatically |

5. Bind the phase resources below. `Hazards` entries carry the exact hazard ID,
   optional Damage Volume devices, and separate enable/disable output Trigger
   devices. For a damage lane, the director operates its Damage Volumes directly.
   For a wall or presentation effect, connect the outputs to the editor graph
   that shows/hides/releases it. `SpawnGroups` carry the exact group ID and
   at least one NPC Spawner; set those add spawners to game-start disabled and
   spawn-on-timer enabled. Their aggregate editor-configured live spawn count
   must stay within BOS-005's authored cap of **12**. The director resets/enables
   the new batch and explicitly disables/despawns the outgoing batch.

| Phase | Hazard IDs | Spawn group |
| --- | --- | --- |
| Fresh Mortar | HZ-BOS005-RED-WALL, HZ-BOS005-MORTAR-FIST | SG-BOS005-BUILDERS |
| Deadman's Stair | HZ-BOS005-STAIR-LANES, HZ-BOS005-HARDENED-WALLS | SG-BOS005-REINFORCEMENTS |
| Foreman's Last Wall | HZ-BOS005-LAST-WALL, HZ-BOS005-MORTAR-FIST | SG-BOS005-FINAL-BUILDERS |

6. Bind each phase's `EnterOutput` to its telegraph/HUD/objective reset graph.
   Bind `CleanupOutput` to remove phase props/path blockers and release project
   tokens. Hazard disable outputs must be idempotent: initial and terminal
   cleanup sweeps invoke them for every authored phase. Phase cleanup runs only
   when leaving an active phase. All resources must be encounter-owned; the
   director must not disable ambient, invasion, or another encounter's devices.
7. Launch Session. Starting the encounter enables Fresh Mortar and spawns the
   body. Either corpse denial or live boss health at/below 70% enters Deadman's
   Stair. Its body becomes invulnerable and all **three** destroyed stair-anchor
   objectives are required. The final phase restores vulnerability. Only the
   owned boss character's final-phase elimination completes BOS-005 and calls
   the existing first-clear reward service. A lethal hit in an earlier phase
   fails the encounter and awards nothing.

All trigger inputs require **zero transmit delay**, unlimited activations, and
separate physical devices from all output triggers. Never connect an output
back into an input. Single-count objectives and weak points reject duplicate
credit. Multi-count mechanics count successful authored occurrences, so their
source graph must emit once per distinct lot/decree. Trigger payloads do not
contain an event nonce; the director cannot distinguish duplicated hardware
delivery from a second legitimate success. Inactive phase inputs are disabled
and also rejected by their captured phase index.

### Native stair anchors and physical ownership

The director now accepts actual `prop_manipulator_device.DestroyedEvent` inputs.
For each of the three stair objectives, select `Source = PropDestroyed` and bind
its own Prop Manipulator. Each region must cover exactly one destructible anchor;
the event contains the destroying agent but does not identify which prop within
a multi-prop region was destroyed. The native callback accepts a registered,
living human player inside the arena, then applies the captured phase gate. It
does not emit fake boss damage or elimination. Blockout weak-point props can use
the same source; they represent separate destructible targets rather than native
body hit-location detection.

Phase entry enables, shows and restores the health of existing affected props;
phase exit hides them and disables the manipulator. A destroyed prop must be
recreated by the authored phase-entry graph for a repeated run. `RestoreHealth`
is not evidence that a destroyed prop has been respawned. Verify reset behavior
in UEFN before accepting repeatable encounter completion.

Startup validates every referenced active physical object before any initial
cleanup. All source, output, damage-volume and spawner roles must be distinct,
including roles in different phases. Repeated canonical hazard/weak-point IDs
therefore use separate physical instances. The boss spawner cannot also belong
to a phase add group. A session lease rejects a second director for the same
encounter and any director sharing an existing director's physical objects.
Rejected directors perform no arena cleanup or participation reset on shutdown.

`content/vertical_slice/first_playable_rig.json` records a complete BOS-005
director binding graph with unique device references and bootstrap readiness
dependencies. These dependencies do not impose engine `OnBegin` order. The file
is authored placement intent; all placement, Verse compilation and Launch
Session fields remain `not_run`. Validate it with
`python tools/validate_first_playable_rig.py`; its mutation tests reject shared
stair sources, boss/add reuse, feedback, unresolved references and dependency
cycles. Native health at 70%, three destroyed anchors and final native
elimination form the first-playable route. Optional corpse/whistle graph inputs
still require their real authored producers.

## Other first-slice directors

Use the same device class for `EC_BOS_006`, `EC_BOS_011`, and
`WD_EVT_011_GraveMarketEclipse`. Copy phase IDs, objective IDs, weak-point IDs,
hazard IDs, and spawn groups from `slice_001_encounters.json`. Exact identity
and order are checked at device startup. BOS-006 allows eight simultaneous adds;
BOS-011 allows sixteen; EVT-011 allows twenty-four. These numeric limits must be
enforced in the owned spawners' editor configuration; this bridge does not read
or rewrite their spawn-count settings.

| Encounter/phase | Required transition | Progression inputs to bind |
| --- | --- | --- |
| BOS-006 Blessing Scent | Live health <=70% AND one failed Halo Bite recorded as OBJ-BOS006-BAIT-POUNCE | None |
| BOS-006 Stolen Halo | OBJ-BOS006-BREAK-STOLEN-HALO OR live health <=35% | None |
| BOS-006 Starved Grin | Owned boss eliminated | None |
| BOS-011 Royal Tax | Treasury threshold OR live health <=75% | SIG-BOS011-TREASURY-THRESHOLD |
| BOS-011 Dead Treasury | Both treasury-anchor objectives | None |
| BOS-011 Black Decree | Three successful OBJ-BOS011-SOLVE-DECREES occurrences | None |
| BOS-011 Bankruptcy | Owned boss eliminated | None |
| EVT-011 Corpse Lots | Three distinct successfully resolved lots | SIG-EVT011-LOT-RESOLVED |
| EVT-011 Black Auction | Authored influence threshold resolved | SIG-EVT011-INFLUENCE-RESOLVED |
| EVT-011 Clean Ledger | Denial threshold OR resolved auction | SIG-EVT011-DENIAL-THRESHOLD, SIG-EVT011-AUCTION-RESOLVED |
| EVT-011 Market Crash | Ledger destroyed | SIG-EVT011-LEDGER-DESTROYED |

World-event directors have an **empty** `BossSpawners` array. Bind event timeout
to `FailInput`; expiry cannot claim completion. Complex treasury, auction,
corpse ownership, counter-decree, VFX, and regional outcome logic remains in the
authored device graphs. The current gate policy executes the four-stage event
chain; normal-auction versus crash outcome branching is not implemented here.
The existing `EscalatesOnFailure` metadata is available to project graphs; this
bridge ends and cleans the run on failure, without inventing escalation rules.

## Verification and editor acceptance

Regenerate after changing canonical encounter content or gate policy:

```bash
python tools/build_slice_encounter_directors.py
python tools/validate_encounter_directors.py
python tools/test_encounter_director_policy.py
python tools/validate_verse_static.py
```

`validate_encounter_directors.py` checks canonical coverage/order, known gate
references, positive counts, mandatory first-slice mechanics, final-only physical
boss victory, generated-file drift, integration guards, and editor assertion
coverage. The Python mutation tests verify rejection of weakened/malformed gate
data. These checks do not prove Verse compilation or device execution.

Place `aeonfall_encounter_director_test_device` in a development map and set
`Enabled = true`. It executes the actual Verse progression logic for all four
encounters and logs `ENCOUNTER DIRECTOR RESULT: ... checks, 0 failures`. Keep it
disabled in production. Record the UEFN version, build result, session result,
and the physical acceptance results below before marking editor verification
complete:

| Physical acceptance | Expected result |
| --- | --- |
| Start with missing reward bootstrap | Start rejected; no body/adds/hazards |
| Start with unknown ID, incomplete phase list, wrong input/resource IDs, wrong boss-spawner count | Configuration rejected; devices disabled |
| Start BOS-005 with a registered live player already in the arena | Exactly one boss body, phase-zero hazards/adds, player registered |
| Kill an earlier-phase boss with an oversized hit | Failure; no first-clear reward |
| Reach 70% health while alive | Phase one, outgoing adds despawned, phase-one hazards active, boss invulnerable |
| Destroy only two stairs | No advance and no reward |
| Destroy the third stair | Final phase, old phase cleaned, vulnerability restored |
| Send old-phase or arbitrary objective/health/death signals | Rejected; trusted body signals cannot be supplied through trigger bindings |
| Eliminate the final-phase boss | Canonical completion/reward once, all owned devices cleaned, completion output |
| Exit the volume before victory or disconnect | No participant reward for the departed player |
| Clear twice on the same saved profile | Existing first-clear policy skips the second reward |
| Fail after any phase, then restart | No old hazards/adds/counters; body spawner can create a new batch |
| NPC body cannot spawn, or a second distinct body arrives | Bounded failure and cleanup |
| Cleanup/entry graph eliminates the boss while transition is busy | Queued original death phase processed; no premature victory |
| End the session during spawn timeout or combat | Subscriptions canceled, timeout race stopped, synchronous cleanup |

This bridge uses the documented Creative APIs: [NPC Spawner settings](https://dev.epicgames.com/documentation/en-us/fortnite/using-npc-spawner-devices-in-unreal-editor-for-fortnite),
[Spawn](https://dev.epicgames.com/documentation/en-us/fortnite/verse-api/fortnitedotcom/devices/npc_spawner_device/spawn),
[DespawnAll](https://dev.epicgames.com/documentation/en-us/fortnite/verse-api/fortnitedotcom/devices/npc_spawner_device/despawnall),
[SetVulnerability](https://dev.epicgames.com/documentation/en-us/fortnite/verse-api/fortnitedotcom/characters/fort_character/setvulnerability),
[Trigger](https://dev.epicgames.com/documentation/en-us/fortnite/verse-api/fortnitedotcom/devices/trigger_device/trigger-1),
[volume occupants](https://dev.epicgames.com/documentation/en-us/fortnite/verse-api/fortnitedotcom/devices/volume_device/getagentsinvolume),
and [OnEnd](https://dev.epicgames.com/documentation/en-us/fortnite/verse-api/fortnitedotcom/devices/creative_device/onend).
The implementation keeps irreversible Creative actions outside failure contexts
and does not spawn cleanup coroutines in OnEnd.
