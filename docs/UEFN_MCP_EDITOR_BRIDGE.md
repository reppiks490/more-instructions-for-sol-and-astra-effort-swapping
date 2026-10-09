# AEONFALL editor MCP bridge

The stdlib client in `tools/uefn_editor/mcp_editor_bridge.py` connects to the MCP
server **inside an already running UEFN editor**. It does not install Windows,
create project metadata or place a map without that editor. The project must
have Epic's documented Python Editor Scripting and UEFN MCP Toolsets enabled;
configure the editor's local server and restart as required by its settings.
The endpoint is normally `http://127.0.0.1:8000/mcp`.

On the Windows machine running UEFN, discover its actual advertised tools:

```powershell
py -3 tools/uefn_editor/mcp_editor_bridge.py discover --out AEONFALL-editor-catalog.json
```

The saved catalog includes tool descriptions, exact input schemas, protocol
initialization and a SHA-256 of the advertised tool list. UEFN may expose toolset
listing/description/call wrappers; use the names and argument schemas in this
actual catalog. First call the advertised read-only toolset-description tools
when their inner device/editor schemas are needed. The bridge does not assume
names for editor placement, editable properties, Verse compilation or play
sessions. `first_playable_rig.json` provides the AEONFALL binding intent, not an
executable list of guessed editor property names.

A concrete plan has this shape; replace the schematic values with names,
arguments and hashes from the discovered catalog:

```json
{
  "schema_version": 1,
  "catalog_sha256": "<catalog_sha256 from discovery>",
  "steps": [
    {
      "tool_name": "<actual advertised name>",
      "input_schema_sha256": "<SHA-256 of canonical advertised inputSchema>",
      "arguments": {},
      "requested_purpose": "Describe the actual editor capability"
    }
  ]
}
```

Use the module's `digest(schema)` helper to compute schema hashes. It encodes
JSON with sorted keys, separators `(',', ':')` and UTF-8, with Unicode characters
preserved. Validate a saved plan without sending any editor requests:

```powershell
py -3 tools/uefn_editor/mcp_editor_bridge.py validate-plan --catalog AEONFALL-editor-catalog.json --plan AEONFALL-editor-plan.json
```

Execute the concrete plan against a fresh live discovery:

```powershell
py -3 tools/uefn_editor/mcp_editor_bridge.py run-plan --plan AEONFALL-editor-plan.json --evidence AEONFALL-editor-evidence.json
```

A changed tool catalog or input schema rejects the plan before a tool call.
Common JSON Schema argument constraints are checked locally; the actual editor
validates the full schema. New placements must use real object identifiers from
actual editor responses for subsequent binding plans. No placeholder identifiers
are silently resolved. Follow the editor's advertised save/compile/session
capabilities and inspect actual diagnostics after each operation.

The client supports JSON and SSE responses, MCP session headers and paginated
tool catalogs. Its default HTTP timeout is 15 seconds, capped at 30 seconds.
Evidence is written after each actual response and records the full response,
errors, schema hash and UTC timestamps. A tool or transport error stops later
steps; previous editor changes may already have happened. Successful transport
is recorded as `response_received`, and engine acceptance remains
`not_assessed`. Compile/session success must be established from real native
editor diagnostics and client logs rather than the tool's HTTP status.

`python tools/test_uefn_mcp_bridge.py` runs ten real HTTP mock-server tests for
protocol, schema pinning, error handling and evidence capture. That server is a
mock, not UEFN; those tests provide no Verse compiler or session evidence.

Official capability reference:
https://dev.epicgames.com/documentation/fortnite/uefn-mcp

Official native objective reference:
https://dev.epicgames.com/documentation/fortnite/verse-api/fortnitedotcom/devices/prop_manipulator_device
