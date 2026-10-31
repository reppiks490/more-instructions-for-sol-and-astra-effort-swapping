"""File-system regressions and editor-call contracts for the UEFN bootstrap.

The installer tests perform real isolated file copies. The editor tests use a
small fake API to check decisions and API calls; they do not compile Verse,
import real geometry, run UEFN validation, or prove doorway clearance.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_script(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load_script("aeonfall_source_installer", "tools/install_uefn_sources.py")
builder = load_script("aeonfall_editor_builder", "tools/uefn_editor/build_ossuary_level.py")


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value if isinstance(value, bytes) else value.encode())
    return path


def snapshot(root):
    """Capture file bytes and symlink targets, without following symlinks."""
    result = {}
    for path in root.rglob("*"):
        key = path.relative_to(root).as_posix()
        if path.is_symlink():
            result[key] = ("symlink", str(path.readlink()))
        elif path.is_file():
            result[key] = ("file", path.read_bytes())
        elif path.is_dir():
            result[key] = ("directory",)
    return result


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "island" / "Fixture.uefnproject"
        self.plugin = self.project.parent / "Plugins" / "Aeon" / "Aeon.uplugin"
        write(self.project, b'{"title":"Creator island","bindings":{"projectId":"unchanged"}}\n')
        write(self.plugin, b'{"CanContainContent":true,"FriendlyName":"Creator content"}\n')
        self.metadata = {p: p.read_bytes() for p in (self.project, self.plugin)}
        self.source = self.root / "source"
        write(self.source / "verse/core/alpha.verse", "alpha := class{}\n")
        write(self.source / "verse/adapters/beta.verse", "beta := class{}\n")
        write(self.source / "assets/source/ossuary_starter/manifest.json", '{"schema_version":1}\n')
        write(self.source / "assets/source/ossuary_starter/meshes/module.glb", b"fake source geometry")
        write(self.source / "tools/uefn_editor/build_ossuary_level.py", "# editor script\n")
        write(self.source / "docs/UEFN_STARTER.md", "Editor setup instructions.\n")
        self.destination = self.plugin.parent / "Content/AEONFALL"
        self.package = self.project.parent / "AEONFALLImportPackage"

    def install(self, **kwargs):
        return installer.install(self.project, self.source, **kwargs)

    def assert_metadata_unchanged(self):
        for path, expected in self.metadata.items():
            self.assertEqual(path.read_bytes(), expected)

    def symlink(self, path, target, directory=False):
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"Symlink creation unavailable: {error}")

    def test_install_copies_flat_verse_and_external_import_package(self):
        result = self.install()
        self.assertEqual(result["source_count"], 2)
        self.assertEqual(result["changed_sources"], 2)
        self.assertEqual(result["plugin"], "Aeon")
        self.assertEqual((self.destination / "alpha.verse").read_bytes(), b"alpha := class{}\n")
        self.assertEqual((self.destination / "beta.verse").read_bytes(), b"beta := class{}\n")
        self.assertFalse((self.destination / "core").exists())
        self.assertEqual((self.package / "assets/source/ossuary_starter/meshes/module.glb").read_bytes(), b"fake source geometry")
        config = json.loads((self.package / "editor_config.json").read_text())
        self.assertEqual(config["plugin_name"], "Aeon")
        self.assertEqual(config["editor_execution"], "pending")
        inventory = json.loads((self.destination / "aeonfall-install.json").read_text())
        self.assertEqual(inventory["files"]["alpha.verse"], installer.digest(self.source / "verse/core/alpha.verse"))
        self.assert_metadata_unchanged()

    def test_rerun_is_idempotent_and_does_not_create_backups(self):
        self.install()
        before = snapshot(self.project.parent)
        verse_mtime = (self.destination / "alpha.verse").stat().st_mtime_ns
        result = self.install()
        self.assertEqual(result["changed_sources"], 0)
        self.assertIsNone(result["backup_directory"])
        self.assertEqual(snapshot(self.project.parent), before)
        self.assertEqual((self.destination / "alpha.verse").stat().st_mtime_ns, verse_mtime)
        self.assertFalse((self.project.parent / "AEONFALLBackups").exists())
        self.assert_metadata_unchanged()

    def test_changed_files_preserve_creator_bytes_in_backup(self):
        self.install()
        write(self.destination / "alpha.verse", "creator edited Verse\n")
        write(self.package / "docs/UEFN_STARTER.md", "creator edited notes\n")
        write(self.source / "verse/core/alpha.verse", "alpha := class{Changed:int=1}\n")
        result = self.install()
        backup = Path(result["backup_directory"])
        self.assertEqual((backup / "Plugins/Aeon/Content/AEONFALL/alpha.verse").read_text(), "creator edited Verse\n")
        self.assertEqual((backup / "AEONFALLImportPackage/docs/UEFN_STARTER.md").read_text(), "creator edited notes\n")
        self.assertEqual((self.destination / "alpha.verse").read_bytes(), (self.source / "verse/core/alpha.verse").read_bytes())
        self.assert_metadata_unchanged()

    def test_unedited_stale_source_is_backed_up_then_removed(self):
        self.install()
        (self.source / "verse/adapters/beta.verse").unlink()
        result = self.install()
        self.assertFalse((self.destination / "beta.verse").exists())
        backup = Path(result["backup_directory"]) / "Plugins/Aeon/Content/AEONFALL/beta.verse"
        self.assertEqual(backup.read_bytes(), b"beta := class{}\n")
        self.assert_metadata_unchanged()

    def test_edited_stale_source_fails_before_any_mutation(self):
        self.install()
        (self.source / "verse/adapters/beta.verse").unlink()
        write(self.source / "verse/core/alpha.verse", "new alpha\n")
        write(self.destination / "beta.verse", "creator stale edit\n")
        before = snapshot(self.project.parent)
        with self.assertRaisesRegex(ValueError, "Edited stale source"):
            self.install()
        self.assertEqual(snapshot(self.project.parent), before)

    def test_ambiguous_plugins_require_explicit_selection(self):
        other = self.project.parent / "Plugins/Other/Other.uplugin"
        write(other, '{"CanContainContent":true}')
        before = snapshot(self.project.parent)
        with self.assertRaisesRegex(ValueError, "Expected one content plugin"):
            self.install()
        self.assertEqual(snapshot(self.project.parent), before)
        self.assertEqual(self.install(plugin_name="Aeon")["plugin"], "Aeon")
        self.assertFalse((other.parent / "Content").exists())
        self.assert_metadata_unchanged()

    def test_casefold_filename_collision_fails_before_mutation(self):
        write(self.source / "verse/elsewhere/ALPHA.verse", "different source\n")
        before = snapshot(self.project.parent)
        with self.assertRaisesRegex(ValueError, "Duplicate flattened Verse filename"):
            self.install()
        self.assertEqual(snapshot(self.project.parent), before)

    def test_source_symlink_escape_fails_before_mutation(self):
        external = write(self.root / "outside/escaped.verse", "external Verse\n")
        self.symlink(self.source / "verse/escape.verse", external)
        before = snapshot(self.project.parent)
        with self.assertRaisesRegex(ValueError, "escapes"):
            self.install()
        self.assertEqual(snapshot(self.project.parent), before)
        self.assertEqual(external.read_text(), "external Verse\n")

    def test_destination_symlink_escape_fails_before_mutation(self):
        external = write(self.root / "outside/alpha.verse", "external destination\n")
        self.symlink(self.destination / "alpha.verse", external)
        before = snapshot(self.project.parent)
        with self.assertRaisesRegex(ValueError, "escapes|Symlink"):
            self.install()
        self.assertEqual(snapshot(self.project.parent), before)
        self.assertEqual(external.read_text(), "external destination\n")

    def test_package_directory_symlink_escape_fails_before_mutation(self):
        external = self.root / "outside"
        external.mkdir()
        self.symlink(self.package, external, directory=True)
        before = snapshot(self.project.parent)
        with self.assertRaisesRegex(ValueError, "escapes|Symlink"):
            self.install()
        self.assertEqual(snapshot(self.project.parent), before)
        self.assertEqual(list(external.iterdir()), [])

    def test_inventory_symlink_escape_fails_before_mutation(self):
        external = write(self.root / "outside/inventory.json", '{"files":{}}')
        self.symlink(self.destination / "aeonfall-install.json", external)
        before = snapshot(self.project.parent)
        with self.assertRaisesRegex(ValueError, "escapes|Symlink"):
            self.install()
        self.assertEqual(snapshot(self.project.parent), before)
        self.assertEqual(external.read_text(), '{"files":{}}')

    def test_in_project_verse_symlink_cannot_overwrite_plugin_metadata(self):
        self.symlink(self.destination / "alpha.verse", self.plugin)
        before = snapshot(self.project.parent)
        with self.assertRaises((ValueError, OSError)):
            self.install()
        self.assertEqual(snapshot(self.project.parent), before)
        self.assert_metadata_unchanged()

    def test_in_project_inventory_symlink_cannot_overwrite_project_metadata(self):
        self.symlink(self.destination / "aeonfall-install.json", self.project)
        before = snapshot(self.project.parent)
        with self.assertRaises((ValueError, OSError)):
            self.install()
        self.assertEqual(snapshot(self.project.parent), before)
        self.assert_metadata_unchanged()

    def test_in_project_editor_config_symlink_cannot_overwrite_project_metadata(self):
        self.symlink(self.package / "editor_config.json", self.project)
        before = snapshot(self.project.parent)
        with self.assertRaises((ValueError, OSError)):
            self.install()
        self.assertEqual(snapshot(self.project.parent), before)
        self.assert_metadata_unchanged()

    def test_in_project_namespace_symlink_cannot_redirect_install(self):
        other = self.project.parent / "CreatorOtherContent"
        other.mkdir()
        self.symlink(self.destination, other, directory=True)
        before = snapshot(self.project.parent)
        with self.assertRaises((ValueError, OSError)):
            self.install()
        self.assertEqual(snapshot(self.project.parent), before)
        self.assertEqual(list(other.iterdir()), [])

    def test_hardlinked_destination_cannot_overwrite_creator_metadata(self):
        for relative, metadata in (("verse", self.plugin), ("inventory", self.project), ("config", self.project)):
            with self.subTest(alias=relative):
                path = {"verse": self.destination / "alpha.verse",
                        "inventory": self.destination / "aeonfall-install.json",
                        "config": self.package / "editor_config.json"}[relative]
                path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    os.link(metadata, path)
                except (OSError, NotImplementedError) as error:
                    self.skipTest(f"Hardlink creation unavailable: {error}")
                try:
                    before = snapshot(self.project.parent)
                    with self.assertRaises((ValueError, OSError)):
                        self.install()
                    self.assertEqual(snapshot(self.project.parent), before)
                    self.assert_metadata_unchanged()
                finally:
                    path.unlink()

    def test_unsafe_inventory_filename_fails_before_mutation(self):
        write(self.destination / "aeonfall-install.json", json.dumps({"files": {"../escaped.verse": "hash"}}))
        before = snapshot(self.project.parent)
        with self.assertRaisesRegex(ValueError, "Unsafe filename"):
            self.install()
        self.assertEqual(snapshot(self.project.parent), before)

    def test_dry_run_is_read_only(self):
        before = snapshot(self.project.parent)
        result = self.install(dry_run=True)
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["changed_sources"], 2)
        self.assertEqual(snapshot(self.project.parent), before)

    def test_minimal_verse_only_source_tree_installs_without_partial_failure(self):
        minimal = self.root / "minimal"
        write(minimal / "verse/single.verse", "single := class{}\n")
        result = installer.install(self.project, minimal)
        self.assertEqual(result["source_count"], 1)
        self.assertEqual(result["import_files"], 0)
        self.assertTrue((self.package / "editor_config.json").is_file())
        self.assert_metadata_unchanged()


class FakeStaticMesh:
    def __init__(self, path, *, simple=0, convex=0):
        self.path = path
        self.simple = simple
        self.convex = convex

    def get_path_name(self):
        return self.path


class FakeImportTask:
    def __init__(self):
        self.properties = {}
        self.objects = []
        self.get_objects_calls = 0

    def set_editor_property(self, name, value):
        self.properties[name] = value

    def get_objects(self):
        self.get_objects_calls += 1
        return self.objects


class FakeActor:
    def __init__(self, mesh, location, rotation):
        self.mesh = mesh
        self.location = location
        self.rotation = rotation
        self.label = "ImportedStaticMeshActor"
        self.scale = None

    def get_actor_label(self):
        return self.label

    def set_actor_label(self, value):
        self.label = value

    def set_actor_scale3d(self, value):
        self.scale = value


class FakeUnreal:
    """Documented API-shaped contract fake, with observable side effects."""
    StaticMesh = FakeStaticMesh
    AssetImportTask = FakeImportTask
    EditorActorSubsystem = type("EditorActorSubsystem", (), {})
    LevelEditorSubsystem = type("LevelEditorSubsystem", (), {})
    StaticMeshEditorSubsystem = type("StaticMeshEditorSubsystem", (), {})
    ScriptCollisionShapeType = type("ScriptCollisionShapeType", (), {"BOX": "BOX"})
    Vector = staticmethod(lambda *values: tuple(values))
    Rotator = staticmethod(lambda *values: tuple(values))

    def __init__(self, mount="/Aeon"):
        self.mount = mount
        self.calls = []
        self.assets = {}
        self.tasks = []
        self.active_level = mount + "/CreatorIsland"
        self.level_actors = {self.active_level: []}
        self.save_results = []
        self.save_asset_result = True
        self.import_simple_count = 0
        self.import_convex_count = 0
        self.import_override_path = None
        self.import_mesh_count = 1
        self.decomposition_result = True
        self.decomposition_convex_count = 3
        self.new_level_result = True
        self.load_level_result = True
        self.EditorAssetLibrary = self
        self.AssetToolsHelpers = self

    def get_project_root_asset_directory(self):
        self.calls.append(("project_mount",))
        return self.mount

    def get_asset_tools(self):
        return self

    def get_editor_subsystem(self, cls):
        return self

    def list_assets(self, folder, recursive=True):
        self.calls.append(("list_assets", folder, recursive))
        return [path for path in self.assets if path.startswith(folder + "/")]

    def load_asset(self, path):
        return self.assets.get(path)

    def make_directory(self, path):
        self.calls.append(("make_directory", path))
        return True

    def does_asset_exist(self, path):
        return path in self.assets

    def import_asset_tasks(self, tasks):
        self.calls.append(("import_asset_tasks", len(tasks)))
        self.tasks.extend(tasks)
        for task in tasks:
            folder = task.properties["destination_path"]
            task.objects = [object()]  # Interchange may also return materials.
            for index in range(self.import_mesh_count):
                path = self.import_override_path or (folder + f"/InterchangeMesh_{index}.InterchangeMesh_{index}")
                mesh = FakeStaticMesh(path, simple=self.import_simple_count, convex=self.import_convex_count)
                self.assets[path] = mesh
                task.objects.append(mesh)

    def get_simple_collision_count(self, mesh):
        self.calls.append(("simple_collision_count", mesh.path))
        return mesh.simple

    def get_convex_collision_count(self, mesh):
        self.calls.append(("convex_collision_count", mesh.path))
        return mesh.convex

    def add_simple_collisions(self, mesh, shape):
        self.calls.append(("add_simple_collisions", mesh.path, shape))
        mesh.simple += 1
        return mesh.simple - 1

    def set_convex_decomposition_collisions(self, mesh, hull_count, max_hull_verts, hull_precision):
        self.calls.append(("convex_decomposition", mesh.path, hull_count, max_hull_verts, hull_precision))
        if self.decomposition_result:
            mesh.convex = self.decomposition_convex_count
        return self.decomposition_result

    def remove_collisions(self, mesh):
        self.calls.append(("remove_collisions", mesh.path))
        mesh.simple = mesh.convex = 0
        return True

    def save_loaded_asset(self, asset):
        self.calls.append(("save_loaded_asset", asset.path))
        return self.save_asset_result

    def save_current_level(self):
        result = self.save_results.pop(0) if self.save_results else True
        self.calls.append(("save_current_level", self.active_level, result))
        return result

    def new_level(self, path, is_partitioned_world=False):
        self.calls.append(("new_level", path, is_partitioned_world))
        if self.new_level_result:
            self.assets[path] = object()
            self.active_level = path
            self.level_actors.setdefault(path, [])
        return self.new_level_result

    def load_level(self, path):
        self.calls.append(("load_level", path))
        if self.load_level_result:
            self.active_level = path
            self.level_actors.setdefault(path, [])
        return self.load_level_result

    def get_all_level_actors(self):
        return list(self.level_actors[self.active_level])

    def spawn_actor_from_object(self, mesh, location, rotation, transient=False):
        self.calls.append(("spawn_actor_from_object", mesh.path, location, rotation, transient))
        actor = FakeActor(mesh, location, rotation)
        self.level_actors[self.active_level].append(actor)
        return actor


class EditorBuilderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = self.root / "manifest.json"
        self.plan = {
            "schema_version": 1,
            "modules": [{"id": "SM_AEON_Floor", "files": {"glb": "meshes/floor.glb"},
                         "collision": {"strategy": "convex_components", "hulls": [{"label": "slab", "vertices_m": [
                             [x, y, z] for x in (-2, 2) for y in (-2, 2) for z in (-0.3, 0)]}]}}],
            "placements": [{"name": "AEON_Floor_001", "mesh": "SM_AEON_Floor",
                            "location_cm": [100, 200, 0], "rotation_deg": [0, 90, 0], "scale": [1, 2, 1]}],
        }
        write(self.root / "meshes/floor.glb", b"fake geometry: API contract test only")
        self.flush()

    def flush(self):
        write(self.manifest, json.dumps(self.plan))

    def build(self, ue=None):
        return builder.build(self.manifest, apply=True, unreal_api=ue or FakeUnreal())

    def arch(self):
        self.plan["modules"][0]["id"] = "SM_AEON_Arch"
        self.plan["modules"][0]["collision"]["hulls"] = [{"label": name} for name in ("left", "right", "lintel")]
        self.plan["placements"][0]["mesh"] = "SM_AEON_Arch"
        self.flush()

    def test_dry_run_does_not_access_editor_or_write_report(self):
        class NoEditor:
            def __getattr__(self, name):
                raise AssertionError(f"Dry run accessed editor API: {name}")
        result = builder.build(self.manifest, apply=False, unreal_api=NoEditor())
        self.assertEqual(result["module_count"], 1)
        self.assertTrue(result["dry_run"])
        self.assertFalse((self.root / "editor_build_report.json").exists())

    def test_interchange_actual_results_drive_spawning_and_transform(self):
        ue = FakeUnreal()
        report = self.build(ue)
        self.assertEqual(report["created_actors"], 1)
        task = ue.tasks[0]
        self.assertEqual(task.get_objects_calls, 1)
        self.assertNotIn("destination_name", task.properties)
        self.assertEqual(task.properties["destination_path"], "/Aeon/AEONFALL/Meshes/SM_AEON_Floor")
        self.assertEqual(task.properties["filename"], str(self.root / "meshes/floor.glb"))
        self.assertIs(task.properties["automated"], True)
        self.assertIs(task.properties["async_"], False)
        self.assertIs(task.properties["save"], True)
        actor = ue.level_actors[report["map_asset"]][0]
        self.assertIn("InterchangeMesh_0", actor.mesh.path)
        self.assertEqual(actor.label, "AEON_Floor_001")
        self.assertEqual(actor.location, (100, 200, 0))
        self.assertEqual(actor.rotation, (0, 90, 0))
        self.assertEqual(actor.scale, (1, 2, 1))
        self.assertEqual(report["uefn_validation"], "not_run")
        self.assertEqual(report["verse_compile"], "not_run")
        self.assertEqual(report["launch_session"], "not_run")

    def test_rerun_reuses_mesh_and_map_without_duplicate_actors(self):
        ue = FakeUnreal()
        first = self.build(ue)
        second = self.build(ue)
        self.assertEqual(first["created_actors"], 1)
        self.assertEqual(second["created_actors"], 0)
        self.assertEqual(len(ue.tasks), 1)
        self.assertEqual(len(ue.level_actors[first["map_asset"]]), 1)
        self.assertEqual(len([call for call in ue.calls if call[0] == "new_level"]), 1)
        self.assertEqual(len([call for call in ue.calls if call[0] == "load_level"]), 1)

    def test_cuboid_uses_box_collision_and_reuses_it_on_rerun(self):
        ue = FakeUnreal()
        self.build(ue)
        self.build(ue)
        boxes = [call for call in ue.calls if call[0] == "add_simple_collisions"]
        self.assertEqual(len(boxes), 1)
        self.assertEqual(boxes[0][2], "BOX")
        self.assertFalse(any(call[0] == "convex_decomposition" for call in ue.calls))

    def test_failed_save_of_creator_level_never_closes_it(self):
        for already_exists in (False, True):
            with self.subTest(already_exists=already_exists):
                ue = FakeUnreal()
                ue.save_results = [False]
                if already_exists:
                    ue.assets["/Aeon/AEONFALL/Maps/OssuaryExchange_Starter"] = object()
                with self.assertRaisesRegex(RuntimeError, "Save the active level"):
                    self.build(ue)
                self.assertEqual(ue.active_level, "/Aeon/CreatorIsland")
                self.assertFalse(any(call[0] in {"new_level", "load_level"} for call in ue.calls))
                self.assertFalse((self.root / "editor_build_report.json").exists())

    def test_save_precedes_every_level_switch(self):
        ue = FakeUnreal()
        self.build(ue)
        self.build(ue)
        for index, call in enumerate(ue.calls):
            if call[0] in {"new_level", "load_level"}:
                previous_saves = [item for item in ue.calls[:index] if item[0] == "save_current_level"]
                self.assertTrue(previous_saves[-1][-1])

    def test_shared_or_malformed_mount_is_rejected_before_import(self):
        for mount in ("/Game", "/Engine", "/Fortnite", "/Other/Nested", "Aeon", "/Bad-Name", "/"):
            with self.subTest(mount=mount):
                ue = FakeUnreal(mount)
                with self.assertRaisesRegex(RuntimeError, "content mount"):
                    self.build(ue)
                self.assertEqual(ue.tasks, [])
                self.assertFalse(any(call[0] == "make_directory" for call in ue.calls))

    def test_foreign_import_result_is_rejected_before_collision_mutation(self):
        for path in ("/Fortnite/Shared/ForeignMesh.ForeignMesh",
                     "/Aeon/CreatorShared/ForeignMesh.ForeignMesh",
                     "/Aeon/AEONFALL/Meshes/SM_AEON_FloorSuffix/ForeignMesh.ForeignMesh"):
            with self.subTest(path=path):
                ue = FakeUnreal()
                ue.import_override_path = path
                with self.assertRaises(RuntimeError):
                    self.build(ue)
                self.assertFalse(any(call[0] in {"add_simple_collisions", "convex_decomposition", "save_loaded_asset", "new_level", "load_level"} for call in ue.calls))

    def test_importer_autogenerated_one_hull_arch_is_decomposed_without_box(self):
        self.arch()
        ue = FakeUnreal()
        ue.import_simple_count = 1
        ue.import_convex_count = 1
        self.build(ue)
        decompositions = [call for call in ue.calls if call[0] == "convex_decomposition"]
        self.assertEqual(len(decompositions), 1)
        self.assertGreaterEqual(decompositions[0][2], 3)
        self.assertEqual(decompositions[0][3:], (16, 100000))
        self.assertFalse(any(call[0] == "add_simple_collisions" for call in ue.calls))

    def test_successful_decomposition_with_only_one_hull_is_rejected(self):
        self.arch()
        ue = FakeUnreal()
        ue.decomposition_convex_count = 1
        with self.assertRaises(RuntimeError):
            self.build(ue)
        self.assertFalse(any(call[0] in {"new_level", "load_level"} for call in ue.calls))
        self.assertFalse((self.root / "editor_build_report.json").exists())

    def test_single_hull_wedge_does_not_receive_blocking_box_collision(self):
        module = self.plan["modules"][0]
        module["id"] = "SM_AEON_Ramp"
        module["collision"]["hulls"] = [{"label": "wedge", "vertices_m": [
            [-2, -2, 0], [2, -2, 0], [-2, 2, 0], [2, 2, 0],
            [-2, 2, 1], [2, 2, 1]]}]
        self.plan["placements"][0]["mesh"] = module["id"]
        self.flush()
        ue = FakeUnreal()
        self.build(ue)
        self.assertFalse(any(call[0] == "add_simple_collisions" and call[2] == "BOX" for call in ue.calls))
        self.assertTrue(any(call[0] == "convex_decomposition" for call in ue.calls))

    def test_failed_collision_save_prevents_level_switch_and_report(self):
        ue = FakeUnreal()
        ue.save_asset_result = False
        with self.assertRaisesRegex(RuntimeError, "save collision"):
            self.build(ue)
        self.assertFalse(any(call[0] in {"new_level", "load_level"} for call in ue.calls))
        self.assertFalse((self.root / "editor_build_report.json").exists())

    def test_multiple_interchange_mesh_results_are_rejected(self):
        ue = FakeUnreal()
        ue.import_mesh_count = 2
        with self.assertRaisesRegex(RuntimeError, "Expected one static mesh"):
            self.build(ue)
        self.assertFalse(any(call[0] in {"new_level", "load_level"} for call in ue.calls))

    def test_ambiguous_existing_meshes_are_rejected_without_import(self):
        ue = FakeUnreal()
        folder = "/Aeon/AEONFALL/Meshes/SM_AEON_Floor"
        for name in ("A", "B"):
            path = folder + f"/{name}.{name}"
            ue.assets[path] = FakeStaticMesh(path)
        with self.assertRaisesRegex(RuntimeError, "Ambiguous existing meshes"):
            self.build(ue)
        self.assertEqual(ue.tasks, [])

    def test_failed_final_save_does_not_publish_success_report(self):
        ue = FakeUnreal()
        ue.save_results = [True, False]
        with self.assertRaisesRegex(RuntimeError, "save the assembled"):
            self.build(ue)
        self.assertFalse((self.root / "editor_build_report.json").exists())

    def test_manifest_escape_is_rejected_before_editor_access(self):
        external = self.root.with_name(self.root.name + "_outside.glb")
        self.plan["modules"][0]["files"]["glb"] = "../" + external.name
        write(external, b"outside source")
        self.addCleanup(external.unlink, missing_ok=True)
        self.flush()
        ue = FakeUnreal()
        with self.assertRaisesRegex(ValueError, "escaped asset source"):
            self.build(ue)
        self.assertEqual(ue.calls, [])

    def test_invalid_transform_is_rejected_before_editor_access(self):
        self.plan["placements"][0]["location_cm"] = [0, float("nan"), 0]
        self.flush()
        ue = FakeUnreal()
        with self.assertRaisesRegex(ValueError, "Invalid transform"):
            self.build(ue)
        self.assertEqual(ue.calls, [])


if __name__ == "__main__":
    unittest.main()
