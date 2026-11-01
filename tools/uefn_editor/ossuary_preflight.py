"""Fail-closed reconciliation of previously placed Ossuary actors.

This module intentionally uses duck-typed editor objects so its safety policy
can be unit-tested without claiming UEFN execution.
"""
from __future__ import annotations


def _coordinates(value, names):
    return tuple(float(getattr(value, name)) for name in names)


def _close(actual, expected, tolerance, *, angular=False):
    if len(actual) != len(expected):
        return False
    for observed, target in zip(actual, expected):
        delta = ((observed - target + 180.0) % 360.0) - 180.0 if angular else observed - target
        if abs(delta) > tolerance:
            return False
    return True


def preflight_existing_placements(placements, actors, imported, unreal_api):
    """Return reusable labels, or refuse to build over ambiguous/drifted actors.

    Only manifest-owned labels are considered. An unrelated actor is left alone.
    The caller must perform this check before spawning any missing placements.
    """
    expected = {placement["name"]: placement for placement in placements}
    if len(expected) != len(placements):
        raise ValueError("Duplicate manifest actor names")
    found = {}
    for actor in actors:
        label = actor.get_actor_label()
        if label not in expected:
            continue
        if label in found:
            raise RuntimeError(f"Duplicate existing Ossuary actor label: {label}")
        found[label] = actor
    for label, actor in found.items():
        placement = expected[label]
        component = actor.get_component_by_class(unreal_api.StaticMeshComponent)
        if component is None:
            raise RuntimeError(f"Ossuary label belongs to a non-static-mesh actor: {label}")
        current_mesh = component.get_editor_property("static_mesh")
        expected_mesh = imported[placement["mesh"]]
        if current_mesh is None or current_mesh.get_path_name() != expected_mesh.get_path_name():
            raise RuntimeError(f"Ossuary actor mesh drift: {label}")
        actual_location = _coordinates(actor.get_actor_location(), ("x", "y", "z"))
        actual_rotation = _coordinates(actor.get_actor_rotation(), ("pitch", "yaw", "roll"))
        actual_scale = _coordinates(actor.get_actor_scale3d(), ("x", "y", "z"))
        if not _close(actual_location, placement["location_cm"], 0.1):
            raise RuntimeError(f"Ossuary actor location drift: {label}")
        if not _close(actual_rotation, placement["rotation_deg"], 0.1, angular=True):
            raise RuntimeError(f"Ossuary actor rotation drift: {label}")
        if not _close(actual_scale, placement["scale"], 0.001):
            raise RuntimeError(f"Ossuary actor scale drift: {label}")
    return set(found)
