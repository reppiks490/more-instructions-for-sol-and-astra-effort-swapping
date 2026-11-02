#!/usr/bin/env python3
"""Author twelve original FUS-001 ability telegraphs, PCM cues and subtitles.

Deterministic offline art/audio source, not a native Niagara/Verse/UEFN import.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import sys
import wave
import zlib

SIZE = 256
RATE = 16000
# Names and non-color geometric signatures align with the authored SFA-001..012
# Arsenal contract. Timings are proposed presentation offsets, not hit windows.
ABILITIES = (
    ("SFA-001", "Blood-Iron Reaver", "descending_chevron", 0, 850),
    ("SFA-002", "Violet Cataclysm", "three_target_lanes", 1, 900),
    ("SFA-003", "Dreadframe Aegis", "locking_shield", 2, 1000),
    ("SFA-004", "Crimson Chainhook", "hooked_chain", 3, 900),
    ("SFA-005", "Violet Graviton Lattice", "six_edge_lattice", 4, 1100),
    ("SFA-006", "Soul-Furnace Overclock", "paired_pistons", 5, 850),
    ("SFA-007", "Sepulchral Null-Tether", "segmented_tether", 6, 900),
    ("SFA-008", "Bastion Vent", "three_exhaust_vents", 7, 3000),
    ("SFA-009", "Scarlet Fracture", "twin_fault_lines", 8, 950),
    ("SFA-010", "Violet Echo Step", "offset_footprints", 9, 900),
    ("SFA-011", "Soul-Furnace Verdict", "furnace_jaws", 10, 1050),
    ("SFA-012", "Crimson-Violet Requiem", "three_crescents", 11, 1150),
)
EXTRA = (
    ("SFA-002", "cls006_mark_bonus", 300, 380, "[Marked target — single bonus accent, only when authorized]"),
    ("SFA-005", "pulse_two", 420, 360, "[Second lattice pulse — separate audible tick]"),
)
LOD = (
    {"tier": "near", "max_distance_cm": 2500, "max_particles": 80, "max_systems": 2},
    {"tier": "mid", "max_distance_cm": 6000, "max_particles": 24, "max_systems": 1},
    {"tier": "far", "max_distance_cm": 12000, "max_particles": 0, "max_systems": 0},
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def segment(x: float, y: float, ax: float, ay: float, bx: float, by: float) -> float:
    vx, vy = bx - ax, by - ay
    t = max(0., min(1., ((x - ax) * vx + (y - ay) * vy) / (vx * vx + vy * vy)))
    return math.hypot(x - ax - t * vx, y - ay - t * vy)


def geometry(i: int, x: float, y: float) -> float:
    """Unsigned stroke distance; each signature has a distinct silhouette."""
    if i == 0:  # downward blade-chevron
        return min(segment(x, y, -.75, -.65, 0, .70), segment(x, y, 0, .70, .75, -.65), abs(x + .05 * y) if y > .35 else 3)
    if i == 1:  # three independent strike lanes
        return min(abs(x - lane) for lane in (-.60, 0, .60)) if abs(y) < .72 else 3
    if i == 2:  # shield crest and locking teeth
        return min(segment(x, y, -.7, -.7, -.7, .25), segment(x, y, .7, -.7, .7, .25),
                   segment(x, y, -.7, .25, 0, .80), segment(x, y, .7, .25, 0, .80),
                   abs(y + .15) if abs(x) < .45 else 3)
    if i == 3:  # segmented chain and hook
        return min(min(math.hypot(x - a, y + .20) - .09 for a in (-.70, -.38, -.06, .26)),
                   segment(x, y, .30, -.20, .65, .25), segment(x, y, .65, .25, .30, .55))
    if i == 4:  # six-sided lattice, internal cross
        angles = [math.pi * (k / 3 - .5) for k in range(6)]
        pts = [(.74 * math.cos(a), .74 * math.sin(a)) for a in angles]
        return min([segment(x, y, *pts[k], *pts[(k + 1) % 6]) for k in range(6)] +
                   [abs(x) if abs(y) < .68 else 3, abs(y) if abs(x) < .68 else 3])
    if i == 5:  # pistons
        return min(abs(x - v) if -.7 < y < .55 else 3 for v in (-.50, .50)) if abs(y) > .18 else min(abs(y - .18), abs(y + .18))
    if i == 6:  # segmented diagonal tether
        return min(segment(x, y, -.80 + k * .31, -.52 + k * .20,
                           -.64 + k * .31, -.41 + k * .20) for k in range(5))
    if i == 7:  # three rising vents
        return min(abs(x - v) if -.70 < y < .45 else 3 for v in (-.60, 0, .60)) if y < .45 else min(math.hypot(x - v, y - .55) - .15 for v in (-.60, 0, .60))
    if i == 8:  # two cracked fault lines
        return min(segment(x, y, -.65, -.8, -.32, -.10), segment(x, y, -.32, -.10, -.62, .8),
                   segment(x, y, .35, -.8, .63, -.05), segment(x, y, .63, -.05, .31, .8))
    if i == 9:  # displaced diamond footprints
        return min(abs(abs(x - a) + abs(y - b) - .30) for a, b in ((-.35, -.30), (.40, .35)))
    if i == 10:  # open furnace jaws
        return min(segment(x, y, -.80, -.60, -.20, -.20), segment(x, y, -.20, -.20, -.80, .60),
                   segment(x, y, .80, -.60, .20, -.20), segment(x, y, .20, -.20, .80, .60),
                   abs(y - .12) if abs(x) < .48 else 3)
    # three crescent crescendos
    return min(abs(math.hypot(x - a, y - b) - r) if x < a + .12 else 3
               for a, b, r in ((-.50, .20, .28), (0, -.20, .43), (.50, .20, .28)))


def chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)


def make_png(i: int) -> bytes:
    rows = bytearray()
    for py in range(SIZE):
        rows.append(0)
        y = (py + .5) * 2 / SIZE - 1
        for px in range(SIZE):
            x = (px + .5) * 2 / SIZE - 1
            d = abs(geometry(i, x, y))
            edge = max(0., min(1., (.065 - d) / .045))
            glow = max(0., min(1., (.22 - d) / .18))
            # White stroke remains legible in monochrome, independent of hue.
            r, g, b = ((242, 214, 222) if edge > .45 else
                       (192, 32 + (i * 11) % 70, 91) if i % 2 == 0 else
                       (133, 53, 213))
            alpha = round(255 * max(edge, glow * .34))
            rows.extend((r, g, b, alpha))
    ihdr = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + chunk(b"IEND", b"")


def make_wav(index: int, duration_ms: int, *, accent: bool = False) -> bytes:
    count = RATE * duration_ms // 1000
    stream = io.BytesIO()
    with wave.open(stream, "wb") as sound:
        sound.setnchannels(1)
        sound.setsampwidth(2)
        sound.setframerate(RATE)
        frames = bytearray()
        base = 125 + 31 * index + (107 if accent else 0)
        for n in range(count):
            t = n / RATE
            envelope = min(1., t / .018) * min(1., (count - n) / (RATE * .12))
            beat = .50 + .50 * math.sin(2 * math.pi * (2 + index % 4) * t)
            sample = (math.sin(2 * math.pi * base * t) * .62 +
                      math.sin(2 * math.pi * (base * 1.51) * t) * .22)
            frames.extend(struct.pack("<h", round(12000 * envelope * (.6 + .4 * beat) * sample)))
        sound.writeframes(frames)
    return stream.getvalue()


def stamp(t: int) -> str:
    return f"00:00:{t // 1000:02}.{t % 1000:03}"


def validate_contract(path: Path | None) -> None:
    if path is None:
        return
    contract = json.loads(path.read_text(encoding="utf-8"))
    if contract.get("form_id") != "FUS-001" or contract.get("universe_first_gate", {}).get("native_enablement_allowed") is not False:
        raise ValueError("Arsenal contract native gate is not closed")
    items = contract.get("abilities", [])
    if [(x.get("id"), x.get("name")) for x in items] != [(a, n) for a, n, *_ in ABILITIES]:
        raise ValueError("Arsenal contract ID/name drift; fail closed")
    if any(x.get("native_enabled") is not False for x in items):
        raise ValueError("Arsenal native activation unexpectedly enabled")


def expected(contract: Path | None = None) -> tuple[dict, dict[str, bytes]]:
    validate_contract(contract)
    files: dict[str, bytes] = {}
    events = []
    for ident, name, shape, index, hold in ABILITIES:
        image = f"textures/{ident}_noncolor_telegraph.png"
        audio = f"audio/{ident}_warning.wav"
        caption = f"captions/{ident}.vtt"
        files[image] = make_png(index)
        files[audio] = make_wav(index, min(hold, 950))
        subtitle = f"[{name} — {shape.replace('_', ' ')} warning]"
        cues = [(0, min(hold, 950), audio, subtitle, "base_warning")]
        for aid, label, start, length, text in EXTRA:
            if aid == ident:
                path = f"audio/{ident}_{label}.wav"
                files[path] = make_wav(index, length, accent=True)
                cues.append((start, start + length, path, text, label))
        cues.sort(key=lambda x: x[0])
        files[caption] = ("WEBVTT\n\n" + "\n".join(
            f"{stamp(start)} --> {stamp(end)}\n{text}\n"
            for start, end, _, text, _ in cues)).encode("utf-8")
        for start, end, wav, text, role in cues:
            events.append({"ability_id": ident, "role": role, "start_ms": start,
                           "end_ms": end, "audio": wav, "caption": caption,
                           "caption_text": text, "requested_visibility": "instigator_only",
                           "source_only_not_hit_authorization": True})
    inventory = [{"path": name, "bytes": len(data), "sha256": digest(data)}
                 for name, data in sorted(files.items())]
    result = {
        "schema_version": 1, "source_only": True, "fusion_mode": "FUS-001",
        "source_status": "generated_original_art_audio_not_imported",
        "native_uefn_import": "not_run", "native_niagara_binding": "not_run",
        "native_sequencer_binding": "not_run", "native_verse_compile": "not_run",
        "fortnite_mobile_profile": "not_run", "cooked_memory": "not_run",
        "enabled_for_native_activation": False, "fused_owner_required": True,
        "trusted_generation_required": True, "fuse_titan_FUS002_enabled": False,
        "event_not_damage_or_hit_receipt": True,
        "ability_count": len(ABILITIES), "audio_event_count": len(events),
        "unique_shape_count": len({x[2] for x in ABILITIES}),
        "abilities": [{"id": ident, "name": name, "shape": shape,
                       "texture": f"textures/{ident}_noncolor_telegraph.png",
                       "caption": f"captions/{ident}.vtt", "presentation_hold_ms": hold}
                      for ident, name, shape, _, hold in ABILITIES],
        "events": events,
        "lod_design_caps_unmeasured": LOD,
        "per_region_concurrency_design_cap_unmeasured": {"near_active_effects": 2, "mid_active_effects": 1, "far_active_effects": 0},
        "region_ids": [f"REG-{i:03}" for i in range(1, 14)],
        "cleanup_triggers": ["owner_revoked", "generation_changed", "cancelled",
                             "actor_despawned", "region_unloaded", "separation", "logout"],
        "accessibility": {"noncolor_shapes": True, "captions": True,
                          "reduced_flash_screen_flashes": 0, "camera_shake": False,
                          "mute_safe_hud_warning_required": True, "touch_safe_warning_required": True},
        "optional_events": {"SFA-002_cls006_mark_bonus": "conditional_existing_equipped_class_only",
                            "SFA-005_pulse_two": "separate_presentation_tick_not_authoritative_damage"},
        "files": inventory,
    }
    return result, files


def build(root: Path, contract: Path | None = None) -> dict:
    manifest, files = expected(contract)
    for rel, data in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    root.mkdir(parents=True, exist_ok=True)
    (root / "arsenal_presentation_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def validate(root: Path, contract: Path | None = None) -> list[str]:
    try:
        manifest, files = expected(contract)
        saved = (root / "arsenal_presentation_manifest.json").read_bytes()
        if saved != (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"):
            return ["manifest/provenance/native-status drift"]
        return [f"original source content drift: {rel}" for rel, data in files.items()
                if (root / rel).read_bytes() != data]
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        return ["arsenal presentation failed closed: " + str(exc)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("dist/omnigod_arsenal_presentation"))
    parser.add_argument("--arsenal-contract", type=Path, default=None,
                        help="Optional external source contract; never fetch or enable native gameplay")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if not args.validate_only:
        build(args.output, args.arsenal_contract)
    failures = validate(args.output, args.arsenal_contract)
    for problem in failures:
        print("ERROR:", problem, file=sys.stderr)
    if failures:
        return 1
    print("PASS: 12 original PNG telegraphs, 14 PCM WAVs, 12 WebVTT files; source only")
    print("UEFN/Niagara/Verse/mobile/cooked memory: NOT RUN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
