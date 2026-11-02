# AEONFALL — Sovereign Fusion native UEFN binding handoff

**Status:** Authored source, native editor observations missing. This is an
engineering installation aid, **not evidence** of a compiled, working
FUS-001/FUS-002 Fortnite transformation. Native UEFN editor/Launch Session
must be performed on the user's Windows UEFN computer.

## What was wired in source

- **FUS-001 Armor Fusion:** one `aeonfall_sovereign_authority_device`
  (trusted owner reference), one `aeonfall_sovereign_fusion_device`
  (three native input triggers, attack request output, owner VFX, owner orbit
  camera, cinematic sequence, HUD), and one
  `aeonfall_sovereign_arsenal_device` (shared Reaver request, distinct
  Cataclysm/Bulwark inputs, HUD).
- **Appearance (optional):** one `aeonfall_sovereign_appearance_device`,
  sharing the authority device but with its own native Disguise device.
- **FUS-002 Titan (experiment only):** one
  `aeonfall_titan_proxy_device`, sharing the existing FUS-001 Avatar
  controller but with a **dedicated** NPC Spawner, four distinct and
  owner-registered Input Trigger devices, one cue-only trigger, a separate
  HUD, and one to eight navmesh-safe waypoint Creative Props.
- **Five intentional aliases:** `armor.Authority → authority`,
  `arsenal.Controller → armor`,
  `arsenal.RendRequest → armor.AttackOutput`,
  `appearance.Authority → authority`,
  `titan.AvatarController → armor`. All other physical object references
  must be distinct. These aliases are editor *links*, not duplicate actors.
- Manifest: `content/sovereign/fusion_native_binding_handoff.json`.
  The inventory parser checks its complete physical `@editable` field
  coverage against the **actual Verse source**, including native type,
  explicit shared links, primitive Enabled default, tier and release gates.

No editor paths, island IDs, native Player References or compiler logs are
invented in the source manifest. Every native actor/asset path is initially
null. Developer asset paths are not account identifiers or owner grants.

## Windows UEFN setup — concrete operator workflow

1. In UEFN, create/open the **actual** AEONFALL island project and verify
   which content plugin and mount are active. Back up the current project.
   Avoid importing project metadata from source; the editor creates it.
2. From an up-to-date AEONFALL repository checkout, run an installer dry run:

   ```powershell
   py -3 tools/install_uefn_sources.py "C:\UEFN\AEONFALL\AEONFALL.uefnproject" --dry-run
   ```

   Replace the illustrative project path with the **real** one. The source
   installer checks binding/owner/attack/geometry source contracts before any
   project mutation. If it reports a missing/invalid contract, correct the
   source instead of bypassing the check.
3. Generate an **unplaced** physical device checklist in the repository.
   This does not make device placements.

   ```powershell
   py -3 tools/uefn_editor/fusion_native_binding_handoff.py template --inventory AEONFALL-fusion-editor-inventory.json
   ```

4. Place the specified Creative and Verse devices **inside the editor**.
   For every physical role in the checklist, record the exact editor
   `object_path` and `observed_type`, obtained from UEFN, not guessed from
   a source label. For `titan.Waypoints`, use `object_paths` and
   `observed_types` arrays, with one to eight props if actually placed.
   Connect each `shared_editor_links` entry to the same `object_path`
   as its declared canonical target. Set optional unplaced roles to null.
5. Before enabling any fusion device, configure:
   - Exactly one trusted `player_reference_device` with **verified**
     intended owner provisioned through a controlled editor path; disable
     public registration/transmitters. The stored display name alone is **not
     identity verification**.
   - Unique Armor `FuseInput`, `SeparateInput`, `AttackInput`, dedicated
     Arsenal `CollapseInput`/`BulwarkInput`, and exact
     `AttackOutput → RendRequest` physical trigger connection. Check
     Architect's one-use receipt, original character, budget and cooldown
     are in the direct path. Never bypass the server-side receipt from a
     global/ambient trigger.
   - `FUS-001` `Enabled=false` until native compile and first controlled
     test. Owner-only visual effect, orbit camera and cinematic are bound
     independently of other players; verify camera return on separation.
   - `FUS-002` `Enabled=false` until a separate experiment. Bind the
     spawner exclusively to Titan, disable spawn-at-start/periodic spawn,
     cap at one live NPC, verify Despawn AIs When Disabled, and configure
     all four inputs `Registered Player Behavior = Require Registered`.
     Never bind the Titan cue trigger to damage, grants or global VFX.
6. Optionally discover **actual** live UEFN MCP tools; no capability names,
   argument schemas or editor object IDs are assumed:

   ```powershell
   py -3 tools/uefn_editor/mcp_editor_bridge.py discover --out AEONFALL-editor-catalog.json
   ```

   Build any mutation plan only from **advertised schemas**. Run
   `validate-plan` before `run-plan`; preserve all editor responses
   to a separately reviewed evidence directory. The bridge reports
   `acceptance_claim=not_assessed`, even if an MCP request returns.
7. Audit operator-reported binding observations:

   ```powershell
   py -3 tools/uefn_editor/fusion_native_binding_handoff.py audit --inventory AEONFALL-fusion-editor-inventory.json --report AEONFALL-fusion-binding-audit.json
   py -3 tools/uefn_editor/fusion_native_binding_handoff.py audit --inventory AEONFALL-fusion-editor-inventory.json --require-core-complete
   ```

   The second command fails while a **core** role is unbound. Editor paths
   are accepted for *all real project mounts*, not just `/Game/`, but
   duplicate paths, mismatched classes, forged aliases, stale source hashes,
   leaked shared actors, nonexistent capture files and altered native-evidence
   flags are rejected. A complete operator report **still is not native
   compilation or multiplayer evidence**.
8. Install sources only after reviewing the dry run, bind the real editor
   actors, build Verse **inside UEFN**, save actual compiler diagnostics and
   run Fortnite Launch Session with **two real clients**. Record the engine
   version, source SHA, screenshots and exact logs under a local evidence
   folder. Never commit account identifiers, session secrets or tokens.

## Native two-player acceptance matrix

| Scenario | Expected authoritative result | Required real evidence |
|---|---|---|
| Unprovisioned and nonowner player requests Armor Fusion | Deny | Two-client input/visual logs, no camera/VFX leak |
| Verified owner activates then separates | Owner alone receives effects; camera and VFX removed on separation | Native Verse compile + both clients |
| Fusion expires, owner dies or disconnects | Source authority cleared, no orphaned camera/sequence, no inherited grant | Both clients + editor device log |
| Reaver from outside range / through wall | No unauthorized damage, no cover bypass | Native target/hit/collision proof; **currently blocking** |
| Spammed/forged/expired paid Reaver request | One-use owner receipt required; no second charge/damage | Actual native receipt, energy and target observations |
| Cataclysm/Bulwark against excluded classes | No player, boss, companion, or unauthorized effect | Combat test with real NPC definitions |
| Titan preexisting/duplicate/unexpected NPC | Dedicated spawner fails closed and cleans up | Editor GetAgents/SpawnAt observation |
| Titan `SpawnAt` returns before behavior | Movement/cues withheld until matching NPC behavior ack | Native NPC navigation and input trace |
| Titan owner changes, NPC eliminated or device ends | Only Titan-owned NPC and inputs cleaned; unrelated actor unaffected | Two-client native lifecycle trace |
| Owner-specific input HUD and lag | Nonowner never gains action or capability; delayed requests revalidate owner | Two-client registered-input screenshots |

**Release boundary:** neither successful Python checks, verified source hashes,
the static binding inventory, an MCP HTTP response, imported GLB/WAV/FBX,
nor locally present log files alone establish a playable UEFN island.
Native compilation, actual Character Definition/animation binding, verified
owner provision, collision/LOS and two-client Launch Session are independent
blocking gates. Sovereign Titan *possession* remains unproven; proxy movement
does not make the player control a different character.

## Developer source checks

```powershell
py -3 -m unittest tests.test_fusion_native_binding_handoff -v
py -3 -m unittest tests.test_uefn_bootstrap -v
```

These are offline source/filesystem simulations, not native editor sessions.
