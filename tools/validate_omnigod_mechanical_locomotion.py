#!/usr/bin/env python3
"""Read and validate actual Omnigod mechanical joint locomotion animation data.

The checks are source-level binary tests, not evidence of UEFN NPC playback.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_omnigod_mechanical_locomotion as gait
import build_omnigod_cinematic as source
import build_omnigod_rigid_skin as skin
import validate_ossuary_starter_assets as gltf


def validate(source_file:Path,output:Path)->list[str]:
    errors=[]
    def need(ok,msg):
        if not ok:errors.append(msg)
    try:
        origin=source_file.read_bytes()
        result=(output/gait.FILENAME).read_bytes()
        manifest=json.loads((output/gait.MANIFEST).read_text(encoding="utf-8"))
        before,original_blob=source.read_glb(source_file)
        doc,blob=source.read_glb(output/gait.FILENAME)
    except (OSError,ValueError,KeyError,IndexError) as error:
        return [f"missing/corrupt source/manifest: {error}"]
    need(manifest.get("schema_version")==1,"manifest version drift")
    need(manifest.get("id")=="AEONFALL-OMNIGOD-MECHANICAL-LOCOMOTION-001","manifest id drift")
    need(manifest.get("source_model")=="AEONFALL-OMNIGOD-RIGID-SKIN-001","rig model drift")
    need(manifest.get("source_filename")==source_file.name,"source filename drift")
    need(manifest.get("source_glb_sha256")==hashlib.sha256(origin).hexdigest(),"source hash mismatch")
    need(manifest.get("output_glb")==gait.FILENAME,"output filename drift")
    need(manifest.get("output_glb_sha256")==hashlib.sha256(result).hexdigest(),"output hash mismatch")
    need(manifest.get("bytes")==len(result),"output length mismatch")
    need(manifest.get("canonical_fusion_id")=="FUS-001" and manifest.get("titan_fusion_id")=="FUS-002",
         "canonical fusion IDs changed")
    need(manifest.get("original_cinematic_clips")==list(source.CLIPS),"original cinematic labels changed")
    need(manifest.get("basic_locomotion_clips")==gait.CLIP_NAMES and
         manifest.get("basic_locomotion_role_count")==5,"five expected locomotion roles changed")
    need(manifest.get("all_clips_count")==8,"total clip count changed")
    need(manifest.get("frame_count")==gait.FRAME_COUNT and
         manifest.get("cycle_seconds")==gait.SOURCE_DURATION and
         manifest.get("times_seconds")==list(gait.TIMES),"clip time samples changed")
    need(manifest.get("in_place") is True and
         manifest.get("max_displacement_m")==gait.MAX_DISPLACEMENT_M and
         manifest.get("max_visual_scale")==gait.MAX_SCALE,"bounded in-place motion policy drift")
    need(manifest.get("real_humanoid_locomotion_rig") is False and
         manifest.get("rig_source_is_skinned") is True,"false humanoid/rig claim")
    for claim in ("uefn_npc_character_definition","uefn_animation_preset",
                  "blender_fbx_export","fortnite_launch_session"):
        need(manifest.get(claim)=="not_run","false engine result: "+claim)
    need(manifest.get("owner_entitlement_modified") is False and
         manifest.get("native_owner_fusion_enabled") is False,
         "source file must not enable owner fusion")
    extra=doc.get("scenes",[{}])[0].get("extras",{})
    need(extra.get("source_skin") is True and
         extra.get("basic_locomotion_role_clips") is True and
         extra.get("true_humanoid_footstep_rig") is False and
         extra.get("native_uefn_import")=="not_run" and
         extra.get("native_npc_movement")=="not_run" and
         extra.get("fortnite_launch_session")=="not_run" and
         extra.get("native_fusion_enabled") is False,"embedded source-proof honesty drift")
    need(len(doc.get("skins",[]))==1 and doc["skins"][0].get("joints")==list(range(14,27)),
         "actual mechanical joint skin lost")
    need(doc.get("nodes",[])==before.get("nodes",[]),"source bones/rest pose moved")
    need(doc.get("meshes",[])==before.get("meshes",[]),"source model topology modified")
    need(doc.get("skins",[])==before.get("skins",[]),"source weighted skin modified")
    clips=doc.get("animations",[])
    originals=before.get("animations",[])
    need(len(clips)==len(originals)+5,"exactly five new skeletal clips required")
    need(clips[:3]==originals,"original three cinematic clips must survive unchanged")
    need([a.get("name") for a in clips[3:]]==list(gait.CLIP_NAMES.values()),
         "locomotion clip names/order incorrect")
    if len(clips)!=8:return errors
    generated_samples={}
    for anim,mode in zip(clips[3:],gait.CLIP_NAMES):
        channels=anim.get("channels",[])
        samplers=anim.get("samplers",[])
        need(len(channels)==len(samplers)==15,
             f"{mode}: expected 13 translations/core pulse/eclipse rotation")
        targets=set()
        for channel in channels:
            sampler_index=channel.get("sampler")
            target=channel.get("target",{})
            if not isinstance(sampler_index,int) or not 0<=sampler_index<len(samplers):
                errors.append(f"{mode}: invalid sampler reference")
                continue
            node=target.get("node")
            path=target.get("path")
            if not isinstance(node,int) or not 14<=node<=26:
                errors.append(f"{mode}: unrigged/external target")
                continue
            key=(node,path)
            if key in targets:errors.append(f"{mode}: duplicate bone animation")
            targets.add(key)
            sampler=samplers[sampler_index]
            need(sampler.get("interpolation")=="LINEAR",f"{mode}: non-linear timeline interpolation")
            try:
                times=[row[0] for row in gltf.accessor(doc,blob,sampler["input"])]
                values=gltf.accessor(doc,blob,sampler["output"])
            except (ValueError,TypeError,KeyError,IndexError,OverflowError) as error:
                errors.append(f"{mode}: invalid timeline bytes: {error}")
                continue
            need(len(times)==len(values)==gait.FRAME_COUNT and
                 all(abs(a-b)<1e-5 for a,b in zip(times,gait.TIMES)),
                 f"{mode}: timeline mismatch")
            need(all(math.isfinite(v) for row in values for v in row),
                 f"{mode}: nonfinite skeletal motion")
            if path=="translation":
                rest=doc["nodes"][node]["translation"]
                need(all(abs(v-r)<1e-5 for v,r in zip(values[0],rest)) and
                     all(abs(v-r)<1e-5 for v,r in zip(values[-1],rest)),
                     f"{mode}: incorrect looping rest-pose closure")
                need(all(abs(v-r)<=gait.MAX_DISPLACEMENT_M+1e-5
                         for row in values for v,r in zip(row,rest)),
                     f"{mode}: uncontrolled bone translation")
                generated_samples[(mode,node)]=values
            elif path=="scale":
                need(node==14+gait.SLOTS.index("AxiomCore"),
                     f"{mode}: unauthorized plate scale change")
                need(all(1.0-1e-5<=v<=gait.MAX_SCALE+1e-5 for row in values for v in row),
                     f"{mode}: unbounded Axiom Core scale")
                need(all(abs(v-1)<1e-5 for v in values[0]+values[-1]),
                     f"{mode}: core scale must restore rest")
            elif path=="rotation":
                need(node==14+gait.SLOTS.index("Eclipse"),
                     f"{mode}: only the eclipse can rotate")
                need(all(len(q)==4 and abs(sum(v*v for v in q)-1)<1e-5
                         for q in values),f"{mode}: nonunit halo quaternion")
                need(all(abs(a-b)<1e-5 for a,b in zip(values[0],values[-1])),
                     f"{mode}: eclipse loop does not close")
            else:
                errors.append(f"{mode}: unsupported joint channel")
        expected={(14+i,"translation") for i in range(13)}
        expected|={(14+gait.SLOTS.index("AxiomCore"),"scale"),
                   (14+gait.SLOTS.index("Eclipse"),"rotation")}
        need(targets==expected,f"{mode}: missing/excess bone channel")
    # Distinct gait directions must actually change foot travel, not just names.
    legs=[14+gait.SLOTS.index(x) for x in ("Greave_L","Greave_R")]
    for node in legs:
        f=generated_samples.get(("forward",node))
        b=generated_samples.get(("backward",node))
        l=generated_samples.get(("left",node))
        r=generated_samples.get(("right",node))
        if not all((f,b,l,r)):
            errors.append("leg direction animation missing")
            continue
        need(abs(f[4][2]-b[4][2])>0.04,f"joint {node}: forward/back gait identical")
        need(abs(l[4][0]-r[4][0])>0.04,f"joint {node}: left/right gait identical")
    need(len(result)<=gait.MAX_PREVIEW_GLTF,"source GLB too large")
    try:
        gltf.validate_glb(output/gait.FILENAME)
    except (ValueError,KeyError,TypeError,IndexError,OverflowError) as error:
        errors.append(f"invalid source mesh topology: {error}")
    return errors


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,default=gait.INPUT)
    p.add_argument("--output",type=Path,default=gait.OUTPUT)
    args=p.parse_args()
    errors=validate(args.source,args.output)
    for e in errors:print("ERROR: "+e,file=sys.stderr)
    if errors:return 1
    print("PASS: five distinct, finite, in-place mechanical-joint locomotion clips.")
    print("Native UEFN Animation Preset, Blender FBX and multiplayer NPC playback NOT run.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
