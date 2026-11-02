#!/usr/bin/env python3
"""Validate Omnigod glTF node-animation clip and cue sheet (source only)."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_omnigod_fusion_animation as builder
import build_omnigod_manifestation_assets as source
import validate_omnigod_manifestation_assets as pack_validation
import validate_ossuary_starter_assets as gltf


def check_animation(output:Path) -> list[str]:
    issues=pack_validation.check_pack(output)
    try:
        cue=json.loads((output/builder.TIMELINE).read_text(encoding="utf-8"))
        raw=(output/builder.FILENAME).read_bytes()
        doc,blob=gltf.read_glb(output/builder.FILENAME)
    except (OSError,ValueError,KeyError,IndexError) as exc:
        return issues+[f"missing or corrupt animation output: {exc}"]

    def need(ok:bool,msg:str):
        if not ok:issues.append(msg)

    need(cue.get("schema_version")==1,"cue schema drift")
    need(cue.get("source_pack")==source.PACK_ID,"source-geometry provenance drift")
    need(cue.get("canonical_mode")=="FUS-001","FUS-001 mode identity drift")
    need(cue.get("duration_seconds")==builder.DURATION_SECONDS,"clip duration drift")
    need(cue.get("sample_times_seconds")==list(builder.TIMES),"sample timeline drift")
    need(cue.get("glb_sha256")==hashlib.sha256(raw).hexdigest(),"GLB content checksum mismatch")
    need(cue.get("preview_glb")==builder.FILENAME,"preview path drift")
    need(cue.get("animation_name")==builder.NAME,"animation identity drift")
    need(cue.get("static_geometry") is True and cue.get("skeletal_rig") is False,
         "unsupported skeletal rig claim")
    need(cue.get("real_audio_generated") is False and cue.get("real_niagara_generated") is False,
         "audio/Niagara source proof cannot be fabricated")
    need(cue.get("owner_entitlement_modified") is False,"asset animation must never grant owner")
    need(cue.get("native_uefn_sequencer")=="not_run","false native Sequencer evidence")
    need(cue.get("native_uefn_compile")=="not_run","false native compiler evidence")
    need(cue.get("fortnite_launch_session")=="not_run","false Launch Session evidence")
    need(cue.get("visibility_warning")==
         "replaceable NPC Sequencer binding requires Everyone, owner-only player cinematic separate",
         "NPC vs owner cinematic visibility boundary drift")
    need(cue.get("beats")==builder.BEATS,"authored audiovisual beat contracts drift")
    budget=cue.get("budget",{})
    need(budget.get("keyframes")==len(builder.TIMES),"keyframe budget drift")
    need(budget.get("channels")==len(builder.OFFSETS)+3,"channel budget drift")
    need(budget.get("max_glb_bytes")==6_000_000,"source file ceiling drift")
    need(len(raw)<=6_000_000,"oversized animated source clip")
    extras=doc.get("scenes",[{}])[0].get("extras",{})
    need(extras.get("not_skeletal") is True and
         extras.get("not_uefn_playtested") is True and
         extras.get("not_player_controlled") is True,
         "GLB preview must not claim a playable UEFN character")
    need(extras.get("fusion_id")=="FUS-001" and extras.get("experimental_titan_id")=="FUS-002",
         "embedded canonical identifiers drift")
    need(len(doc.get("meshes",[]))==len(source.ANCHORS),"original geometry components missing")
    names=[x.get("name") for x in doc.get("nodes",[])]
    need(names==["Prototype_"+x for x in source.ANCHORS],"module node mapping drift")
    animations=doc.get("animations",[])
    if len(animations)!=1:
        return issues+["expected exactly one original animation"]
    clip=animations[0]
    need(clip.get("name")==builder.NAME,"glTF animation name drift")
    samplers=clip.get("samplers",[])
    channels=clip.get("channels",[])
    need(len(samplers)==len(builder.OFFSETS)+3 and len(channels)==len(samplers),
         "missing or extra animation channels")
    seen=set()
    for chan in channels:
        idx=chan.get("sampler")
        if not isinstance(idx,int) or idx<0 or idx>=len(samplers):
            issues.append("animation channel references invalid sampler")
            continue
        spec=samplers[idx]
        target=chan.get("target",{})
        node=target.get("node")
        kind=target.get("path")
        if not isinstance(node,int) or node<0 or node>=len(names):
            issues.append("animation channel references invalid scene node")
            continue
        key=(names[node],kind)
        if key in seen:
            issues.append(f"duplicate target/path {key}")
        seen.add(key)
        need(spec.get("interpolation")=="LINEAR","animation interpolation drift")
        try:
            times=[x[0] for x in gltf.accessor(doc,blob,spec["input"])]
            values=gltf.accessor(doc,blob,spec["output"])
        except (ValueError,KeyError,IndexError,TypeError) as exc:
            issues.append(f"invalid animation accessor {key}: {exc}")
            continue
        need(len(times)==len(builder.TIMES) and all(
            abs(t-v)<1e-5 for t,v in zip(times,builder.TIMES)),
            f"{key}: time accessor drift")
        need(len(values)==len(builder.TIMES),f"{key}: value sample count drift")
        if not values:
            continue
        need(all(math.isfinite(x) for row in values for x in row),f"{key}: nonfinite animation")
        if kind=="translation":
            origin=tuple(doc["nodes"][node]["translation"])
            need(all(abs(v-o)<1e-5 for v,o in zip(values[0],origin)) and
                 all(abs(v-o)<1e-5 for v,o in zip(values[-1],origin)),
                 f"{key}: clip must return to original rest pose")
            need(all(abs(v-o)<2.0 for row in values for v,o in zip(row,origin)),
                 f"{key}: uncontrolled displacement")
        elif kind=="scale":
            need(all(0.95<=v<=1.65 for row in values for v in row),
                 f"{key}: uncontrolled size change")
            need(all(abs(v-1.0)<1e-5 for v in values[0]+values[-1]),
                 f"{key}: must restore original scale")
        elif kind=="rotation":
            need(all(len(row)==4 and abs(sum(v*v for v in row)-1)<1e-5 for row in values),
                 f"{key}: nonunit or invalid quaternion")
            need(key==("Prototype_Eclipse","rotation"),"only halo may rotate in source preview")
        else:
            issues.append(f"{key}: unexpected animation channel kind")
    expected={("Prototype_"+p,"translation") for p in builder.OFFSETS}
    expected|={("Prototype_AxiomCore","scale"),("Prototype_Eclipse","scale"),
               ("Prototype_Eclipse","rotation")}
    need(seen==expected,"animated component names/paths mismatch")
    try:
        gltf.validate_glb(output/builder.FILENAME)
    except (ValueError,KeyError,IndexError,TypeError,OverflowError) as exc:
        issues.append(f"animated scene geometry invalid: {exc}")
    return issues


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,default=source.DEFAULT_OUTPUT)
    opts=p.parse_args()
    errors=check_animation(opts.output)
    for error in errors:
        print("ERROR: "+error,file=sys.stderr)
    if errors:
        return 1
    print("Omnigod mechanical-fusion GLB animation/timeline verified as DCC source.")
    print("UEFN editor, actual skeletal animation and Fortnite Launch Session NOT run.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
