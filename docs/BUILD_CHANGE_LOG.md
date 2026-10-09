# Build change log

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
