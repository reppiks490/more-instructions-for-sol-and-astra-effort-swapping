#!/usr/bin/env python3
"""Independently inspect Omnigod PNG/WAV source bytes and fail-closed claims."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import wave
import zlib

SIZE = 256
RATE = 22050
TEXTURE_NAMES = (
    "armor_crimson_fissures", "reactor_violet_veins", "eclipse_occlusion",
    "telegraph_reaver_chevrons", "telegraph_cataclysm_broken_ring",
    "telegraph_aegis_shield",
)
AUDIO = {"reaver_blade_warning": .55, "cataclysm_siege_warning": .90,
         "aegis_guard_warning": .70}
PALETTE = ((233, 21, 49), (151, 49, 248), (22, 11, 35),
           (240, 51, 74), (194, 50, 241), (230, 194, 253))
EXPECTED = sorted([f"textures/{n}.png" for n in TEXTURE_NAMES] +
                  [f"audio/{n}.wav" for n in AUDIO])


def parse_png(data: bytes) -> bytes:
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("invalid PNG signature")
    pos, chunks = 8, []
    while pos < len(data):
        if pos + 12 > len(data):
            raise ValueError("truncated PNG chunk")
        size = struct.unpack_from(">I", data, pos)[0]
        if size > 8_000_000 or pos + 12 + size > len(data):
            raise ValueError("oversized/truncated PNG chunk")
        kind = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + size]
        crc = struct.unpack_from(">I", data, pos + 8 + size)[0]
        if zlib.crc32(kind + payload) & 0xffffffff != crc:
            raise ValueError("PNG CRC mismatch")
        chunks.append((kind, payload))
        pos += size + 12
    if [c[0] for c in chunks] != [b"IHDR", b"IDAT", b"IEND"]:
        raise ValueError("unexpected PNG chunk structure")
    if chunks[0][1] != struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0):
        raise ValueError("wrong PNG size or RGBA8 encoding")
    if chunks[2][1]:
        raise ValueError("IEND must be empty")
    obj = zlib.decompressobj()
    raw = obj.decompress(chunks[1][1], SIZE * (SIZE * 4 + 1) + 1)
    if not obj.eof or obj.unused_data or obj.unconsumed_tail:
        raise ValueError("PNG zlib payload truncated/oversized")
    if len(raw) != SIZE * (SIZE * 4 + 1):
        raise ValueError("wrong decoded PNG length")
    rgba = bytearray()
    for y in range(SIZE):
        row = raw[y * (SIZE * 4 + 1):(y + 1) * (SIZE * 4 + 1)]
        if row[0] != 0:
            raise ValueError("unsupported PNG filter")
        rgba.extend(row[1:])
    return bytes(rgba)


def validate(output: Path) -> list[str]:
    errors = []
    def require(ok: bool, why: str):
        if not ok:
            errors.append(why)
    try:
        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return [f"missing/invalid manifest: {e}"]
    require(manifest.get("schema_version") == 1 and manifest.get("fusion_id") == "FUS-001",
            "wrong fusion/source schema")
    require(manifest.get("id") == "AEONFALL-OMNIGOD-VFX-TEXTURE-SOURCE-001", "wrong source identity")
    require(manifest.get("native_activation_enabled") is False and
            manifest.get("owner_entitlement_modified") is False, "unauthorized native/owner claim")
    for key in ("native_uefn_import", "native_niagara_binding", "native_sequencer_binding",
                "native_verse_compile", "fortnite_launch_session"):
        require(manifest.get(key) == "not_run", f"unverified native claim: {key}")
    require(manifest.get("status") == "original_png_wav_source_not_imported_into_uefn",
            "incorrect imported-asset status")
    require(manifest.get("resolution") == [SIZE, SIZE] and
            manifest.get("format") == "RGBA8_PNG_straight_alpha", "texture format contract drift")
    require(manifest.get("audio_format") == {"sample_rate": RATE, "channels": 1, "bit_depth": 16},
            "audio format contract drift")
    access = manifest.get("accessibility", {})
    require(access.get("screen_flashes") == 0 and access.get("camera_shake") is False and
            access.get("non_color_shape_cues") is True and access.get("audio_optional") is True and
            access.get("hud_text_fallback_required") is True, "accessibility contract drift")
    require(manifest.get("lod_design_caps_unmeasured") == [
        {"tier": "near", "max_distance_cm": 2500, "max_particles": 80, "max_systems": 2},
        {"tier": "mid", "max_distance_cm": 6000, "max_particles": 24, "max_systems": 1},
        {"tier": "far", "max_distance_cm": 12000, "max_particles": 0, "max_systems": 0},
    ], "LOD design budget drift")
    bind = manifest.get("binding", {})
    require(bind.get("owner_only_sequence") == "Instigator_Only_no_replaceable_NPC_binding" and
            bind.get("replaceable_npc_sequence") == "Everyone_separate_sequence" and
            bind.get("require_authoritative_generation") is True and
            bind.get("stop_all_on_abort_or_revocation") is True and
            bind.get("cleanup_before_canonical_abort") is True,
            "owner/sequence/cleanup contract drift")
    events = manifest.get("attack_telegraphs", [])
    require(isinstance(events, list) and len(events) == 3 and
            [e.get("ability") for e in events] == ["Reaver", "Cataclysm", "Aegis"] and
            [e.get("shape") for e in events] == ["three_forward_chevrons", "interrupted_aoe_ring", "outlined_shield_with_inset"] and
            [e.get("audio") for e in events] == ["audio/reaver_blade_warning.wav", "audio/cataclysm_siege_warning.wav", "audio/aegis_guard_warning.wav"] and
            [e.get("texture") for e in events] == ["textures/telegraph_reaver_chevrons.png", "textures/telegraph_cataclysm_broken_ring.png", "textures/telegraph_aegis_shield.png"],
            "attack shape/audio/identity mismatch")
    entries = manifest.get("files", [])
    if not isinstance(entries, list):
        return errors + ["file inventory missing"]
    require([e.get("path") for e in entries] == EXPECTED, "source file inventory missing/extra/reordered")
    require(sorted(p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file() and p.name != "manifest.json") == EXPECTED,
            "actual source file inventory missing/extra")
    for entry in entries:
        rel = entry.get("path", "")
        if rel not in EXPECTED:
            continue
        try:
            payload = (output / rel).read_bytes()
        except OSError as e:
            errors.append(f"missing {rel}: {e}")
            continue
        require(entry.get("bytes") == len(payload) and
                entry.get("sha256") == hashlib.sha256(payload).hexdigest(),
                f"hash/size mismatch: {rel}")
    alphas = []
    for name, palette in zip(TEXTURE_NAMES, PALETTE):
        rel = f"textures/{name}.png"
        try:
            rgba = parse_png((output / rel).read_bytes())
            pixels = [rgba[i:i + 4] for i in range(0, len(rgba), 4)]
            alpha = bytes(p[3] for p in pixels)
            require(all(tuple(p[:3]) == palette for p in pixels), f"palette mismatch: {name}")
            coverage = sum(a > 0 for a in alpha) / len(alpha)
            require(.05 < coverage < .45, f"texture shape coverage out of bounds: {name}")
            alphas.append(hashlib.sha256(alpha).hexdigest())
            center = alpha[(SIZE // 2) * SIZE + SIZE // 2]
            if name == "eclipse_occlusion":
                require(center == 255 and alpha[0] == 0, "eclipse disc/clear corner invalid")
            if name.startswith("telegraph_"):
                require(center == 0, f"telegraph center must remain readable: {name}")
        except (OSError, ValueError, zlib.error, struct.error) as e:
            errors.append(f"invalid PNG {name}: {e}")
    require(len(set(alphas)) == len(TEXTURE_NAMES), "duplicate texture silhouettes")
    sound_hashes = []
    for name, seconds in AUDIO.items():
        try:
            with wave.open(str(output / "audio" / f"{name}.wav"), "rb") as w:
                require(w.getnchannels() == 1 and w.getsampwidth() == 2 and
                        w.getframerate() == RATE and w.getcomptype() == "NONE",
                        f"wrong WAV PCM encoding: {name}")
                require(w.getnframes() == round(seconds * RATE), f"wrong WAV duration: {name}")
                data = w.readframes(w.getnframes())
            samples = [v[0] for v in struct.iter_unpack("<h", data)]
            peak = max(abs(v) for v in samples)
            require(100 < peak < 8500, f"WAV peak unsafe/empty: {name}")
            require(abs(samples[0]) < 100 and abs(samples[-1]) < 1000,
                    f"WAV start/end transient: {name}")
            require(max(abs(a-b) for a, b in zip(samples, samples[1:])) < 2500,
                    f"WAV discontinuity: {name}")
            sound_hashes.append(hashlib.sha256(data).hexdigest())
        except (OSError, ValueError, wave.Error, struct.error) as e:
            errors.append(f"invalid WAV {name}: {e}")
    require(len(set(sound_hashes)) == len(AUDIO), "duplicate audio signatures")
    return errors


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "dist/omnigod_vfx_textures")
    args = p.parse_args()
    errors = validate(args.output)
    for e in errors:
        print("ERROR: " + e, file=sys.stderr)
    if errors:
        return 1
    print("PASS: 6 original RGBA PNGs, 3 original PCM WAV cues, hashes, shape and safety contracts")
    print("UEFN import, Niagara, Sequencer, native Verse and Launch Session NOT RUN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
