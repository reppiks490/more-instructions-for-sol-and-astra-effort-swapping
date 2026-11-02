# Sovereign Armor Fusion — two-step source implementation

This opt-in integration extends the existing **UNI-001** sovereign authority.
It does not create a new canonical class, grant a public unlock, change the
single persistent player profile, or modify Transcendent Zero/ Axiom Heart.

## Step 1: authoritative session fusion

`verse/sovereign/sovereign_fusion_runtime.verse` introduces a session-scoped
controller lease and armor-only state machine. A request must originate from
the single acquired controller, contain a live native player, and pass the
**existing** `aeonfall_sovereign_authority_device.CanWield` check. A single
session owner is latched and cannot be replaced by join order, team, display
name, a public button, or ordinary class progression.

The runtime admits one armor manifestation at a time, increments a generation
token for each admission, enforces 15–180 seconds and 30–120 starting energy,
and requires the prior cooldown to expire before re-entry. All energy spending
is atomic and token-bound (1–25 energy per request). Revoked, expired, swapped
or interrupted sessions must end and enter a 30–300 second cooldown. No
persistent progression changes. No claim of unlimited combat damage, immunity,
or native NPC possession is made.

## Step 2: native presentation and lifecycle bridge

`verse/sovereign/sovereign_fusion_device.verse` subscribes to two distinct
input triggers. After successful authority/runtime admission it applies a
dedicated **visual_effect_powerup_device** aura to the owner, pushes a
dedicated **gameplay_camera_orbit_device** onto that player's camera stack,
and plays an instigator-only **cinematic_sequence_device**. The owner can
separate with the second input. A 1-second maintenance loop rechecks native
authority, generation, original live character and finite energy. Timeouts,
owner disconnect, death/character replacement, revocation and device end
terminate the fusion and clean up only this device's camera/aura/cinematic.
Effects are requests to native devices and cannot by themselves prove that
the final cosmetic attachment worked.

This is an **Armor Fusion foundation**: it makes a normal player visually
glow, changes camera framing, and provides a controlled presentation handoff.
It does **not** import the concept's skeletal armor, replace the player's
native cosmetic mesh or grant physical NPC control. The Titan Fusion
proxy-control experiment must remain separate and disabled until validated.

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
