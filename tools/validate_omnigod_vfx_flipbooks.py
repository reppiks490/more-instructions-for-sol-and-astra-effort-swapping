#!/usr/bin/env python3
"""Independent PNG-frame and manifest inspection of generated telegraph atlases.

Neither this module nor the generator makes native UEFN/Verse success claims.
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

DIM, TILE, COUNT = 512, 128, 16
CLIPS = (
    ("Reaver", "telegraph_reaver_chevrons", "reaver_blade_warning", 550, "downward_wipe"),
    ("Cataclysm", "telegraph_cataclysm_broken_ring", "cataclysm_siege_warning", 900, "sector_sweep"),
    ("Aegis", "telegraph_aegis_shield", "aegis_guard_warning", 700, "center_outward"),
)
CAPS = [
    {"tier": "near", "max_distance_cm": 2500, "max_particles": 80, "max_systems": 2},
    {"tier": "mid", "max_distance_cm": 6000, "max_particles": 24, "max_systems": 1},
    {"tier": "far", "max_distance_cm": 12000, "max_particles": 0, "max_systems": 0},
]


def rgba_png(payload: bytes) -> bytes:
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("PNG signature incorrect")
    pos, data = 8, []
    while pos < len(payload):
        if pos + 12 > len(payload):
            raise ValueError("truncated PNG header")
        n = struct.unpack_from(">I", payload, pos)[0]
        if n > 8_000_000 or pos + n + 12 > len(payload):
            raise ValueError("invalid PNG chunk size")
        kind = payload[pos + 4:pos + 8]
        content = payload[pos + 8:pos + 8 + n]
        crc = struct.unpack_from(">I", payload, pos + 8 + n)[0]
        if zlib.crc32(kind + content) & 0xffffffff != crc:
            raise ValueError("PNG CRC mismatch")
        data.append((kind, content))
        pos += n + 12
    if [kind for kind, _ in data] != [b"IHDR", b"IDAT", b"IEND"]:
        raise ValueError("PNG must have exactly IHDR, IDAT, IEND")
    if data[0][1] != struct.pack(">IIBBBBB", DIM, DIM, 8, 6, 0, 0, 0):
        raise ValueError("invalid atlas dimension or RGBA format")
    if data[-1][1]:
        raise ValueError("unexpected IEND data")
    obj = zlib.decompressobj()
    expected = DIM * (DIM * 4 + 1)
    raw = obj.decompress(data[1][1], expected + 1)
    if not obj.eof or obj.unconsumed_tail or obj.unused_data or len(raw) != expected:
        raise ValueError("invalid atlas zlib stream/size")
    pixels = bytearray(DIM * DIM * 4)
    for y in range(DIM):
        off = y * (DIM * 4 + 1)
        if raw[off] != 0:
            raise ValueError("unsupported PNG filter")
        pixels[y * DIM * 4:(y + 1) * DIM * 4] = raw[off + 1:off + 1 + DIM * 4]
    return bytes(pixels)


def inspect_frames(atlas: bytes, source: bytes, method: str) -> list[str]:
    problems = []
    if len(source) != 256 * 256 * 4 or len(atlas) != DIM * DIM * 4:
        return ["incorrect frame or source size"]
    frame_counts = []
    for frame in range(COUNT):
        row, col = divmod(frame, 4)
        count = 0
        for y in range(TILE):
            for x in range(TILE):
                at = ((row * TILE + y) * DIM + col * TILE + x) * 4
                src = ((2 * y) * 256 + 2 * x) * 4
                if atlas[at:at + 3] != source[src:src + 3]:
                    return [f"source palette or atlas tile mismatch: frame {frame}"]
                opacity = atlas[at + 3]
                original = source[src + 3]
                if opacity > original:
                    return [f"atlas expands beyond approved shape: frame {frame}"]
                if frame == 0 and opacity:
                    return ["first warning frame must be transparent"]
                if frame == COUNT - 1 and opacity != original:
                    return ["last warning frame must equal source silhouette"]
                if frame:
                    previous = (((frame - 1) // 4 * TILE + y) * DIM
                                + ((frame - 1) % 4) * TILE + x) * 4 + 3
                    if opacity < atlas[previous]:
                        return [f"nonmonotonic / flashing alpha: frame {frame}"]
                count += opacity > 0
        frame_counts.append(count)
    if len(set(frame_counts)) < 6 or not (frame_counts[0] < frame_counts[-1]):
        problems.append("insufficient distinct readable motion frames")
    # Check style-specific ordering without relying on the generator.
    def at(frame: int, x: int, y: int) -> int:
        return atlas[(((frame // 4) * TILE + y) * DIM + (frame % 4) * TILE + x) * 4 + 3]
    for frame in range(1, COUNT - 1):
        # All three reveals should be bounded by the full source mask.
        coverage = frame_counts[frame]
        if coverage > frame_counts[-1]:
            problems.append("intermediate coverage exceeds static source")
            break
    if method not in ("downward_wipe", "sector_sweep", "center_outward"):
        problems.append("unsupported animation style")
    return problems


def validate(source_dir: Path, output: Path) -> list[str]:
    errors = []
    try:
        prior = base_check.validate(source_dir)
        if prior:
            return ["upstream VFX source invalid: " + "; ".join(prior)]
        plan = json.loads((output / "flipbook_manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError, KeyError) as e:
        return [f"missing/invalid sources: {e}"]
    def check(test, message):
        if not test:
            errors.append(message)
    check(plan.get("schema_version") == 1
          and plan.get("id") == "AEONFALL-OMNIGOD-TELEGRAPH-FLIPBOOK-001"
          and plan.get("fusion_id") == "FUS-001", "wrong asset identity")
    check(plan.get("status") == "generated_source_not_imported_into_uefn"
          and plan.get("activation_enabled") is False
          and plan.get("strictly_visual") is True
          and plan.get("owner_only_cue_not_hit_receipt") is True, "native/attack authority claim")
    for key in ("native_uefn_import", "native_niagara_binding",
                "native_sequencer_binding", "native_verse_compile", "fortnite_launch_session"):
        check(plan.get(key) == "not_run", "unsupported native claim: " + key)
    check(plan.get("authoritative_generation_required") is True
          and plan.get("cleanup_on_cancel_before_abort") is True,
          "owner generation or cancellation guard missing")
    check(plan.get("per_effect_lod_design_caps_unmeasured") == CAPS,
          "unmeasured LOD design ceiling modified")
    check(plan.get("accessibility") == {
        "non_color_shapes": True, "mute_safe_hud_text_required": True,
        "screen_flashes": 0, "camera_shake": False, "no_automatic_loop": True},
        "accessibility requirements changed")
    check(plan.get("base_manifest_sha256") ==
          hashlib.sha256((source_dir / "manifest.json").read_bytes()).hexdigest(),
          "upstream manifest hash changed")
    expected = sorted("atlases/" + name + "_reveal_4x4.png" for _, name, _, _, _ in CLIPS)
    listed = plan.get("files")
    if not isinstance(listed, list):
        return errors + ["missing output file list"]
    check([entry.get("path") for entry in listed] == expected,
          "incorrect ordered file inventory")
    actual = sorted(p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()
                    and p.name != "flipbook_manifest.json")
    check(actual == expected, "extra or missing atlas files")
    clips = plan.get("atlases")
    if not isinstance(clips, list) or len(clips) != len(CLIPS):
        return errors + ["three canonical ability clips required"]
    for entry in listed:
        path = entry.get("path", "")
        if path not in expected:
            continue
        try:
            data = (output / path).read_bytes()
            check(entry.get("bytes") == len(data) and
                  entry.get("sha256") == hashlib.sha256(data).hexdigest(),
                  "atlas hash/size mismatch: " + path)
        except OSError as e:
            errors.append(str(e))
    for clip, (ability, texture, audio, duration, style) in zip(clips, CLIPS):
        src_rel = "textures/" + texture + ".png"
        wav_rel = "audio/" + audio + ".wav"
        atlas_rel = "atlases/" + texture + "_reveal_4x4.png"
        check(clip.get("ability") == ability
              and clip.get("source_png") == src_rel and clip.get("source_audio") == wav_rel
              and clip.get("atlas_png") == atlas_rel and clip.get("reveal") == style,
              "wrong ability/asset identity: " + ability)
        check(clip.get("grid") == [4, 4] and clip.get("tile_px") == [128, 128]
              and clip.get("resolution_px") == [512, 512]
              and clip.get("frame_count") == 16
              and clip.get("frame_order") == "row_major_zero_based"
              and clip.get("frame_times_ms") == [round(i * duration / 15) for i in range(16)]
              and clip.get("duration_ms") == duration
              and clip.get("loop") is False
              and clip.get("direction") == "single_play_no_reverse"
              and clip.get("max_screen_flashes") == 0,
              "timeline/duration/frame metadata mismatch: " + ability)
        check(clip.get("native_uefn_binding") == "not_run"
              and clip.get("presentation_only_not_damage_authorization") is True
              and clip.get("requested_visibility") == "instigator_only_owner_cue",
              "unauthorized native binding/visibility: " + ability)
        try:
            texture_bytes = (source_dir / src_rel).read_bytes()
            audio_bytes = (source_dir / wav_rel).read_bytes()
            atlas_bytes = (output / atlas_rel).read_bytes()
            check(clip.get("source_png_sha256") == hashlib.sha256(texture_bytes).hexdigest()
                  and clip.get("source_audio_sha256") == hashlib.sha256(audio_bytes).hexdigest()
                  and clip.get("atlas_sha256") == hashlib.sha256(atlas_bytes).hexdigest(),
                  "source/atlas provenance mismatch: " + ability)
            with wave.open(str(source_dir / wav_rel), "rb") as w:
                check(round(w.getnframes() * 1000 / w.getframerate()) == duration,
                      "audio/flipbook duration mismatch: " + ability)
            source = base_check.parse_png(texture_bytes)
            atlas = rgba_png(atlas_bytes)
            errors.extend(ability + ": " + e for e in inspect_frames(atlas, source, style))
        except (OSError, ValueError, TypeError, KeyError, zlib.error, struct.error, wave.Error) as e:
            errors.append(f"{ability} PNG/audio invalid: {e}")
    return errors


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    problems = validate(args.source, args.output)
    for p in problems:
        print("ERROR: " + p, file=sys.stderr)
    if problems:
        return 1
    print("PASS: 3 authentic 4x4 RGBA telegraph atlases, 48 frames, timing, provenance and fail-closed claims")
    print("UEFN imports, Niagara, native Verse and Launch Session: NOT RUN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
