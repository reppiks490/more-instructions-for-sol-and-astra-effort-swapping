#!/usr/bin/env python3
"""Independent structural validation of generated cinematic DCC source artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import wave

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_omnigod_cinematic as source


def floats(doc, binary, accessor_index):
    access = doc["accessors"][accessor_index]
    if access.get("componentType") != 5126:
        raise ValueError("animation accessor must be FLOAT")
    width = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}.get(access.get("type"))
    if width is None:
        raise ValueError("unexpected animation accessor type")
    view = doc["bufferViews"][access["bufferView"]]
    if view.get("buffer") != 0 or view.get("byteStride") is not None:
        raise ValueError("unsupported animation buffer layout")
    offset = view.get("byteOffset", 0) + access.get("byteOffset", 0)
    size = access["count"] * width * 4
    if offset % 4 or size > view["byteLength"] or offset + size > len(binary):
        raise ValueError("invalid animation accessor range")
    data = struct.unpack_from("<" + "f" * (size // 4), binary, offset)
    if not all(math.isfinite(v) for v in data):
        raise ValueError("non-finite animation data")
    return [data[i:i + width] for i in range(0, len(data), width)]


def validate(output: Path):
    errors = []
    def require(test, message):
        if not test:
            errors.append(message)
    try:
        cue = json.loads((output / "cue_sheet.json").read_text(encoding="utf-8"))
        doc, binary = source.read_glb(output / "omnigod_mechanical_motion.glb")
    except (OSError, ValueError, KeyError, struct.error) as exc:
        return [f"missing/corrupt source: {exc}"]
    require(cue.get("schema_version") == 1 and cue.get("mode") == "FUS-001",
            "wrong cue schema/mode")
    require(cue.get("enabled_for_native_activation") is False, "native activation must stay disabled")
    require(cue.get("native_uefn_import") == "not_run" and cue.get("launch_session") == "not_run",
            "native evidence falsely claimed")
    require(cue.get("npc_skeletal_rig") is False, "rig claim unsupported")
    access = cue.get("accessibility", {})
    require(access.get("reduced_flash") is True and access.get("non_color_cues") is True
            and access.get("screen_flash_count") == 0, "accessible fallback absent")
    rules = cue.get("binding_rules", {})
    require(rules.get("requires_authoritative_generation") is True
            and rules.get("abort_cancels_all_cues") is True
            and rules.get("cleanup_before_canonical_abort") is True,
            "stale-token or cleanup contract lost")
    require(rules.get("npc_replaceable_binding_visibility") == "Everyone_separate_sequence"
            and rules.get("owner_sequence_visibility") == "Instigator_Only_no_replaceable_npc_binding",
            "NPC/player cinematic visibility collision")
    tiers = cue.get("lod_policy", [])
    require(len(tiers) == 3 and [x.get("max_particles") for x in tiers] == [80, 24, 0]
            and [x.get("max_concurrent_systems") for x in tiers] == [2, 1, 0],
            "VFX source design caps changed")
    require(len(cue.get("cue_events", [])) == 3 and all(
        x.get("shape") and x.get("visibility") == "instigator_only"
        and x.get("audio") in ["audio/" + name + ".wav" for name in source.SOUNDS]
        for x in cue.get("cue_events", [])), "cue visibility/audio/shape invalid")
    expected = sorted(["omnigod_mechanical_motion.glb"] +
                      ["audio/" + name + ".wav" for name in source.SOUNDS])
    inventory = cue.get("files", [])
    require([x.get("path") for x in inventory] == expected, "source file inventory drift")
    for entry in inventory:
        rel = entry.get("path", "")
        if rel not in expected:
            continue
        path = output / rel
        if not path.is_file():
            errors.append(f"missing: {rel}")
            continue
        payload = path.read_bytes()
        require(entry.get("bytes") == len(payload)
                and entry.get("sha256") == hashlib.sha256(payload).hexdigest(),
                f"source hash mismatch: {rel}")
    require([n.get("name") for n in doc.get("nodes", [])] ==
            ["Prototype_" + name for name in source.PARTS], "wrong GLB node identity")
    require(len(doc.get("meshes", [])) == 13, "wrong GLB mesh count")
    animations = doc.get("animations", [])
    require([a.get("name") for a in animations] == list(source.CLIPS),
            "missing/renamed animation clips")
    for anim in animations:
        try:
            channels = anim["channels"]
            samplers = anim["samplers"]
            require(len(channels) == 14 and len(samplers) == 14,
                    "clip channel count drift")
            targets = [(ch["target"]["node"], ch["target"]["path"]) for ch in channels]
            require(len(set(targets)) == 14, "duplicate animation target")
            require(set(targets) == {(i, "translation") for i in range(13)} |
                    {(source.PARTS.index("Eclipse"), "rotation")},
                    "unexpected animation targets")
            for sampler in samplers:
                require(sampler.get("interpolation") == "LINEAR",
                        "unexpected animation interpolation")
                times = [row[0] for row in floats(doc, binary, sampler["input"])]
                values = floats(doc, binary, sampler["output"])
                require(len(times) == len(values) and len(times) == 5
                        and all(a < b for a, b in zip(times, times[1:])),
                        "non-monotonic/mismatched animation keyframes")
                require(times[0] == 0 and times[-1] == source.CLIPS[anim["name"]][0][-1],
                        "wrong clip duration")
            for ch in channels:
                if ch["target"]["path"] == "rotation":
                    values = floats(doc, binary, samplers[ch["sampler"]]["output"])
                    require(all(abs(sum(v * v for v in q) - 1) < 0.0001 for q in values),
                            "non-unit quaternion")
        except (KeyError, IndexError, TypeError, ValueError, struct.error) as exc:
            errors.append(f"invalid animation: {exc}")
    for name in source.SOUNDS:
        try:
            with wave.open(str(output / "audio" / (name + ".wav")), "rb") as audio:
                require(audio.getnchannels() == 1 and audio.getsampwidth() == 2
                        and audio.getframerate() == source.SAMPLE_RATE,
                        f"audio format drift: {name}")
                data = audio.readframes(audio.getnframes())
                peak = max(abs(sample[0]) for sample in struct.iter_unpack("<h", data))
                require(100 < peak < 9000, f"audio peak out of bound: {name}")
        except (OSError, EOFError, ValueError, wave.Error) as exc:
            errors.append(f"invalid WAV {name}: {exc}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=source.OUTPUT)
    args = parser.parse_args()
    errors = validate(args.output)
    for error in errors:
        print("ERROR: " + error, file=sys.stderr)
    if errors:
        return 1
    print("PASS: source glTF animations, PCM audio, provenance, accessibility and cue contracts.")
    print("Native UEFN import and Launch Session NOT RUN.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
