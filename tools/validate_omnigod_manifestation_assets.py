#!/usr/bin/env python3
"""Validate actual generated Omnigod static meshes, manifests and provenance.

Source geometry validation does not prove UEFN import, skeletal rigging,
native Verse compilation, NPC gameplay or multiplayer performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_omnigod_manifestation_assets as builder
import validate_ossuary_starter_assets as glb_validator


def check_pack(output:Path) -> list[str]:
    errors=[]
    output=output.resolve()
    try:
        manifest=json.loads((output/"manifest.json").read_text(encoding="utf-8"))
    except (OSError,ValueError) as exc:
        return [f"manifest missing or invalid: {exc}"]

    def expect(test:bool,reason:str):
        if not test:
            errors.append(reason)

    expect(manifest.get("pack_id")==builder.PACK_ID,"pack identity changed")
    expect(manifest.get("schema_version")==1,"unsupported schema version")
    expect(manifest.get("status")=="original_static_blockout_editor_import_not_run",
           "do not claim imported or tested UEFN assets")
    expect(manifest.get("native_uefn_import")=="not_run","UEFN import evidence unsupported")
    expect(manifest.get("verse_compile")=="not_run","Verse compile evidence unsupported")
    expect(manifest.get("launch_session")=="not_run","Launch Session evidence unsupported")
    expect(manifest.get("npc_possession_implemented") is False,"NPC possession claim unsupported")
    expect(manifest.get("skeletal_mesh_implemented") is False,"skeletal rig claim unsupported")
    expect(manifest.get("owner_entitlement_granted") is False,"owner grant claim unsupported")
    expect(manifest.get("canonical_fusion_mode")=="FUS-001","canonical armor ID changed")
    expect(manifest.get("titan_mode")=="FUS-002","canonical experimental Titan ID changed")
    provenance=manifest.get("provenance",{})
    expect(provenance.get("original") is True and provenance.get("external_geometry") is False,
           "source/provenance drift")
    expect(provenance.get("source_generator")=="tools/build_omnigod_manifestation_assets.py",
           "generator provenance drift")
    parts=manifest.get("parts",[])
    placements=manifest.get("placements",[])
    budget=manifest.get("budget",{})
    ids=[p.get("id") for p in parts]
    expected=["SM_AEON_OMNI_"+suffix for suffix in builder.ANCHORS]
    expect(ids==expected,"module identity, count or order changed")
    expect(len(parts)==len(placements),"part/placement cardinality mismatch")
    expect(len(ids)==len(set(ids)),"duplicate armor module names")
    expect(10<=len(parts)<=builder.MAX_PARTS,"module budget exceeded")
    expect(budget.get("parts")==len(parts),"module count does not match budget")
    expect(budget.get("maximum_triangles")==builder.MAX_TRIANGLES_PER_PACK,"triangle budget drift")
    expect(budget.get("physical_spawns")==0,"source generator may not spawn gameplay entities")
    expect(budget.get("unique_triangles")==sum(p.get("triangles",0) for p in parts),
           "triangle accounting mismatch")
    expect(budget.get("unique_triangles",999999)<=builder.MAX_TRIANGLES_PER_PACK,
           "total triangle budget exceeded")
    expect(manifest.get("import",{}).get("collision")==
           "disable cosmetic static-mesh collision; actual NPC uses tested capsule/navmesh",
           "cosmetic mesh cannot become an untested gameplay collision hull")
    expect(manifest.get("import",{}).get("sequencer_visibility")==
           "NPC replaceable bindings require Everyone; keep owner-only player cinematic separate",
           "unverified NPC Sequencer visibility setting")
    coord=manifest.get("coordinate_system",{})
    expect(coord.get("obj")=="centimeters X east Y north Z up","OBJ source basis drift")
    expect(coord.get("glb")=="glTF2 meters Y up, source (x,y,z) -> (x,z,-y)",
           "GLB source basis drift")
    for part,placement in zip(parts,placements):
        suffix=part.get("id","").removeprefix("SM_AEON_OMNI_")
        intended=builder.ANCHORS.get(suffix)
        if intended is None:
            errors.append("unknown source module or anchor")
            continue
        pos,socket,role=intended
        expect(placement.get("mesh")==part.get("id"),f"{suffix}: mesh/anchor mismatch")
        expect(placement.get("location_cm")==list(pos),f"{suffix}: placement moved unexpectedly")
        expect(placement.get("planned_socket")==socket,f"{suffix}: skeleton socket drift")
        expect(placement.get("role")==role,f"{suffix}: intent/role drift")
        expect(placement.get("collision")=="disabled_for_cosmetic_proxy",
               f"{suffix}: cosmetic collision must remain disabled")
        expect(placement.get("scale")==[1,1,1],f"{suffix}: unit mesh scale drift")
        expect(placement.get("rotation_deg")==[0,0,0],f"{suffix}: unvalidated orientation")
        expect(part.get("triangles",0)>0,f"{suffix}: no geometry")
        bounds=part.get("bounds_m",{})
        if "min" in bounds and "max" in bounds:
            expect(all(math.isfinite(x) for x in bounds["min"]+bounds["max"]),
                   f"{suffix}: nonfinite geometry extent")
            expect(all(a<b for a,b in zip(bounds["min"],bounds["max"])),
                   f"{suffix}: degenerate extent")
    files=manifest.get("files",[])
    paths=[x.get("path") for x in files]
    expect(paths==sorted(paths) and len(paths)==len(set(paths)),
           "file inventory must be sorted and unique")
    expected_files=sorted([f"meshes/{p['id']}.{ext}" for p in parts for ext in ("glb","obj","mtl")]+
                          ["omnigod_dormant_assembly.glb"])
    expect(paths==expected_files,"missing or extra source geometry file")
    for f in files:
        rel=f.get("path","")
        if not rel or Path(rel).is_absolute() or ".." in Path(rel).parts:
            errors.append("unsafe relative path in manifest")
            continue
        path=output/rel
        if not path.is_file():
            errors.append(f"missing generated asset: {rel}")
            continue
        data=path.read_bytes()
        if f.get("sha256")!=hashlib.sha256(data).hexdigest() or f.get("bytes")!=len(data):
            errors.append(f"asset inventory mismatch: {rel}")
    for part in parts:
        path=output/"meshes"/(part["id"]+".glb")
        if path.is_file():
            try:
                glb_validator.validate_glb(path,part)
            except (ValueError,KeyError,IndexError,TypeError,OverflowError) as exc:
                errors.append(f"{part['id']} failed GLB geometry validation: {exc}")
        path_obj=output/"meshes"/(part["id"]+".obj")
        if path_obj.is_file():
            txt=path_obj.read_text(encoding="utf-8")
            expect(txt.startswith("# AEONFALL original source."),f"{part['id']}: OBJ provenance")
            expect(f"o {part['id']}" in txt,f"{part['id']}: OBJ object identity")
            expect(txt.count("\nf ")==part.get("triangles"),f"{part['id']}: OBJ face mismatch")
    scene=output/"omnigod_dormant_assembly.glb"
    if scene.is_file():
        try:
            doc,_=glb_validator.read_glb(scene)
            expect(len(doc.get("meshes",[]))==len(parts),"assembly missing module mesh")
            expect(len(doc.get("nodes",[]))==len(placements),"assembly missing module nodes")
            expect(len(doc.get("scenes",[{}])[0].get("nodes",[]))==len(parts),
                   "assembly scene node drift")
            for node,place in zip(doc.get("nodes",[]),placements):
                expect(node.get("name")==place["name"] and node.get("extras",{}).get("role")==place["role"],
                       f"{place['name']}: assembled node identity mismatch")
        except (ValueError,KeyError,IndexError,TypeError,OverflowError) as exc:
            errors.append(f"assembled GLB invalid: {exc}")
    return errors


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=builder.DEFAULT_OUTPUT)
    opts=parser.parse_args()
    errors=check_pack(opts.output)
    for e in errors:
        print("ERROR: "+e,file=sys.stderr)
    if errors:
        return 1
    print("Original Omnigod source geometry, GLB/OBJ and manifest validated.")
    print("UEFN native import/rigging/Launch Session were not executed.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
