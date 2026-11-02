#!/usr/bin/env python3
"""Build deterministic 4x4 static PNG flipbook atlases from validated VFX sources.

Source-only 16-frame non-flashing reveals. Not a Niagara/UEFN imported asset.
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
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_omnigod_vfx_textures as base_check

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "dist/omnigod_vfx_textures"
OUTPUT = ROOT / "dist/omnigod_vfx_flipbooks"
TILE = 128
GRID = 4
DIM = TILE * GRID
FRAMES = GRID * GRID
MAP = (
    ("Reaver", "telegraph_reaver_chevrons", "reaver_blade_warning", 550, "downward_wipe"),
    ("Cataclysm", "telegraph_cataclysm_broken_ring", "cataclysm_siege_warning", 900, "radial_expansion"),
    ("Aegis", "telegraph_aegis_shield", "aegis_guard_warning", 700, "center_outward"),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return (struct.pack(">I", len(data)) + kind + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff))


def png_rgba(size: int, rgba: bytes) -> bytes:
    if len(rgba) != size * size * 4:
        raise ValueError("wrong RGBA atlas size")
    rows = b"".join(b"\0" + rgba[y * size * 4:(y + 1) * size * 4]
                    for y in range(size))
    return (b"\x89PNG\r\n\x1a\n"
            + png_chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
            + png_chunk(b"IDAT", zlib.compress(rows, 9))
            + png_chunk(b"IEND", b""))


def reveal(method: str, x: int, y: int, frame: int) -> float:
    if frame == 0:
        return 0.
    if frame == FRAMES - 1:
        return 1.
    xx, yy = x / (TILE - 1), y / (TILE - 1)
    if method == "downward_wipe":
        position = yy
    elif method == "radial_expansion":
        position = math.hypot(xx - .5, yy - .5) / math.sqrt(.5)
    elif method == "center_outward":
        position = abs(xx - .5) * 2.
    else:
        raise ValueError("unknown reveal style")
    progress = frame / (FRAMES - 1)
    return max(0., min(1., (progress - position + .05) / .10))


def frame_base(source_rgba: bytes) -> bytes:
    """128x128 nearest-neighbor downsample of a validated 256x256 RGBA source."""
    raw = bytearray()
    for y in range(TILE):
        for x in range(TILE):
            i = ((y * 2) * 256 + x * 2) * 4
            raw.extend(source_rgba[i:i + 4])
    return bytes(raw)


def make_atlas(base_rgba: bytes, style: str) -> bytes:
    if len(base_rgba) != TILE * TILE * 4:
        raise ValueError("bad base frame")
    atlas = bytearray(DIM * DIM * 4)
    for i in range(FRAMES):
        col, row = i % GRID, i // GRID
        for y in range(TILE):
            for x in range(TILE):
                src = (y * TILE + x) * 4
                dst = ((row * TILE + y) * DIM + col * TILE + x) * 4
                atlas[dst:dst + 3] = base_rgba[src:src + 3]
                atlas[dst + 3] = round(base_rgba[src + 3] * reveal(style, x, y, i))
    return bytes(atlas)


def build(source: Path, output: Path) -> dict:
    problems = base_check.validate(source)
    if problems:
        raise ValueError("base PNG/WAV source rejected: " + "; ".join(problems))
    base_manifest_bytes = (source / "manifest.json").read_bytes()
    output.mkdir(parents=True, exist_ok=True)
    atlas_dir = output / "atlases"
    atlas_dir.mkdir(exist_ok=True)
    clips = []
    inventory = []
    for ability, texture, sound, duration, style in MAP:
        src_rel = "textures/" + texture + ".png"
        sound_rel = "audio/" + sound + ".wav"
        base = frame_base(base_check.parse_png((source / src_rel).read_bytes()))
        rel = "atlases/" + texture + "_reveal_4x4.png"
        raw = png_rgba(DIM, make_atlas(base, style))
        (output / rel).write_bytes(raw)
        inventory.append({"path": rel, "bytes": len(raw), "sha256": sha256(raw)})
        with wave.open(str(source / sound_rel), "rb") as wav:
            actual_duration = round(wav.getnframes() * 1000 / wav.getframerate())
        if actual_duration != duration:
            raise ValueError(f"unexpected duration: {ability}")
        clips.append({
            "ability": ability,
            "source_png": src_rel, "source_png_sha256": sha256((source / src_rel).read_bytes()),
            "source_audio": sound_rel, "source_audio_sha256": sha256((source / sound_rel).read_bytes()),
            "atlas_png": rel, "atlas_sha256": sha256(raw),
            "grid": [GRID, GRID], "tile_px": [TILE, TILE],
            "resolution_px": [DIM, DIM],
            "frame_count": FRAMES, "frame_order": "row_major_zero_based",
            "frame_times_ms": [round(i * duration / (FRAMES - 1)) for i in range(FRAMES)],
            "duration_ms": duration, "reveal": style, "loop": False,
            "direction": "single_play_no_reverse", "max_screen_flashes": 0,
            "presentation_only_not_damage_authorization": True,
            "requested_visibility": "instigator_only_owner_cue",
            "native_uefn_binding": "not_run",
        })
    result = {
        "schema_version": 1, "id": "AEONFALL-OMNIGOD-TELEGRAPH-FLIPBOOK-001",
        "fusion_id": "FUS-001", "status": "generated_source_not_imported_into_uefn",
        "base_manifest_sha256": sha256(base_manifest_bytes),
        "native_uefn_import": "not_run", "native_niagara_binding": "not_run",
        "native_sequencer_binding": "not_run", "native_verse_compile": "not_run",
        "fortnite_launch_session": "not_run", "activation_enabled": False,
        "strictly_visual": True,
        "owner_only_cue_not_hit_receipt": True,
        "authoritative_generation_required": True,
        "cleanup_on_cancel_before_abort": True,
        "per_effect_lod_design_caps_unmeasured": [
            {"tier": "near", "max_distance_cm": 2500, "max_particles": 80, "max_systems": 2},
            {"tier": "mid", "max_distance_cm": 6000, "max_particles": 24, "max_systems": 1},
            {"tier": "far", "max_distance_cm": 12000, "max_particles": 0, "max_systems": 0},
        ],
        "accessibility": {"non_color_shapes": True, "mute_safe_hud_text_required": True,
                          "screen_flashes": 0, "camera_shake": False, "no_automatic_loop": True},
        "atlases": clips,
        "files": sorted(inventory, key=lambda entry: entry["path"]),
    }
    (output / "flipbook_manifest.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=SOURCE)
    p.add_argument("--output", type=Path, default=OUTPUT)
    args = p.parse_args()
    result = build(args.source, args.output)
    print(f"Built {len(result['atlases'])} original 16-frame 4x4 telegraph sprite atlases.")
    print("Actual Niagara, UEFN import, native Verse and Launch Session: NOT RUN.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
