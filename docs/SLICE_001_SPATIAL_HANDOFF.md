# SLICE-001 spatial/editor handoff — unplaced source checklist

The Ossuary March geometry manifest defines **18 meshes, 593 authored placements, four progression checkpoints, a player-spawn anchor, the Gore-Mason arena, the Black Throne, the Grave Market Eclipse site, and the quartermaster marker**. The first-playable rig defines **49 logical devices**. None of these source definitions is proof of an editor-placed actor.

After installing the source kit into an editor-created UEFN project, run this from the repository or the copied `AEONFALLImportPackage` folder:

```powershell
py -3 tools/uefn_editor/slice_001_spatial_handoff.py --out AEONFALL-spatial-handoff.json
```

The generator validates marker uniqueness and coordinates, boss/event room footprints, ordered checkpoints, route dimensions, rig dependencies, 12 weapons, 12 monsters, six tameables, eight hireables, three bosses, three vehicles, and canonical Launch Session test identifiers. The resulting checklist includes SHA-256 hashes of its four source inputs. It **refuses to overwrite** an existing handoff.

**Design anchors are not physical placements.** `design_anchor_location_cm` is a reference point for the human editor layout. `actual_editor_position_cm` and `editor_object_path` remain null. Do not stack phase hazards, spawners, prop manipulators, or volumes at the shared BOS-005 marker. These need distinct collision, navmesh, activation, cleanup, and signal wiring in UEFN.

Import and assemble the geometry; verify collision/navigation; place and configure the rig devices; and reconcile their actual editor paths using `tools/uefn_editor/slice_001_binding_audit.py`. The King Without Pulse, Grave Market Eclipse, quartermaster, loadout/crafting/progression, companions, NPCs, and vehicles still require separate native editor integration.

Record actual Verse compiler output and Fortnite Launch Session evidence for boss completion/failure, reward idempotency, encounter gates, checkpoint respawn/rejoin, event cleanup, and the remaining acceptance tests. Source-only Python validation **cannot** establish UEFN compilation, physical wiring, or playability.

Test with `python -m unittest discover -s tests -p 'test_slice_001_spatial_handoff.py' -v`.
