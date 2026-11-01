# Build change log

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
