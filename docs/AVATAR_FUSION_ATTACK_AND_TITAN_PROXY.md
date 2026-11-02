# Avatar FUS-001 attack bridge and FUS-002 Titan proxy feasibility

**Status:** Source-authored, disabled by default. This is not a native-compiled
playable custom armor mesh, verified attack hit, or NPC possession.

## FUS-001 — native player movement, camera and bounded attack request

The player **remains their native Fortnite player character** and retains
normal movement. The existing fusion controller adds an owner-specific orbit
camera, visual powerup and instigator-only cinematic after the Architect's
FUS-001 admission and finite budget reservation. The added `AttackInput`
listens for an input press and, on the server Verse device, requires:

- The controller is running and the instigator is the current verified
  `VisualOwner`, with the **same live `fort_character`** recorded at fusion.
- The Architect's `IsAuthorizedActive(Self, Player, Token)` accepts the exact
  owner, controller and generation; the finite budget's `Spend` accepts the
  cost, deadline and generation.
- A 2–10 second configurable cooldown (default 2 seconds), with a 1–25
  point energy cost (default 10), and distinct fuse/separate/attack inputs.

The paid admission and one-use Architect receipt must succeed together in a
transaction. A refused receipt rolls back the 10-energy debit. The minimum
2-second attack cooldown matches Arsenal Reaver's secondary gate. This is
source wiring only, not a native hit acknowledgement.

Only then does `AttackOutput.Trigger(Player)` send an **instigator-tagged
request** to an editor-bound `trigger_device`. This does not apply damage by
itself, select a target, certify a hit or prove replication of any downstream
graph. The Arsenal loop must supply a bounded, target-validated native
attack/damage adapter with explicit result acknowledgement. Never wire the
trigger directly to global damage, a shared camera, an unrestricted NPC
spawner or a grant of `UNI-001`.

The output device should have no transmit delay, reset delay or max-trigger
limit that silently discards valid inputs; verify these settings in UEFN.
Do not enable this controller until its complete attack graph and safe
failure/feedback path are physically configured. Input Trigger registration
is not used to authenticate the owner. The input may be visible to nonowners,
but they cannot pass the server-side owner and token checks.

Separation, expiry, character replacement, disconnect, authority revocation
and device end continue to clear the owned camera, visual effect and
cinematic before invalidating the canonical generation. Attack requests are
synchronous and cannot carry a pending asynchronous generation into a new
fusion. The attack cooldown resets only after teardown; the finite budget
cooldown still blocks immediate re-fusion.

## FUS-002 — Titan as experimental NPC proxy, not possession

Epic documents NPC Spawner + NPC Character Definition + Verse `npc_behavior`
and `navigatable.NavigateTo` for custom NPC movement. This supports an
**independently simulated NPC** following server-authorized commands. It
does **not** establish native player possession, transferring the player's
controller to the NPC, a custom player skeletal mesh or moving the orbit
camera's follow target to the NPC.

A future isolated prototype should keep FUS-002 disabled in the Architect
state machine and use a separate sandbox spawner (not a shared encounter
spawner). Bind the spawned NPC to the current owner and generation, then
consume bounded directional/target commands via owner-validated input.
The NPC's single `npc_behavior` should own navigation and cancellation;
do not run two competing `NavigateTo` loops. A titan attack must validate
range, target, faction and cooldown and use an explicit physical damage
adapter; no damage may follow an arbitrary input trigger alone.

The player remains an ordinary player character with native movement;
experimental proxy control could suppress or constrain player movement
**only if a supported native device and safe restoration are demonstrated**.
A fixed-point/third-person camera might provide a Titan viewpoint, but
tracking a dynamic custom NPC is unproven here and must not be claimed.
Network ownership remains server-authoritative Verse plus native NPC
replication; each remote client must observe the same NPC, animation and
damage result in a two-client Launch Session before any claim of correctness.

Cleanup requirements: record spawned agent and generation, cancel navigation
and combat tasks, restore the owner's camera/controls, despawn only NPCs
owned by the dedicated Titan spawner, release subscriptions, and reject
late spawn, attack and death callbacks after token invalidation. Never
`DespawnAll` on a shared world/encounter spawner. Test owner disconnect,
respawn, duplicate input, 2-client join-in-progress, concurrent ordinary
NPCs, streaming and memory budget. The feature remains **research only**
until those native proofs exist.

## Editor and source acceptance

1. Keep `Enabled=false`; provision the trusted owner reference and verify
   `CanWield` without any public registration path.
2. Bind three distinct Input Trigger devices, one dedicated Orbit Camera,
   dedicated per-player Visual Effect Powerup, instigator-only Cinematic
   Sequence, and a dedicated Attack Output Trigger. Configure the native
   player to retain movement and a comfortable camera.
3. Wire the output to an **Arsenal-reviewed** instigator-specific attack
   adapter, including target validation, hit/miss feedback, cooldown and
   accessibility cues. A triggered graph is not proof of damage.
4. Run `python tools/validate_sovereign_fusion.py`,
   `python tools/validate_fusion_attack_bridge.py`, and
   `python -m unittest tests.test_fusion_attack_bridge -v`.
   These are static/mutation checks, not Verse compiler tests.
5. Record exact source SHA, UEFN version, real Verse compile diagnostics,
   device bindings and two-client Launch Session footage. Check owner vs
   nonowner inputs, 10 rapid presses, 0/insufficient energy, token change,
   2 players attacking simultaneously, respawn, disconnect, rejoin and
   partial visual/attack adapter failures. Verify no leaked effects or
   cross-client/global damage. Keep publication blocked until proof exists.

## API references (official Epic documentation)

- Input Trigger: https://dev.epicgames.com/documentation/fortnite/verse-api/fortnitedotcom/devices/input_trigger_device
- Trigger device: https://dev.epicgames.com/documentation/fortnite/verse-api/fortnitedotcom/devices/trigger_device
- Orbit Camera: https://dev.epicgames.com/documentation/fortnite/verse-api/fortnitedotcom/devices/gameplay_camera_orbit_device
- NPC Spawner: https://dev.epicgames.com/documentation/fortnite/using-npc-spawner-devices-in-unreal-editor-for-fortnite
- NPC behavior: https://dev.epicgames.com/documentation/fortnite/understanding-npc-behavior-in-unreal-editor-for-fortnite

**Coordination:** Architect owns `fusion_state_runtime.verse`; Avatar owns
this input/presentation bridge; Arsenal owns physical damage and validated
ability effects; Cinematics owns authored VFX/audio/telegraph bindings; QA
owns independent mutation, native and multiplayer acceptance. Coordinate
via issue #37 and review this PR before any shared file edits.
