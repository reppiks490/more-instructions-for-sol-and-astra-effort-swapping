# Sovereign Unmaking — UNI-001

One ability, one provisioned owner. Drawing it announces the sovereign to the
whole island, starts a red-void sky sequence, opens regional maelstroms and
rifts, and recruits eligible living monsters into an army. Everyone else
receives **Tribute or Unmaking**: pay 40 Ossuary Resin, or defy and stop the
sovereign before the three-minute manifestation ends. The owner can hide and
reveal at will, with no resource cost or cooldown, even outside a manifestation.

The implementation is in `verse/sovereign/`. The authored contract is
[`sovereign_unmaking.json`](../content/sovereign/sovereign_unmaking.json).
This source has not been compiled or played in Fortnite. Sky animation, VFX,
NPC Character Definitions and physical bindings must be authored in UEFN.

## Bind the one owner

The creator identified **User-f4d40f7823**, the player shown in their supplied
Fortnite screenshot, as the intended sole owner of the god status. This is
recorded in [`owner_identity.json`](../content/sovereign/owner_identity.json).
The character's cosmetic appearance is not design material or an access key.

Both the controller and authority start disabled. The authority accepts one
native `player` held by its configured Player Reference device, latches that
identity for the session, and checks the current reference on every use.
Clearing, replacing or disconnecting the owner revokes the grant. Duplicate
authority devices are refused. Display names, teams and join order never grant
access. There is no public claim button or authority `Register` method.

**The reference must be populated through a trusted operator-only provisioning
path after verifying the owner's actual Epic account.** Do not connect it to
public spawn events, public buttons, score conditions or an ordinary class
selector. The reference API identifies a session player; it does not establish
that player's Epic account ID. No unsupported Epic-account lookup is assumed.
Without verified provisioning, leave both devices disabled. Owner identity is
still awaiting the creator's account information and an actual editor/session.
The supplied source therefore does not claim production account authentication.

## Assemble the manifestation

Place one authority and one controller. Bind three distinct input devices for
Draw, Veil and Dismiss; three separate HUD devices; an individual nonpersistent
tracker; tribute and defiance altar buttons; and a nonpersistent global HUD
timer. Configure the cinematic sequence for **Everyone** and restoration of
the previous sky state on stop. Author red illumination, dark void clouds and
rifts in that sequence and the regional VFX devices.

Each configured region needs two distinct VFX spawners and an exclusively
owned NPC spawner. Disable timer spawning and spawn-at-game-start. Set spawn
capacity to the finite regional burst. Bind the shared sovereign monster
behavior to every eligible world monster Character Definition and provide its
normal-state patrol device with real anchors. This behavior switches between
normal navigation and following the sovereign; competing independent behavior
loops will prevent reliable allegiance. Protected boss encounter actors remain
under their encounter director.

The default budget is 64 commanded monsters, at most eight region bindings,
and four rift creatures per region. Increasing the command budget cannot exceed
96. These caps keep the event finite; they require memory and multiplayer
performance measurements in the editor before release. Native team membership
changes allegiance; native navigation gathers the army. The event restores
original teams and stops commanded navigation when it ends.

## Quest and termination

Tribute transfers canonical material between two checked profiles in one Verse
transaction. A refused save rolls back both writes. Paid players are spared for
that manifestation. Defiance offers a concrete counterplay objective: eliminate
the sovereign. Late joins and replacement characters receive the current quest
snapshot, with a minimum exposure grace period. The owner is exempt.

By default, Unmade is an in-session quest outcome. The authored
`EnableUnmakingElimination` option additionally eliminates explicit defiant
players after sufficient exposure. It does not delete profiles or account
progress. Dismissal, owner elimination, disconnect, lost authorization, timeout
and session end stop the world event. Cleanup restores visibility, sky control,
teams, quest presentation and exclusively owned rift NPCs. Failed live team
restores remain queued for maintenance rather than being silently forgotten.

## Required Fortnite checks

Test owner and non-owner input separately, changed/cleared references,
duplicate authority/controller placement, draw spam, unlimited Veil toggles,
owner death while hidden, respawns, late joins, tribute save refusal and repeat
payment. Observe the actual Everyone sky sequence, persistent quest and HUD
timer. Check army gathering, allegiance and restoration after each termination
path. Test wrong spawner configuration and maximum monster budgets. Record
native Verse compilation and a multiplayer Launch Session before describing
UNI-001 as playable.

Verified API references:
[Player Reference](https://dev.epicgames.com/documentation/en-us/fortnite/verse-api/fortnitedotcom/devices/player_reference_device),
[GetAgent (returns an option)](https://dev.epicgames.com/documentation/en-us/fortnite/verse-api/fortnitedotcom/devices/player_reference_device/getagent),
and [IsReferenced](https://dev.epicgames.com/documentation/en-us/fortnite/verse-api/fortnitedotcom/devices/player_reference_device/isreferenced).
