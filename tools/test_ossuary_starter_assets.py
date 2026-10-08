#!/usr/bin/env python3
"""Focused regression tests for actual asset corruption and navigation gaps."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import struct
import tempfile
import unittest

import build_ossuary_starter_assets as build
import validate_ossuary_starter_assets as validate


class OssuaryAssetTests(unittest.TestCase):
    def test_each_collision_component_is_closed_and_convex(self):
        meshes=build.build_modules()
        build.check_geometry(meshes)
        for mesh in meshes:
            for solid in mesh.solids:
                for triangle in solid["triangles"]:
                    a,b,c=[mesh.positions[i] for i in triangle]
                    normal=build.cross(build.subtract(b,a),build.subtract(c,a))
                    for point in solid["vertices_m"]:
                        self.assertLessEqual(build.dot(normal,build.subtract(point,a)),1e-7,
                                             f"{mesh.name}/{solid['label']}: nonconvex hull")

    def test_generator_rejects_missing_surface_triangle(self):
        mesh=build.build_modules()[0]
        mesh.solids[0]["triangles"].pop()
        with self.assertRaisesRegex(ValueError,"nonmanifold"):
            build.check_geometry([mesh])

    def test_glb_parser_rejects_out_of_range_triangle_indices(self):
        mesh=build.build_modules()[0]
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/"corrupt.glb"
            path.write_bytes(build.encode_glb([mesh]))
            doc,_=validate.read_glb(path)
            index=doc["meshes"][0]["primitives"][0]["indices"]
            accessor=doc["accessors"][index]
            view=doc["bufferViews"][accessor["bufferView"]]
            raw=bytearray(path.read_bytes())
            json_length=struct.unpack_from("<I",raw,12)[0]
            binary_offset=12+8+json_length+8
            struct.pack_into("<I",raw,binary_offset+view["byteOffset"],len(mesh.positions)+1)
            path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError,"invalid indices"):
                validate.validate_glb(path)

    def test_glb_parser_rejects_reversed_triangle_winding(self):
        mesh=build.build_modules()[0]
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/"backward.glb"
            path.write_bytes(build.encode_glb([mesh]))
            doc,_=validate.read_glb(path)
            index=doc["meshes"][0]["primitives"][0]["indices"]
            view=doc["bufferViews"][doc["accessors"][index]["bufferView"]]
            raw=bytearray(path.read_bytes())
            json_length=struct.unpack_from("<I",raw,12)[0]
            offset=12+8+json_length+8+view["byteOffset"]
            a,b,c=struct.unpack_from("<III",raw,offset)
            struct.pack_into("<III",raw,offset,a,c,b)
            path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError,"backward triangle"):
                validate.validate_glb(path)

    def test_route_validation_rejects_inserted_blocker(self):
        manifest=json.loads((build.DEFAULT_OUTPUT/"manifest.json").read_text())
        manifest["placements"].append({"name":"TEST_ROUTE_BLOCKER","mesh":"SM_AEON_Wall_4m",
                                      "location_cm":[0,2000,0],"rotation_deg":[0,0,0],
                                      "scale":[1,1,1],"role":"architecture","zone":"test"})
        with self.assertRaisesRegex(ValueError,"route blocked by TEST_ROUTE_BLOCKER"):
            validate.validate_paths(manifest)

    def test_route_validation_rejects_missing_connector_floor(self):
        manifest=json.loads((build.DEFAULT_OUTPUT/"manifest.json").read_text())
        manifest["placements"]=[p for p in manifest["placements"] if p["zone"]!="market_link"]
        with self.assertRaisesRegex(ValueError,"unsupported floor"):
            validate.validate_paths(manifest)

    def test_regeneration_matches_committed_generated_artifacts(self):
        expected=json.loads((build.DEFAULT_OUTPUT/"manifest.json").read_text())
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)/"pack"
            actual=build.generate(output)
            self.assertEqual(expected,actual)
            for item in expected["files"]:
                self.assertEqual((build.DEFAULT_OUTPUT/item["path"]).read_bytes(),
                                 (output/item["path"]).read_bytes(),item["path"])
            self.assertEqual(validate.validate_pack(output)["instances"],593)


if __name__=="__main__":
    unittest.main(verbosity=2)
