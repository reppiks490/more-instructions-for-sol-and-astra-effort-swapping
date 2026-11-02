#!/usr/bin/env python3
"""Author ALL 13 original AEONFALL streamed-region landscape source heightmaps.

- REG-001 reuses its original Ossuary source terrain; no substitute/rewrite.
- REG-002..013 generate deterministic, region-distinct, import-source r16+PNG.
- 253^2 samples, 16-bit grayscale PNG and unsigned little-endian r16.
- Output is source TERRAIN only: no actual level, NPC, HLOD, navmesh, portal,
  published island, UE project, or native UEFN import/test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import zlib

ROOT=Path(__file__).resolve().parents[1]
WORLD=ROOT/"content/world/world_topology.json"
OSSUARY=ROOT/"assets/source/ossuary_starter/landscape"
OUTPUT=ROOT/"dist/full_universe_13_region_terrain"
N=253
SPACING_CM=200
ZSCALE_CM=20
HEIGHT_SAMPLE_UNITS_PER_M=100*128/ZSCALE_CM
REGION_COUNT=13
PLACEMENT_STEP_CM=65000

REGION_SLUGS={
    "REG-001":"ossuary_march",
    "REG-002":"black_sun_meridian",
    "REG-003":"crownless_tempest",
    "REG-004":"leviathan_red_coast",
    "REG-005":"worldroot_cathedral",
    "REG-006":"court_of_broken_hours",
    "REG-007":"infernal_ledgerlands",
    "REG-008":"glass_wyrm_expanse",
    "REG-009":"hollow_astral_synod",
    "REG-010":"null_cartography",
    "REG-011":"titans_last_orchard",
    "REG-012":"axiom_scar",
    "REG-013":"threshold_of_zero",
}
REGION_MOTIFS={
    "REG-001":"original Ossuary March marshland source reused unchanged",
    "REG-002":"long solar dune bands, blown ridges and low eclipse basin",
    "REG-003":"sawtooth storm spine, lightning-pass saddle, steep windward terraces",
    "REG-004":"coastal shelf, blackwater channels and submerged approach",
    "REG-005":"rootlike branching ridges around a gentle woodland court",
    "REG-006":"concentric urban terraces and fractured repeating rings",
    "REG-007":"volcanic mesas, infernal rift cuts and fortified upper flats",
    "REG-008":"oblique crystal spines and wide wyrm migration trench",
    "REG-009":"astral observatory crater and ringed impact basin",
    "REG-010":"broken checkerfield plateaus and a diagonal dimensional rift",
    "REG-011":"titan grave-garden mounds and great skeletal burial grooves",
    "REG-012":"two-sided Axiom fracture valley with shear faults",
    "REG-013":"minimal zero-field platform and symmetrical ascension terraces",
}


def _clamp(v,lo,hi):
    return max(lo,min(hi,v))


def _smoothstep(a,b,v):
    t=_clamp((v-a)/(b-a),0.0,1.0)
    return t*t*(3.0-2.0*t)


def height_m(number:int,x:float,y:float)->float:
    """Distinct authored mathematical terrain silhouettes in [-1,+1] XY."""
    r=math.hypot(x,y)
    angle=math.atan2(y,x)
    detail=0.50*math.sin(13*x+number*0.7)*math.cos(11*y-number*0.3)
    coarse=1.20*math.sin(2.7*x+3*y+number)*math.cos(2.4*y-0.7*x)
    if number==2:  # Black Sun solar dunes
        h=6+6*math.sin(16*x+4*y)**2+2.8*math.sin(9*y-3*x)-9*math.exp(-r*r/0.13)
    elif number==3:  # Tempest mountains
        spine=math.exp(-((x+0.1+0.20*math.sin(4*y))/.25)**2)
        h=4+29*spine*(0.72+0.28*abs(math.sin(18*y)))+4*math.sin(8*x-5*y)
        h-=13*math.exp(-((x-.27)**2+(y+.35)**2)/0.025)
    elif number==4:  # Red Coast
        shore=x+.16*math.sin(5*y)+.06*math.cos(17*y)
        h=2+15*_smoothstep(-.18,.30,shore)-19*(1-_smoothstep(-.6,-.03,shore))
        h-=4*math.exp(-(shore/.16)**2)*abs(math.sin(8*y))
    elif number==5:  # Worldroot
        roots=sum(9*math.exp(-((x-.08*math.sin(k*y*2+.4*k)-
                 (k-3)*.18)**2)/(.032+k*.003)) for k in range(1,6))
        h=2+roots+4*math.sin(4*r-5*angle)**2-9*math.exp(-r*r/0.10)
    elif number==6:  # Broken Hours
        terraces=math.floor((r+.035*math.sin(12*angle))*8)/8
        h=3+14*(1-terraces)+4*math.cos(8*angle+2*r)
        h-=7*math.exp(-((x-.12)**2+(y-.12)**2)/0.035)
    elif number==7:  # Infernal mesa
        mesa=math.tanh(6*(math.sin(5*x)+.58*math.cos(7*y)))
        fissure=math.exp(-((y+.23*math.sin(5*x))/.055)**2)
        h=6+11*mesa-19*fissure+3*math.sin(8*y)
    elif number==8:  # Crystal badlands
        shards=abs(math.sin(8*x+6*y))**6
        trench=math.exp(-((y-.42*x-.12*math.sin(7*x))/.18)**2)
        h=2+24*shards+5*math.cos(4*y)-17*trench
    elif number==9:  # Astral crater
        rim=24*math.exp(-((r-.61)/.11)**2)
        h=5+rim-22*math.exp(-(r/.44)**2)+2*math.sin(9*angle)*math.exp(-r*r)
    elif number==10:  # Null
        cells=5*(math.tanh(4*math.sin(5*math.pi*x))+
                 math.tanh(4*math.cos(4*math.pi*y)))
        seam=math.exp(-((x+y-.1*math.sin(10*x))/.09)**2)
        h=4+cells-16*seam+3*math.sin(4*r)
    elif number==11:  # Titan Orchard
        mounds=sum(12*math.exp(-((x-cx)**2+(y-cy)**2)/.045)
                   for cx,cy in ((-.6,-.5),(-.3,.4),(.35,-.35),(.6,.6),(0,.0)))
        grooves=5*math.exp(-((y-.3*math.sin(7*x))/.07)**2)
        h=2+mounds-grooves+3*math.sin(4*x+3*y)
    elif number==12:  # Axiom Scar
        shear=y-.32*x-.1*math.sin(5*x)
        h=7+12*math.tanh(4*x)-25*math.exp(-(shear/.13)**2)
        h+=5*math.sin(7*y)*math.exp(-abs(shear))
    elif number==13:  # Threshold of Zero
        ring=math.floor(r*6)/6
        h=2+12*(1-ring)-6*_smoothstep(.55,.9,r)
        h+=7*math.exp(-((x/.25)**8+(y/.25)**8))
    else:
        raise ValueError("unknown terrain region")
    # Avoid clipping while retaining real visible regional silhouette.
    return _clamp(h+coarse+detail,-40.,48.)


def build_values(number:int):
    samples=[]
    for row in range(N):
        y=-1.0+2*row/(N-1)
        for col in range(N):
            x=-1.0+2*col/(N-1)
            h=height_m(number,x,y)
            value=round(32768+h*HEIGHT_SAMPLE_UNITS_PER_M)
            if not 0<=value<=65535:
                raise ValueError(f"height sample clipped: region {number}")
            samples.append(value)
    return samples


def _png_chunk(kind:bytes,data:bytes)->bytes:
    return (struct.pack(">I",len(data))+kind+data+
            struct.pack(">I",zlib.crc32(kind+data)&0xffffffff))


def make_png16(samples):
    rows=b"".join(
        b"\x00"+struct.pack(">"+str(N)+"H",*samples[i*N:(i+1)*N])
        for i in range(N)
    )
    return (b"\x89PNG\r\n\x1a\n"+
            _png_chunk(b"IHDR",struct.pack(">IIBBBBB",N,N,16,0,0,0,0))+
            _png_chunk(b"IDAT",zlib.compress(rows,9))+
            _png_chunk(b"IEND",b""))


def sha(path:Path):
    data=path.read_bytes()
    return {"path":path.name,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}


def generate(output:Path):
    output=output.resolve()
    output.mkdir(parents=True,exist_ok=True)
    world=json.loads(WORLD.read_text(encoding="utf-8"))
    regions=world.get("regions",[])
    required=list(REGION_SLUGS)
    actual=[r.get("id") for r in regions]
    if len(regions)!=REGION_COUNT or set(actual)!=set(required):
        raise ValueError("canonical 13-region world topology changed")
    entry=[]
    signatures=set()
    for order,r in enumerate(regions):
        ident=r["id"]
        idx=int(ident[-3:])
        slug=REGION_SLUGS[ident]
        folder=output/ident
        folder.mkdir(exist_ok=True)
        png=folder/(slug+"_253.png")
        r16=folder/(slug+"_253.r16")
        if ident=="REG-001":
            # Preserve the real original region terrain, byte-for-byte.
            png.write_bytes((OSSUARY/"ossuary_march_253.png").read_bytes())
            r16.write_bytes((OSSUARY/"ossuary_march_253.r16").read_bytes())
            original_provenance="assets/source/ossuary_starter/landscape"
        else:
            samples=build_values(idx)
            r16.write_bytes(struct.pack("<"+str(len(samples))+"H",*samples))
            png.write_bytes(make_png16(samples))
            original_provenance="tools/build_all_region_terrain.py"
        samples=struct.unpack("<"+str(N*N)+"H",r16.read_bytes())
        terrain_hash=hashlib.sha256(r16.read_bytes()).hexdigest()
        if terrain_hash in signatures:
            raise ValueError(f"terrain duplicate for {ident}")
        signatures.add(terrain_hash)
        if min(samples)==max(samples):
            raise ValueError(f"flat un authored landscape for {ident}")
        # Geographical coordinates are SOURCE PLANNING OFFSETS only,
        # NOT validated World Partition region placements.
        logical_x=order%4
        logical_y=order//4
        entry.append({
            "region_id":ident,"name":r["name"],"theme":r["theme"],
            "motif":REGION_MOTIFS[ident],"neighbor_ids":r["neighbors"],
            "source_terrain_provenance":original_provenance,
            "r16":f"{ident}/{r16.name}","png":f"{ident}/{png.name}",
            "r16_sha256":sha(r16)["sha256"],"png_sha256":sha(png)["sha256"],
            "r16_bytes":sha(r16)["bytes"],"png_bytes":sha(png)["bytes"],
            "min_sample":min(samples),"max_sample":max(samples),
            "min_height_m":round((min(samples)-32768)/HEIGHT_SAMPLE_UNITS_PER_M,3),
            "max_height_m":round((max(samples)-32768)/HEIGHT_SAMPLE_UNITS_PER_M,3),
            "recommended_region_plan_offset_cm":[logical_x*PLACEMENT_STEP_CM,
                                                    logical_y*PLACEMENT_STEP_CM,0],
            "not_assembled_in_uefn":True,"navmesh_not_verified":True,
            "mobile_hlod_not_baked":True,
        })
    manifest={
        "schema_version":1,
        "id":"AEONFALL-FULL-THIRTEEN-REGION-TERRAIN-SOURCE-001",
        "world_name":"AEONFALL",
        "terrain_region_count":len(entry),
        "original_authored_ossuary_reused":True,
        "generated_region_count":12,
        "source_terrain_only":True,
        "region_completion_claim":False,
        "uefn_landscape_import":"not_run",
        "world_partition_assembled":"not_run",
        "navigation_compiled":"not_run",
        "fortnite_mobile_playtest":"not_run",
        "publishing_memory_calculated":"not_run",
        "canonical_world_source":"content/world/world_topology.json",
        "format":{
            "resolution":[N,N],
            "r16":"16-bit unsigned little-endian, row-major, no header",
            "png":"16-bit grayscale PNG with matching values",
            "xy_spacing_cm":SPACING_CM,"z_scale_cm":ZSCALE_CM,
            "sample_height":"height_cm = (value - 32768) * z_scale_cm / 128",
            "landscape_component_grid":[4,4],
            "quads_per_section":63,
            "landscape_extent_cm":[(N-1)*SPACING_CM,(N-1)*SPACING_CM],
        },
        "regions":entry,
        "limitations":[
            "Original source terrain is not a fully built streamed UEFN region.",
            "Portal adjacency is a topology contract, not physical traversable connections.",
            "No landmarks, spawned actors, NPC ecosystems, quests, imported UEFN assets, cooked memory or mobile proof.",
            "REG-001 original Ossuary terrain is reused exactly; other twelve are original authored mathematical heightmaps requiring artistic review.",
        ],
    }
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=OUTPUT)
    args=parser.parse_args()
    result=generate(args.output)
    print(f"Generated {result['terrain_region_count']} canonical source landscapes,"
          f" including original Ossuary + {result['generated_region_count']} distinct terrains.")
    print("Real UEFN region assembly and mobile playtest: NOT RUN.")


if __name__=="__main__":
    main()
