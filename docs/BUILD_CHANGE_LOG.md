## 2026-11-01 — Avatar FUS-001 attack request and Titan proxy feasibility

Extended the disabled-by-default Armor Fusion controller with a third
owner-gated attack input, bounded server-side energy cost/cooldown, canonical
generation validation and a dedicated instigator-scoped trigger output.
The player retains native movement and the existing owner-only orbit camera.
Added attack source/mutation tests, CI guard and a FUS-002 NPC-proxy
feasibility/cleanup design. Native hit detection, custom armor mesh, Titan
possession, Verse compile, editor binding and multiplayer Launch Session
remain unverified.

# Build change log

## 2026-11-01 — Runtime Forge: native input and volume subscription ownership

Added owned and canceled subscriptions to the self, targeted and position
ability-input devices. Empty ability IDs refuse startup; stopped callbacks
cannot request an activation. Encounter context volumes now track their own
one-per-agent admissions, reconcile already-inside agents and atomically
balance EnterEncounter/ExitEncounter so duplicates cannot inflate context
depth. Shutdown cancels native callbacks and releases only the volume's
tracked context contributions. The participant-volume bridge also retains
and cancels subscriptions and refuses blank encounter IDs, without erasing a
director's participant list. New mutation checks and editor acceptance guidance
cover stale callbacks, overlapping contexts and lifecycle teardown. This is
source-level validation only: native Verse compilation and Fortnite Launch
Session results remain unverified.


## 2026-11-01 — Fusion Reaver: transactional attack-receipt handoff

Wired the Architect's canonical FUS-001 one-use paid-attack receipt between
the merged Avatar AttackOutput and Arsenal TryRend. The upstream 10-energy
debit and one-second, generation-scoped receipt issuance now share one
deciding admission; refused issuance rolls back the debit before any
instigator-tagged trigger. Downstream TryRend consumes the receipt before
its additional 5-energy debit and cooldown in the same deciding transaction.
A forged/ambient Trigger(Player) alone cannot produce a paid Reaver strike.

This is source-level authorization, not native Verse compilation, real
line-of-sight collision, projectile hit confirmation, damage attribution or
two-client Fortnite verification. The native adapters remain disabled by
default until all these release gates are met.


## 2026-11-01 — Cinematics: original glTF mechanical motion and PCM cue sources

Added a deterministic DCC-preview animation pipeline for the 13-part original
Omnigod machine-demon geometry. It emits three genuine glTF 2.0 animation
clips (fusion, separation and dormant breathing), three original playable
16-kHz PCM WAV cues, and a hashed cue sheet with accessible telegraphs,
cancellation contract and distance-tier VFX design caps. A dedicated GitHub
Actions workflow builds and tests the downloadable source package. The editor
handoff covers separate Everyone-visible replaceable-NPC sequences versus
instigator-only player fusion, Niagara, Verse generation-token teardown,
LOD, memory and two-client acceptance. This is NOT a skeletal rig, native
Niagara/Sequencer binding, imported UEFN asset or playable transformation;
native tests remain pending.

## 2026-11-01 — Fusion Architect: one-use Reaver admission receipts

Added a session-local, generation-bound, one-second attack receipt to the
canonical FUS-001 fusion state machine. Receipt issuance and consumption
revalidate owner/controller and native authority, reject concurrent issuance,
and invalidate on every separation, abort and controller release. Documented
atomic Avatar upstream-cost issuance and Arsenal secondary-cost consumption;
their draft device adapters still require independent wiring and UEFN
verification before the feature can be enabled. Added source/mutation tests
for replay, expiry, authority, invalidation and contract evidence boundaries.
No persistence, canonical IDs, public unlocks or native enablement changed.


## 2026-11-01 — Omnigod: deterministic original 3D manifestation source

Built a 13-piece original, crimson-violet machine-demon static source-geometry
pack (GLB/OBJ/MTL and full assembled preview) from the audited Ossuary mesh
encoder. A dedicated source-artifact workflow now validates watertight geometry,
fixed source/Unreal coordinate mappings, real exported material/part files,
SHA-256 inventories, repeatability, safe collision policy and honest native
proof boundaries. The independent validator and mutation tests run in CI.
The production handoff describes converting the blockout into a rigged FBX
Custom NPC, with separate instigator-only player fusion and Everyone-visible
replaceable NPC Sequencer bindings. No native UEFN import, rig, NPC possession
or Launch Session has been claimed.


## 2026-11-01 — Living World: enforce bounded wave retirement

The invasion NPC adapter now rejects `DespawnOnRelease = false` at startup
before leasing or touching native spawners. A disabled retirement despawn
could otherwise retain old-wave NPCs alongside the incoming wave and violate
per-wave authored AI reserves. Existing physical ownership/terminal cleanup
is unchanged. Added source regression cases and UEFN negative-config and
multiplayer acceptance guidance. No new waves, spawners or NPCs were added.
Native engine and streaming evidence remains unverified.


## 2026-11-01 — Runtime Forge: loadout reconnect generation isolation

Mirrored the checkpoint reconnect-safety pattern in the player loadout
device. A bounded readiness waiter now carries a distinct generation token;
disconnect and device shutdown invalidate older requests. An old waiter
cannot act on the rejoined player or clear the new request's pending slot.
OnEnd now cancels listeners before relinquishing exclusive session ownership.
Static guard checks, mutation tests and a native multiplayer acceptance case
were added. Persistent player schema and equipment policies are unchanged;
UEFN compile and Launch Session evidence remain unverified.



## 2026-11-01 — Living World: hard terminal invasion NPC cleanup

Verified that existing terminal completion/failure events already reach the
canonical owned NPC adapter, so duplicate release events were unnecessary.
Closed the remaining physical lifecycle gap: successfully owned terminal
completion, failure/timeout and adapter shutdown now despawn their NPC bodies
regardless of the optional intermediate wave-release configuration. Ownership,
region, active requester and terminal-state guards are unchanged. Added
source tests and UEFN two-player/streaming acceptance instructions. No new
encounter directors, AI spawners or gameplay stat scaling were introduced.
Native Verse compilation and physical NPC counts remain editor verification.


## 2026-11-01 — Runtime Forge: profile bootstrap lease and truthful NPC removal

The persistence bootstrap now acquires exclusive session ownership before
subscribing to player events or initializing profiles. Duplicate placed devices
fail closed, callbacks stop before lease release, and the existing single
persistent player root remains unchanged. NPC lifecycle OnEnd now emits
`npc.removed` only following a successful runtime-key unregister; failed
registration or failed teardown cannot masquerade as a successful removal.
Source mutation coverage and native Launch Session acceptance steps are in
[the lifecycle acceptance guide](FIRST_PLAYABLE_LIFECYCLE_ACCEPTANCE.md).
Native Verse compilation and physical multiplayer execution are unverified.


## 2026-11-01 — Sovereign Armor Fusion adapter and bounded budget

Added the creator-only FUS-001 physical presentation prototype atop the
Fusion Architect's canonical `fusion_state_runtime.verse` phase contract.
A dedicated session budget enforces finite energy, duration and cooldown
without duplicating owner identity or phase state. The native adapter
requests owner-specific visual glow, orbit camera and cinematic playback,
then restores effects on separation, revocation, disconnect, death,
character replacement, timeout and device end. A source validator,
24 mutation tests, UEFN editor binding instructions and multiplayer
acceptance matrix were added. Device defaults disabled; owner provisioning,
native Verse compilation, actual custom armor mesh and multiplayer Launch
Session remain unverified.


## 2026-11-01 — Fusion Architect: creator-only state and cross-loop contract

Added a session-scoped fusion state service with a single leased controller,
native Sovereign authority rechecks, immutable session owner, monotonic
generation tokens and explicit Dormant/Activating/Active/Separating transitions.
Stale callbacks, duplicate activation, cross-player operations and unsupported
Titan activation are rejected by source guards. Cleanup and controller release
remain callable after authority revocation, but physical adapter teardown is
still a required future handoff. A machine-readable contract, source validator,
14 mutation tests, CI gate and cross-loop ownership guide coordinate Avatar,
Arsenal, Cinematics and QA work (issue #37). No persistent profile schema,
existing UNI-001 entitlement or canonical progression was modified.
Native UEFN compilation, editor binding, multiplayer execution, physical
fusion effects and publication remain unverified.

## 2026-11-01 — Runtime Forge: actor bootstrap lease and transactional activation cancellation

Player identity bootstrap now acquires an exclusive session lease before subscribing to join/remove events or enumerating existing players. Only the owner can release that lease after canceling callbacks. This prevents duplicate bootstrap devices from duplicating identity-ready notifications or racing player removal.

Activation result handling now stops before resource settlement when coordinator pending-record removal fails. Pending-request cancellation now uses a failable Verse transaction for pending-map removal, canonical cancellation, and conditional class reservation release. Source mutation checks and native multiplayer acceptance scenarios are documented in [first-playable lifecycle hardening](FIRST_PLAYABLE_LIFECYCLE_HARDENING.md). Native UEFN compiler, device binding, and Launch Session evidence remain outstanding.


## 2026-11-01 — QA: checkpoint reconnect generation isolation

Hardened the new SLICE-001 checkpoint device against suspended restore tasks
outliving their player session. Per-request generation tokens are invalidated
on disconnect and device teardown; only the current task can request a native
teleport or clear pending restoration. Added source mutation tests for stale
rejoin, cross-generation cleanup, disconnect invalidation and shutdown. This
remains source-level evidence; multiplayer Fortnite Launch Session is required.



## 2026-11-01 — QA: reject invalid world-event transitions

The shared world-event runtime now rejects empty event/objective identities
and noncontiguous stage jumps. Added fail-closed source checks in the runtime
invariant validator and mutation coverage for stage ordering, active-state
authorization, terminal region cleanup, reward sequencing and failed-event
participation cleanup. UEFN native runtime and streaming evidence remain open.


## 2026-11-01 — QA: checkpoint reconnect generation isolation

Hardened the new SLICE-001 checkpoint device against suspended restore tasks
outliving their player session. Per-request generation tokens are invalidated
on disconnect and device teardown; only the current task can request a native
teleport or clear pending restoration. Added source mutation tests for stale
rejoin, cross-generation cleanup, disconnect invalidation and shutdown. This
remains source-level evidence; multiplayer Fortnite Launch Session is required.



## 2026-11-01 — Living World: faction pressure and battle admission

Faction-led REG-001 invasions now require canonical aggressor influence at
admission: FAC-002 >=30, FAC-004 >=20 and FAC-007 >=15. Existing faction-war
influence transfers (+20 winner, -10 loser) can therefore close or reopen
future invasion windows without stat inflation. Ecology invasions keep their
zero influence gate. Bounded authoring validation, generated bootstrap parity
and source regressions cover the optional admission field.

Invasions and faction conflicts now mutually refuse admission while the other
encounter family has an active battle in that region. Two faction conflicts in
the same region are likewise refused. Conflict admission now requires an
initialized canonical region. No extra director, AI allocation, or persisted
player state is introduced. Native Verse compilation, physical spawner
exclusivity, multiplayer admission order and streaming-cell behavior require
UEFN Launch Session verification.



## 2026-11-01 — QA: reject invalid world-event transitions

The shared world-event runtime now rejects empty event/objective identities
and noncontiguous stage jumps. Added fail-closed source checks in the runtime
invariant validator and mutation coverage for stage ordering, active-state
authorization, terminal region cleanup, reward sequencing and failed-event
participation cleanup. UEFN native runtime and streaming evidence remain open.


## 2026-11-01 — QA: checkpoint reconnect generation isolation

Hardened the new SLICE-001 checkpoint device against suspended restore tasks
outliving their player session. Per-request generation tokens are invalidated
on disconnect and device teardown; only the current task can request a native
teleport or clear pending restoration. Added source mutation tests for stale
rejoin, cross-generation cleanup, disconnect invalidation and shutdown. This
remains source-level evidence; multiplayer Fortnite Launch Session is required.


## 2026-11-01 — Playable Slice: persistent Ossuary checkpoint/respawn runtime

Added a project-bindable four-checkpoint Verse device with distinct volume,
teleporter and spawner preflight, a single session owner lease, contiguous
checkpoint discovery, checked immutable-profile saves, and bounded
character-spawn/rejoin restoration. Progress is stored only in the existing
DiscoveredPoiIds field; transient character tracking is removed on leave and
device shutdown. The source contract pins each checkpoint to the authored
Ossuary geometry anchors without inventing editor object paths. A new
validator, mutation tests, CI step and Windows editor/Launch Session handoff
document cover sequential unlocks, save refusal, repeat entry, respawn and
multiplayer rejoin. Native Verse compilation, actual teleporter arrival,
collision/navmesh and Fortnite session tests remain unverified.


## 2026-11-01 — QA Sentinel: enforce generated status drift in CI

AEONFALL Validation now runs `tools/build_status.py --check` rather than
regenerating STATUS.md and suppressing the Git diff exit code. Catalog and
endgame summary drift is now a failing check; authors must regenerate and
commit the canonical status snapshot before merge. This is a source-level
consistency gate, not native UEFN compilation or runtime profiling.

## 2026-11-01 — QA Sentinel: fail-closed source provenance

The source ZIP verifier now rejects rewritten build provenance that claims
native UEFN compilation, editor import, Fortnite Launch Session, or a published
island code. It validates required provenance fields, commit/tree identifier
shapes, and source-check status values; it also rejects missing metadata before
reading it. Regression tests regenerate valid checksums around forged evidence
to verify the fail-closed behavior. These are source-package integrity checks,
not a cryptographic signature, native Verse compilation, or publication proof.


## 2026-11-01 — Runtime Forge: preflight actor teardown before cleanup

The session actor registry now rebuilds and validates all three replacement
identity maps before clearing dependent gameplay state. Previously a failed
map reconstruction could leave an actor registered while its pending ability
requests, statuses, companions and other session state had already been
destroyed. A failed preflight now returns without teardown. The registered
identity predicate also checks the agent-to-key reverse mapping, rather than
accepting a forward-only entry. Source mutation tests cover both invariants.

This changes no persistent player schema, authored IDs, or editor assets.
Native Verse compilation and NPC/player lifecycle Launch Session evidence
remain outstanding.

## 2026-11-01 — Arsenal Ascension: atomic Axiom Heart final forge

Implemented the canonical RCP-013 Throne of Zero final craft using a generated,
source-checked twelve-material cost vector. The server-side forge requires the
existing Level 1000, mastery, Absolute and Trials I–IX gates, rejects duplicate
or pre-existing apex output, and acknowledges one persistent profile write for
all ingredient debits, MAT-030 creation, and AxiomHeartCrafted=true. A refused
write cannot grant the Heart or emit success. The legacy flag setter is disabled.
A project-bound button adapter owns and cancels its subscription. Seven source
regression checks cover generation, gates, debits, save ordering and cleanup.
Refined component production RCP-001–012/014 and the actual Throne of Zero
editor placement remain separate work; no native Verse compile or Launch
Session has been performed by this change.

## 2026-11-01 — Playable Slice: source-pinned physical binding audit

Added a fail-closed, source-pinned editor inventory for the 49-device
BOS-005 first-playable rig and its 42 exclusive physical encounter roles.
The audit compares observed editor object paths, device classes, director
links, project/level identity, source contract hashes and optional captured
editor-output SHA-256. Missing, aliased or mismatched placements are rejected.
The checklist carries all 24 canonical Launch Session IDs without treating
self-reported passes as native evidence. Twelve source-only regression tests
cover identity drift, physical aliases, wrong classes, wrong links, stale
contracts and evidence provenance. No editor placement, native Verse compile
or Fortnite Launch Session was performed by this change.


## 2026-11-01 — Runtime Forge: exclusive result-router subscriptions

The ability-effect result router and physical unlock-delivery result router
now each acquire a session-retained exclusive subscription lease before
listening to the shared event bus. Duplicate placed devices fail closed,
preventing duplicate result callbacks and misleading unresolved-result
telemetry. Only the owner cancels its listener and releases the lease during
teardown. Added source-mutation regression coverage and explicit native
duplicate-device, owner-shutdown and replacement acceptance scenarios.
The leases are independent and do not alter player persistence or ability
cost semantics. Source tests and GitHub CI do not prove native Verse compilation,
UEFN editor bindings or a Fortnite Launch Session.

## 2026-11-01 — QA Sentinel: source-manifest provenance integrity

The source-package verifier now rejects duplicate and noncanonical manifest source paths and checks each declared Git blob object ID against the actual archived source bytes. Regression fixtures rewrite both the manifest and its checksum inventory to ensure self-consistent forged metadata is rejected. This verifies internal source provenance consistency; independent commit authenticity and native UEFN compilation remain separate gates.

## 2026-11-01 — Living World: corpse denial changes canonical corruption

Burn (-2), sanctify (-4), and necromancy (+5) now use the existing regional
corruption/hostility/mutation reconciliation before an exclusive corpse token
is removed. Harvest remains corruption-neutral. Missing canonical region
state fails closed for the three pressure-changing uses; the test-only
unregistered horde service keeps its prior behavior. No new director, actor
population, persistent player field, or stat multiplier was introduced.
Added source regression tests and a UEFN threshold/multiplayer acceptance plan.
Native Verse compilation and physical encounter/biome effects remain unverified.


## 2026-11-01 — Arsenal Ascension: authoritative one-use-per-form epochs

The ability runtime now guards each canonical God/Absolute ability with an
owner-scoped, active-form activation epoch. Pre-dispatch checks reject repeat
uses; each in-flight request records its originating epoch, and adapter-result
handling rechecks the form and commits the ability state
and use ledger atomically. Failed effects do not spend the use, ending a
managed effect cannot refund it, and owner teardown drops ledger state.
Added ten source mutation guards. Canonical IDs and one-use quotas are
unchanged; Transcendent Zero remains separate and unbound. This does not
claim native Verse compilation or a functional apex physical adapter.

## 2026-11-01 — Arsenal Ascension: close generic adapter apex bypasses

Centralized transformation-bound preflight detection across exact IDs, legacy
transformation flags and TransformationOnly resource policies. Generic trigger,
status and composite adapters reject apex effects before physical dispatch;
prop spawning and Royal Scent challenge setup also fail closed for transformed
definitions. Added source mutation tests. Canonical IDs and content quotas are
unchanged. This is source-level hardening, not a native Verse compile or a
functional apex effect adapter.

## 2026-11-01 — Living World: exclusive invasion NPC ownership

The REG-001 invasion spawn-group adapter now acquires a session-scoped lease
before disabling any native NPC Spawner. Duplicate region/group adapters,
duplicate spawners within a binding and cross-group shared spawners fail closed
without touching the legitimate owner's devices. Only a leased adapter may
subscribe, disable, despawn or release its devices on shutdown.

Invasion release events are checked against the authoritative current wave:
delayed old-wave releases cannot disable reused groups. Terminal cleanup
notifications require the canonical invasion's completed/failed state. Added
source regression guards and updated the UEFN physical-binding acceptance
checklist. This is a source-level hardening change; native Verse compilation,
editor streaming behavior and actual NPC concurrency remain unverified.


## 2026-11-01 — Runtime Forge: one authoritative session clock

Added an exclusive, session-retained lease to the canonical runtime tick
Creative device. A second accidentally placed scheduler now refuses startup,
so it cannot double-advance ability cooldowns, status durations, encounter
state, horde/invasion waves or delivery timeouts. OnEnd releases the lease
only for the device that acquired it; rejected duplicates cannot stop the
active scheduler. Added source invariant and mutation regression coverage.

This change preserves the elapsed-simulation-time delta and existing service
order. It does not claim a native Verse compile or Fortnite Launch Session.
A private editor test must place two clocks, confirm only one advances,
end the owner, and verify a replacement can acquire the lease.


## 2026-11-01 — Arsenal Ascension: bounded apex contracts and fail-closed generic triggers

Added ten canonical God/Absolute mechanical contracts with explicit effect quotas, telegraph/counterplay, distinct planned audiovisual cues, class synergy, boss immunity and destination preflight requirements. The generic trigger adapter now rejects all transformation-bound abilities before physical dispatch; only specialized validated adapters may report success. Added cross-catalog validation and mutation tests. These contracts are specified and unbound, not UEFN-compiled or Launch Session verified.\n
## 2026-11-01 — Living World: regional invasion admission and AI reserves

Hardened REG-001 invasion admission without adding a parallel world director.
The runtime now rejects concurrent invasions in the same region, reserves the
canonical region event before committing active state, and accepts only
registered invasion objectives. Physical spawn adapters require matching
canonical region and active wave and clean up their owned spawners on shutdown.

Fixed three REG-001 group caps so every authored invasion wave fits its own
declared concurrent-AI reserve; validation now rejects over-budget and
duplicate-group waves. The new policy regression tests cover the authored
allocation and source-level admission guards. Physical NPC Spawner counts,
streaming behavior, Verse compilation and multiplayer Launch Session remain
editor verification gates; source checks do not prove those results.

## 2026-11-01 — Runtime Forge: checked material spends and atomic dev seeding

Inspected current `main` and open pull requests (none open at start of
this pass). The material ledger's generic `Spend` and `TrySpendMany`
previously called unchecked void profile setters; `TrySpendMany` could
return success even when persistence refused the write. Both paths now
require `TrySaveProfile` acknowledgement before success.

The first-slice dev harness formerly wrote three materials and reputation
separately and always displayed success. It now builds one immutable profile
candidate, commits once, and reports success only on an acknowledged save.
The first-play source guard and mutation tests cover these invariants.

This change does **not** claim an actual UEFN Verse compile, project import,
or Fortnite Launch Session. Those remain required for production readiness.


## 2026-10-08 — continue the build through the live gameplay path

Requested by the project owner in this chat: continue AEONFALL to completion using the granted access. Implementation and review are performed by the root Codex agent and the gameplay, Verse reliability, encounter and world/editor specialists. No new approval is required for these source changes.

The prior saved build was an authored source/import starter: modular dungeon geometry, catalog definitions, logical gameplay services and partial device adapters. It had no editor-produced UEFN project or observed native compiler/session result. The audit found that player classes had no live activation path, targeting and renewable class/meter resources had missing producers, and some physical item delivery could follow an unconfirmed persistent write.

This change connects player loadouts and checked delivery, provides an input-driven NPC selector and elimination-backed corpse harvesting, makes class transitions atomic, and supplies a native prop-spawn provider for the first position abilities. Switching classes retains spent session resources. Ordinary corpse materials provide a route into the existing recipe and faction systems; boss-only materials remain encounter rewards. The [first playable loop guide](FIRST_PLAYABLE_LOOP.md) records the acceptance checks and the source mechanisms.

Source delivery now packages the exact committed tree after successful validation, checks the bytes and inventory, and includes explicit provenance. [Source delivery](SOURCE_DELIVERY.md) is the operational home for download and integrity instructions. The artifact is intended for review and import; use actual UEFN output as the evidence for a playable island.

The earlier executor failure required saving authored source through GitHub. The restored Linux executor now supports local integration and source tests. It has no Windows UEFN editor or native Verse compiler. Plugin discovery for UEFN and Unreal returned no matching integration; discovery against the documented localhost MCP endpoint returned connection refused. Editor setup automation discovers actual advertised schemas and does not guess project metadata or device properties.

Verification of this change is pending its GitHub Actions run. Successful artifacts record the exact tested commit and run automatically in `BUILD_PROVENANCE.json`; engine import, compile and Launch Session remain explicitly `not_run` until their real outputs are observed. Source guards, mutation tests and bundle corruption tests are separate from native gameplay acceptance.

The implementation preserves the current persistent schema. Mutable runtime state is session-only. Reverting the source change does not require inventing or rewriting a published save schema. Persistent compatibility must be reviewed before the first island publication.

Review the current-state guidance when editor availability changes, a source guard or native test exposes a defect, item mappings change, or an engine update changes the supported APIs. This historical record describes why the source change was made; the linked guides and generated provenance carry current behavior and verification.

## 2026-10-09 — unique sovereign event and integration hardening

The creator requested a single exclusive power with red-void skies, regional
maelstroms and rifts, an obeying monster army, mandatory tribute/resistance
quests and unlimited invisibility. [Sovereign Unmaking](SOVEREIGN_UNMAKING.md)
implements these native-device control paths with a single-caster session
lease, bounded army/spawn budgets, transactional tribute and termination
cleanup. Owner access defaults to disabled until a trusted native-player
reference is provisioned; no Epic identity API or account match is invented.

The player loop now checks profile saves before grants and retains deferred
delivery when the event queue is full. Encounter directors reject duplicate
physical roles before touching shared devices and accept native prop-destruction
objectives from living participants. A typed first-playable rig describes
physical bindings. The editor MCP bridge pins discovered tool schemas and
records actual call results; no editor was found on this machine.

Mutable gameplay services are being moved into retained session accessors for
current UEFN compatibility. Independent review also identified status effects
that did not reconcile a new character after respawn; the bridge now discovers
canonical status state and tracks the physical character. Source and mutation
checks are run locally and in CI; actual compiler and session verification
remain separate acceptance requirements.

## 2026-10-09 — replace the owner's outfit inside AEONFALL

The creator asked to appear differently from their current Fortnite character.
Current Epic documentation exposes a native `disguise_device` that replaces a
human player's cosmetic outfit with an available disguise. The owner appearance
adapter uses the existing single-owner authority, reapplies after respawn, and
removes only its own disguise when access ends. It confirms native applied state
instead of treating a void `ApplyDisguise` call as proof of success.

The source and policy leave automatic all-player spawn application off and
require a fixed disguise from the actual editor catalog. Arbitrary uploaded
player skins are not documented by this device; custom NPC meshes and visual
proxies are not claimed as supported native-player replacements. The original
screenshot supplies owner identification only. It is not used to design the
replacement appearance. Physical outfit choice and multiplayer/veil verification
remain editor acceptance checks.


## 2026-11-01 — Living World: fail-closed horde spawner and identity admission

- Guarded horde adapter startup against unbound, game-start-enabled (declared),
  and invalid corpse-biomass configurations before any spawner is enabled.
- Require canonical identity agreement when an NPC lifecycle behavior has
  already registered the spawned agent; recheck it on delayed death callbacks.
- Added focused Python source regression checks and updated UEFN acceptance
  instructions. Physical editor settings, native Verse compilation, streaming,
  and multiplayer behavior remain unverified.
