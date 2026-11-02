#!/usr/bin/env python3
"""Turn the ORIGINAL AEONFALL cinematic plate meshes into a real glTF skin.

Each of thirteen independent armor components is rigidly bound (100% weight)
to one mechanical joint under a common armature root. Existing cinematic node
motion is retargeted to the joints. Geometry is baked into global bind-space
and inverse-bind matrices recover the exact original rest appearance.

This is an actual skinned glTF asset for a DCC handoff, NOT a finished humanoid
rig, playable player cosmetic, FBX, imported UEFN NPC or native execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_omnigod_cinematic as cinema

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/"dist/omnigod_cinematics/omnigod_mechanical_motion.glb"
OUTPUT=ROOT/"dist/omnigod_skeletal_handoff"
FILENAME="omnigod_mechanical_rigid_skin.glb"
MANIFEST="rig_handoff.json"
RIG_NAME="AEON_OMNIGOD_MECHANICAL_ROOT"
SKIN_NAME="AEON_OMNIGOD_RIGID_PLATES"
JOINT_PREFIX="J_OMNI_"
EXPECTED_PARTS=tuple(cinema.PARTS)
MAX_SKINNED_VERTICES=60000
MAX_FILE_BYTES=7_000_000


def _append_accessor(doc, data:bytearray, rows, fmt:str, component:int, kind:str) -> int:
    rows=list(rows)
    sizes={"SCALAR":1,"VEC4":4,"MAT4":16}
    width=sizes[kind]
    if not rows or any(len(row)!=width for row in rows):
        raise ValueError("invalid rigid-skin accessor shape")
    numbers=[v for row in rows for v in row]
    if fmt=="f" and not all(math.isfinite(float(x)) for x in numbers):
        raise ValueError("nonfinite skeletal accessor")
    while len(data)%4:
        data.append(0)
    offset=len(data)
    packed=struct.pack("<"+fmt*len(numbers),*numbers)
    data.extend(packed)
    idx=len(doc["bufferViews"])
    doc["bufferViews"].append({"buffer":0,"byteOffset":offset,"byteLength":len(packed)})
    accessor=len(doc["accessors"])
    doc["accessors"].append({"bufferView":idx,"byteOffset":0,
                              "componentType":component,"count":len(rows),"type":kind})
    return accessor


def _position_accessor(doc, data, index):
    item=doc["accessors"][index]
    if item.get("type")!="VEC3" or item.get("componentType")!=5126:
        raise ValueError("rig requires float VEC3 positions")
    view=doc["bufferViews"][item["bufferView"]]
    if view.get("buffer")!=0 or "byteStride" in view:
        raise ValueError("rig expects tightly packed binary positions")
    count=item["count"]
    offset=view.get("byteOffset",0)+item.get("byteOffset",0)
    if count<=0 or offset%4 or offset+count*12>len(data) or count*12>view["byteLength"]:
        raise ValueError("invalid position accessor bounds")
    return item,offset,count


def _inverse_translation_matrix(t):
    # glTF column-major, equivalent to inverse(translation(t)).
    return (1.,0.,0.,0., 0.,1.,0.,0., 0.,0.,1.,0.,
            -t[0],-t[1],-t[2],1.)


def _copy_source_geometry_and_create_skin(doc:dict, data:bytearray):
    expected=["Prototype_"+p for p in EXPECTED_PARTS]
    if [n.get("name") for n in doc.get("nodes",[])]!=expected:
        raise ValueError("unexpected module node identity or order")
    if len(doc.get("meshes",[]))!=len(EXPECTED_PARTS):
        raise ValueError("expected precisely 13 original armor meshes")
    if doc.get("skins"):
        raise ValueError("source already contains a skin; refuse re-skinning")
    if [a.get("name") for a in doc.get("animations",[])]!=list(cinema.CLIPS):
        raise ValueError("source cinematic animations missing or renamed")
    if doc.get("extensionsRequired"):
        raise ValueError("unexpected required glTF extension")

    bind_positions=[]
    counts=[]
    ids=[]
    root=len(doc["nodes"])
    doc["nodes"].append({"name":RIG_NAME,"children":[],"extras":{"non_humanoid_rig":True}})
    for i,part in enumerate(EXPECTED_PARTS):
        node=doc["nodes"][i]
        if node.get("mesh")!=i or node.get("scale",[1,1,1])!=[1,1,1]:
            raise ValueError(f"{part}: noncanonical mesh/scale binding")
        if "rotation" in node and node["rotation"]!=[0,0,0,1]:
            raise ValueError(f"{part}: noncanonical source rotation")
        t=node.get("translation")
        if not isinstance(t,list) or len(t)!=3 or not all(math.isfinite(v) for v in t):
            raise ValueError(f"{part}: invalid bind translation")
        bind_positions.append(tuple(t))
        joint=len(doc["nodes"])
        ids.append(joint)
        doc["nodes"].append({"name":JOINT_PREFIX+part,"translation":list(t),
                              "extras":{"mechanical_plate":part,"requires_humanoid_rig_refinement":True}})
        doc["nodes"][root]["children"].append(joint)
        node["translation"]=[0.,0.,0.]
        node["skin"]=0
        node.setdefault("extras",{})["original_bind_m"]=[round(x,7) for x in t]

        mesh=doc["meshes"][i]
        poses=set()
        for prim in mesh.get("primitives",[]):
            attrs=prim["attributes"]
            if any(k in attrs for k in ("JOINTS_0","WEIGHTS_0","JOINTS_1","WEIGHTS_1")):
                raise ValueError(f"{part}: existing vertex skinning")
            poses.add(attrs["POSITION"])
        if len(poses)!=1:
            raise ValueError(f"{part}: unexpected split position streams")
        position_id=poses.pop()
        item,offset,count=_position_accessor(doc,data,position_id)
        # Bake original mesh-node rest translation into each position, so
        # joint(t) * inverse_bind(-t) * world_bind_position is exact at rest.
        coords=[]
        for vertex in range(count):
            address=offset+vertex*12
            p=struct.unpack_from("<fff",data,address)
            shifted=tuple(float(p[k]+t[k]) for k in range(3))
            if not all(math.isfinite(v) for v in shifted):
                raise ValueError(f"{part}: invalid bind-space coordinates")
            struct.pack_into("<fff",data,address,*shifted)
            coords.append(shifted)
        item["min"]=[min(p[k] for p in coords) for k in range(3)]
        item["max"]=[max(p[k] for p in coords) for k in range(3)]
        joint_access=_append_accessor(doc,data,((i,0,0,0) for _ in range(count)),
                                      "H",5123,"VEC4")
        weight_access=_append_accessor(doc,data,((1.,0.,0.,0.) for _ in range(count)),
                                       "f",5126,"VEC4")
        for prim in mesh["primitives"]:
            prim["attributes"]["JOINTS_0"]=joint_access
            prim["attributes"]["WEIGHTS_0"]=weight_access
        counts.append(count)
    if sum(counts)>MAX_SKINNED_VERTICES:
        raise ValueError("excessive skinned vertex count")
    inverse_bind=_append_accessor(doc,data,(_inverse_translation_matrix(t) for t in bind_positions),
                                  "f",5126,"MAT4")
    doc["skins"]=[{"name":SKIN_NAME,"skeleton":root,"joints":ids,
                   "inverseBindMatrices":inverse_bind}]
    doc["scenes"][0]["nodes"].append(root)

    # The existing three clips have 13 plate translations and 1 eclipse spin.
    # Retarget exactly those channels to the corresponding skin joint; bone
    # rest positions and original target values are both in glTF Y-up meters.
    for animation in doc["animations"]:
        for channel in animation["channels"]:
            target=channel.get("target",{})
            old=target.get("node")
            if not isinstance(old,int) or not 0<=old<len(EXPECTED_PARTS):
                raise ValueError("animated target is not an original armor plate")
            if target.get("path") not in ("translation","rotation"):
                raise ValueError("unknown plate animation channel")
            if target["path"]=="rotation" and old!=EXPECTED_PARTS.index("Eclipse"):
                raise ValueError("non-eclipse rotation not designed")
            target["node"]=ids[old]
    doc["asset"]["generator"]="AEONFALL original rigid-skinned Omnigod DCC handoff v1"
    doc["scenes"][0]["extras"]={
        "source_is_real_skin":True,
        "humanoid_locomotion_rig":False,
        "uefn_fbxs_exported":False,
        "native_uefn_import":"not_run",
        "fortnite_launch_session":"not_run",
        "sovereign_form":"FUS-001",
        "titan_possession":False
    }
    return {"armature_node":root,"joint_nodes":ids,
            "original_bind_translations":bind_positions,
            "skinned_vertices":sum(counts),
            "part_vertex_counts":dict(zip(EXPECTED_PARTS,counts)),
            "animations":[a["name"] for a in doc["animations"]]}


def build(source:Path, output:Path):
    source=source.resolve()
    output=output.resolve()
    doc,data=cinema.read_glb(source)
    rig=_copy_source_geometry_and_create_skin(doc,data)
    output.mkdir(parents=True,exist_ok=True)
    glb_path=output/FILENAME
    glb=cinema.pack_glb(doc,data)
    if len(glb)>MAX_FILE_BYTES:
        raise ValueError("skinned GLB exceeds source handoff file cap")
    glb_path.write_bytes(glb)
    payload={
        "schema_version":1,
        "id":"AEONFALL-OMNIGOD-RIGID-SKIN-001",
        "source_model":"AEONFALL-OMNIGOD-MANIFESTATION-SOURCE-001",
        "canonical_fusion_id":"FUS-001",
        "experimental_titan_fusion_id":"FUS-002",
        "format":"glTF_2.0_real_skin_rigid_plate_weights",
        "source_glb_name":source.name,
        "source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
        "skinned_glb":FILENAME,
        "skinned_glb_sha256":hashlib.sha256(glb).hexdigest(),
        "skinned_bytes":len(glb),
        "armature_node_name":RIG_NAME,
        "joint_names":[JOINT_PREFIX+p for p in EXPECTED_PARTS],
        "part_vertex_counts":rig["part_vertex_counts"],
        "skinned_vertices":rig["skinned_vertices"],
        "animations":rig["animations"],
        "max_skinned_vertices":MAX_SKINNED_VERTICES,
        "max_file_bytes":MAX_FILE_BYTES,
        "native_uefn_import":"not_run",
        "native_uefn_compile":"not_run",
        "fortnite_launch_session":"not_run",
        "blender_fbx_export":"not_run",
        "humanoid_locomotion_rig":False,
        "owner_entitlement_modified":False,
        "native_npc_possession":False,
        "limitations":[
            "Real glTF skin has 13 rigid armor joints, not a production-ready humanoid skeleton.",
            "3 source animation clips animate plates, not footstep locomotion or melee combat.",
            "Blender or equivalent DCC must inspect geometry and export FBX for UEFN import.",
            "Custom NPC Character Definition, native UEFN skeletal import, Verse compile, memory and multiplayer tests remain unverified."
        ]
    }
    (output/MANIFEST).write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return payload


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,default=INPUT)
    parser.add_argument("--output",type=Path,default=OUTPUT)
    args=parser.parse_args()
    result=build(args.source,args.output)
    print(json.dumps({key:result[key] for key in ("id","skinned_vertices","animations","skinned_glb_sha256")},
                     sort_keys=True))
    print("A real rigid glTF skin was generated; no Blender FBX or UEFN import was performed.")


if __name__=="__main__":
    main()
