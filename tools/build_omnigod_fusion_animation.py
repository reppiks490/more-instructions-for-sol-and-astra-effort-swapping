#!/usr/bin/env python3
"""Produce original glTF node animations of the 13-piece Omnigod proxy.

This is a deterministic DCC/visual blocking timeline, not a skeletal NPC rig,
a player skin, native UEFN cinematic, audio file, Niagara VFX or possession.
It extends the existing source geometry by animated module transforms only.
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
import build_omnigod_manifestation_assets as source

NAME="Omnigod_Armor_Fusion_Beats"
FILENAME="omnigod_mechanical_fusion_preview.glb"
TIMELINE="omnigod_mechanical_fusion_timeline.json"
DURATION_SECONDS=8.0
TIMES=(0.0,0.6,1.6,2.7,4.5,6.8,8.0)
# [initially dormant, rising, fully separated, supercharged, folding,
#  closing, steady awakening]. Position deltas use SOURCE Z-up meters.
EXPANSION=(0.0,0.25,1.0,1.0,0.65,0.10,0.0)
OFFSETS={
    "Crown":(0.0,0.0,0.48),
    "Pauldron_L":(-0.65,0.0,0.23),
    "Pauldron_R":(0.65,0.0,0.23),
    "Gauntlet_L":(-0.43,-0.15,-0.19),
    "Gauntlet_R":(0.43,-0.15,-0.19),
    "Reactor":(0.0,0.48,0.13),
    "Hips":(0.0,0.0,-0.16),
    "AxiomCore":(0.0,-0.38,0.11),
    "Eclipse":(0.0,0.45,0.42),
    "SiegeBlade":(0.46,-0.10,0.28),
}
CORE_SCALE=(1.0,1.08,1.38,1.60,1.27,1.05,1.0)
ECLIPSE_SCALE=(1.0,1.08,1.30,1.42,1.26,1.03,1.0)
# Source-Z rotation maps to glTF-Y quaternion. Angles monotonic, bounded
# between adjacent frames to avoid ambiguous full-spin shortest-path flips.
ECLIPSE_TURNS=(0.0,0.08,0.24,0.42,0.68,0.89,1.0)
BEATS=[
    {"at":0.0,"name":"Silent Throne","vfx":"dark idle embers","audio":"distant sub-bass pulse",
     "telegraph":"whole-body silhouette"},
    {"at":0.6,"name":"Axiom Ignition","vfx":"violet core brightens","audio":"mechanical bell",
     "telegraph":"visible chest-core pulse"},
    {"at":1.6,"name":"Armor Severance","vfx":"crimson plate seams flare","audio":"thirteen descending metal locks",
     "telegraph":"distinct moving plate silhouettes"},
    {"at":2.7,"name":"Eclipse Ascension","vfx":"corona expands; violet and crimson pulses",
     "audio":"layered choir plus bass impact","telegraph":"expanding concentric rings"},
    {"at":4.5,"name":"Sovereign Reforging","vfx":"segmented armor returns",
     "audio":"armored tectonic convergence","telegraph":"motion inward"},
    {"at":6.8,"name":"Crown Seal","vfx":"halo decelerates",
     "audio":"one high metallic strike","telegraph":"crown silhouette clears"},
    {"at":8.0,"name":"Awakened Stillness","vfx":"reduced-intensity rim glow",
     "audio":"low idle engine","telegraph":"steady halo silhouette"},
]


def unpack_glb(data:bytes):
    if len(data)<20:
        raise ValueError("truncated glTF")
    magic,version,total=struct.unpack_from("<III",data,0)
    if (magic,version,total)!=(0x46546C67,2,len(data)):
        raise ValueError("invalid GLB header/version/length")
    cursor=12
    chunks=[]
    while cursor<len(data):
        if cursor+8>len(data):
            raise ValueError("invalid GLB chunk header")
        size,kind=struct.unpack_from("<II",data,cursor)
        cursor+=8
        if size%4 or cursor+size>len(data):
            raise ValueError("GLB chunk alignment/range violation")
        chunks.append((kind,data[cursor:cursor+size]))
        cursor+=size
    if [x[0] for x in chunks]!=[0x4E4F534A,0x004E4942]:
        raise ValueError("expected JSON and BIN chunks")
    doc=json.loads(chunks[0][1].decode("utf-8"))
    actual=doc["buffers"][0]["byteLength"]
    if actual>len(chunks[1][1]):
        raise ValueError("missing GLB geometry bytes")
    return doc,bytearray(chunks[1][1][:actual])


def pack_glb(doc,blob:bytes):
    doc["buffers"][0]["byteLength"]=len(blob)
    encoded=json.dumps(doc,separators=(",",":"),sort_keys=True,ensure_ascii=False).encode("utf-8")
    encoded+=b" "*((-len(encoded))%4)
    raw=bytes(blob)+b"\0"*((-len(blob))%4)
    total=12+8+len(encoded)+8+len(raw)
    return (struct.pack("<III",0x46546C67,2,total)+
            struct.pack("<II",len(encoded),0x4E4F534A)+encoded+
            struct.pack("<II",len(raw),0x004E4942)+raw)


def augment(doc:dict,blob:bytearray):
    names=[node["name"] for node in doc["nodes"]]
    desired=["Prototype_"+name for name in source.ANCHORS]
    if names!=desired or len(doc["meshes"])!=len(names):
        raise ValueError("source composition no longer matches canonical 13-part geometry")
    if doc.get("animations"):
        raise ValueError("do not overwrite a preexisting animation")
    doc["asset"]["generator"]="AEONFALL deterministic mechanical proxy animation v1"
    doc["scenes"][0]["name"]="AEONFALL One True Omnigod Sovereign — source preview"
    doc["scenes"][0]["extras"]={
        "not_skeletal":True,"not_uefn_playtested":True,
        "not_player_controlled":True,"native_editor_import":"not_run",
        "fusion_id":"FUS-001","experimental_titan_id":"FUS-002",
    }
    if "accessors" not in doc or "bufferViews" not in doc:
        raise ValueError("source GLB missing geometry buffers")

    def accessor(values,kind):
        values=list(values)
        if not values:
            raise ValueError("animation accessor empty")
        arity={"SCALAR":1,"VEC3":3,"VEC4":4}[kind]
        if any(len(row)!=arity for row in values):
            raise ValueError("invalid animation vector dimensions")
        if any(not math.isfinite(v) for row in values for v in row):
            raise ValueError("nonfinite timeline value")
        while len(blob)%4:
            blob.append(0)
        pos=len(blob)
        data=struct.pack("<"+str(arity*len(values))+"f",*(v for row in values for v in row))
        blob.extend(data)
        view=len(doc["bufferViews"])
        doc["bufferViews"].append({"buffer":0,"byteOffset":pos,
                                   "byteLength":len(data)})
        out={"bufferView":view,"componentType":5126,"count":len(values),"type":kind}
        if kind=="SCALAR":
            out["min"]=[min(row[0] for row in values)]
            out["max"]=[max(row[0] for row in values)]
        i=len(doc["accessors"])
        doc["accessors"].append(out)
        return i

    timeline=accessor([(t,) for t in TIMES],"SCALAR")
    animation={"name":NAME,"samplers":[],"channels":[]}
    def channel(suffix,kind,values):
        node=names.index("Prototype_"+suffix)
        out=accessor(values,"VEC4" if kind=="rotation" else "VEC3")
        idx=len(animation["samplers"])
        animation["samplers"].append({"input":timeline,"output":out,"interpolation":"LINEAR"})
        animation["channels"].append({"sampler":idx,"target":{"node":node,"path":kind}})

    for suffix,offset in OFFSETS.items():
        p=source.ANCHORS[suffix][0]
        origin=tuple(v/100.0 for v in p)
        frames=[]
        for weight in EXPANSION:
            target=tuple(origin[i]+offset[i]*weight for i in range(3))
            frames.append(tuple(float(v) for v in (target[0],target[2],-target[1])))
        channel(suffix,"translation",frames)

    for suffix,scales in (("AxiomCore",CORE_SCALE),("Eclipse",ECLIPSE_SCALE)):
        channel(suffix,"scale",[(s,s,s) for s in scales])
    channel("Eclipse","rotation",
            [(0.0,math.sin(math.pi*t),0.0,math.cos(math.pi*t))
             for t in ECLIPSE_TURNS])
    if len(animation["channels"])!=len(OFFSETS)+3:
        raise ValueError("incomplete animation channels")
    doc["animations"]=[animation]
    return doc,blob


def generate(output:Path):
    output=output.resolve()
    if not (output/"omnigod_dormant_assembly.glb").exists():
        source.generate(output)
    source_glb=(output/"omnigod_dormant_assembly.glb").read_bytes()
    doc,blob=unpack_glb(source_glb)
    doc,blob=augment(doc,blob)
    generated=pack_glb(doc,blob)
    (output/FILENAME).write_bytes(generated)
    cue={
        "schema_version":1,"id":"AEONFALL-OMNIGOD-FUSION-PREVIEW-001",
        "source_pack":source.PACK_ID,"canonical_mode":"FUS-001",
        "duration_seconds":DURATION_SECONDS,"sample_times_seconds":list(TIMES),
        "preview_glb":FILENAME,"glb_sha256":hashlib.sha256(generated).hexdigest(),
        "animation_name":NAME,"static_geometry":True,"skeletal_rig":False,
        "native_uefn_sequencer":"not_run","native_uefn_compile":"not_run",
        "fortnite_launch_session":"not_run","real_audio_generated":False,
        "real_niagara_generated":False,"owner_entitlement_modified":False,
        "visibility_warning":"replaceable NPC Sequencer binding requires Everyone, owner-only player cinematic separate",
        "beat_notes":"Visual/audio cues are design labels, not emitted audio or Niagara assets",
        "beats":BEATS,"budget":{"keyframes":len(TIMES),"channels":len(doc["animations"][0]["channels"]),
                           "max_glb_bytes":6_000_000},
        "limitation":"Animated static glTF node transforms are a DCC prototype, not UEFN skeletal animation, NPC possession or an imported island.",
    }
    if len(generated)>cue["budget"]["max_glb_bytes"]:
        raise ValueError("source animation exceeded bounded output size")
    (output/TIMELINE).write_text(json.dumps(cue,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return cue


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,default=source.DEFAULT_OUTPUT)
    args=p.parse_args()
    cue=generate(args.output)
    print(json.dumps({key:cue[key] for key in ("id","duration_seconds","glb_sha256","budget")},sort_keys=True))


if __name__=="__main__":
    main()
