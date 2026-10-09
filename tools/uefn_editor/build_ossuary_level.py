"""Run inside UEFN Python: import original modules and assemble the starter map.

Normal Python can inspect the plan; only the UEFN editor can create .uassets and
the level. Uses documented editor APIs and UI-exposed collision operations.
"""
from __future__ import annotations
import json
import math
import re
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = PACKAGE_ROOT / "assets/source/ossuary_starter/manifest.json"

def checked_file(base: Path, relative: str) -> Path:
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()) or not path.is_file():
        raise ValueError(f"Missing or escaped asset source: {relative}")
    return path

def is_box_hull(hull: dict) -> bool:
    vertices = hull.get("vertices_m", [])
    if len(vertices) != 8:
        return False
    try:
        axes = [{vertex[axis] for vertex in vertices} for axis in range(3)]
        return all(len(values) == 2 for values in axes) and len({tuple(vertex) for vertex in vertices}) == 8
    except (TypeError, IndexError):
        return False

def load_plan(manifest_path: Path = MANIFEST) -> dict:
    manifest_path = Path(manifest_path).resolve()
    doc = json.loads(manifest_path.read_text())
    if doc.get("schema_version") != 1:
        raise ValueError("Unsupported asset manifest version.")
    modules = {module["id"]: module for module in doc["modules"]}
    if len(modules) != len(doc["modules"]):
        raise ValueError("Duplicate mesh identity.")
    names = set()
    for module in modules.values():
        if not re.fullmatch(r"SM_AEON_[A-Za-z0-9_]+", module["id"]):
            raise ValueError("Unsafe mesh identity.")
        checked_file(manifest_path.parent, module["files"]["glb"])
    for placement in doc["placements"]:
        if placement["mesh"] not in modules or placement["name"] in names:
            raise ValueError("Unknown mesh or duplicate actor name.")
        if not re.fullmatch(r"AEON_[A-Za-z0-9_]+", placement["name"]):
            raise ValueError("Unsafe actor identity.")
        names.add(placement["name"])
        for field in ["location_cm", "rotation_deg", "scale"]:
            values = placement[field]
            if len(values) != 3 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
                raise ValueError(f"Invalid transform: {placement['name']}")
        if any(v <= 0 for v in placement["scale"]):
            raise ValueError("Mirrored/zero scale is not allowed in the starter layout.")
    return doc

def build(manifest_path: Path = MANIFEST, *, apply: bool = False, unreal_api=None) -> dict:
    plan = load_plan(manifest_path)
    report = {"module_count": len(plan["modules"]), "placement_count": len(plan["placements"]),
              "dry_run": not apply, "uefn_validation": "not_run", "verse_compile": "not_run",
              "launch_session": "not_run", "collision_clearance": "requires_editor_validation"}
    if not apply:
        return report
    if unreal_api is None:
        import unreal as unreal_api
    ue = unreal_api
    root = ue.EditorAssetLibrary.get_project_root_asset_directory().rstrip("/")
    if not re.fullmatch(r"/[A-Za-z_][A-Za-z0-9_]*", root) or root in {"/Engine", "/Fortnite", "/Game"}:
        raise RuntimeError("Expected the real UEFN project content mount; refusing engine/shared content.")
    namespace = root + "/AEONFALL"
    asset_tools = ue.AssetToolsHelpers.get_asset_tools()
    actor_editor = ue.get_editor_subsystem(ue.EditorActorSubsystem)
    level_editor = ue.get_editor_subsystem(ue.LevelEditorSubsystem)
    mesh_editor = ue.get_editor_subsystem(ue.StaticMeshEditorSubsystem)
    imported = {}
    for module in plan["modules"]:
        folder = namespace + "/Meshes/" + module["id"]
        # GLB uses Interchange; destination_name is intentionally not relied on.
        # On rerun, discover the one existing static mesh in our owned folder.
        existing = [ue.EditorAssetLibrary.load_asset(path) for path in ue.EditorAssetLibrary.list_assets(folder, recursive=True)]
        meshes = [asset for asset in existing if isinstance(asset, ue.StaticMesh)]
        if len(meshes) > 1:
            raise RuntimeError(f"Ambiguous existing meshes in {folder}")
        if not meshes:
            ue.EditorAssetLibrary.make_directory(folder)
            task = ue.AssetImportTask()
            task.set_editor_property("filename", str(checked_file(Path(manifest_path).resolve().parent, module["files"]["glb"])))
            task.set_editor_property("destination_path", folder)
            task.set_editor_property("automated", True)
            task.set_editor_property("async_", False)
            task.set_editor_property("replace_existing", False)
            task.set_editor_property("save", True)
            asset_tools.import_asset_tasks([task])
            meshes = [asset for asset in task.get_objects() if isinstance(asset, ue.StaticMesh)]
        if len(meshes) != 1:
            raise RuntimeError(f"Expected one static mesh from {module['id']}; inspect Interchange import log.")
        mesh = meshes[0]
        if not mesh.get_path_name().startswith(folder + "/"):
            raise RuntimeError(f"Importer returned a mesh outside the owned source folder: {module['id']}")
        # A single convex box across an arch blocks its doorway. Decompose
        # multipart modules using the same operation as UI Auto Convex.
        hulls = module.get("collision", {}).get("hulls", [])
        box = len(hulls) == 1 and is_box_hull(hulls[0])
        needs_collision = not box or mesh_editor.get_simple_collision_count(mesh) == 0
        if needs_collision:
            if box:
                if mesh_editor.add_simple_collisions(mesh, ue.ScriptCollisionShapeType.BOX) < 0:
                    raise RuntimeError(f"Could not generate box collision for {module['id']}")
            else:
                if not mesh_editor.set_convex_decomposition_collisions(mesh, max(8, min(32, len(hulls) * 2)), 16, 100000):
                    raise RuntimeError(f"Could not decompose collision for {module['id']}")
                minimum_hulls = 2 if len(hulls) > 1 else 1
                if mesh_editor.get_convex_collision_count(mesh) < minimum_hulls:
                    raise RuntimeError(f"Insufficient convex collision for {module['id']}; inspect the opening/slope.")
            if not ue.EditorAssetLibrary.save_loaded_asset(mesh):
                raise RuntimeError(f"Could not save collision for {module['id']}")
        imported[module["id"]] = mesh

    map_path = namespace + "/Maps/OssuaryExchange_Starter"
    # These editor operations close the active level; save it first. Never
    # overwrite a creator's unsaved map through automation.
    if not level_editor.save_current_level():
        raise RuntimeError("Save the active level before running the scene builder.")
    ue.EditorAssetLibrary.make_directory(namespace + "/Maps")
    if ue.EditorAssetLibrary.does_asset_exist(map_path):
        if not level_editor.load_level(map_path):
            raise RuntimeError("Could not reopen the existing AEONFALL starter map.")
    elif not level_editor.new_level(map_path, is_partitioned_world=False):
        raise RuntimeError("UEFN did not create the starter level. Inspect editor validation output.")
    existing_names = {actor.get_actor_label() for actor in actor_editor.get_all_level_actors()}
    created = 0
    for placement in plan["placements"]:
        if placement["name"] in existing_names:
            continue
        location = ue.Vector(*placement["location_cm"])
        rotation = ue.Rotator(*placement["rotation_deg"])
        actor = actor_editor.spawn_actor_from_object(imported[placement["mesh"]], location, rotation, transient=False)
        if actor is None:
            raise RuntimeError(f"Could not place {placement['name']}")
        actor.set_actor_label(placement["name"])
        actor.set_actor_scale3d(ue.Vector(*placement["scale"]))
        existing_names.add(placement["name"])
        created += 1
    if not level_editor.save_current_level():
        raise RuntimeError("Could not save the assembled starter level.")
    report.update({"dry_run": False, "map_asset": map_path, "created_actors": created,
                   "required_next": ["Add Island Settings, player spawners, lighting and navigation",
                                     "Place/configure generated Verse devices and encounter signal bindings",
                                     "Inspect arch/stair collision clearance and run UEFN validation",
                                     "Compile Verse, Launch Session, and profile memory"]})
    (Path(manifest_path).resolve().parent / "editor_build_report.json").write_text(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    # Explicit execution in UEFN is the application boundary. Loading this
    # module from tests/ordinary Python does not modify an editor project.
    import unreal
    unreal.log(json.dumps(build(apply=True, unreal_api=unreal), indent=2))
