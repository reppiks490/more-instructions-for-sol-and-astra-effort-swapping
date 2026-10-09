# Owner-only appearance inside AEONFALL

`aeonfall_sovereign_appearance_device` applies a native Fortnite disguise to the sole verified Sovereign owner throughout the island session. It uses the same `Authority.CanWield` gate as Sovereign Unmaking and remains independent of the world event, so drawing or ending the ability does not grant or remove its appearance. The source defaults to disabled and grants nothing until the owner authority and physical device are securely configured.

The [official Disguise device](https://dev.epicgames.com/documentation/fortnite/using-disguise-devices-in-fortnite) replaces the native player's visible outfit with a selection from its supported combat or casual character catalog. An exact outfit remains unselected until the actual editor catalog can be inspected. Additional brand characters belong to their corresponding brand island projects. This implementation does not import an arbitrary original skin into the player's Locker, replace the native player with an NPC, or use the supplied character screenshot as design reference.

## Required editor binding

1. Place exactly one `aeonfall_sovereign_appearance_device`, one dedicated native `disguise_device`, and the existing sole Sovereign authority. Bind its `Authority` and `Disguise` to those actual placed instances. No other device should use this disguise device or directly grant its disguise.
2. Select a specific supported combat or casual character in **Disguise to Apply**. Do not use the random options when a consistent owner appearance is wanted.
3. Set **Apply Disguise on Player Spawn** to **False**, **Start Enabled** to **False**, **Disguise Breaks on Attack** to **Off**, **Disguise Breaks on Damage** to **Off**, and **Replace Existing Disguise** to **True**. Leave its team and class filters at **Any**; the authority gate, rather than a team/class selector, authenticates the owner.
4. Securely verify and provision the intended owner in the authority's native player reference, following [Sovereign Unmaking setup](SOVEREIGN_UNMAKING.md). Enable the appearance controller only after the physical binding and native checks below succeed.

Startup rejects a missing or true automatic-spawn option and an already enabled native disguise device before enabling anything. A session lease rejects duplicate appearance controllers. Rejected controllers never disable or clean up another controller's device. The controller does not register an owner, match a display name, assign an authentication team, apply to every player, or expose a public appearance grant input.

## Native reconciliation and cleanup

Every second the controller resolves an active native player and live character, then checks `Authority.CanWield`. It attempts replacement at most 16 times for a particular native character. Success requires the native `IsDisguiseApplied[Player]` check; `ApplyDisguise(Player)` returns void and alone provides no success evidence. A genuine native character change creates a new bounded respawn budget.

The original Locker outfit may be visible during initial spawn, the one-second reconciliation interval, or a refused or delayed native application. Zero visual gaps cannot be promised without editor and observer-client testing.

Revocation, elimination or disconnect clears the tracked appearance. Cleanup calls `RemoveDisguise(Player)` for an active tracked player, affecting only this device's disguise; a disconnected native player is no longer a live presentation target. OnEnd cancels maintenance, removes the owned disguise, disables only the acquired native rig and releases its session lease. Native `Disable()` alone does not remove a disguise.

The appearance controller never calls `fort_character.Show()` or `Hide()`, so it does not explicitly override the owner's unlimited veil. Whether applying or removing a native disguise while hidden changes visibility, equipment, effects or networking still requires a real Fortnite session check. Authored attack/damage break options must also be verified in the editor because no runtime getter for those settings is used here.

## Required native session evidence

- The verified owner receives the selected outfit before and after drawing Sovereign Unmaking; another player never receives it.
- Damage, attacks, weapon use, movement and ability effects preserve the intended appearance.
- Respawn uses the new native character, repeats the bounded application and preserves intended equipment.
- Clearing or replacing the authority's reference revokes the appearance within the one-second reconciliation interval; another player cannot inherit it.
- Applying and cleaning up the disguise while the owner is invisible does not unexpectedly reveal the owner. Test observer clients as well as the owner client.
- A duplicate controller and a native device configured for automatic spawn are rejected without touching the accepted rig.
- End/restart cleans up the disguise; no retry loop exceeds 16 attempts for the same live character.

`tools/validate_sovereign_appearance.py` and its mutation tests check source guards and authored policy. They do not compile Verse or prove any native session outcome. Compilation, exact catalog selection and Fortnite playtesting remain unexecuted.

Review this guide when the owner authority, native disguise API, catalog availability or retry/cleanup behavior changes. Source lives in `verse/sovereign/sovereign_appearance_device.verse`; the explicit binding policy is `content/sovereign/sovereign_appearance.json`.
