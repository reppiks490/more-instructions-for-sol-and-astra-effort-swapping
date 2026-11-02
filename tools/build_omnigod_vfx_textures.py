#!/usr/bin/env python3
"""Build original Omnigod emissive/telegraph PNGs and attack audio sources.

Pure Python 3.12 stdlib. Source art only: no UEFN material, Niagara emitter,
Sequencer binding, native character, combat damage or player grant is created.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import wave
import zlib

SIZE = 256
RATE = 22050
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "dist/omnigod_vfx_textures"
TEXTURES = (
    "armor_crimson_fissures", "reactor_violet_veins", "eclipse_occlusion",
    "telegraph_reaver_chevrons", "telegraph_cataclysm_broken_ring",
    "telegraph_aegis_shield",
)
SOUNDS = {
    "reaver_blade_warning": (0.55, 172.0, (0.0, 0.17, 0.34)),
    "cataclysm_siege_warning": (0.90, 92.0, (0.0, 0.26, 0.52, 0.74)),
    "aegis_guard_warning": (0.70, 286.0, (0.0, 0.23, 0.46)),
}


def _chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)


def _png(rgba: bytes) -> bytes:
    if len(rgba) != SIZE * SIZE * 4:
        raise ValueError("invalid source RGBA length")
    scanlines = b"".join(b"\x00" + rgba[y * SIZE * 4:(y + 1) * SIZE * 4] for y in range(SIZE))
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0))
            + _chunk(b"IDAT", zlib.compress(scanlines, 9)) + _chunk(b"IEND", b""))


def _segment_distance(x: float, y: float, ax: float, ay: float, bx: float, by: float) -> float:
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(x - ax - t * dx, y - ay - t * dy)


def _shape(name: str, x: float, y: float) -> float:
    r = math.hypot(x, y)
    theta = math.atan2(y, x)
    if name == "armor_crimson_fissures":
        # Distinct, non-strobing branched energy channels; seamless at UV edges.
        a = abs(math.sin(10 * math.pi * x + 1.8 * math.sin(6 * math.pi * y)))
        b = abs(math.sin(8 * math.pi * y - 2.1 * math.sin(4 * math.pi * x)))
        return max(0.0, 1.0 - min(a, b * 1.3) / 0.22) * 0.90
    if name == "reactor_violet_veins":
        ring = max(0.0, 1.0 - abs(r - 0.47) / 0.045)
        branches = max(0.0, 1.0 - abs(math.sin(6 * theta + 0.8 * math.sin(9 * r))) / 0.14)
        return max(ring, branches * max(0.0, 1 - r / 0.95))
    if name == "eclipse_occlusion":
        # Opaque black disc with segmented luminous corona, no flashing frames.
        disc = 1.0 if r < 0.48 else 0.0
        segment = 1.0 if abs(math.sin(8 * theta)) > 0.12 else 0.0
        corona = max(0.0, 1.0 - abs(r - 0.64) / 0.075) * segment
        return max(disc, corona)
    if name == "telegraph_reaver_chevrons":
        # Three angular teeth directed forward (+Y), distinct from circles/shield.
        return max(max(0.0, 1 - min(
            _segment_distance(x, y, -0.65, yy - 0.28, 0, yy + 0.18),
            _segment_distance(x, y, 0, yy + 0.18, 0.65, yy - 0.28)) / 0.065)
            for yy in (-0.55, 0.0, 0.55))
    if name == "telegraph_cataclysm_broken_ring":
        # Three non-color sectors make the area-of-effect warning recognizable.
        sector = int(((theta + math.pi) / (2 * math.pi)) * 12) % 12
        return max(0.0, 1 - abs(r - 0.68) / 0.085) if sector % 4 != 0 else 0.0
    if name == "telegraph_aegis_shield":
        edges = ((-0.57, 0.67, 0.57, 0.67), (0.57, 0.67, 0.64, -0.12),
                 (0.64, -0.12, 0.0, -0.82), (0.0, -0.82, -0.64, -0.12),
                 (-0.64, -0.12, -0.57, 0.67))
        outline = min(_segment_distance(x, y, *e) for e in edges)
        center = min(_segment_distance(x, y, -0.21, -0.03, 0, -0.29),
                     _segment_distance(x, y, 0, -0.29, 0.27, 0.24))
        return max(max(0, 1 - outline / 0.06), max(0, 1 - center / 0.055))
    raise ValueError("unknown texture")


def _texture(name: str) -> bytes:
    palette = {
        "armor_crimson_fissures": (233, 21, 49),
        "reactor_violet_veins": (151, 49, 248),
        "eclipse_occlusion": (22, 11, 35),
        "telegraph_reaver_chevrons": (240, 51, 74),
        "telegraph_cataclysm_broken_ring": (194, 50, 241),
        "telegraph_aegis_shield": (230, 194, 253),
    }
    rgb = palette[name]
    rgba = bytearray()
    for iy in range(SIZE):
        y = 1 - 2 * (iy + 0.5) / SIZE
        for ix in range(SIZE):
            x = 2 * (ix + 0.5) / SIZE - 1
            alpha = max(0, min(255, round(_shape(name, x, y) * 255)))
            rgba.extend((*rgb, alpha))
    return _png(bytes(rgba))


def _audio(path: Path, seconds: float, frequency: float, beats: tuple[float, ...]):
    pcm = bytearray()
    for i in range(round(seconds * RATE)):
        t = i / RATE
        fade = min(1.0, t / 0.025, (seconds - t) / 0.06)
        pulses = max((1.0 - math.exp(-(t - b) * 300.0)) * math.exp(-(t - b) * 17.0)
                     if t >= b else 0.0 for b in beats)
        wave_value = (math.sin(2 * math.pi * frequency * t) +
                      0.31 * math.sin(2 * math.pi * frequency * 1.505 * t))
        sample = max(-0.25, min(0.25, 0.16 * max(0.0, fade) * pulses * wave_value))
        pcm.extend(struct.pack("<h", round(sample * 32767)))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm)


def build(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    (output / "textures").mkdir(exist_ok=True)
    (output / "audio").mkdir(exist_ok=True)
    for name in TEXTURES:
        (output / "textures" / f"{name}.png").write_bytes(_texture(name))
    for name, (seconds, freq, beats) in SOUNDS.items():
        _audio(output / "audio" / f"{name}.wav", seconds, freq, beats)
    events = [
        {"ability": "Reaver", "shape": "three_forward_chevrons", "audio": "audio/reaver_blade_warning.wav", "texture": "textures/telegraph_reaver_chevrons.png"},
        {"ability": "Cataclysm", "shape": "interrupted_aoe_ring", "audio": "audio/cataclysm_siege_warning.wav", "texture": "textures/telegraph_cataclysm_broken_ring.png"},
        {"ability": "Aegis", "shape": "outlined_shield_with_inset", "audio": "audio/aegis_guard_warning.wav", "texture": "textures/telegraph_aegis_shield.png"},
    ]
    manifest = {
        "schema_version": 1, "id": "AEONFALL-OMNIGOD-VFX-TEXTURE-SOURCE-001",
        "fusion_id": "FUS-001", "native_activation_enabled": False,
        "status": "original_png_wav_source_not_imported_into_uefn",
        "native_uefn_import": "not_run", "native_niagara_binding": "not_run",
        "native_sequencer_binding": "not_run", "native_verse_compile": "not_run",
        "fortnite_launch_session": "not_run", "owner_entitlement_modified": False,
        "resolution": [SIZE, SIZE], "format": "RGBA8_PNG_straight_alpha",
        "audio_format": {"sample_rate": RATE, "channels": 1, "bit_depth": 16},
        "accessibility": {"screen_flashes": 0, "camera_shake": False,
                          "non_color_shape_cues": True, "audio_optional": True,
                          "hud_text_fallback_required": True},
        "lod_design_caps_unmeasured": [
            {"tier": "near", "max_distance_cm": 2500, "max_particles": 80, "max_systems": 2},
            {"tier": "mid", "max_distance_cm": 6000, "max_particles": 24, "max_systems": 1},
            {"tier": "far", "max_distance_cm": 12000, "max_particles": 0, "max_systems": 0},
        ],
        "binding": {"owner_only_sequence": "Instigator_Only_no_replaceable_NPC_binding",
                    "replaceable_npc_sequence": "Everyone_separate_sequence",
                    "require_authoritative_generation": True,
                    "stop_all_on_abort_or_revocation": True,
                    "cleanup_before_canonical_abort": True},
        "attack_telegraphs": events, "files": [],
    }
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            data = path.read_bytes()
            manifest["files"].append({"path": path.relative_to(output).as_posix(),
                                      "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    (output / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    m = build(args.output)
    print(f"Built {len(TEXTURES)} original RGBA PNGs and {len(SOUNDS)} original PCM WAV cues")
    print(f"Files: {len(m['files'])}; UEFN import, Niagara, Sequencer, Verse compile: NOT RUN")


if __name__ == "__main__":
    main()
