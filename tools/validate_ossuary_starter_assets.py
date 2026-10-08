#!/usr/bin/env python3
"""Validate actual generated GLBs/OBJs, collision recipes and dungeon clear lanes.

Checks source artifacts only. This cannot replace UEFN import, navmesh, memory,
Verse compilation, or Launch Session verification.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACK = ROOT / "assets/source/ossuary_starter"


def read_glb(path):
    raw=path.read_bytes()
    if len(raw)<20:
        raise ValueError(f"{path.name}: truncated GLB")
    magic,version,length=struct.unpack_from("<III",raw)
    if (magic,version,length)!=(0x46546C67,2,len(raw)):
        raise ValueError(f"{path.name}: invalid GLB header")
    chunks=[]
    cursor=12
    while cursor<len(raw):
        length,kind=struct.unpack_from("<II",raw,cursor)
        if length%4 or cursor+8+length>len(raw):
            raise ValueError(f"{path.name}: invalid chunk length/alignment")
        chunks.append((kind,raw[cursor+8:cursor+8+length]))
        cursor+=8+length
    if [c[0] for c in chunks]!=[0x4E4F534A,0x004E4942]:
        raise ValueError(f"{path.name}: expected JSON and embedded BIN chunks")
    doc=json.loads(chunks[0][1])
    if doc["asset"]["version"]!="2.0" or len(doc["buffers"])!=1:
        raise ValueError(f"{path.name}: unexpected glTF version/buffers")
    blob=chunks[1][1]
    if doc["buffers"][0]["byteLength"]>len(blob):
        raise ValueError(f"{path.name}: incomplete binary buffer")
    return doc,blob


def accessor(doc,blob,index):
    item=doc["accessors"][index]
    view=doc["bufferViews"][item["bufferView"]]
    fmt,width={5126:("f",4),5125:("I",4),5123:("H",2)}[item["componentType"]]
    arity={"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4}[item["type"]]
    stride=view.get("byteStride",width*arity)
    offset=view.get("byteOffset",0)+item.get("byteOffset",0)
    end=offset+(item["count"]-1)*stride+width*arity
    if offset%width or end>view.get("byteOffset",0)+view["byteLength"] or end>len(blob):
        raise ValueError("Accessor alignment/range violation")
    return [struct.unpack_from("<"+fmt*arity,blob,offset+i*stride) for i in range(item["count"])]


def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])


def dot(a,b):
    return sum(x*y for x,y in zip(a,b))


def validate_glb(path,expected=None):
    doc,blob=read_glb(path)
    total=0
    for mesh in doc["meshes"]:
        mesh_total=0
        for primitive in mesh["primitives"]:
            if primitive.get("mode",4)!=4:
                raise ValueError(f"{path.name}: expected triangle geometry")
            positions=accessor(doc,blob,primitive["attributes"]["POSITION"])
            normals=accessor(doc,blob,primitive["attributes"]["NORMAL"])
            uvs=accessor(doc,blob,primitive["attributes"]["TEXCOORD_0"])
            indices=[i[0] for i in accessor(doc,blob,primitive["indices"])]
            if len(positions)!=len(normals) or len(positions)!=len(uvs) or len(indices)%3:
                raise ValueError(f"{path.name}: mismatched accessor counts")
            if not all(math.isfinite(v) for row in positions+normals+uvs for v in row):
                raise ValueError(f"{path.name}: nonfinite geometry")
            if not all(0<=i<len(positions) for i in indices):
                raise ValueError(f"{path.name}: invalid indices")
            if not all(abs(dot(n,n)-1)<1e-5 for n in normals):
                raise ValueError(f"{path.name}: nonunit normals")
            for i in range(0,len(indices),3):
                a,b,c=[positions[v] for v in indices[i:i+3]]
                normal=cross(tuple(y-x for x,y in zip(a,b)),tuple(y-x for x,y in zip(a,c)))
                if dot(normal,normal)<1e-14 or dot(normal,normals[indices[i]])<=0:
                    raise ValueError(f"{path.name}: degenerate/backward triangle")
            item=doc["accessors"][primitive["attributes"]["POSITION"]]
            for axis in range(3):
                if abs(min(v[axis] for v in positions)-item["min"][axis])>1e-5 or abs(max(v[axis] for v in positions)-item["max"][axis])>1e-5:
                    raise ValueError(f"{path.name}: accessor bounds mismatch")
            mesh_total+=len(indices)//3
        if expected:
            if mesh["name"]!=expected["id"] or mesh_total!=expected["triangles"]:
                raise ValueError(f"{path.name}: mesh metadata mismatch")
            pos=accessor(doc,blob,mesh["primitives"][0]["attributes"]["POSITION"])
            source=[(p[0],-p[2],p[1]) for p in pos]
            for axis in range(3):
                if abs(min(p[axis] for p in source)-expected["bounds_m"]["min"][axis])>1e-5 or abs(max(p[axis] for p in source)-expected["bounds_m"]["max"][axis])>1e-5:
                    raise ValueError(f"{path.name}: source/GLB coordinate conversion mismatch")
        total+=mesh_total
    return doc,total


def world_bounds(points,placement):
    angle=math.radians(placement["rotation_deg"][1])
    c,s=math.cos(angle),math.sin(angle)
    sx,sy,sz=placement["scale"]
    ox,oy,oz=[v/100 for v in placement["location_cm"]]
    transformed=[(ox+p[0]*sx*c-p[1]*sy*s,oy+p[0]*sx*s+p[1]*sy*c,oz+p[2]*sz) for p in points]
    return ([min(p[i] for p in transformed) for i in range(3)],
            [max(p[i] for p in transformed) for i in range(3)])


def validate_paths(manifest):
    modules={m["id"]:m for m in manifest["modules"]}
    obstacles=[]
    floors=[]
    for p in manifest["placements"]:
        m=modules[p["mesh"]]
        if p["role"]=="calibration":
            continue
        for hull in m["collision"]["hulls"]:
            lo,hi=world_bounds(hull["vertices_m"],p)
            if p["mesh"] in ("SM_AEON_Floor_4m","SM_AEON_Floor_8m"):
                if abs(hi[2])>1e-6:
                    raise ValueError("Starter route floors must have top faces at Z=0")
                floors.append((lo,hi))
            elif hi[2]>.02:
                obstacles.append((p["name"],hull["label"],lo,hi))
    samples=0
    for path in manifest["walkable_paths"]:
        half=path["required_clear_width_cm"]/200
        height=path["required_clear_height_cm"]/100
        for start,end in zip(path["points_cm"],path["points_cm"][1:]):
            a,b=[v/100 for v in start],[v/100 for v in end]
            if not (a[0]==b[0] or a[1]==b[1]) or a[2]!=b[2]:
                raise ValueError("This validator requires flat axis-aligned route segments")
            horizontal= a[1]==b[1]
            route_lo=[min(a[i],b[i]) for i in range(3)]
            route_hi=[max(a[i],b[i]) for i in range(3)]
            transverse=1 if horizontal else 0
            route_lo[transverse]-=half
            route_hi[transverse]+=half
            route_lo[2]=.02
            route_hi[2]=height
            for name,label,lo,hi in obstacles:
                if all(min(hi[i],route_hi[i])-max(lo[i],route_lo[i])>1e-6 for i in range(3)):
                    raise ValueError(f"{path['id']}: route blocked by {name}/{label}")
            length=math.dist(a,b)
            intervals=max(1,math.ceil(length/.5))
            for n in range(intervals+1):
                center=[a[i]+(b[i]-a[i])*n/intervals for i in range(3)]
                for across in (-half,0,half):
                    point=center[:]
                    point[transverse]+=across
                    if not any(all(lo[i]-1e-6<=point[i]<=hi[i]+1e-6 for i in (0,1)) for lo,hi in floors):
                        raise ValueError(f"{path['id']}: unsupported floor at {point}")
                    samples+=1
    return samples


def validate_pack(pack):
    manifest=json.loads((pack/"manifest.json").read_text(encoding="utf-8"))
    if manifest["schema_version"]!=1 or manifest["provenance"]["external_geometry"]:
        raise ValueError("Unexpected schema/provenance")
    modules={m["id"]:m for m in manifest["modules"]}
    if len(modules)!=len(manifest["modules"]):
        raise ValueError("Duplicate module IDs")
    for item in manifest["files"]:
        path=(pack/item["path"]).resolve()
        if not path.is_relative_to(pack.resolve()):
            raise ValueError("Manifest file path escapes pack")
        data=path.read_bytes()
        if len(data)!=item["bytes"] or hashlib.sha256(data).hexdigest()!=item["sha256"]:
            raise ValueError(f"{item['path']}: stale content/hash")
    triangles=0
    for module in modules.values():
        _,count=validate_glb(pack/module["files"]["glb"],module)
        triangles+=count
        vertices=[]
        face_count=0
        for line in (pack/module["files"]["obj"]).read_text().splitlines():
            if line.startswith("v "):
                vertices.append([float(v) for v in line.split()[1:]])
            elif line.startswith("f "):
                values=line.split()[1:]
                if len(values)!=3 or not all(1<=int(v.split("/")[0])<=module["vertices"] for v in values):
                    raise ValueError(f"{module['id']}: invalid OBJ faces")
                face_count+=1
        if len(vertices)!=module["vertices"] or face_count!=module["triangles"]:
            raise ValueError(f"{module['id']}: OBJ count mismatch")
        for axis in range(3):
            if abs(min(v[axis] for v in vertices)/100-module["bounds_m"]["min"][axis])>1e-6 or abs(max(v[axis] for v in vertices)/100-module["bounds_m"]["max"][axis])>1e-6:
                raise ValueError(f"{module['id']}: OBJ is not centimeter geometry")
        for hull in module["collision"]["hulls"]:
            if len(hull["vertices_m"])<4 or not all(math.isfinite(v) for p in hull["vertices_cm"] for v in p):
                raise ValueError(f"{module['id']}: invalid collision hull")
            if any(abs(cm-m*100)>1e-5 for p,q in zip(hull["vertices_m"],hull["vertices_cm"]) for m,cm in zip(p,q)):
                raise ValueError(f"{module['id']}: collision scale mismatch")
    doc,_=validate_glb(pack/"ossuary_exchange_preview.glb")
    scene_names=[n["name"] for n in doc["nodes"]]
    placement_names=[p["name"] for p in manifest["placements"]]
    if Counter(scene_names)!=Counter(placement_names) or len(set(placement_names))!=len(placement_names):
        raise ValueError("Scene/placement manifest mismatch")
    for node,p in zip(doc["nodes"],manifest["placements"]):
        if doc["meshes"][node["mesh"]]["name"]!=p["mesh"]:
            raise ValueError("Preview mesh reference mismatch")
        x,y,z=[v/100 for v in p["location_cm"]]
        if any(abs(a-b)>1e-6 for a,b in zip(node["translation"],(x,z,-y))):
            raise ValueError("Preview translation/unit mismatch")
        theta=math.radians(p["rotation_deg"][1])/2
        if any(abs(a-b)>1e-6 for a,b in zip(node["rotation"],(0,math.sin(theta),0,math.cos(theta)))):
            raise ValueError("Preview yaw mismatch")
        if node["scale"]!=p["scale"]:
            raise ValueError("Preview scale mismatch")
    samples=validate_paths(manifest)
    marker_ids={m["id"] for m in manifest["markers"]}
    if not {f"CHECKPOINT-{i}" for i in range(1,5)}<=marker_ids or not {"OBJ-BOS011-BREAK-TREASURY-A","OBJ-BOS011-BREAK-TREASURY-B","EC_BOS_011"}<=marker_ids:
        raise ValueError("Missing slice checkpoint/boss objective markers")
    land=manifest["landscape"]
    raw=(pack/land["r16"]).read_bytes()
    width,height=land["resolution"]
    if len(raw)!=width*height*2:
        raise ValueError("Landscape r16 dimensions do not match byte count")
    values=struct.unpack("<"+str(width*height)+"H",raw)
    if min(values)==0 or max(values)==65535:
        raise ValueError("Clipped landscape elevations")
    png=(pack/land["png"]).read_bytes()
    if png[:8]!=b"\x89PNG\r\n\x1a\n":
        raise ValueError("Landscape PNG missing signature")
    cursor=8; compressed=bytearray()
    while cursor<len(png):
        length=struct.unpack_from(">I",png,cursor)[0]
        kind=png[cursor+4:cursor+8]
        data=png[cursor+8:cursor+8+length]
        crc=struct.unpack_from(">I",png,cursor+8+length)[0]
        if (zlib.crc32(kind+data)&0xFFFFFFFF)!=crc:
            raise ValueError("Landscape PNG checksum failure")
        if kind==b"IHDR" and struct.unpack(">IIBBBBB",data)!=(width,height,16,0,0,0,0):
            raise ValueError("Landscape PNG is not 16-bit grayscale")
        if kind==b"IDAT":
            compressed.extend(data)
        cursor+=12+length
    rows=zlib.decompress(compressed)
    png_values=[]
    for y in range(height):
        offset=y*(1+2*width)
        if rows[offset]!=0:
            raise ValueError("Unexpected PNG row filter")
        png_values.extend(struct.unpack_from(">"+str(width)+"H",rows,offset+1))
    if tuple(png_values)!=values:
        raise ValueError("Landscape PNG and r16 elevation samples differ")
    if triangles!=manifest["budget"]["unique_triangles"] or len(doc["nodes"])!=manifest["budget"]["static_mesh_instances"]:
        raise ValueError("Geometry budget mismatch")
    return {"modules":len(modules),"instances":len(doc["nodes"]),"unique_triangles":triangles,
            "scene_triangles":manifest["budget"]["scene_triangles"],"supported_route_samples":samples,
            "landscape_samples":len(values),"verified_file_hashes":len(manifest["files"])}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack",type=Path,default=DEFAULT_PACK)
    args=parser.parse_args()
    try:
        result=validate_pack(args.pack)
    except (ValueError,KeyError,OSError,struct.error,IndexError) as error:
        print("AEONFALL Ossuary source-asset validation FAILED")
        print(str(error))
        return 1
    print("AEONFALL Ossuary source-asset validation PASSED")
    print(json.dumps(result,indent=2))
    print("UEFN import, navmesh, memory and Launch Session verification remain pending.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
