#!/usr/bin/env python3
"""Audit 39 actual WAV binaries and full per-region audio provenance.

Checks RIFF structure, PCM samples, independently parsed duration/loudness,
unique wave hashes, physically existing files and honest editor status.
Original WAV source does NOT imply completed UEFN audio integration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import wave

sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_all_region_audio as source
import build_all_region_terrain as terrain


def parse_wav(path:Path):
    raw=path.read_bytes()
    if len(raw)<44 or raw[:4]!=b"RIFF" or raw[8:12]!=b"WAVE":
        raise ValueError("not a RIFF/WAVE original PCM source")
    if struct.unpack_from("<I",raw,4)[0]!=len(raw)-8:
        raise ValueError("RIFF declared byte length inconsistent")
    if raw[12:16]!=b"fmt " or struct.unpack_from("<I",raw,16)[0]!=16:
        raise ValueError("unknown/WAVE extensible fmt block")
    if raw[36:40]!=b"data":
        raise ValueError("not a 44-byte original source format")
    if struct.unpack_from("<I",raw,40)[0]!=len(raw)-44:
        raise ValueError("inconsistent data chunk length")
    with wave.open(str(path),"rb") as reader:
        fields=(reader.getnchannels(),reader.getsampwidth(),
                reader.getframerate(),reader.getcomptype())
        if fields!=(source.CHANNELS,source.SAMPLE_WIDTH,
                   source.SAMPLE_RATE,"NONE"):
            raise ValueError(f"unexpected audio encoding {fields!r}")
        frames=reader.getnframes()
        body=reader.readframes(frames)
        if reader.readframes(1):
            raise ValueError("trailing audible PCM after end")
    if frames*2!=len(body):
        raise ValueError("incorrect source PCM byte count")
    values=struct.unpack("<"+str(frames)+"h",body)
    return raw,values


def audit(output:Path):
    errors=[]
    def check(value,message):
        if not value:errors.append(message)
    output=output.resolve()
    try:
        document=json.loads((output/"manifest.json").read_text(encoding="utf-8"))
        topo=json.loads(terrain.WORLD.read_text(encoding="utf-8"))
    except (OSError,ValueError,KeyError) as exc:
        return [f"missing or invalid source manifest: {exc}"]
    check(document.get("schema_version")==1 and
          document.get("id")==source.PACK_ID,"audio source schema/id drift")
    check(document.get("source_generator")=="tools/build_all_region_audio.py",
          "audio source provenance drift")
    check(document.get("external_samples_used") is False and
          document.get("origin")==
          "original deterministic mathematical PCM synthesis",
          "external sample/license assertion changed")
    check(document.get("source_audio_only") is True,
          "source audio cannot represent complete native soundscape")
    check(document.get("region_count")==13 and document.get("cue_count")==39,
          "thirteen regions and 39 real sounds are mandatory")
    check(document.get("sample_rate_hz")==source.SAMPLE_RATE and
          document.get("channels")==1 and
          document.get("sample_format")==
          "PCM signed 16-bit little endian RIFF WAV mono",
          "source PCM audio format changed")
    check(document.get("max_peak_abs_pcm")==source.MAX_ABS_PCM,
          "bounded source peak limit changed")
    check(document.get("native_uefn_import")=="not_run" and
          document.get("native_audio_device_binding")=="not_run" and
          document.get("fortnite_mobile_playtest")=="not_run" and
          document.get("automatic_gameplay_triggers_implemented") is False,
          "fabricated native sound/UEFN verification")
    regions=document.get("regions",[])
    canonical=topo.get("regions",[])
    check([r.get("id") for r in regions]==[r["id"] for r in canonical],
          "canonical 13-region audio scope changed")
    records=document.get("files",[])
    paths=[r.get("path") for r in records]
    check(paths==sorted(paths) and len(set(paths))==39,
          "audio SHA inventory must be unique and cover all 39 files")
    required=set()
    seen_hashes=set()
    for index,region in enumerate(regions):
        ident=region.get("id")
        if ident not in terrain.REGION_SLUGS:
            errors.append("unknown regional audio identity")
            continue
        number=int(ident[-3:])
        official=canonical[index] if index<len(canonical) else {}
        check(region.get("name")==official.get("name") and
              region.get("neighbors")==official.get("neighbors"),
              f"{ident}: canonical regional audio identity drift")
        a,b,c,mod,description=source.SONIC_IDENTITIES[number]
        check(region.get("sonic_identity")==description and
              region.get("ambient_loop_cycles")==[a,b,c] and
              region.get("modulation_cycles")==mod,
              f"{ident}: source sonic signature altered")
        for field in ("editor_import","sound_mix_and_occlusion","subtitles_cue_binding"):
            check(region.get(field)=="not_run",f"{ident}: fabricated native {field}")
        regional=region.get("sources",[])
        check([x.get("kind") for x in regional]==list(source.KINDS),
              f"{ident}: source cue roles missing")
        for cue in regional:
            kind=cue.get("kind")
            if kind not in source.KINDS:
                errors.append(f"{ident}: unknown kind {kind!r}")
                continue
            rel=f"{ident}/{ident}_{kind}_original.wav"
            required.add(rel)
            check(cue.get("file")==rel and
                  cue.get("role")==source.MOBILITY_CUES[kind],
                  f"{ident}/{kind}: cue role/file drift")
            check(cue.get("uefn_audio_cue_bound") is False and
                  cue.get("real_mobile_playback")=="not_run" and
                  cue.get("loudness_lufs_measured")=="not_run",
                  f"{ident}/{kind}: unsupported native sound/mix claim")
            wav=output/rel
            try:
                raw,values=parse_wav(wav)
                metrics=source.audio_metrics(values,kind)
                check(len(values)==source.frames_for(kind),
                      f"{rel}: duration/sample count incorrect")
                check(metrics==cue.get("metrics"),
                      f"{rel}: actual sound level/sample metrics changed")
                check(metrics["peak_pcm"]<=source.MAX_ABS_PCM and
                      metrics["rms_pcm"]>=200,
                      f"{rel}: silent, clipped or excessive peak")
                check(metrics["seam_delta_pcm"]<=700,
                      f"{rel}: discontinuous sound or loop edge")
                check(values==tuple(source.pcm(number,kind)),
                      f"{rel}: PCM is not original designated regional synthesis")
                digest=hashlib.sha256(raw).hexdigest()
                if digest in seen_hashes:
                    errors.append(f"{rel}: source duplicate PCM asset")
                seen_hashes.add(digest)
                check(cue.get("sha256")==digest and cue.get("bytes")==len(raw),
                      f"{rel}: asset content hash/size drift")
            except (OSError,ValueError,TypeError,EOFError,struct.error,wave.Error) as exc:
                errors.append(f"{rel}: invalid original PCM WAV source: {exc}")
    check(len(seen_hashes)==39,"39 different binary source sound files required")
    check(set(paths)==required,
          "audio manifest asset inventory does not match all three per region")
    on_disk={p.relative_to(output).as_posix() for p in output.rglob("*")
             if p.is_file()}
    check(on_disk==required|{"manifest.json"},
          f"unexpected/missing WAV source files: {sorted(on_disk ^ (required|{'manifest.json'}))[:10]}")
    for record in records:
        path=record.get("path")
        if (not isinstance(path,str) or Path(path).is_absolute() or
            ".." in Path(path).parts):
            errors.append("unsafe WAV file path in manifest")
            continue
        f=output/path
        if not f.is_file():
            errors.append(f"missing WAV in inventory: {path}")
            continue
        data=f.read_bytes()
        check(record.get("sha256")==hashlib.sha256(data).hexdigest() and
              record.get("bytes")==len(data),
              f"{path}: independent inventory SHA/length mismatch")
    return errors


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,default=source.DEFAULT_OUTPUT)
    args=p.parse_args()
    errors=audit(args.output)
    for error in errors:print("ERROR: "+error,file=sys.stderr)
    if errors:return 1
    print("PASS: 39 real region-specific original PCM WAV source files and source-only constraints.")
    print("Native UEFN Audio Player binding, mobile playback, sound mix and spatialization are unverified.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
