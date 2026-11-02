# First-playable profile/NPC lifecycle acceptance

The authored source must not be described as a working Fortnite island until
it compiles in the actual UEFN project and passes native Launch Session tests.

## Exclusive profile bootstrap

Place **exactly one** `aeonfall_profile_bootstrap_device` in production.
Its session lease is acquired before PlayerAdded subscriptions or any profile
initialization. A duplicate device rejects startup. All callbacks require
`Running`; OnEnd stops callbacks, cancels subscriptions, then releases the
lease only if the current owner is Self.

**Private UEFN checks:** place two bootstrap instances and join with two
clients simultaneously. Confirm only the owner initializes/refreshes player
profiles. Remove the rejected duplicate and confirm the owner still works.
End the owner and start a replacement: verify a newly joining player receives
exactly one initialized root and existing material/unlock/class/checkpoint
fields survive. Test a refused profile write: no false-ready announcement.
Only the existing `AEONFALLPlayerProfiles` player weak_map is permitted.

## Truthful NPC teardown

`npc.spawned` is emitted only after registry registration. `npc.removed`
is now emitted only if `Unregister(RuntimeKey)` confirms success. An NPC
whose registration failed has no key and emits no phantom removal. A failed
unregister emits `npc.runtime_identity_cleanup_failed` instead, retaining
the observed failure for diagnosis rather than signaling completion.

**Private UEFN checks:** bind an NPC Character Definition and actual Spawner
with the correct nonempty canonical ID. Spawn two instances with the same
canonical ID and confirm different runtime keys. Despawn only one: observe one
matching `npc.removed` and unaffected second-instance statuses, targets and
encounter state. Force registration failure with a blank/mismatched identity:
do not observe `npc.removed`. Exercise a failed teardown and verify it
reports cleanup failure rather than a false removal. Repeat on despawn/rejoin
and with multiple connected players.

## Source checks versus native execution

`python -m unittest tests.test_first_playable_profile_npc_lifecycle -v`
runs mutation/structural checks. GitHub AEONFALL Validation also discovers
the file via `unittest discover -s tests -v`. Neither checks Verse compiler
diagnostics, physical NPC presentation, multiplayer replication, Epic editor
asset bindings, or an actual Fortnite Launch Session. Record those independently
with exact installed source SHA, editor version, error logs and a native run.
