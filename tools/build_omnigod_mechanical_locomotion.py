#!/usr/bin/env python3
"""Five actual glTF bone-animation source clips for the Omnigod mechanical rig.

Implements UEFN Basic Locomotion role previews (Idle/F/B/L/R) as in-place,
bounded rigid-plate motion on the real 13-joint skin from the prior handoff.
Not humanoid mocap, an NPC Animation Preset, gameplay movement or UEFN proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_omnigod_cinematic as glb_source
import build_omnigod_rigid_skin as rig

ROOT=Path(__file__).resolve().parents[1]
INPUT=rig.OUTPUT/rig.FILENAME
OUTPUT=ROOT/"dist/omnigod_npc_locomotion"
FILENAME="omnigod_mechanical_five_way_locomotion.glb"
MANIFEST="locomotion_handoff.json"
SOURCE_DURATION=1.6
FRAME_COUNT=17
TIMES=tuple(round(SOURCE_DURATION*i/(FRAME_COUNT-1),4) for i in range(FRAME_COUNT))
CLIP_NAMES={
    "idle":"AEON_NPC_Idle_Mechanical",
    "forward":"AEON_NPC_MoveForward_Mechanical",
    "backward":"AEON_NPC_MoveBackward_Mechanical",
    "left":"AEON_NPC_MoveLeft_Mechanical",
    "right":"AEON_NPC_MoveRight_Mechanical"
}
SLOTS=tuple(rig.EXPECTED_PARTS)
MAX_PREVIEW_GLTF=9_000_000
MAX_DISPLACEMENT_M=0.28
MAX_SCALE=1.07


def _delta(slot,phase,mode):
    """In-place motion offsets, source GLB space X right, Y up, Z forward."""
    if mode=="idle":
        h=math.sin(phase)**2
        if slot in ("Torso","Hips","Reactor"):
            return (0.0,0.012*h,0.0)
        if slot in ("Crown","Pauldron_L","Pauldron_R"):
            return (0.0,0.010*h,0.0)
        if slot=="AxiomCore":
            return (0.0,0.018*h,0.0)
        return (0.0,0.0,0.0)

    s=math.sin(phase)
    left=s if slot.endswith("_L") else -s
    lift=max(0.0,left)*0.16
    fb=1.0 if mode=="forward" else (-0.70 if mode=="backward" else 0.0)
    side=-1.0 if mode=="left" else (1.0 if mode=="right" else 0.0)
    gait=math.sin(2*phase)**2
    if slot.startswith("Greave_"):
        return (side*left*0.12,lift,fb*left*0.15)
    if slot.startswith("Gauntlet_"):
        return (side*left*-0.07,gait*0.02,fb*left*-0.12)
    if slot.startswith("Pauldron_"):
        return (side*-0.022*s,0.018*gait,fb*-0.016*s)
    if slot=="Hips":
        return (side*0.035*s,0.027*gait,fb*0.015*s)
    if slot=="Torso":
        return (side*0.032*s,0.021*gait,fb*0.011*s)
    if slot=="Crown":
        return (side*0.013*s,0.018*gait,fb*-0.018*s)
    if slot=="Reactor":
        return (side*0.021*s,0.018*gait,0.0)
    if slot=="AxiomCore":
        return (0.0,0.025*gait,0.0)
    if slot=="Eclipse":
        return (side*0.035*s,0.015*gait,0.0)
    if slot=="SiegeBlade":
        return (side*0.04*s,0.015*gait,fb*-0.065*s)
    return (0.0,0.0,0.0)


def _build(doc,blob):
    expected=["J_OMNI_"+part for part in SLOTS]
    names=[n.get("name") for n in doc.get("nodes",[])]
    if len(doc.get("skins",[]))!=1 or names[14:]!=expected:
        raise ValueError("real Omnigod skin/joints missing or re-ordered")
    if [a.get("name") for a in doc.get("animations",[])]!=list(glb_source.CLIPS):
        raise ValueError("original source cinematic clips changed")
    if len(doc.get("meshes",[]))!=13 or doc["skins"][0].get("joints")!=list(range(14,27)):
        raise ValueError("source mechanical armature invalid")
    if any("skin" not in doc["nodes"][i] for i in range(13)):
        raise ValueError("source mesh is not weighted to an armature")

    original_count=len(doc["animations"])
    for mode,clip_name in CLIP_NAMES.items():
        anim={"name":clip_name,"samplers":[],"channels":[]}
        input_id=glb_source.accessor(doc,blob,list(TIMES),"SCALAR")
        for index,part in enumerate(SLOTS):
            joint_node=14+index
            bind=doc["nodes"][joint_node].get("translation")
            if not isinstance(bind,list) or len(bind)!=3:
                raise ValueError(f"{part}: invalid rest-joint translation")
            frames=[]
            for k in range(FRAME_COUNT):
                phase=2*math.pi*k/(FRAME_COUNT-1)
                delta=_delta(part,phase,mode)
                if any(abs(v)>MAX_DISPLACEMENT_M for v in delta):
                    raise ValueError(f"{part}: unsafe movement amplitude")
                frames.append([round(bind[i]+delta[i],6) for i in range(3)])
            out=glb_source.accessor(doc,blob,frames,"VEC3")
            sampler=len(anim["samplers"])
            anim["samplers"].append({"input":input_id,"output":out,"interpolation":"LINEAR"})
            anim["channels"].append({"sampler":sampler,
                                     "target":{"node":joint_node,"path":"translation"}})

        pulses=[1+0.06*(math.sin(math.pi*k/(FRAME_COUNT-1))**2)
                for k in range(FRAME_COUNT)]
        out=glb_source.accessor(doc,blob,[[p,p,p] for p in pulses],"VEC3")
        index=len(anim["samplers"])
        anim["samplers"].append({"input":input_id,"output":out,"interpolation":"LINEAR"})
        anim["channels"].append({"sampler":index,
                                 "target":{"node":14+SLOTS.index("AxiomCore"),"path":"scale"}})

        # A 2-degree controlled eclipse sway; no constant strobe or spin.
        angles=[0.034*math.sin(2*math.pi*k/(FRAME_COUNT-1))
                for k in range(FRAME_COUNT)]
        quats=[[0.,round(math.sin(a/2),7),0.,round(math.cos(a/2),7)]
               for a in angles]
        out=glb_source.accessor(doc,blob,quats,"VEC4")
        index=len(anim["samplers"])
        anim["samplers"].append({"input":input_id,"output":out,"interpolation":"LINEAR"})
        anim["channels"].append({"sampler":index,
                                 "target":{"node":14+SLOTS.index("Eclipse"),"path":"rotation"}})
        doc["animations"].append(anim)
    if len(doc["animations"])!=original_count+5:
        raise ValueError("mechanical NPC five-way clips missing")
    doc["asset"]["generator"]="AEONFALL original in-place Omnigod mechanical locomotion DCC source v1"
    doc["scenes"][0]["extras"]={
        "source_skin":True,"basic_locomotion_role_clips":True,
        "true_humanoid_footstep_rig":False,"native_uefn_import":"not_run",
        "native_npc_movement":"not_run","fortnite_launch_session":"not_run",
        "native_fusion_enabled":False
    }
    return doc,blob


def generate(source:Path,output:Path):
    source=source.resolve()
    output=output.resolve()
    doc,binary=glb_source.read_glb(source)
    newdoc,newbytes=_build(doc,binary)
    result=glb_source.pack_glb(newdoc,newbytes)
    if len(result)>MAX_PREVIEW_GLTF:
        raise ValueError("oversized source locomotion clip")
    output.mkdir(parents=True,exist_ok=True)
    (output/FILENAME).write_bytes(result)
    manifest={
        "schema_version":1,"id":"AEONFALL-OMNIGOD-MECHANICAL-LOCOMOTION-001",
        "source_model":"AEONFALL-OMNIGOD-RIGID-SKIN-001",
        "source_glb_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_filename":source.name,"output_glb":FILENAME,
        "output_glb_sha256":hashlib.sha256(result).hexdigest(),"bytes":len(result),
        "canonical_fusion_id":"FUS-001","titan_fusion_id":"FUS-002",
        "original_cinematic_clips":list(glb_source.CLIPS),
        "basic_locomotion_clips":CLIP_NAMES,
        "basic_locomotion_role_count":5,
        "all_clips_count":len(newdoc["animations"]),
        "frame_count":FRAME_COUNT,"cycle_seconds":SOURCE_DURATION,
        "times_seconds":list(TIMES),"in_place":True,
        "max_displacement_m":MAX_DISPLACEMENT_M,"max_visual_scale":MAX_SCALE,
        "designed_npc_sync_contacts":{"left_foot":[0.0,0.8,1.6],
                                      "right_foot":[0.4,1.2]},
        "real_humanoid_locomotion_rig":False,
        "rig_source_is_skinned":True,
        "uefn_npc_character_definition":"not_run",
        "uefn_animation_preset":"not_run",
        "blender_fbx_export":"not_run",
        "fortnite_launch_session":"not_run",
        "owner_entitlement_modified":False,
        "native_owner_fusion_enabled":False,
        "limitations":[
            "Five actual keyed skeletal-plate source animations, not full-body humanoid gait or root motion.",
            "Rigging improvements, actual FBX and in-editor animation import are still needed.",
            "No live UEFN NPC physics/navmesh/collision/replication was tested."
        ]
    }
    (output/MANIFEST).write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,default=INPUT)
    p.add_argument("--output",type=Path,default=OUTPUT)
    args=p.parse_args()
    d=generate(args.source,args.output)
    print(json.dumps({"clips":d["basic_locomotion_clips"],
                      "source_sha256":d["source_glb_sha256"],
                      "result_sha256":d["output_glb_sha256"]},sort_keys=True))
    print("This is in-place keyed mechanical skin animation only; native UEFN NPC not tested.")


if __name__=="__main__":
    main()
