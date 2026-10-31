# UEFN automation capabilities

Public documentation reviewed on **2026-10-08**. This is a source-backed integration guide, not evidence that AEONFALL has compiled or run in UEFN.

## Create the real project in the Windows editor

Install Epic Games Launcher, Fortnite, and Unreal Editor for Fortnite under the intended Epic account. Fortnite is required for UEFN playtesting. Epic lists 16 GB RAM and a DX11 GPU with 4 GB VRAM as minimum UEFN hardware; 32 GB RAM and 8 GB VRAM are recommended. [Epic installation guide](https://dev.epicgames.com/documentation/fortnite/install-and-launch-fortnite-creative-and-unreal-editor-for-fortnite)

Use **New Project / Island Templates / Blank**, name the project `AEONFALL`, and choose its destination. Letters, numbers, and underscores are valid project-name characters. The editor creates the actual project, initial level, Island Settings, and starter devices. Keep those editor-produced files. No supported standalone API for creating a complete new `.uefnproject` was found in the reviewed public documentation; a JSON descriptor alone is not an authored island. [Epic project creation](https://dev.epicgames.com/documentation/fortnite/starting-and-organizing-a-project-in-fortnite)

Epic's bundled **Feature Examples** are the most direct legitimate templates; create them through the Project Browser. A downloaded Verse repository is not a project template unless its usable project assets and license are actually present. [Epic starter templates](https://dev.epicgames.com/documentation/fortnite/unreal-editor-for-fortnite-starter-templates)

## Source assets and project paths

GLB, glTF, FBX, and OBJ are supported source model formats. Import them through UEFN's Content Browser or editor import APIs; copying a `.glb` into a folder does not create its `.uasset`. Non-FBX imports use Interchange. Put generated source files in an external `SourceAssets` folder, and imported assets only under the project's content mount, not the Epic or Fortnite content mounts. [Epic asset import](https://dev.epicgames.com/documentation/fortnite/importing-assets-in-unreal-editor-for-fortnite)

UEFN can import a heightmap through **Landscape Mode / Manage / Import From File**. Its documented landscape limit is 2048 by 2048 vertices or equivalent total area. A standard 2017 by 2017 heightmap is within that limit; this alone does not establish physical scale or memory cost. A terrain GLB imports as a static mesh, not automatically as a Landscape. [Epic Landscape Mode](https://dev.epicgames.com/documentation/fortnite/landscape-mode-in-unreal-editor-for-fortnite)

Use `unreal.EditorAssetLibrary.get_project_root_asset_directory()` to resolve the running UEFN project's asset mount. The API explicitly distinguishes UEFN project mounts from the Unreal Engine `/Game/` convention. Build destination package paths under that returned root; do not infer the mounted name from a Windows directory. `make_directory`, `load_asset`, `does_asset_exist`, and `save_loaded_asset` are documented asset operations. [Epic EditorAssetLibrary API](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EditorAssetLibrary?application_version=5.7)

## Supported editor Python route

Enable **Python Editor Scripting** in Project Settings. Epic now explicitly supports import automation and scene setup in UEFN. Restrict modifications to project-owned assets and properties exposed by the UEFN UI; Python access to an engine property does not make that property valid for an island. Run validation after content changes. [Epic Python Tools in UEFN](https://dev.epicgames.com/documentation/fortnite/python-tools-in-uefn)

Run scripts in the editor's embedded Python environment, not ordinary Windows or Linux Python. The guide referenced by Epic documents the Output Log's Python console, `py "C:\\path\\bootstrap.py"`, and automatic `Content/Python/init_unreal.py` initialization. Startup scripts run after the startup level loads; `init_unreal.py` runs immediately, so level-dependent initialization needs a readiness check. Unreal Engine's headless `.uproject` commandlet examples are not documented UEFN project-creation commands. [Epic Python scripting guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-unreal-editor-using-python)

### Import APIs

Construct `unreal.AssetImportTask` with `filename`, `destination_path`, `automated`, `async_`, `save`, and `replace_existing`. Read `get_objects()` and `imported_object_paths` to determine what was actually imported. `get_objects()` waits for asynchronous import completion. **Interchange ignores `destination_name`**; discover generated asset names or configure an appropriate pipeline. [Epic AssetImportTask API](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/AssetImportTask?application_version=5.7)

`unreal.AssetTools.import_asset_tasks(import_tasks)` accepts an array of those tasks and returns no success value. Inspect each task's results and the editor log. [Epic AssetTools API](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/AssetTools?application_version=5.7)

### Placement and level APIs

Obtain subsystems with `unreal.get_editor_subsystem(...)`. Check that each required class and method exists in the installed UEFN version before changing the scene. The cited reference signatures are Unreal Python 5.7/5.8 APIs, not an AEONFALL editor test.

| API | Documented behavior |
| --- | --- |
| `EditorActorSubsystem.spawn_actor_from_object(object_to_use, location, rotation, transient=False)` | Places an asset, factory, archetype, Blueprint, or class in the current level and returns the actor. |
| `EditorActorSubsystem.get_all_level_actors()` | Lists loaded editor actors. |
| `EditorActorSubsystem.set_actor_transform(actor, world_transform)` | Returns whether a transform could be set. |
| `LevelEditorSubsystem.new_level(asset_path, is_partitioned_world=False)` | Creates, saves, and opens a blank level. |
| `LevelEditorSubsystem.new_level_from_template(asset_path, template_asset_path)` | Creates, saves, and opens a level based on a template. |
| `LevelEditorSubsystem.save_current_level()` | Saves the current level, which must already have a valid asset path. |
| `LevelEditorSubsystem.save_all_dirty_levels()` | Saves loaded dirty levels. |

`new_level`, `new_level_from_template`, and `load_level` close the current persistent level **without saving it**. Save successfully before switching. For an initial island, populating the editor-created Blank level preserves its required devices; creating a generic blank level does not substitute for island setup. [Epic EditorActorSubsystem API](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EditorActorSubsystem?application_version=5.7), [Epic LevelEditorSubsystem API](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/LevelEditorSubsystem)

An imported StaticMesh placed as an actor is scenery until it receives the intended gameplay implementation. A Verse Scene Graph entity is a different object model; importing or placing a mesh does not create a creature, weak point, custom weapon, or Verse component automatically.

## Collision that preserves passages

UEFN's Static Mesh Editor supports simplified shapes, multiple shapes, K-DOP, and **Auto Convex Collision**. A single box or convex hull around an arch or doorway fills the passage. Use separate pillar/lintel modules with individual collision, or multiple convex hulls around the complete structure; then test the passage using the actual player capsule. [Epic UEFN collision guide](https://dev.epicgames.com/documentation/fortnite/configuring-collision-for-a-static-mesh-in-unreal-editor-for-fortnite)

`unreal.StaticMeshEditorSubsystem` exposes the corresponding UI operations:

| API | Result / constraint |
| --- | --- |
| `add_simple_collisions(static_mesh, shape_type)` | Returns a collision index; a negative value means failure. Current enum: `unreal.ScriptCollisionShapeType`. |
| `remove_collisions(static_mesh)` | Returns a boolean. |
| `set_convex_decomposition_collisions(static_mesh, hull_count, max_hull_verts, hull_precision)` | Returns a boolean; reproduces Auto Convex and replaces existing collision. Positive hull count and precision are required. |
| `get_simple_collision_count(static_mesh)` | Returns a count; negative means failure. |
| `get_convex_collision_count(static_mesh)` | Returns a count; negative means failure. |

Check every return value and save only the project's imported meshes. Auto Convex parameters are approximations, so a successful operation and positive hull count do not prove doorway clearance. Avoid raw edits to hidden collision properties. [Epic StaticMeshEditorSubsystem API](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/StaticMeshEditorSubsystem?application_version=5.7), [Epic collision enum](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/ScriptCollisionShapeType?application_version=5.7)

The documented Interchange mesh pipeline has `combine_static_meshes`, `collision`, `import_collision_according_to_mesh_name`, and `one_convex_hull_per_ucx`. Naming-based collision recognizes `UBX_`, `UCP_`, `USP_`, and `UCX_`. `import_collision` is deprecated. This establishes a possible source-collision route, but does not prove that a particular generated GLB's collision nodes import correctly in UEFN. Inspect the imported collision and use the documented editor fallback. [Epic InterchangeGenericMeshPipeline API](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/InterchangeGenericMeshPipeline?application_version=5.7)

## Official UEFN MCP route

Enable **Python Editor Scripting** and **UEFN MCP Toolsets** in Project Settings, configure auto-start in Editor Preferences, and restart the editor. The default endpoint is `http://127.0.0.1:8000/mcp`. UEFN's official toolsets cover Verse editing/compilation, Creative device placement and `@editable` properties, Scene Graph entities, and play-session control. UEFN sessions use Play-in-Client. The current docs note XYZ versus Verse LUF conversion issues and editor hitching; keep placement coordinates explicit. [Epic UEFN MCP](https://dev.epicgames.com/documentation/fortnite/uefn-mcp)

The upstream MCP documentation specifies discovery tools `list_toolsets`, `describe_toolset`, and `call_tool`. With Tool Search enabled, `tools/list` returns these meta-tools rather than every editor tool. Fetch live tool schemas, then describe the required toolsets and use their advertised argument names. The public overview does not enumerate every UEFN-specific tool signature. Send editor calls sequentially. The default listener is local-only and has no authentication; a cloud container's `127.0.0.1` is not the Windows editor. [Epic Unreal MCP reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor?application_version=5.8)

Useful documented console commands are `ModelContextProtocol.StartServer [port]`, `ModelContextProtocol.StopServer`, `ModelContextProtocol.RefreshTools`, and `ModelContextProtocol.GenerateClientConfig <Client|All>`. Use client-specific generated configuration rather than inventing a client protocol. These are upstream Unreal MCP commands; confirm their availability in the installed UEFN build. [Epic Unreal MCP reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor?application_version=5.8)

## Evidence boundary

Until the editor actually runs the automation, generated assets and scripts are a **bootstrap package**. Claim a real island only after editor-created project files exist; claim compilation only from UEFN's build results; claim playable behavior only from a Fortnite Launch Session. Capture imported paths, actor counts, saved-level paths, validation results, Verse compilation output, and test-session results in the editor run report.
