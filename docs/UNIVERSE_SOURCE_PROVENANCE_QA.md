# AEONFALL ∞ — Independent Full-Universe Source Provenance QA

**Authority:** creator's universe-first directive, master issue #84 and QA issue #89.  
**Scope:** all canonical major-entity packages, all 13 regional source packages, and all required cross-universe systems; **not** an early playable prototype.

## What this source gate verifies

The inventory in `content/implementation/universe_source_delivery_inventory.json` is the sole reviewed-delivery registration surface; catalog ideas and generator names do not count as native assets. The auditor must inspect every canonical ID, reject fabricated or missing file paths, and preserve distinct source/native completion states.

On the isolated QA branch, `tools/audit_universe_readiness.py` adds:

- Casefolded, whitespace-normalized uniqueness for approved entity `unique_visual_key` labels.
- Streaming SHA-256 content signatures over **complete visual file sets**, so two approved weapon/armor/creature source packs cannot substitute byte-identical visual assets under different filenames. Faction `visual_identity` source sets receive the same protection.
- Streaming SHA-256 signatures for each approved region's terrain file set; copying identical regional heightmap bytes under different paths does not count as a second independently authored terrain source.
- A deliberate exception for shared **nonvisual** family infrastructure: shared authoritative mechanics, behavior utilities and runtime tools are legal and do not invalidate separately authored entity visuals.
- Structured fail-closed errors for malformed unhashable source-registry IDs and region scopes, preserving the full backlog JSON where possible instead of terminating with a type error.

Content hashes are calculated from actual source bytes in bounded chunks rather than trusting filenames or self-reported hashes. The checks compare file sets, **not** artistic quality; a trivial unique marker file could still mask cloned geometry. Independent visual and gameplay review is mandatory before `source_review.state=approved_source` is entered.

## Verification and status semantics

- The complete catalog remains **840 currently authored definitions**, not 840 production-ready entities. Expand as genuine new entities are authored; never apply a sample ceiling.
- All **13** required regions remain individually in scope. A region's heightmap source alone does not provide its landmarks, ecology, encounters, quests, navigation, streaming, VFX/audio and mobile LOD.
- All **13** required universe systems remain in scope, including crafting and ascension, progression/entitlement, living factions, economy, owner-authorized fusion, multiplayer lifecycle and mobile accessibility.
- `--require-source-complete` intentionally fails until each reviewed package has all family-specific file-backed source categories.
- `--require-native-complete` remains a **separate** later gate; an approved source pack cannot claim a native Verse compile, imported assets, two-client replication, real mobile performance or Fortnite publication.

### Local commands

```bash
python -m unittest discover -s tests -p 'test_universe_first_readiness.py' -v
python tools/audit_universe_readiness.py --json dist/universe_coverage/full.json --markdown dist/universe_coverage/full.md
python tools/audit_universe_readiness.py --require-source-complete
python tools/audit_universe_readiness.py --require-native-complete
```

Only the **first two commands** are expected to succeed during source construction. The two strict completion gates must remain blocked until there is authentic evidence. Do not label a successful integrity-only workflow as complete-universe production.

## Future native acceptance — postponed by creator until source-wide milestone

Capture real Windows UEFN editor revision, Verse compiler diagnostics, full-region import and streaming bindings, native owner authorization, receipt/resource atomicity and rollback, NPC proxy navigation and safe teardown, camera restoration, bounded VFX/audio/telegraphs, two-client cross-player races, and touch/low-end Fortnite mobile results. The actual cooked publishing-memory measurement must be checked against the **300 MiB** threshold. Source calculations or Blender previews cannot replace that measurement.

## Workflow policy

No Codex usage or Codex-powered review, no unapproved spending, no force-push, no branch deletion, no new owner entitlement, no premature PR with automatic Codex integration, no island publication. Work on an isolated QA branch, coordinate with #85–#89 and existing five Omnigod owners. Preserve production branches and unrelated content.

## Limitations of these QA additions

SHA-256 equivalence of a full source file set catches exact clones, not near-duplicate meshes, duplicate visual scenes embedded inside distinct containers, trivial metadata changes, license defects or fake human reviews. Image/mesh inspection, provenance records, real build output, gameplay mechanics and eventual native execution must be verified separately. No source-only tool can honestly prove the island meets 300 MiB cooked memory or mobile framerate constraints.
