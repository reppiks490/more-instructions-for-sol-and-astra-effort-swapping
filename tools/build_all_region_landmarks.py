#!/usr/bin/env python3
"""Build 39 ORIGINAL modular landmark source meshes covering ALL 13 AEONFALL regions.

Three distinct static models per canonical region: Sanctum, ThresholdGate and
EventBeacon. Geometry is closed per-solid and source-authored; materials are
preview metadata. Placements sample the ACTUAL regional heightmap values.
This builds no actual UEFN level, NPC, quest, portal or native collision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_ossuary_starter_assets as geometry
import build_all_region_terrain as terrain

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT=ROOT/"dist/full_universe_region_landmarks"
PACK_ID="AEONFALL-THIRTEEN-REGION-LANDMARK-SOURCE-001"
KINDS=("Sanctum","ThresholdGate","EventBeacon")
MAX_TRIANGLES_PER_MESH=2600
MAX_TRIANGLES_TOTAL=45000
MAX_PARTS=39
# Regional base, structure, ornament, emissive, trim. Not UEFN native materials.
COLORS={
    1:((.09,.11,.13),(.46,.41,.36),(.17,.27,.22),(.20,.62,.45),(.40,.10,.12)),
    2:((.18,.13,.12),(.63,.40,.17),(.21,.13,.18),(.98,.41,.11),(.65,.19,.09)),
    3:((.10,.16,.23),(.36,.48,.62),(.18,.24,.31),(.25,.68,.98),(.76,.79,.90)),
    4:((.11,.13,.19),(.27,.39,.42),(.17,.21,.28),(.75,.08,.17),(.60,.48,.42)),
    5:((.09,.19,.13),(.30,.36,.20),(.17,.29,.14),(.35,.86,.30),(.67,.45,.18)),
    6:((.14,.11,.20),(.46,.36,.51),(.24,.20,.27),(.89,.73,.42),(.20,.62,.83)),
    7:((.21,.10,.10),(.40,.21,.18),(.14,.12,.12),(.88,.09,.07),(.96,.47,.14)),
    8:((.12,.14,.24),(.35,.48,.62),(.19,.25,.36),(.32,.85,.91),(.76,.43,.91)),
    9:((.10,.10,.22),(.36,.31,.55),(.20,.21,.37),(.61,.57,.98),(.84,.70,.42)),
   10:((.07,.08,.10),(.33,.36,.39),(.17,.18,.24),(.41,.98,.87),(.72,.27,.66)),
   11:((.19,.19,.17),(.54,.47,.36),(.28,.32,.23),(.87,.60,.23),(.66,.24,.18)),
   12:((.18,.09,.16),(.52,.23,.47),(.20,.13,.30),(.96,.22,.64),(.51,.36,.97)),
   13:((.035,.035,.045),(.68,.69,.76),(.12,.12,.14),(.95,.95,.99),(.49,.10,.16)),
}
MOTIF={
 1:"ribbed necrotic reliquary and black-water ossuary",
 2:"eclipse-disc solar geometry and radiant monoliths",
 3:"forked lightning spines and storm conductor crowns",
 4:"colossal leviathan ribs, tides and drowned altars",
 5:"intertwined worldroot trunks and concentric canopy",
 6:"fractured timewheel rings and broken clock hands",
 7:"infernal furnace vents and volcanic siege towers",
 8:"vertical faceted crystalline wyrm teeth",
 9:"astral observatory hoops and lunar orrery",
10:"offset null-plane stacks and displaced geometry",
11:"titan remains, enormous fossil spines and bones",
12:"sheared magenta axiom monolith and divergent halves",
13:"near-silent black/white void plane and ritual axis",
}
SITE_CANDIDATES={
    "Sanctum":(-128.0,-102.0),
    "ThresholdGate":(118.0,-83.0),
    "EventBeacon":(64.0,143.0),
}
SOURCE_ROLE={
    "Sanctum":"regional_identity_landmark",
    "ThresholdGate":"visual_gateway_shell_not_travel_device",
    "EventBeacon":"regional_event_locator_not_gameplay_device",
}


def palette(number):
    shades=COLORS[number]
    names=("Groundstone","LoadBearing","Signature","InnerGlow","RitualMetal")
    values=[]
    for n,(name,rgb) in enumerate(zip(names,shades)):
        is_glow=(n==3)
        values.append((f"REG{number:03d}_{name}",(*rgb,1.0),
                       (0.48 if n==4 else 0.11),
                       (0.40 if n==4 else 0.74),
                       tuple(v*0.55 for v in rgb) if is_glow else None))
    return values


def _ring(mesh,cx,cz,r_inner,r_outer,depth,count,mat,prefix):
    for step in range(count):
        a=math.tau*step/count
        b=math.tau*(step+1)/count
        # Quadrilaterals are convex; concave polygons are not accepted by
        # the source mesh exporter and must NEVER bypass manifold validation.
        polygon=((cx+r_inner*math.cos(a),cz+r_inner*math.sin(a)),
                 (cx+r_outer*math.cos(a),cz+r_outer*math.sin(a)),
                 (cx+r_outer*math.cos(b),cz+r_outer*math.sin(b)),
                 (cx+r_inner*math.cos(b),cz+r_inner*math.sin(b)))
        mesh.xz_extrusion(polygon,depth,mat,f"{prefix}_{step:02d}")


def _ornament(mesh,number,cx,base,scale):
    """Actually distinct regional structural silhouettes, not recolored copies."""
    def box(x,y,z,w,d,h,mat,label):
        mesh.box((cx+x*scale,y*scale,base+z*scale),
                 (w*scale,d*scale,h*scale),mat,label)
    def taper(x,y,z0,z1,r0,r1,mat,label,sides=6):
        mesh.taper((cx+x*scale,y*scale),r0*scale,r1*scale,
                   base+z0*scale,base+z1*scale,mat,label,sides)
    def xz(poly,depth,mat,label):
        mesh.xz_extrusion(tuple((cx+x*scale,base+z*scale) for x,z in poly),
                          depth*scale,mat,label)
    def ring(x,z,r0,r1,depth,count,mat,label):
        _ring(mesh,cx+x*scale,base+z*scale,r0*scale,r1*scale,
              depth*scale,count,mat,label)

    if number==1:
        for j,x in enumerate((-2.25,-1.35,-.45,.45,1.35,2.25)):
            xz(((x-.11,.3),(x+.11,.3),(x+.18,5.8-abs(x)*.4),
                (x,6.9-abs(x)*.45),(x-.18,5.8-abs(x)*.4)),
               .40,1,f"blackwater_bone_rib_{j}")
        taper(0,0,.0,2.8,.8,.27,2,"reliquary_crown")
        box(0,-.80,1.2,.35,.18,2.3,3,"jade_death_seal")
    elif number==2:
        ring(0,5.5,2.3,2.75,.38,16,1,"eclipsed_sun_rim")
        for j in range(12):
            a=j*math.tau/12
            x,z=3.15*math.cos(a),5.5+3.15*math.sin(a)
            xz(((x-.16,z-.20),(x+.16,z-.20),
                (x+.12,z+.40),(x,z+.70),(x-.12,z+.40)),
               .24,4,f"sun_spear_{j}")
        taper(0,0,0,3.6,.75,.17,2,"solar_altar")
        box(0,-.2,5.5,.32,.18,1.50,3,"eclipse_axis")
    elif number==3:
        for j,x in enumerate((-1.8,0,1.8)):
            xz(((x-.40,.0),(x+.38,.0),(x+.09,2.8),
                (x+.60,3.45),(x-.15,6.8),(x-.47,4.25)),
               .58,1,f"forked_storm_rod_{j}")
            box(x,-.42,3.1,.16,.13,2.4,3,f"storm_plasma_{j}")
        ring(0,6.8,.45,.72,.35,8,4,"tempest_crown")
    elif number==4:
        for j,offset in enumerate((-2.7,-1.35,0,1.35,2.7)):
            xz(((offset-.34,.15),(offset+.36,.15),
                (offset+.30,4.8),(offset,6.7-abs(offset)*.35)),
               .62,1,f"leviathan_rib_{j}")
            box(offset,.54,2.0,.15,.16,2.5,2,f"drowned_scale_{j}")
        box(0,-.9,1.1,4.4,.25,.25,3,"blood_tide_line")
    elif number==5:
        for j,offset in enumerate((-2.9,-1.7,-.5,.7,1.9)):
            xz(((offset-.48,.1),(offset+.30,.1),(offset+.45,3.1),
                (offset+.10,5.9),(offset-.32,4.1)),
               .46,1,f"ancient_root_{j}")
        ring(0,5.8,2.6,2.9,.30,12,2,"worldroot_bough_crown")
        box(0,-.50,3.2,.3,.18,3.2,3,"heartwood_channel")
    elif number==6:
        ring(0,5.1,2.4,2.85,.38,16,1,"broken_hour_outer")
        ring(0,5.1,1.6,1.83,.27,16,4,"chronal_inner")
        for j,(x,z) in enumerate(((-1.4,5.6),(1.3,3.9))):
            xz(((0,5.1),(x-.15,z-.10),(x+.18,z+.16)),
               .25,3,f"ruptured_clock_hand_{j}")
        box(0,-.32,2.1,.75,.32,3.4,2,"memory_pendulum")
    elif number==7:
        for j,x in enumerate((-2.5,0,2.5)):
            taper(x,0,.2,4.6,1.15,.83,1,f"hellforge_shaft_{j}",4)
            taper(x,0,4.6,6.0,.88,.42,2,f"infernal_chimney_{j}",4)
            box(x,-.95,2.65,.74,.18,3.0,3,f"furnace_flame_{j}")
        box(0,-1.05,1.0,5.0,.18,.23,4,"iron_contract_line")
    elif number==8:
        for j,(x,y,h) in enumerate(((-2.4,0,6.3),(-1.1,.35,4.7),
                                    (.7,-.3,7.4),(2.25,.1,5.9))):
            taper(x,y,.05,h,.85,.08,1,f"wyrm_crystal_{j}",4)
            taper(x,y,h,h+1.2,.20,.01,3,f"crystal_tip_{j}",4)
        ring(0,2.8,2.75,2.94,.16,8,4,"shard_reflection_band")
    elif number==9:
        ring(0,5.8,2.55,2.89,.30,18,1,"astral_orbit_outer")
        ring(.55,5.2,1.55,1.80,.30,12,4,"lunar_orbit_inner")
        taper(0,0,.3,5.9,.45,.23,2,"observatory_needle",8)
        box(0,-.52,3.1,.18,.12,4.0,3,"star_axis")
        for j,x in enumerate((-2.0,2.0)):
            taper(x,0,.2,2.4,.30,.28,1,f"astral_pedestal_{j}")
    elif number==10:
        for j,(x,z) in enumerate(((-2.2,1.6),(-1.2,3.2),
                                   (.3,4.5),(1.45,6.0),(2.4,7.1))):
            box(x,(-1)**j*.35,z,1.6,.93,.54,1,f"null_displaced_plate_{j}")
            box(x+.28,(-1)**j*.43,z+.20,.78,.13,.10,3,f"null_rift_seam_{j}")
        box(0,0,.6,4.6,1.6,.25,2,"impossible_ground_plane")
    elif number==11:
        for j,x in enumerate((-2.4,-1.2,0,1.2,2.4)):
            xz(((x-.20,0),(x+.30,0),(x+.37,4.5),
                (x,7.2-abs(x)*.55),(x-.41,4.5)),
               .52,1,f"titan_spinal_fossil_{j}")
        taper(0,0,0,1.3,.9,.54,2,"grave_garden_skull")
        box(0,-.78,1.3,.42,.18,3.1,4,"titan_artery")
    elif number==12:
        xz(((-2.7,.1),(-.80,.1),(-.80,7.8),(-2.4,6.3)),
           .80,1,"axiom_left_rupture")
        xz(((.80,.1),(2.7,.1),(2.2,8.2),(.80,6.1)),
           .80,1,"axiom_right_rupture")
        box(-1.52,-.48,3.1,.18,.13,3.5,3,"left_law_rift")
        box(1.52,-.48,4.7,.18,.13,3.1,3,"right_law_rift")
        ring(0,4.3,.45,.82,.25,8,4,"broken_axiom")
    elif number==13:
        for j,x in enumerate((-2.45,2.45)):
            box(x,0,3.8,.68,.67,7.4,1,f"primordial_silent_plane_{j}")
        box(0,-.08,5.8,3.8,.38,.18,3,"sovereign_white_threshold")
        ring(0,5.8,1.5,1.66,.12,16,2,"zero_empty_corona")
        box(0,-.1,.4,3.0,1.2,.13,4,"chosen_seal")
    else:
        raise ValueError("unknown canonical regional motif")


def module(number,kind):
    ident=f"REG{number:03d}"
    mesh=geometry.Mesh(f"SM_AEON_{ident}_{kind}",
                       f"{MOTIF[number]}; original {kind} source blockout.")
    if kind=="Sanctum":
        mesh.box((0,0,-.25),(17,16,.5),0,"broad_sanctum_foundation")
        for j,x in enumerate((-7.1,7.1)):
            mesh.box((x,0,2.7),(.9,11.8,5.4),1,f"sanctum_outer_wall_{j}")
        for j,y in enumerate((-6.8,6.8)):
            mesh.box((0,y,.60),(14.5,.90,1.20),1,f"sanctum_ceremonial_threshold_{j}")
        mesh.box((0,0,.16),(9.2,7.5,.32),4,"inner_ritual_dais")
        _ornament(mesh,number,0,.40,1.0)
    elif kind=="ThresholdGate":
        for side in (-1,1):
            x=side*6.4
            mesh.box((x,0,3.9),(2.6,2.3,7.8),1,f"gateway_tower_{side}")
            mesh.box((x,-1.28,1.75),(.20,.17,2.7),3,f"gateway_glow_{side}")
            _ornament(mesh,number,x,1.0,.40)
        # Maintains 9.3m+ clear width between original towers at ground.
        mesh.box((0,0,9.45),(16.4,2.1,1.4),4,"gateway_high_lintel")
        mesh.box((0,0,10.5),(3.2,1.6,.55),2,"gateway_keystone")
    elif kind=="EventBeacon":
        mesh.taper((0,0),4.3,4.3,-.3,.13,0,"locator_lower_pedestal",8)
        mesh.taper((0,0),2.8,2.8,.13,.62,4,"locator_upper_pedestal",8)
        mesh.taper((0,0),1.12,.72,.62,2.2,1,"event_beacon_column",8)
        _ornament(mesh,number,0,1.35,.73)
        for j in range(8):
            a=math.tau*j/8
            mesh.box((3.65*math.cos(a),3.65*math.sin(a),.74),
                     (.27,.25,.54),2,f"beacon_ring_mark_{j}")
    else:
        raise ValueError("unknown landmark kind")
    return mesh


def height_samples(ident):
    if ident=="REG-001":
        data=(terrain.OSSUARY/"ossuary_march_253.r16").read_bytes()
        return struct.unpack("<"+str(terrain.N**2)+"H",data),(-252.,-152.)
    no=int(ident[-3:])
    return terrain.build_values(no),(-252.,-252.)


def terrain_at(samples,southwest,x,y):
    # source x/y in meters. Nearest source sample is exact, not native terrain.
    i=round((x-southwest[0])/2)
    j=round((y-southwest[1])/2)
    if not 0<=i<terrain.N or not 0<=j<terrain.N:
        raise ValueError("landmark planned outside landscape source footprint")
    value=samples[j*terrain.N+i]
    return (value-32768)/terrain.HEIGHT_SAMPLE_UNITS_PER_M


def best_anchor(samples,sw,kind,ident):
    tx,ty=SITE_CANDIDATES[kind]
    if ident=="REG-001" and kind=="EventBeacon":
        tx,ty=143.0,151.0  # preserve authored Ossuary throne at x~0,y150
    offsets=((0,0),(-12,0),(12,0),(0,12),(0,-12),(-24,12),(24,-12))
    candidates=[]
    for dx,dy in offsets:
        x,y=tx+dx,ty+dy
        heights=[terrain_at(samples,sw,x+ox,y+oy) for ox,oy in
                 ((0,0),(-8,0),(8,0),(0,-8),(0,8))]
        spread=max(heights)-min(heights)
        candidates.append((round(spread,7),abs(dx)+abs(dy),x,y,heights[0]))
    slope,_,x,y,z=min(candidates)
    return {"center_local_m":[x,y,round(z,5)],
            "footprint_relief_m":round(slope,5),
            "terrain_foundation_clearance_m":.65,
            "requires_editor_grading":slope>.65,
            "terrain_sample_basis":"raw 253x253 R16 source, 2m spacing; placement not engine tested"}


def encode_region_glb(meshes,placements,region_id):
    # The shared exporter has an Ossuary-specific scene title. Rewrite only
    # the JSON chunk and keep all actual geometry/image bytes unchanged.
    data=geometry.encode_glb(meshes,placements)
    json_length,json_kind=struct.unpack_from("<II",data,12)
    if json_kind!=0x4e4f534a:
        raise ValueError("bad exporter JSON chunk")
    doc=json.loads(data[20:20+json_length])
    doc["asset"]["generator"]="AEONFALL 13-region original landmark source v1"
    doc["scenes"][0]["name"]=f"{region_id} original landmark source, NOT UEFN imported"
    doc["scenes"][0]["extras"]={"source_only":True,"region_id":region_id,
                                "native_uefn_import":"not_run",
                                "actual_landscape_alignment":"not_run"}
    encoded=json.dumps(doc,separators=(",",":"),sort_keys=True).encode()
    encoded+=b" "*((-len(encoded))%4)
    offset=20+json_length
    bin_length,bin_kind=struct.unpack_from("<II",data,offset)
    if bin_kind!=0x004e4942:
        raise ValueError("bad exporter binary chunk")
    binary=data[offset+8:offset+8+bin_length]
    total=12+8+len(encoded)+8+len(binary)
    return (struct.pack("<III",0x46546c67,2,total)+
            struct.pack("<II",len(encoded),0x4e4f534a)+encoded+
            struct.pack("<II",len(binary),0x004e4942)+binary)


def file_hash(file,output):
    raw=file.read_bytes()
    return {"path":file.relative_to(output).as_posix(),
            "bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}


def build(output:Path):
    output=output.resolve()
    output.mkdir(parents=True,exist_ok=True)
    topology=json.loads(terrain.WORLD.read_text(encoding="utf-8"))
    regions=topology.get("regions",[])
    if [x["id"] for x in regions]!=list(terrain.REGION_SLUGS):
        raise ValueError("world topology changed or region order/number not canonical")
    prior_palette=geometry.MATERIALS
    region_records=[]
    all_files=[]
    total_triangles=0
    try:
        for world_region in regions:
            ident=world_region["id"]
            number=int(ident[-3:])
            geometry.MATERIALS=palette(number)
            meshes=[module(number,k) for k in KINDS]
            geometry.check_geometry(meshes)
            triangles=sum(sum(len(indices)//3 for indices in m.material_indices.values())
                          for m in meshes)
            if triangles>MAX_TRIANGLES_PER_MESH*len(KINDS):
                raise ValueError(f"{ident}: triangle capacity exceeded")
            samples,sw=height_samples(ident)
            sub=output/ident
            (sub/"meshes").mkdir(parents=True,exist_ok=True)
            entries=[]
            placements=[]
            for k,m in zip(KINDS,meshes):
                count=sum(len(v)//3 for v in m.material_indices.values())
                if count>MAX_TRIANGLES_PER_MESH:
                    raise ValueError(f"{m.name}: per-mesh triangle limit exceeded")
                anchor=best_anchor(samples,sw,k,ident)
                x,y,z=anchor["center_local_m"]
                transform=[round(x*100),round(y*100),round((z+.65)*100)]
                placement={
                    "name":f"{ident}_{k}_SourceProxy","mesh":m.name,
                    "location_cm":transform,"rotation_deg":[0,0,0],
                    "scale":[1,1,1],"zone":ident,"role":SOURCE_ROLE[k],
                }
                placements.append(placement)
                root=sub/"meshes"/m.name
                root.with_suffix(".glb").write_bytes(encode_region_glb([m],None,ident))
                geometry.write_obj(m,root.with_suffix(".obj"))
                entries.append({"kind":k,"mesh":m.name,"triangles":count,
                                "bounds_m":m.bounds(),"solids":len(m.solids),
                                "placement":placement,"terrain_contact":anchor,
                                "signature":MOTIF[number],
                                "source_only":True,
                                "uses_generated_assets_not_uefn_import":True})
            (sub/"landmark_preview.glb").write_bytes(encode_region_glb(meshes,placements,ident))
            for file in sorted(sub.rglob("*")):
                if file.is_file():
                    all_files.append(file_hash(file,output))
            total_triangles+=triangles
            region_records.append({
                "id":ident,"name":world_region["name"],
                "theme":world_region["theme"],"neighbors":world_region["neighbors"],
                "source_landscape_origin_m":list(sw),
                "source_terrain":"tools/build_all_region_terrain.py",
                "palette":[{"name":m[0],"color":list(m[1]),"emissive":m[4]}
                           for m in palette(number)],
                "motif":MOTIF[number],
                "source_modules":entries,
                "assembly_glb":f"{ident}/landmark_preview.glb",
                "triangles":triangles,
                "uefn_import":"not_run","navmesh":"not_run",
                "streaming_hlod":"not_run","mobile_playtest":"not_run",
            })
    finally:
        geometry.MATERIALS=prior_palette
    if len(region_records)!=13 or len(all_files)!=(13*10) or total_triangles>MAX_TRIANGLES_TOTAL:
        raise ValueError("landmark source coverage or triangle budget violation")
    all_files.sort(key=lambda x:x["path"])
    manifest={
        "schema_version":1,"id":PACK_ID,
        "source_tool":"tools/build_all_region_landmarks.py",
        "canonical_world":"content/world/world_topology.json",
        "source_terrain":"tools/build_all_region_terrain.py",
        "source_artifact_only":True,
        "native_uefn_import":"not_run",
        "actual_region_completion":False,
        "npc_navmesh_quest_or_streaming_verified":False,
        "fortnite_mobile_playtest":"not_run",
        "source_module_count":13*len(KINDS),
        "region_count":len(region_records),
        "unique_module_target":39,
        "total_triangles":total_triangles,
        "max_triangles_per_module":MAX_TRIANGLES_PER_MESH,
        "max_triangles_total":MAX_TRIANGLES_TOTAL,
        "regions":region_records,
        "files":all_files,
        "limitations":[
          "Generated 39 original static architectural source blockouts; not production-finished environments.",
          "The native UEFN project, gameplay devices, materials, terrain sculpt integration, collision, navmesh and HLOD are unverified.",
          "Placement anchors are sampled from R16 source. Artist-approved landscaping and actual editor alignment are required.",
          "Emissive material preview is not a native Niagara effect or real lighting; gate is a visual shell, not actual travel.",
          "Geometry does not alone satisfy all nine reviewed universe-first source categories for a region."
        ]
    }
    (output/"manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    return manifest


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",type=Path,default=DEFAULT_OUTPUT)
    opts=ap.parse_args()
    m=build(opts.output)
    print(json.dumps({"regions":m["region_count"],"modules":m["source_module_count"],
                      "triangles":m["total_triangles"],"files":len(m["files"])},sort_keys=True))
    print("No native UEFN import, real NPC spawning or Fortnite mobile test performed.")


if __name__=="__main__":
    main()
