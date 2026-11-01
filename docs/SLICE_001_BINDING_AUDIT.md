# SLICE-001 physical binding audit (BOS-005)

`tools/uefn_editor/slice_001_binding_audit.py` converts the first-playable
rig's 49 logical device entries and 42 exclusive encounter roles into a
source-pinned editor inventory. It does **not** place devices, invent editor
properties, compile Verse, or run Fortnite.

After installing the source kit into an editor-created UEFN project, generate
a checklist from the **same** source revision:

```powershell
py -3 tools/uefn_editor/slice_001_binding_audit.py template --inventory AEONFALL-device-inventory.json
```

Inside the real editor, place and inspect each source-defined device. Fill
`observations` with the actual `object_path` and `observed_class`.
Populate `director_observed_links` with the referenced canonical device ID
mapped to the *actual linked* editor object path, not merely a proposed target.
Record `editor_project` and `editor_level`. Keep the contract SHA-256
values unchanged. When source changes, regenerate and reconcile.

Save the raw editor inspection/MCP response in a local evidence folder.
Set `editor_capture` to its relative path and SHA-256. The audit checks
that the file is present, nonempty, within the evidence root, and byte-for-byte
matches its digest. **An inventory assertion alone cannot prove an actual
editor binding.** Compare the capture against the claimed object paths and
Verse editable properties during review.

```powershell
py -3 tools/uefn_editor/slice_001_binding_audit.py audit --inventory AEONFALL-device-inventory.json --evidence-root . --report AEONFALL-binding-audit.json
```

The command exits nonzero on missing/duplicate devices, wrong types, aliased
physical objects, missing/misdirected links, changed contracts, unknown IDs,
incorrect Launch Session status IDs, or invalid capture provenance.
A clean report means `inventory_consistent: true`, **not** a verified
UEFN compilation or playable island. The `native_verse_compile` and
`fortnite_launch_session` fields remain `not_assessed` even when a
human enters `passed` in one of the 24 Launch Session status fields.
Native acceptance requires actual compiler and client logs, including both
success and failure paths for Grave Market Eclipse.

The first rig covers Gore-Mason (BOS-005). King Without Pulse (BOS-011),
Grave Market Eclipse (EVT-011), the remaining weapons, monsters, companions,
vehicles, navigation, respawn, and rejoin still need their own physical
integration and native acceptance.

Run `python -m unittest discover -s tests -p 'test_slice_001_binding_audit.py' -v`
for source-only mock regressions. Mock observations are not UEFN evidence.
