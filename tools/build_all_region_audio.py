#!/usr/bin/env python3
"""Make 39 real ORIGINAL regional audio cues (13 regions × 3 distinct WAVs).

Deterministic, bounded 16-bit PCM; no external libraries, AI samples or music
licensing. These are raw DCC/sound-design SOURCE layers, not imported UEFN
sound cues, real NPC triggers or claimed Fortnite mobile playback.
"""
from __future__ import annotations

import argparse
from array import array
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import wave

sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_all_region_terrain as terrain

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT=ROOT/"dist/full_universe_region_audio"
PACK_ID="AEONFALL-THIRTEEN-REGION-ORIGINAL-AUDIO-SOURCE-001"
SAMPLE_RATE=24000
CHANNELS=1
SAMPLE_WIDTH=2
DURATION={"ambient":4.0,"danger":1.2,"navigation":0.42}
MAX_ABS_PCM=19000
KINDS=tuple(DURATION)
# Pitches are source cycles per ambient loop; integer bins ensure clean
# periodic Fourier layers. Different dissonance/contour is authored by region.
SONIC_IDENTITIES={
 1:(171,329,581,9,"bone resonance and blackwater pressure"),
 2:(223,421,739,11,"dry eclipse gong and solar wind"),
 3:(263,503,887,13,"storm conductor whine and electrical arcing"),
 4:(137,293,487,7,"submerged leviathan lament and tidal swell"),
 5:(199,367,643,8,"worldroot wooden overtone and canopy breath"),
 6:(241,457,823,17,"fractured clock chimes and temporal beating"),
 7:(163,311,601,12,"infernal furnace harmonics and iron pulse"),
 8:(317,607,941,15,"cold crystal glass resonance and shard shimmer"),
 9:(283,557,859,6,"hollow orrery and celestial low bell"),
10:(307,593,997,19,"null-tone phase displacement and unstable plates"),
11:(151,347,677,10,"titan fossil resonance and heavy ground groan"),
12:(271,523,881,16,"axiom law dissonance and magenta fracture"),
13:(101,601,1201,5,"near-silent singularity and distant zero-tone"),
}
MOBILITY_CUES={
    "ambient":"optional reduced-volume local environmental layer",
    "danger":"priority threat warning with distinct audible onset; pair with non-color HUD",
    "navigation":"short regional waypoint confirmation; pair with tactile/visual route cue",
}


def frames_for(kind:str) -> int:
    return round(DURATION[kind]*SAMPLE_RATE)


def _env(t):
    """Finite audio event onset/decay with zero at both endpoints."""
    return math.sin(math.pi*max(0.0,min(1.0,t)))**2


def signal(number:int,kind:str,index:int,total:int):
    a,b,c,mod,_=SONIC_IDENTITIES[number]
    theta=math.tau*index/total
    u=index/(total-1)
    variant=number*.137
    if kind=="ambient":
        # An EXACT cyclic set of sine bins, avoiding random-wave seams;
        # layers incorporate region-specific modal intervals and modulation.
        under=.20*math.sin(a*theta)
        bell=.13*math.sin(b*theta+variant)
        air=.075*math.sin(c*theta+.2*number)
        beating=.095*math.sin((b-a)*theta)*(0.60+0.40*math.sin(mod*theta))
        flecks=.025*math.sin((c+mod*17)*theta+variant)
        # reduced-level voice for Minimal Zero rather than loud pseudo-silence
        return (under+bell+air+beating+flecks)*(.63 if number==13 else 1.)
    if kind=="danger":
        # A short ascending sweep; unique contour for all 13. Alternate
        # layers announce danger without requiring visual perception.
        f0=90+number*13
        f1=490+number*37
        t=u*DURATION[kind]
        phase=math.tau*(f0*t + (f1-f0)*t*t/(2*DURATION[kind]))
        resonant=.24*math.sin(phase)
        call=.16*math.sin((260+number*23)*math.tau*t+variant)
        gated=.075*math.sin((70+number*7)*math.tau*t)
        return _env(u)*(resonant+call+gated)
    if kind=="navigation":
        t=u*DURATION[kind]
        base=430+number*37
        top=base*1.497
        primary=.31*math.sin(math.tau*base*t)
        harmony=.17*math.sin(math.tau*top*t+variant)
        decay=(1-u)**1.3
        return _env(u)*decay*(primary+harmony)
    raise ValueError(f"unexpected source audio kind {kind}")


def pcm(number,kind):
    if number not in SONIC_IDENTITIES or kind not in KINDS:
        raise ValueError("unknown region/source cue kind")
    count=frames_for(kind)
    # 32767 × at-most-0.475 theoretical peak = < 15565 PCM.
    values=[]
    for i in range(count):
        value=round(signal(number,kind,i,count)*32767)
        if not -MAX_ABS_PCM<=value<=MAX_ABS_PCM:
            raise ValueError("unsafe/clipped audio source amplitude")
        values.append(value)
    return values


def wav_bytes(pcm_values):
    frames=struct.pack("<"+str(len(pcm_values))+"h",*pcm_values)
    # Explicit deterministic RIFF/WAVE/fmt/data output, no timestamps or
    # metadata chunks, so byte hashes are stable across Windows/Linux.
    byte_rate=SAMPLE_RATE*CHANNELS*SAMPLE_WIDTH
    block_align=CHANNELS*SAMPLE_WIDTH
    riff_size=4+(8+16)+(8+len(frames))
    return (b"RIFF"+struct.pack("<I",riff_size)+b"WAVE"+
            b"fmt "+struct.pack("<IHHIIHH",16,1,CHANNELS,SAMPLE_RATE,
                                 byte_rate,block_align,SAMPLE_WIDTH*8)+
            b"data"+struct.pack("<I",len(frames))+frames)


def audio_metrics(values,kind):
    if not values:
        raise ValueError("empty audio sample stream")
    peak=max(abs(v) for v in values)
    rms=math.sqrt(sum(v*v for v in values)/len(values))
    return {"frames":len(values),"seconds":DURATION[kind],
            "peak_pcm":peak,"rms_pcm":round(rms,3),
            "first_pcm":values[0],"last_pcm":values[-1],
            "seam_delta_pcm":abs(values[0]-values[-1])}


def build(output:Path):
    output=output.resolve()
    output.mkdir(parents=True,exist_ok=True)
    topology=json.loads(terrain.WORLD.read_text(encoding="utf-8"))
    regions=topology["regions"]
    if [r["id"] for r in regions]!=list(terrain.REGION_SLUGS):
        raise ValueError("world topology changed or order lost")
    inventory=[]
    entries=[]
    signatures=set()
    for world in regions:
        ident=world["id"]
        number=int(ident[-3:])
        folder=output/ident
        folder.mkdir(parents=True,exist_ok=True)
        regional=[]
        for kind in KINDS:
            values=pcm(number,kind)
            metrics=audio_metrics(values,kind)
            if metrics["peak_pcm"]>MAX_ABS_PCM or metrics["rms_pcm"]<200:
                raise ValueError(f"invalid source loudness for {ident}/{kind}")
            if metrics["seam_delta_pcm"]>700:
                raise ValueError(f"audible source loop/cue boundary click for {ident}/{kind}")
            file=folder/f"{ident}_{kind}_original.wav"
            data=wav_bytes(values)
            file.write_bytes(data)
            signature=hashlib.sha256(data).hexdigest()
            if signature in signatures:
                raise ValueError("duplicated regional audio asset bytes")
            signatures.add(signature)
            relative=file.relative_to(output).as_posix()
            entry={"kind":kind,"role":MOBILITY_CUES[kind],"file":relative,
                   "bytes":len(data),"sha256":signature,
                   "metrics":metrics,
                   "uefn_audio_cue_bound":False,
                   "real_mobile_playback":"not_run",
                   "loudness_lufs_measured":"not_run"}
            regional.append(entry)
            inventory.append({"path":relative,"bytes":len(data),"sha256":signature})
        a,b,c,mod,description=SONIC_IDENTITIES[number]
        entries.append({
            "id":ident,"name":world["name"],"neighbors":world["neighbors"],
            "sonic_identity":description,
            "ambient_loop_cycles":[a,b,c],
            "modulation_cycles":mod,
            "sources":regional,
            "editor_import":"not_run",
            "sound_mix_and_occlusion":"not_run",
            "subtitles_cue_binding":"not_run",
        })
    manifest={
        "schema_version":1,"id":PACK_ID,
        "source_generator":"tools/build_all_region_audio.py",
        "origin":"original deterministic mathematical PCM synthesis",
        "external_samples_used":False,
        "license":"original generated source; no third-party sample files",
        "region_count":len(entries),"cue_count":len(inventory),
        "sample_rate_hz":SAMPLE_RATE,"channels":CHANNELS,
        "sample_format":"PCM signed 16-bit little endian RIFF WAV mono",
        "max_peak_abs_pcm":MAX_ABS_PCM,
        "source_audio_only":True,
        "native_uefn_import":"not_run",
        "native_audio_device_binding":"not_run",
        "fortnite_mobile_playtest":"not_run",
        "automatic_gameplay_triggers_implemented":False,
        "regions":entries,
        "files":sorted(inventory,key=lambda x:x["path"]),
        "mobile_accessibility_requirements":[
            "Threat cue pairs with shape/icon and readable high-priority visual telegraph.",
            "Navigation cue pairs with text and haptic-capable interaction when supported.",
            "Provide user-facing volume controls and respect platform audio mixing/voice chat.",
            "Validate native loudness, hearing comfort, simultaneous cue limits, spatial mix and optional subtitle semantics in UEFN.",
        ],
        "limitations":[
            "39 actual source WAV files are not native Fortnite Sound Cues, Audio Player device bindings, or fully composed regional soundscapes.",
            "No native UE audio compression/memory, streaming concurrency, player-specific spatialization, editor import or iOS gameplay was performed.",
            "These are low-cost original tonal/atmospheric stems requiring final professional sound-design, mixing and device authoring.",
        ]
    }
    if len(inventory)!=39 or len(entries)!=13:
        raise ValueError("full-universe source audio scope incomplete")
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",
                                        encoding="utf-8")
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,default=DEFAULT_OUTPUT)
    opts=p.parse_args()
    m=build(opts.output)
    print(json.dumps({"regions":m["region_count"],"wav_sources":m["cue_count"],
                      "source_only":m["source_audio_only"]},sort_keys=True))
    print("No native UEFN audio import/trigger or Fortnite mobile audio playback verified.")


if __name__=="__main__":
    main()
