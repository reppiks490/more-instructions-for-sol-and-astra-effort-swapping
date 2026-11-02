#!/usr/bin/env python3
"""Binary/provenance checks for all 39 real AEONFALL regional landmark meshes.

Inspects all original GLB vertices/triangles, real OBJ count, material slots,
terrain-sampled anchor positions and exact file SHA-256 integrity.
This is not evidence of native UEFN import or playable streamed worlds.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_all_region_landmarks as source
import validate_ossuary_starter_assets as gltf
import build_all_region_terrain as terrain


def audit(output:Path) -> list[str]:
    output=output.resolve()
    errors=[]
    def check(ok,message):
        if not ok:errors.append(message)
    try:
        manifest=json.loads((output/"manifest.json").read_text(encoding="utf-8"))
        world=json.loads(terrain.WORLD.read_text(encoding="utf-8"))
    except (OSError,ValueError,KeyError) as e:
        return [f"invalid or missing source manifest/topology: {e}"]
    check(manifest.get("schema_version")==1 and manifest.get("id")==source.PACK_ID,
          "landmark source manifest identity drift")
    check(manifest.get("source_tool")=="tools/build_all_region_landmarks.py",
          "source generator provenance drift")
    check(manifest.get("canonical_world")=="content/world/world_topology.json",
          "world topology provenance drift")
    check(manifest.get("source_artifact_only") is True and
          manifest.get("actual_region_completion") is False,
          "source cannot claim full region completion")
    check(manifest.get("native_uefn_import")=="not_run" and
          manifest.get("fortnite_mobile_playtest")=="not_run",
          "native UEFN/mobile test never executed by source pipeline")
    check(manifest.get("npc_navmesh_quest_or_streaming_verified") is False,
          "static geometry cannot imply gameplay/nav/quest streaming")
    check(manifest.get("source_module_count")==39 and manifest.get("region_count")==13,
          "all 39 modules and 13 regions required")
    check(manifest.get("unique_module_target")==39,"no reduced sample size permitted")
    check(manifest.get("max_triangles_per_module")==source.MAX_TRIANGLES_PER_MESH and
          manifest.get("max_triangles_total")==source.MAX_TRIANGLES_TOTAL,
          "polygon envelope changed")
    world_rows=world.get("regions",[])
    source_regions=manifest.get("regions",[])
    check([r.get("id") for r in source_regions]==[r["id"] for r in world_rows],
          "missing/reordered regional landmark sources")
    all_files=manifest.get("files",[])
    paths=[entry.get("path") for entry in all_files]
    check(paths==sorted(paths) and len(paths)==len(set(paths))==130,
          "complete sorted 130-file source asset inventory required")
    expected_paths=set()
    seen_module_names=set()
    triangle_sum=0
    unique_signatures=set()
    sample_cache={}
    for ri,region in enumerate(source_regions):
        ident=region.get("id")
        if ident not in source.terrain.REGION_SLUGS:
            errors.append(f"unknown region {ident!r}")
            continue
        n=int(ident[-3:])
        original=world_rows[ri] if ri<len(world_rows) else {}
        check(region.get("name")==original.get("name") and
              region.get("theme")==original.get("theme") and
              region.get("neighbors")==original.get("neighbors"),
              f"{ident}: canonical region/theme/neighbor mismatch")
        check(region.get("motif")==source.MOTIF[n],
              f"{ident}: signature architecture motif drift")
        check(region.get("uefn_import")=="not_run" and
              region.get("navmesh")=="not_run" and
              region.get("streaming_hlod")=="not_run" and
              region.get("mobile_playtest")=="not_run",
              f"{ident}: fabricated editor/gameplay evidence")
        check(region.get("source_terrain")=="tools/build_all_region_terrain.py",
              f"{ident}: terrain provenance changed")
        shades=region.get("palette",[])
        expected_palette=source.palette(n)
        check(len(shades)==len(expected_palette) and
              [s.get("name") for s in shades]==[p[0] for p in expected_palette],
              f"{ident}: regional material signatures missing")
        modules=region.get("source_modules",[])
        check([m.get("kind") for m in modules]==list(source.KINDS),
              f"{ident}: all three canonical landmark roles required")
        check(region.get("assembly_glb")==f"{ident}/landmark_preview.glb",
              f"{ident}: assembled source path drift")
        expected_paths.add(f"{ident}/landmark_preview.glb")
        if ident not in sample_cache:
            sample_cache[ident]=source.height_samples(ident)
        samples,southwest=sample_cache[ident]
        check(region.get("source_landscape_origin_m")==list(southwest),
              f"{ident}: heightmap sample-space drift")
        region_triangles=0
        for kind,row in zip(source.KINDS,modules):
            name=f"SM_AEON_REG{n:03d}_{kind}"
            check(row.get("mesh")==name and row.get("kind")==kind,
                  f"{ident}: mismatched/duplicate mesh identity")
            seen_module_names.add(name)
            count=row.get("triangles",0)
            check(isinstance(count,int) and 0<count<=source.MAX_TRIANGLES_PER_MESH,
                  f"{name}: per-module polygon budget exceeded")
            region_triangles+=count
            check(row.get("signature")==source.MOTIF[n],
                  f"{name}: region-specific geometry provenance missing")
            check(row.get("source_only") is True and
                  row.get("uses_generated_assets_not_uefn_import") is True,
                  f"{name}: fabricated editor import")
            mesh=root=output/ident/"meshes"/name
            expected_paths|={f"{ident}/meshes/{name}.{ext}"
                             for ext in ("glb","obj","mtl")}
            if not root.with_suffix(".glb").is_file():
                errors.append(f"{name}: missing actual GLB asset")
                continue
            try:
                doc,actual=gltf.validate_glb(root.with_suffix(".glb"),
                    {"id":name,"triangles":count,"bounds_m":row["bounds_m"]})
                check(len(doc.get("meshes",[]))==1,
                      f"{name}: per-module GLB must contain one real mesh")
                check(doc["scenes"][0]["extras"].get("region_id")==ident,
                      f"{name}: regional scene provenance wrong")
                check(doc["scenes"][0]["extras"].get("native_uefn_import")=="not_run",
                      f"{name}: imported state cannot be claimed")
                check(actual==count,f"{name}: GLB triangle count wrong")
                check([m.get("name") for m in doc["materials"]]==
                      [m[0] for m in expected_palette],
                      f"{name}: regional GLB color/material palette drift")
                obj=root.with_suffix(".obj").read_text(encoding="utf-8")
                check(obj.count("\nf ")==count,
                      f"{name}: OBJ source triangles missing")
                check(obj.startswith("# AEONFALL original source."),
                      f"{name}: OBJ source attribution missing")
                mtl=root.with_suffix(".mtl").read_text(encoding="utf-8")
                check(all("newmtl "+m[0] in mtl for m in expected_palette),
                      f"{name}: OBJ material source drift")
                unique_signatures.add(hashlib.sha256(root.with_suffix(".glb").read_bytes()).hexdigest())
            except (OSError,TypeError,KeyError,IndexError,ValueError,OverflowError) as e:
                errors.append(f"{name}: invalid GLB/OBJ/MTL geometry: {e}")
            p=row.get("placement",{})
            check(p.get("name")==f"{ident}_{kind}_SourceProxy" and
                  p.get("mesh")==name and p.get("zone")==ident and
                  p.get("role")==source.SOURCE_ROLE[kind],
                  f"{name}: locator metadata drift")
            check(p.get("rotation_deg")==[0,0,0] and
                  p.get("scale")==[1,1,1],
                  f"{name}: non-neutral source-only placement")
            anchor=row.get("terrain_contact",{})
            expected_anchor=source.best_anchor(samples,southwest,kind,ident)
            check(anchor==expected_anchor,
                  f"{name}: terrain-dependent locator/grade claims incorrect")
            coords=p.get("location_cm",[])
            x,y,z=expected_anchor["center_local_m"]
            check(coords==[round(x*100),round(y*100),round((z+.65)*100)],
                  f"{name}: actual terrain-sampled location incorrect")
            if kind=="ThresholdGate":
                bounds=row.get("bounds_m",{})
                check(bounds.get("min",[0])[0] < -6 and
                      bounds.get("max",[0])[0] > 6,
                      f"{name}: gate frame/columns missing")
        check(region.get("triangles")==region_triangles,
              f"{ident}: summed source triangles inconsistent")
        triangle_sum+=region_triangles
        assembly=output/ident/"landmark_preview.glb"
        if assembly.is_file():
            try:
                doc,actual=gltf.validate_glb(assembly)
                check(len(doc.get("meshes",[]))==3 and
                      len(doc.get("nodes",[]))==3,
                      f"{ident}: assembled preview must contain all three meshes/nodes")
                check(doc["scenes"][0]["extras"].get("region_id")==ident,
                      f"{ident}: assembly regional identity")
                check(actual==region_triangles,
                      f"{ident}: source assembly changed underlying geometry")
                check([node["name"] for node in doc["nodes"]]==
                      [x["placement"]["name"] for x in modules],
                      f"{ident}: assembled preview nodes/source binding changed")
                check([node["extras"]["role"] for node in doc["nodes"]]==
                      [source.SOURCE_ROLE[k] for k in source.KINDS],
                      f"{ident}: assembly roles drift")
            except (OSError,ValueError,KeyError,TypeError,IndexError,OverflowError) as e:
                errors.append(f"{ident}: invalid assembled GLB: {e}")
        else:
            errors.append(f"{ident}: assembled preview missing")
    check(len(seen_module_names)==39 and len(unique_signatures)==39,
          "all 39 actual original mesh identities/geometries required")
    check(manifest.get("total_triangles")==triangle_sum and
          0<triangle_sum<=source.MAX_TRIANGLES_TOTAL,
          "global source mesh triangle accounting/budget mismatch")
    expected_names=expected_paths|{"manifest.json"}
    observed={p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()}
    check(observed==expected_names,
          f"unexpected/missing physical source files: {sorted(observed^expected_names)[:12]}")
    check(set(paths)==expected_paths,
          "manifest file inventory does not cover exactly all geometry")
    for record in all_files:
        rel=record.get("path")
        if not isinstance(rel,str) or Path(rel).is_absolute() or ".." in Path(rel).parts:
            errors.append("unsafe relative source asset path")
            continue
        path=output/rel
        if not path.is_file():
            errors.append(f"missing source path {rel}")
            continue
        data=path.read_bytes()
        check(record.get("bytes")==len(data) and
              record.get("sha256")==hashlib.sha256(data).hexdigest(),
              f"{rel}: SHA-256/content integrity failed")
    return errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=source.DEFAULT_OUTPUT)
    opts=parser.parse_args()
    problems=audit(opts.output)
    for error in problems:print("ERROR: "+error,file=sys.stderr)
    if problems:return 1
    print("PASS: all 39 region-distinct GLB and OBJ+MTL sources; 13 assembled previews and true R16-sampled placements.")
    print("Real UEFN integration, actual portal movement, quests, NPCs or Fortnite mobile play NOT run.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
