#!/usr/bin/env python3
"""Numerically verify Omnigod source-to-rigid-skin geometry and animation.

Checks true glTF JOINTS_0/WEIGHTS_0 and inverse bind matrices, not merely
a JSON skeleton label. Does not execute Blender, FBX or UEFN.
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
import build_omnigod_rigid_skin as builder
import build_omnigod_cinematic as cinema
import validate_ossuary_starter_assets as gltf


def _rows(doc,raw,index,component,kind):
    try:
        a=doc["accessors"][index]
        view=doc["bufferViews"][a["bufferView"]]
        n={"VEC3":3,"VEC4":4,"MAT4":16}[kind]
        fmt={5123:"H",5126:"f"}[component]
        size=struct.calcsize(fmt)*n
        offset=view.get("byteOffset",0)+a.get("byteOffset",0)
        if a.get("componentType")!=component or a.get("type")!=kind or a.get("normalized",False):
            raise ValueError("wrong accessor type/normalized attribute")
        if view.get("buffer")!=0 or "byteStride" in view or a.get("count",0)<=0:
            raise ValueError("unsupported or empty accessor layout")
        if offset%struct.calcsize(fmt) or offset+size*a["count"]>len(raw):
            raise ValueError("accessor out of binary bounds")
        if size*a["count"]>view.get("byteLength",0):
            raise ValueError("accessor exceeds its buffer view")
        return [struct.unpack_from("<"+fmt*n,raw,offset+i*size) for i in range(a["count"])]
    except (KeyError,IndexError,TypeError,struct.error) as error:
        raise ValueError(f"invalid skin accessor: {error}") from error


def inspect(source:Path, output:Path):
    errors=[]
    def check(test,message):
        if not test:errors.append(message)
    try:
        manifest=json.loads((output/builder.MANIFEST).read_text(encoding="utf-8"))
        original=source.read_bytes()
        actual=(output/builder.FILENAME).read_bytes()
        source_doc,source_bin=cinema.read_glb(source)
        doc,blob=cinema.read_glb(output/builder.FILENAME)
    except (OSError,ValueError,KeyError,IndexError) as error:
        return [f"missing/corrupt source or skinned artifact: {error}"]
    check(manifest.get("id")=="AEONFALL-OMNIGOD-RIGID-SKIN-001","rig identity drift")
    check(manifest.get("schema_version")==1,"unsupported manifest version")
    check(manifest.get("source_model")=="AEONFALL-OMNIGOD-MANIFESTATION-SOURCE-001",
          "original model identity drift")
    check(manifest.get("canonical_fusion_id")=="FUS-001" and
          manifest.get("experimental_titan_fusion_id")=="FUS-002",
          "canonical fusion identifiers drift")
    check(manifest.get("format")=="glTF_2.0_real_skin_rigid_plate_weights",
          "false or wrong format description")
    check(manifest.get("skinned_glb")==builder.FILENAME,"unexpected output filename")
    check(manifest.get("source_glb_name")==source.name,"unexpected source GLB")
    check(manifest.get("source_sha256")==hashlib.sha256(original).hexdigest(),"source GLB checksum drift")
    check(manifest.get("skinned_glb_sha256")==hashlib.sha256(actual).hexdigest(),
          "skinned GLB checksum drift")
    check(manifest.get("skinned_bytes")==len(actual),"artifact length drift")
    check(manifest.get("max_skinned_vertices")==builder.MAX_SKINNED_VERTICES and
          manifest.get("max_file_bytes")==builder.MAX_FILE_BYTES and
          len(actual)<=builder.MAX_FILE_BYTES,
          "bounded source budget drift")
    check(manifest.get("armature_node_name")==builder.RIG_NAME,"root rig name drift")
    check(manifest.get("joint_names")==[builder.JOINT_PREFIX+p for p in builder.EXPECTED_PARTS],
          "joint names/order drift")
    check(manifest.get("animations")==list(cinema.CLIPS),"source clip names changed")
    for claim in ("native_uefn_import","native_uefn_compile","fortnite_launch_session",
                  "blender_fbx_export"):
        check(manifest.get(claim)=="not_run",f"unsupported native result: {claim}")
    for claim in ("humanoid_locomotion_rig","owner_entitlement_modified","native_npc_possession"):
        check(manifest.get(claim) is False,f"unsafe unsupported claim: {claim}")
    extra=doc.get("scenes",[{}])[0].get("extras",{})
    check(extra.get("source_is_real_skin") is True and
          extra.get("humanoid_locomotion_rig") is False and
          extra.get("uefn_fbxs_exported") is False and
          extra.get("native_uefn_import")=="not_run" and
          extra.get("fortnite_launch_session")=="not_run" and
          extra.get("sovereign_form")=="FUS-001" and
          extra.get("titan_possession") is False,
          "GLB native/skin evidence drift")

    names=["Prototype_"+p for p in builder.EXPECTED_PARTS]
    source_nodes=source_doc.get("nodes",[])
    nodes=doc.get("nodes",[])
    root=len(names)
    joints=list(range(root+1,root+1+len(names)))
    check(len(source_nodes)==13 and [n.get("name") for n in source_nodes]==names,
          "source assembly drift")
    check(len(nodes)==27 and [n.get("name") for n in nodes[:13]]==names,
          "skinned scene mesh/rig node cardinality drift")
    check(nodes[root].get("name")==builder.RIG_NAME and
          nodes[root].get("children")==joints,"armature root/children mismatch")
    check(doc.get("scenes",[{}])[0].get("nodes")==list(range(13))+[root],
          "armature scene topology changed")
    skins=doc.get("skins",[])
    if len(skins)!=1:
        return errors+["expected precisely one complete glTF skin"]
    skin=skins[0]
    check(skin.get("name")==builder.SKIN_NAME,"skin name drift")
    check(skin.get("joints")==joints and skin.get("skeleton")==root,
          "joint mapping, skeleton root or skin order changed")
    check(len(doc.get("meshes",[]))==13,"skinned mesh count drift")
    check([n.get("name") for n in nodes[14:]]==
          [builder.JOINT_PREFIX+p for p in builder.EXPECTED_PARTS],
          "named rig joints drift")

    try:
        ibms=_rows(doc,blob,skin["inverseBindMatrices"],5126,"MAT4")
    except (ValueError,KeyError,TypeError) as error:
        errors.append(str(error))
        ibms=[]
    check(len(ibms)==13,"inverse bind count mismatch")
    counted=0
    for index,part in enumerate(builder.EXPECTED_PARTS):
        if index>=len(source_nodes) or index>=len(doc.get("meshes",[])):
            break
        original_node=source_nodes[index]
        bound=nodes[index]
        bone=nodes[joints[index]]
        T=original_node.get("translation",[])
        if len(T)!=3:errors.append(f"{part}: source rest transform missing");continue
        check(bone.get("translation")==T,f"{part}: bone rest transform wrong")
        check(bound.get("translation")==[0.,0.,0.] and bound.get("skin")==0,
              f"{part}: original mesh node must have zero transform and skin binding")
        check(bound.get("mesh")==index,f"{part}: mesh index changed")
        check(bound.get("extras",{}).get("original_bind_m")==[round(x,7) for x in T],
              f"{part}: original rest translation provenance drift")
        if index<len(ibms):
            desired=builder._inverse_translation_matrix(T)
            check(all(abs(a-b)<1e-5 for a,b in zip(ibms[index],desired)),
                  f"{part}: incorrect inverse bind matrix")
        original_prims=source_doc["meshes"][index]["primitives"]
        new_prims=doc["meshes"][index]["primitives"]
        check(len(original_prims)==len(new_prims),f"{part}: primitive count changed")
        if not original_prims or not new_prims:continue
        o_attrs=original_prims[0]["attributes"]
        attrs=new_prims[0]["attributes"]
        try:
            orig_pos=_rows(source_doc,source_bin,o_attrs["POSITION"],5126,"VEC3")
            baked_pos=_rows(doc,blob,attrs["POSITION"],5126,"VEC3")
            weights=_rows(doc,blob,attrs["WEIGHTS_0"],5126,"VEC4")
            bones=_rows(doc,blob,attrs["JOINTS_0"],5123,"VEC4")
        except (ValueError,KeyError) as error:
            errors.append(f"{part}: invalid geometry/weight buffer {error}")
            continue
        count=len(orig_pos)
        counted+=count
        check(len(baked_pos)==count and len(weights)==count and len(bones)==count,
              f"{part}: skinned stream vertex count drift")
        check(all(row==(index,0,0,0) for row in bones),
              f"{part}: wrong per-vertex bone binding")
        check(all(all(abs(v-t)<1e-6 for v,t in zip(row,(1.,0.,0.,0.))) for row in weights),
              f"{part}: wrong per-vertex rigid skin weight")
        check(all(all(abs((p[k]+T[k])-q[k])<=1e-5 for k in range(3))
                  for p,q in zip(orig_pos,baked_pos)),
              f"{part}: skin rest pose differs from original source")
        check(all(prim["attributes"].get("JOINTS_0")==attrs["JOINTS_0"] and
                  prim["attributes"].get("WEIGHTS_0")==attrs["WEIGHTS_0"]
                  for prim in new_prims), f"{part}: not all primitives skinned")
        check(manifest.get("part_vertex_counts",{}).get(part)==count,
              f"{part}: manifest vertex count drift")
    check(counted==manifest.get("skinned_vertices") and 0<counted<=builder.MAX_SKINNED_VERTICES,
          "total rigid-skinned vertices mismatch/limit")
    source_animations=source_doc.get("animations",[])
    animated=doc.get("animations",[])
    check(len(source_animations)==len(animated)==3,"three source cinematic clips not retained")
    for old,new in zip(source_animations,animated):
        check(old.get("name")==new.get("name"),"clip name changed")
        check(old.get("samplers")==new.get("samplers"),"source clip sampler data/indices changed")
        ocs=old.get("channels",[])
        ncs=new.get("channels",[])
        check(len(ocs)==len(ncs)==14,"source clip channel count changed")
        for a,b in zip(ocs,ncs):
            t=a.get("target",{})
            old_node=t.get("node")
            mapped=old_node if isinstance(old_node,int) and 0<=old_node<13 else 0
            check(b.get("sampler")==a.get("sampler") and
                  b.get("target")=={"node":joints[mapped],"path":t.get("path")},
                  "animation channel not correctly retargeted to mechanical joint")
    try:
        gltf.validate_glb(output/builder.FILENAME)
    except (ValueError,IndexError,TypeError,KeyError,OverflowError) as error:
        errors.append(f"generated skinned glTF geometry invalid: {error}")
    return errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,default=builder.INPUT)
    parser.add_argument("--output",type=Path,default=builder.OUTPUT)
    args=parser.parse_args()
    issues=inspect(args.source,args.output)
    for issue in issues:
        print("ERROR: "+issue,file=sys.stderr)
    if issues:return 1
    print("PASS: genuine glTF rigid plate skin, joints, inverse binds, geometry and three motion clips.")
    print("UEFN, Blender FBX, native NPC playback and multiplayer Launch Session NOT run.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
