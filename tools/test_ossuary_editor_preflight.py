#!/usr/bin/env python3
"""Mock-object regression checks; these do not run a UEFN editor."""
import unittest
from types import SimpleNamespace
from uefn_editor.ossuary_preflight import preflight_existing_placements


class Mesh:
    def __init__(self, path):
        self.path = path

    def get_path_name(self):
        return self.path


class Component:
    def __init__(self, mesh):
        self.mesh = mesh

    def get_editor_property(self, name):
        assert name == "static_mesh"
        return self.mesh


class Actor:
    def __init__(self, label="AEON_Floor", mesh=None, location=(100, 200, 0),
                 rotation=(0, 90, 0), scale=(1, 1, 1)):
        self.label = label
        self.component = Component(mesh) if mesh else None
        self.location = SimpleNamespace(**dict(zip(("x", "y", "z"), location)))
        self.rotation = SimpleNamespace(**dict(zip(("pitch", "yaw", "roll"), rotation)))
        self.scale = SimpleNamespace(**dict(zip(("x", "y", "z"), scale)))

    def get_actor_label(self):
        return self.label

    def get_component_by_class(self, _):
        return self.component

    def get_actor_location(self):
        return self.location

    def get_actor_rotation(self):
        return self.rotation

    def get_actor_scale3d(self):
        return self.scale


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.mesh = Mesh("/Project/AEONFALL/Meshes/SM_AEON_Floor_4m/mesh")
        self.imported = {"SM_AEON_Floor_4m": self.mesh}
        self.placements = [{"name": "AEON_Floor", "mesh": "SM_AEON_Floor_4m",
                            "location_cm": [100, 200, 0], "rotation_deg": [0, 90, 0],
                            "scale": [1, 1, 1]}]
        self.ue = SimpleNamespace(StaticMeshComponent=Component)

    def check(self, actors):
        return preflight_existing_placements(self.placements, actors, self.imported, self.ue)

    def test_empty_level_can_build(self):
        self.assertEqual(self.check([]), set())

    def test_identical_actor_reused(self):
        self.assertEqual(self.check([Actor(mesh=self.mesh)]), {"AEON_Floor"})

    def test_unrelated_actor_ignored(self):
        self.assertEqual(self.check([Actor(label="Creator_Art")]), set())

    def test_duplicate_label_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "Duplicate"):
            self.check([Actor(mesh=self.mesh), Actor(mesh=self.mesh)])

    def test_non_mesh_collision_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "non-static"):
            self.check([Actor()])

    def test_wrong_mesh_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "mesh drift"):
            self.check([Actor(mesh=Mesh("/Project/Other"))])

    def test_moved_actor_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "location drift"):
            self.check([Actor(mesh=self.mesh, location=(101, 200, 0))])

    def test_rotated_actor_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "rotation drift"):
            self.check([Actor(mesh=self.mesh, rotation=(0, 95, 0))])

    def test_rescaled_actor_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "scale drift"):
            self.check([Actor(mesh=self.mesh, scale=(1.2, 1, 1))])

    def test_full_turn_rotation_equivalent(self):
        self.assertEqual(self.check([Actor(mesh=self.mesh, rotation=(0, 450, 0))]), {"AEON_Floor"})

    def test_duplicate_manifest_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate manifest"):
            preflight_existing_placements(self.placements * 2, [], self.imported, self.ue)


if __name__ == "__main__":
    unittest.main()
