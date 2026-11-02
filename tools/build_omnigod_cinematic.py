#!/usr/bin/env python3
"""Create real, deterministic glTF node animation and original PCM cue sources.

This is DCC preview motion on independent STATIC modules, not a skeletal rig,
UEFN imported asset, native Niagara system or owner-authorized gameplay adapter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import wave

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "dist/omnigod_manifestation/omnigod_dormant_assembly.glb"
OUTPUT = ROOT / "dist/omnigod_cinematics"
PARTS = (
    "Torso", "Crown", "Pauldron_L", "Pauldron_R", "Reactor",
    "Gauntlet_L", "Gauntlet_R", "Hips", "Greave_L", "Greave_R",
    "AxiomCore", "Eclipse", "SiegeBlade",
)
# Local source X-east/Y-rear/Z-up, centimeters; independent source module pivots.
SPREAD_CM = {
    "Torso": (0, 0, 6), "Crown": (0, 0, 48),
    "Pauldron_L": (-66, 0, 30), "Pauldron_R": (66, 0, 30),
    "Reactor": (0, 55, 20), "Gauntlet_L": (-52, -15, -24),
    "Gauntlet_R": (52, -15, -24), "Hips": (0, 0, -18),
    "Greave_L": (-20, 0, -38), "Greave_R": (20, 0, -38),
    "AxiomCore": (0, -70, 0), "Eclipse": (0, 85, 30),
    "SiegeBlade": (64, 0, 20),
}
CLIPS = {
    "AEON_FUS001_Fusion_Preview": ([0, 0.65, 1.6, 3.1, 4.0], [0, 0.75, 1, 0.20, 0]),
    "AEON_FUS001_Separation_Preview": ([0, 0.5, 1.3, 2.2, 3.0], [0, 0.15, 0.60, 1, 1.30]),
    "AEON_OMNI_DormantBreath_Preview": ([0, 1.5, 3, 4.5, 6], [0, 0.08, 0, -0.08, 0]),
}
SOUNDS = {
    "eclipse_subpulse": (55.0, 1.3),
    "iron_plate_lock": (110.0, 0.48),
    "void_separation": (73.4, 1.1),
}
SAMPLE_RATE = 16000


def read_glb(path: Path):
    data = path.read_bytes()
    if len(data) < 28 or struct.unpack_from("<III", data) != (0x46546C67, 2, len(data)):
        raise ValueError("invalid glTF 2.0 GLB header")
    offset = 12
    chunks = []
    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError("truncated GLB chunk")
        size, kind = struct.unpack_from("<II", data, offset)
        offset += 8
        if size % 4 or offset + size > len(data):
            raise ValueError("misaligned or truncated GLB chunk")
        chunks.append((kind, data[offset:offset + size]))
        offset += size
    if len(chunks) != 2 or chunks[0][0] != 0x4E4F534A or chunks[1][0] != 0x004E4942:
        raise ValueError("expected JSON and BIN GLB chunks")
    doc = json.loads(chunks[0][1])
    binary = chunks[1][1]
    if doc.get("asset", {}).get("version") != "2.0" or len(doc.get("buffers", [])) != 1:
        raise ValueError("unsupported glTF layout")
    if doc["buffers"][0]["byteLength"] > len(binary):
        raise ValueError("GLB binary shorter than declared buffer")
    return doc, bytearray(binary)


def pack_glb(doc: dict, binary: bytearray) -> bytes:
    doc["buffers"][0]["byteLength"] = len(binary)
    raw = json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    raw += b" " * (-len(raw) % 4)
    binary.extend(b"\0" * (-len(binary) % 4))
    return (struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(raw) + 8 + len(binary))
            + struct.pack("<II", len(raw), 0x4E4F534A) + raw
            + struct.pack("<II", len(binary), 0x004E4942) + binary)


def accessor(doc: dict, binary: bytearray, rows: list, kind: str) -> int:
    width = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[kind]
    flat = [float(v) for row in rows for v in (row if width > 1 else [row])]
    if len(flat) != len(rows) * width or not all(math.isfinite(v) for v in flat):
        raise ValueError("invalid animation accessor")
    binary.extend(b"\0" * (-len(binary) % 4))
    offset = len(binary)
    binary.extend(struct.pack("<" + "f" * len(flat), *flat))
    view = len(doc["bufferViews"])
    doc["bufferViews"].append({"buffer": 0, "byteOffset": offset, "byteLength": len(flat) * 4})
    result = len(doc["accessors"])
    item = {"bufferView": view, "byteOffset": 0, "componentType": 5126,
            "count": len(rows), "type": kind}
    if kind == "SCALAR":
        item["min"], item["max"] = [min(flat)], [max(flat)]
    doc["accessors"].append(item)
    return result


def gltf_offset(offset_cm):
    x, y, z = offset_cm
    return (x / 100.0, z / 100.0, -y / 100.0)


def animate(doc: dict, binary: bytearray):
    names = [node.get("name") for node in doc.get("nodes", [])]
    expected = ["Prototype_" + p for p in PARTS]
    if names != expected or len(doc.get("meshes", [])) != len(PARTS):
        raise ValueError("source assembly modules/order changed; refusing wrong node animation")
    if doc.get("animations"):
        raise ValueError("source already animated; refusing to overwrite")
    for clip, (times, weights) in CLIPS.items():
        if not all(a < b for a, b in zip(times, times[1:])):
            raise ValueError("non-monotonic animation times")
        anim = {"name": clip, "samplers": [], "channels": []}
        input_index = accessor(doc, binary, times, "SCALAR")
        for node_index, suffix in enumerate(PARTS):
            node = doc["nodes"][node_index]
            base = node.get("translation")
            if not isinstance(base, list) or len(base) != 3:
                raise ValueError("source node missing placement")
            delta = gltf_offset(SPREAD_CM[suffix])
            # Independent, deterministic plate separation; no runtime collision.
            positions = [[round(base[j] + delta[j] * w, 6) for j in range(3)] for w in weights]
            output_index = accessor(doc, binary, positions, "VEC3")
            sampler = len(anim["samplers"])
            anim["samplers"].append({"input": input_index, "output": output_index, "interpolation": "LINEAR"})
            anim["channels"].append({"sampler": sampler,
                                     "target": {"node": node_index, "path": "translation"}})
        # Eclipse is a separate spinning visual plate; glTF Y is the vertical axis.
        node_index = PARTS.index("Eclipse")
        angles = [0, 0.2, 0.65, 1.0, 1.2] if "Fusion" in clip else (
            [0, 0.1, 0.3, 0.6, 0.9] if "Separation" in clip else [0, 0.03, 0, -0.03, 0])
        rotations = [[0, round(math.sin(a / 2), 7), 0, round(math.cos(a / 2), 7)] for a in angles]
        output_index = accessor(doc, binary, rotations, "VEC4")
        sampler = len(anim["samplers"])
        anim["samplers"].append({"input": input_index, "output": output_index, "interpolation": "LINEAR"})
        anim["channels"].append({"sampler": sampler,
                                 "target": {"node": node_index, "path": "rotation"}})
        doc.setdefault("animations", []).append(anim)


def synth_wav(path: Path, frequency: float, seconds: float):
    count = int(SAMPLE_RATE * seconds)
    pcm = bytearray()
    for i in range(count):
        t = i / SAMPLE_RATE
        envelope = (1 - math.exp(-t * 18)) * max(0, 1 - t / seconds) ** 1.7
        # Layered low-mid tonal source; conservative peak, no third-party samples.
        signal = (math.sin(2 * math.pi * frequency * t)
                  + 0.28 * math.sin(2 * math.pi * frequency * 1.503 * t)
                  + 0.13 * math.sin(2 * math.pi * frequency * 2.017 * t))
        value = max(-1, min(1, 0.16 * envelope * signal))
        pcm.extend(struct.pack("<h", round(value * 32767)))
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm)


def build(source: Path, output: Path) -> dict:
    doc, binary = read_glb(source)
    animate(doc, binary)
    output.mkdir(parents=True, exist_ok=True)
    glb = output / "omnigod_mechanical_motion.glb"
    glb.write_bytes(pack_glb(doc, binary))
    sound_dir = output / "audio"
    sound_dir.mkdir(exist_ok=True)
    for name, (freq, seconds) in SOUNDS.items():
        synth_wav(sound_dir / (name + ".wav"), freq, seconds)
    cue_sheet = {
        "schema_version": 1, "mode": "FUS-001", "enabled_for_native_activation": False,
        "status": "dcc_preview_only_not_imported_into_uefn",
        "source_glb": source.name, "animations": list(CLIPS),
        "native_uefn_import": "not_run", "verse_compile": "not_run",
        "launch_session": "not_run", "npc_skeletal_rig": False,
        "accessibility": {"reduced_flash": True, "non_color_cues": True,
                          "camera_shake_opt_out": True, "screen_flash_count": 0},
        "lod_policy": [
            {"tier": "near", "max_distance_cm": 2500, "plate_motion": True,
             "eclipse": True, "max_particles": 80, "max_concurrent_systems": 2},
            {"tier": "mid", "max_distance_cm": 6000, "plate_motion": False,
             "eclipse": True, "max_particles": 24, "max_concurrent_systems": 1},
            {"tier": "far", "max_distance_cm": 12000, "plate_motion": False,
             "eclipse": False, "max_particles": 0, "max_concurrent_systems": 0},
        ],
        "cue_events": [
            {"phase": "Activating", "time_seconds": 0.0, "name": "eclipse_begin",
             "audio": "audio/eclipse_subpulse.wav", "shape": "expanding_ring",
             "vfx": "Niagara_editor_binding_required", "visibility": "instigator_only"},
            {"phase": "Activating", "time_seconds": 3.1, "name": "plates_lock",
             "audio": "audio/iron_plate_lock.wav", "shape": "converging_chevrons",
             "vfx": "Niagara_editor_binding_required", "visibility": "instigator_only"},
            {"phase": "Separating", "time_seconds": 0.0, "name": "separation_begin",
             "audio": "audio/void_separation.wav", "shape": "contracting_ring",
             "vfx": "Niagara_editor_binding_required", "visibility": "instigator_only"},
        ],
        "binding_rules": {"requires_authoritative_generation": True,
                          "abort_cancels_all_cues": True,
                          "cleanup_before_canonical_abort": True,
                          "npc_replaceable_binding_visibility": "Everyone_separate_sequence",
                          "owner_sequence_visibility": "Instigator_Only_no_replaceable_npc_binding"},
        "files": [],
    }
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name != "cue_sheet.json":
            payload = path.read_bytes()
            cue_sheet["files"].append({"path": path.relative_to(output).as_posix(),
                                       "bytes": len(payload),
                                       "sha256": hashlib.sha256(payload).hexdigest()})
    (output / "cue_sheet.json").write_text(json.dumps(cue_sheet, indent=2, sort_keys=True) + "\n",
                                            encoding="utf-8")
    return cue_sheet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    result = build(args.source, args.output)
    print(f"Created {len(result['animations'])} animated glTF clips and {len(SOUNDS)} original WAV cues.")
    print("UEFN import, skeletal rig, native Niagara and Launch Session NOT RUN.")


if __name__ == "__main__":
    main()
