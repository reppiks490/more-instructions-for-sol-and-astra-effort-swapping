# SLICE-001 checkpoint persistence and respawn — native acceptance pending

The Ossuary March now includes a **Verse runtime device** for four sequential
checkpoints, backed by the existing persistent player profile. The code is not
evidence of a compiled UEFN island or a successful Fortnite teleport.

## Editor installation

Install the source bundle into an **editor-created** UEFN project, as described
in [UEFN starter](UEFN_STARTER.md). Add exactly one
`aeonfall_slice_001_checkpoint_device` to the map. The source contract is
`content/vertical_slice/slice_001_checkpoint_bindings.json`.

Place four distinct **Volume** devices and four distinct **Teleporter** devices,
one pair at each of the geometry marker anchors in this order:

| Slot | Marker | Design anchor (cm) | Persisted ID |
| --- | --- | --- | --- |
| 0 | CHECKPOINT-1 | (0, -1000, 100) | SLICE-001:CHECKPOINT-1 |
| 1 | CHECKPOINT-2 | (0, 2900, 100) | SLICE-001:CHECKPOINT-2 |
| 2 | CHECKPOINT-3 | (0, 6500, 100) | SLICE-001:CHECKPOINT-3 |
| 3 | CHECKPOINT-4 | (0, 11900, 100) | SLICE-001:CHECKPOINT-4 |

These are **design anchors**, not actual placed editor object paths or tested
teleport arrival points. Adjust safe landing positions for collision/navmesh
without modifying the canonical source markers. Verify each Teleporter's native
options permit programmatic `Teleport(Agent)`, do not loop on arrival, and do
not require an item or team that would reject a valid player.

Bind `CheckpointVolumes[0..3]` and `CheckpointTeleporters[0..3]` in the same
order. Bind **every actual player spawner** to `PlayerSpawners`, including
spawners used by the existing `aeonfall_player_loadout_device`; missing pads
mean some respawns will not be observed. Bind a player-targeted HUD Message
device to `Feedback`. The checkpoint runtime rejects duplicate/missing
physical objects before subscribing. Keep this checkpoint device unique per
session; the lease rejects a second copy.

## Runtime behavior

A player's first checkpoint can be recorded only by physically entering its
Volume. Checkpoints 2–4 require the immediately preceding checkpoint in the
same persisted profile. Reentering an unlocked checkpoint is a no-op. A new
checkpoint is saved with `TrySaveProfile` using the immutable profile copy
constructor; a refused write must not report success.

On a newly observed active character (spawn or rejoin), the runtime waits for
the existing profile and character, selects the **latest contiguous** persisted
checkpoint, and requests a native Teleporter move. A player without a
checkpoint is left at the ordinary island spawn. A bounded startup wait avoids
indefinite retry loops. Disconnect and device shutdown clear transient
character/pending state and cancel native event subscriptions. The runtime does
not rewrite the profile during restoration or duplicate loadout delivery.

**Scope:** This handles checkpoint discovery and spawn/rejoin relocation. It
does not claim to solve dungeon gate progression, boss encounter cleanup,
persistent active combat state, or a general-purpose multiplayer respawn
controller. Teleporter return/arrival cannot be established by Python tests.

## Launch Session acceptance — evidence required

1. Compile the exact installed Verse source in UEFN and record the native
   compiler result, project version, and source SHA.
2. With an empty profile, spawn at the normal start. Enter checkpoint 3 first;
   verify it does **not** unlock. Enter checkpoint 1; verify the first save.
3. Enter checkpoint 1 repeatedly; verify no duplicate persistent ID or
   repeated progression reward. Enter checkpoints 2, 3, 4 in order.
4. Eliminate/respawn after each checkpoint and verify the player arrives at
   the correct safe Teleporter location, not merely that a request event fired.
5. Leave the island and rejoin; verify checkpoint 4 restores with the same
   persistent profile and the normal loadout restoration still works.
6. Two players with different checkpoint progress must respawn to their own
   destinations. Verify that a checkpoint event from an NPC does nothing.
7. Test refused/oversized profile saves and missing bootstrap: no false
   checkpoint success. Test a disabled/incorrectly bound Teleporter and
   document actual native failure behavior.
8. Remove a player during the readiness wait, restart the session, and
   exercise a duplicate checkpoint owner. Verify no lingering subscriptions
   or cross-session state.

Run `python tools/validate_slice_checkpoints.py` and
`python -m unittest tests.test_slice_001_checkpoints -v` for **source-only**
checks. The automated contract deliberately leaves all editor paths null and
all native evidence `not_run` until a real editor capture exists.
