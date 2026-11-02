#!/usr/bin/env python3
"""Verify every byte of ALL 13 AEONFALL landscape sources (no region sampling).

Checks full 253x253 PNG/R16 parity, IDAT CRCs, source provenance, independent
regional identities, canonical adjacency, and honest UEFN status.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import zlib

sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_all_region_terrain as terrain

PNG_MAGIC=b"\x89PNG\r\n\x1a\n"


def decode_png16(payload:bytes):
    if not payload.startswith(PNG_MAGIC):
        raise ValueError("invalid grayscale PNG magic")
    ptr=len(PNG_MAGIC)
    chunks=[]
    while ptr<len(payload):
        if ptr+12>len(payload):
            raise ValueError("truncated PNG chunk header")
        size=struct.unpack_from(">I",payload,ptr)[0]
        ptr+=4
        kind=payload[ptr:ptr+4]
        ptr+=4
        if ptr+size+4>len(payload):
            raise ValueError("out-of-range PNG chunk")
        data=payload[ptr:ptr+size]
        ptr+=size
        expected=struct.unpack_from(">I",payload,ptr)[0]
        ptr+=4
        if zlib.crc32(kind+data)&0xffffffff!=expected:
            raise ValueError("PNG CRC mismatch")
        chunks.append((kind,data))
        if kind==b"IEND":
            break
    if ptr!=len(payload) or not chunks or chunks[0][0]!=b"IHDR" or chunks[-1][0]!=b"IEND":
        raise ValueError("invalid PNG layout/trailing bytes")
    width,height,bit_depth,color,compression,flt,interlaced=struct.unpack(">IIBBBBB",chunks[0][1])
    if (width,height,bit_depth,color,compression,flt,interlaced)!=(terrain.N,terrain.N,16,0,0,0,0):
        raise ValueError("unexpected 16-bit grayscale dimensions or PNG features")
    compressed=b"".join(data for kind,data in chunks if kind==b"IDAT")
    raw=zlib.decompress(compressed)
    pitch=terrain.N*2+1
    if len(raw)!=pitch*terrain.N:
        raise ValueError("PNG scanline bytes/dimensions mismatch")
    values=[]
    for row in range(terrain.N):
        line=raw[row*pitch:(row+1)*pitch]
        if line[0]!=0:
            raise ValueError("unsupported PNG scanline filter")
        values.extend(struct.unpack(">"+str(terrain.N)+"H",line[1:]))
    return values


def validate(output:Path):
    errors=[]
    def need(test,msg):
        if not test:errors.append(msg)
    output=output.resolve()
    try:
        m=json.loads((output/"manifest.json").read_text(encoding="utf-8"))
        world=json.loads(terrain.WORLD.read_text(encoding="utf-8"))
    except (OSError,ValueError,TypeError) as err:
        return [f"unreadable regional source manifest/topology: {err}"]
    need(m.get("schema_version")==1,"unsupported regional manifest schema")
    need(m.get("id")=="AEONFALL-FULL-THIRTEEN-REGION-TERRAIN-SOURCE-001",
         "region source identity drift")
    need(m.get("terrain_region_count")==13 and m.get("generated_region_count")==12,
         "all thirteen regions, including original Ossuary, are required")
    need(m.get("original_authored_ossuary_reused") is True,
         "original Ossuary terrain must not be silently replaced")
    need(m.get("source_terrain_only") is True and
         m.get("region_completion_claim") is False,
         "unsupported region-complete claim")
    for key in ("uefn_landscape_import","world_partition_assembled",
                "navigation_compiled","fortnite_mobile_playtest",
                "publishing_memory_calculated"):
        need(m.get(key)=="not_run",f"false native UEFN completion: {key}")
    fmt=m.get("format",{})
    need(fmt.get("resolution")==[253,253],"landscape resolution drift")
    need(fmt.get("xy_spacing_cm")==200 and fmt.get("z_scale_cm")==20,
         "landscape cm scale/height encoding drift")
    need(fmt.get("landscape_component_grid")==[4,4] and
         fmt.get("quads_per_section")==63,
         "UEFN landscape source component shape drift")
    required=set(terrain.REGION_SLUGS)
    regions=m.get("regions",[])
    names=[r.get("region_id") for r in regions if isinstance(r,dict)]
    need(set(names)==required and len(names)==len(set(names))==13,
         "missing, duplicated or invented region")
    need(names==list(terrain.REGION_SLUGS),"region sequence changed")
    official={r["id"]:r for r in world.get("regions",[])}
    seen_hash=set()
    for order,reg in enumerate(regions):
        ident=reg.get("region_id")
        if ident not in required:
            errors.append(f"unknown regional source ID {ident!r}")
            continue
        original=official.get(ident,{})
        need(reg.get("name")==original.get("name") and
             reg.get("theme")==original.get("theme"),
             f"{ident}: canonical identity or theme changed")
        need(reg.get("motif")==terrain.REGION_MOTIFS[ident],
             f"{ident}: unique region landscape motif drift")
        need(reg.get("neighbor_ids")==original.get("neighbors"),
             f"{ident}: region topology/portal plan drift")
        need(reg.get("not_assembled_in_uefn") is True and
             reg.get("navmesh_not_verified") is True and
             reg.get("mobile_hlod_not_baked") is True,
             f"{ident}: native terrain/nav claims unsupported")
        plan=[(order%4)*terrain.PLACEMENT_STEP_CM,
              (order//4)*terrain.PLACEMENT_STEP_CM,0]
        need(reg.get("recommended_region_plan_offset_cm")==plan,
             f"{ident}: planning-only source placement drift")
        expected_slug=terrain.REGION_SLUGS[ident]
        expected={kind:f"{ident}/{expected_slug}_253.{kind}" for kind in ("png","r16")}
        for key,expected_path in expected.items():
            need(reg.get(key)==expected_path,f"{ident}: {key} path changed")
        try:
            r16=(output/expected["r16"]).read_bytes()
            png=(output/expected["png"]).read_bytes()
            if len(r16)!=terrain.N*terrain.N*2:
                raise ValueError("bad R16 length")
            numeric=list(struct.unpack("<"+str(terrain.N*terrain.N)+"H",r16))
            decoded=decode_png16(png)
            if numeric!=decoded:
                raise ValueError("PNG and R16 terrain values differ")
            if min(numeric)==max(numeric):
                raise ValueError("flat landscape source")
            rsha=hashlib.sha256(r16).hexdigest()
            psha=hashlib.sha256(png).hexdigest()
            if rsha in seen_hash:
                errors.append(f"{ident}: duplicate terrain data")
            seen_hash.add(rsha)
            need(reg.get("r16_sha256")==rsha and reg.get("png_sha256")==psha,
                 f"{ident}: terrain inventory SHA-256 mismatch")
            need(reg.get("r16_bytes")==len(r16) and
                 reg.get("png_bytes")==len(png),
                 f"{ident}: wrong terrain byte-size manifest")
            need(reg.get("min_sample")==min(numeric) and
                 reg.get("max_sample")==max(numeric),
                 f"{ident}: min/max sample mismatch")
            low=(min(numeric)-32768)/terrain.HEIGHT_SAMPLE_UNITS_PER_M
            high=(max(numeric)-32768)/terrain.HEIGHT_SAMPLE_UNITS_PER_M
            need(abs(reg.get("min_height_m",-999)-round(low,3))<.0001 and
                 abs(reg.get("max_height_m",-999)-round(high,3))<.0001,
                 f"{ident}: incorrect centimeter/meter height conversion")
            if ident=="REG-001":
                need(r16==(terrain.OSSUARY/"ossuary_march_253.r16").read_bytes(),
                     "REG-001 original Ossuary R16 is not preserved")
                need(png==(terrain.OSSUARY/"ossuary_march_253.png").read_bytes(),
                     "REG-001 original Ossuary PNG is not preserved")
            else:
                need(reg.get("source_terrain_provenance")==
                     "tools/build_all_region_terrain.py",
                     f"{ident}: new original terrain provenance drift")
                need(high-low>3.0,f"{ident}: insufficient unique elevation variation")
        except (OSError,ValueError,TypeError,struct.error,zlib.error) as err:
            errors.append(f"{ident}: invalid terrain data: {err}")
    output_paths={p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()}
    expected_files={"manifest.json"}|{f"{ident}/{terrain.REGION_SLUGS[ident]}_253.{ext}"
                                     for ident in required for ext in ("png","r16")}
    need(output_paths==expected_files,
         f"unexpected/missing terrain source artifacts: {sorted(expected_files^output_paths)}")
    return errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=terrain.OUTPUT)
    args=parser.parse_args()
    errors=validate(args.output)
    for e in errors:print("ERROR: "+e,file=sys.stderr)
    if errors:return 1
    print("PASS: all 13 unique terrain sources, full 64,009-sample PNG/R16 parity each.")
    print("Native UEFN region/World Partition/mobile verification: NOT RUN.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
