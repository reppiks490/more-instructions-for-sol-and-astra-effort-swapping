# Sovereign Armor Fusion — two-step source implementation

This opt-in integration extends the existing **UNI-001** sovereign authority.
It does not create a new canonical class, grant a public unlock, change the
single persistent player profile, or modify Transcendent Zero/ Axiom Heart.

## Step 1: integrate the canonical fusion architect state

The canonical FUS-001/FUS-002 phase machine is owned by
`verse/sovereign/fusion_state_runtime.verse` in **Fusion Architect PR #42**.
This follow-on adapter intentionally does NOT introduce a second owner or
alternative phase machine. It acquires the canonical single-controller lease
using the existing native `aeonfall_sovereign_authority_device`.
`BeginActivation(Self, Player, "FUS-001")` is the only admission path;
FUS-002 stays explicitly disabled until a supported Titan control design
passes native verification.

`verse/sovereign/sovereign_fusion_runtime.verse` is a separate *budget
ledger only*, not an alternative fusion owner/phase state. It persists per
Verse session, grants 30–120 initial energy for 15–180 seconds, enforces
a 30–300 second cooldown, and accepts individual 1–25 point spend requests
only after `State.IsAuthorizedActive` checks the exact owner, leased
controller and generation. Controller replacement does not reset cooldown.
No new persistent player flags or canonical unlocks are introduced.

## Step 2: native presentation and lifecycle bridge

`verse/sovereign/sovereign_fusion_device.verse` subscribes to two separate
player inputs. After successful canonical FUS-001 admission and resource
reservation, it requests a dedicated visual powerup effect, orbit camera and
instigator-only cinematic for the verified owner. The powerup's
`HasEffect[Player]` provides a limited native acknowledgement before
`ConfirmActivated`, but the device API may recognize other effects of the
same type: dedicate the asset exclusively and verify real-client visuals.

A one-second loop checks that the canonical fusion remains authorized,
the native character has not changed, and the budget has not expired. It
spends one point per tick. On any rejection, expiry, owner separation,
disconnect, defeat, revocation or device end, the adapter restores its
owned physical presentation BEFORE completing/aborting canonical fusion
state. On separation it also applies the resource cooldown.

This is **not a custom imported playable armor mesh, arbitrary outfit swap,
NPC possession, or validated Titan Fusion**. No actual editor assets,
Character Definitions, imported meshes or native tests are claimed.

## Required editor setup before enabling

1. First complete owner verification and trusted native player-reference
   provisioning from [Sovereign Unmaking](SOVEREIGN_UNMAKING.md). Current
   `owner_identity.json` is *not* verified. If not verified, leave the
   authority, fusion controller and physical effects disabled.
2. Place exactly one new fusion controller and bind **the existing** single
   authority device. Give it two separate input trigger devices. Do not expose
   a public entitlement-grant button or wire the owner reference to player
   spawn/any-team registration.
3. Bind a dedicated visual effect powerup configured for a per-player glow or
   outline. Prevent public pickup or automatic granting through its physical
   island settings; do not reuse a gameplay powerup already used elsewhere.
   Confirm `Pickup(Agent)` and `Clear(Agent)` target only the authorized
   player's effect in a real multiplayer session.
4. Bind a dedicated orbit camera. Do not use another gameplay system's camera.
   Configure a comfortable third-person view and ensure that its source
   defaults are suitable for per-agent `AddTo` / `RemoveFrom`.
5. Bind a dedicated fusion cinematic sequence set to **instigator only**;
   author the core ignition, segmented armor awakening, crimson-violet solar
   aura, and audio in the actual editor. The sequence cannot be assumed to
   have those assets until they are created and bound.
6. Set `DurationSeconds=90`, `CooldownSeconds=90`,
   `InitialEnergy=100`. Verify device uniqueness and ownership of the
   physical bindings before setting `Enabled=true`.

## Native acceptance tests

- Nonowners and unprovisioned players never fuse; duplicate controller is
  rejected; another player cannot trigger separation for the owner.
- Rapid repeated input cannot start a second fusion, overwrite an energy
  balance, or bypass cooldown.
- An old generation cannot spend resources after separation and re-entry.
- Every exit restores camera, effect and cinematic **without** changing
  other players' appearance or the original sovereign Veil visibility.
- Revocation, disconnect, defeat, respawn, expired deadline and session
  shutdown each trigger restoration; rejoining cannot inherit a grant.
- Test two clients with simultaneous inputs, standing near the dormant
  Omnigod NPC, and prove only the designated owner receives presentation.
- Measure input latency, replication, camera stability, VFX visibility,
  memory, streaming and ability interaction during Fortnite Launch Session.
- Record actual Verse compiler diagnostics and observable before/after
  footage or logs; do not promote to implemented or production on Python
  source tests alone.

## Supported API boundaries

- [Input Trigger](https://dev.epicgames.com/documentation/fortnite/verse-api/fortnitedotcom/devices/input_trigger_device)
- [Visual Effect Powerup](https://dev.epicgames.com/documentation/fortnite/verse-api/fortnitedotcom/devices/visual_effect_powerup_device)
- [Orbit Camera](https://dev.epicgames.com/documentation/fortnite/verse-api/fortnitedotcom/devices/gameplay_camera_orbit_device)
- [Cinematic Sequence](https://dev.epicgames.com/documentation/fortnite/verse-api/fortnitedotcom/devices/cinematic_sequence_device)

Source validators: `tools/validate_sovereign_fusion.py` and
`tests/test_sovereign_fusion.py`. They inspect authored contracts and
mutations, **not** Verse compile or native multiplayer execution.
