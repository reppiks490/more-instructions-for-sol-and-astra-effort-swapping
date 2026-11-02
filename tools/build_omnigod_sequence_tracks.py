#!/usr/bin/env python3
"""Generate real GLB-backed Sequencer edit-decision tracks; NOT native UEFN."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_omnigod_cinematic as motion
import build_omnigod_presentation_handoff as handoff

JSON_NAME = "sequencer_track_handoff.json"
CSV_NAME = "sequencer_track_handoff.csv"
MANIFEST_NAME = "sequencer_track_manifest.json"
FIELDS = ("sequence", "role", "track", "time_ms", "offset_x_cm", "offset_y_cm",
          "offset_z_cm", "distance_cm", "fov_deg", "visibility", "source")
CAMERAS = {
    "Activating": [(0, 900, 55), (650, 850, 55), (1600, 780, 56),
                   (3100, 720, 57), (4000, 700, 57)],
    "Separating": [(0, 700, 57), (500, 740, 56), (1300, 800, 55),
                   (2200, 850, 55), (3000, 900, 55)],
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def verify_glb(root):
    path = root / "omnigod_mechanical_motion.glb"
    doc, binary = motion.read_glb(path)
    if [n.get("name") for n in doc.get("nodes", [])] != [
            "Prototype_" + p for p in motion.PARTS]:
        raise ValueError("13 plate GLB node identity/order drift")
    if len(doc.get("animations", [])) != len(motion.CLIPS):
        raise ValueError("GLB animation count drift")
    for anim, (clip, (times, _)) in zip(doc["animations"], motion.CLIPS.items()):
        if anim.get("name") != clip:
            raise ValueError("GLB animation clip name drift")
        channels = anim.get("channels", [])
        if len(channels) != len(motion.PARTS) + 1:
            raise ValueError("GLB channel count drift")
        for i, channel in enumerate(channels):
            expected = ("translation", i) if i < len(motion.PARTS) else (
                "rotation", motion.PARTS.index("Eclipse"))
            target = channel.get("target", {})
            if (target.get("path"), target.get("node")) != expected:
                raise ValueError("GLB channel target drift")
            if channel.get("sampler") != i:
                raise ValueError("GLB channel sampler drift")
        sampler0 = anim["samplers"][0]
        accessor = doc["accessors"][sampler0["input"]]
        view = doc["bufferViews"][accessor["bufferView"]]
        if (accessor.get("componentType"), accessor.get("type"),
                accessor.get("count")) != (5126, "SCALAR", len(times)):
            raise ValueError("GLB time accessor drift")
        offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        actual = struct.unpack_from("<" + "f" * len(times), binary, offset)
        if any(abs(x - y) > 0.00001 for x, y in zip(actual, times)):
            raise ValueError("GLB animation times drift")
        weights = motion.CLIPS[clip][1]
        for i, sampler in enumerate(anim["samplers"]):
            if (sampler.get("input") != sampler0["input"]
                    or sampler.get("interpolation") != "LINEAR"):
                raise ValueError("GLB per-plate time sampler drift")
            output = doc["accessors"][sampler["output"]]
            width = 3 if i < len(motion.PARTS) else 4
            if (output.get("componentType"), output.get("type"),
                    output.get("count")) != (5126, "VEC3" if width == 3 else "VEC4",
                                              len(times)):
                raise ValueError("GLB plate value accessor drift")
            output_view = doc["bufferViews"][output["bufferView"]]
            start = output_view.get("byteOffset", 0) + output.get("byteOffset", 0)
            values = struct.unpack_from("<" + "f" * (len(times) * width),
                                        binary, start)
            if width == 3:
                base = doc["nodes"][i].get("translation")
                if not isinstance(base, list) or len(base) != 3:
                    raise ValueError("GLB source node base placement missing")
                delta = motion.gltf_offset(motion.SPREAD_CM[motion.PARTS[i]])
                expected_values = [
                    round(base[j] + delta[j] * weight, 6)
                    for weight in weights for j in range(3)]
            else:
                import math
                angles = ([0, 0.2, 0.65, 1.0, 1.2] if "Fusion" in clip
                          else [0, 0.1, 0.3, 0.6, 0.9] if "Separation" in clip
                          else [0, 0.03, 0, -0.03, 0])
                expected_values = [
                    component for angle in angles
                    for component in (0, round(math.sin(angle / 2), 7),
                                      0, round(math.cos(angle / 2), 7))]
            if any(abs(value - expected_value) > 0.00001
                   for value, expected_value in zip(values, expected_values)):
                raise ValueError("GLB actual plate/rotation keyframe value drift")
    return sha(path.read_bytes())

def compile_tracks(root):
    failures = handoff.validate(root)
    if failures:
        raise ValueError("upstream presentation rejected: " + "; ".join(failures))
    glb_hash = verify_glb(root)
    presentation_bytes = (root / "presentation_handoff.json").read_bytes()
    presentation = json.loads(presentation_bytes)
    if (presentation.get("mode") != "FUS-001"
            or presentation.get("native_devices_bound") is not False
            or presentation.get("native_uefn_import") != "not_run"
            or presentation.get("clips_ms") != handoff.CLIP_MS):
        raise ValueError("unsafe presentation authority/native status")
    rows = []
    plates = []
    for phase, clip in handoff.TRACKS.items():
        times, weights = motion.CLIPS[clip]
        if round(times[-1] * 1000) != handoff.CLIP_MS[phase]:
            raise ValueError("GLB and phase durations disagree")
        for part in motion.PARTS:
            plates.append({"sequence": phase, "node": "Prototype_" + part,
                           "clip": clip, "keyframes": len(times)})
            for t, weight in zip(times, weights):
                offset = [round(v * weight, 3) for v in motion.SPREAD_CM[part]]
                rows.append(dict(sequence=phase, role="npc_plate_translation",
                                 track="Prototype_" + part, time_ms=round(t * 1000),
                                 offset_x_cm=offset[0], offset_y_cm=offset[1],
                                 offset_z_cm=offset[2], distance_cm="", fov_deg="",
                                 visibility="everyone_npc_sequence",
                                 source="omnigod_mechanical_motion.glb#" + clip))
        for t, distance, fov in CAMERAS[phase]:
            rows.append(dict(sequence=phase, role="owner_camera_dolly",
                             track="OwnerOrbitCamera", time_ms=t,
                             offset_x_cm="", offset_y_cm="", offset_z_cm="",
                             distance_cm=distance, fov_deg=fov,
                             visibility="instigator_only",
                             source="offline_edit_decision_not_native_camera"))
    for binding in presentation["bindings"]:
        phase = binding["canonical_phase"]
        if (phase not in handoff.TRACKS
                or binding["animation"] != handoff.TRACKS[phase]
                or binding["sequence_visibility"] != "Instigator Only"
                or binding["native_device_binding"] != "NOT_BOUND_EDITOR_REQUIRED"):
            raise ValueError("unsafe cue binding/visibility")
        for role, source in (("owner_audio_cue", binding["audio_source"]),
                             ("owner_caption", binding["caption_source"])):
            rows.append(dict(sequence=phase, role=role, track=binding["id"],
                             time_ms=binding["start_ms"], offset_x_cm="",
                             offset_y_cm="", offset_z_cm="", distance_cm="",
                             fov_deg="", visibility="instigator_only", source=source))
    order = {"Activating": 0, "Separating": 1}
    rows.sort(key=lambda r: (order[r["sequence"]], r["time_ms"], r["role"], r["track"]))
    if len(plates) != 26 or len(rows) != 146:
        raise ValueError("missing source plate/camera/audio/caption rows")
    if any(row["time_ms"] < 0 or row["time_ms"] > handoff.CLIP_MS[row["sequence"]]
           for row in rows):
        raise ValueError("source row outside clip")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    plan = {
        "schema_version": 1, "mode": "FUS-001", "source_only": True,
        "native_uefn_import": "not_run", "native_sequencer_binding": "not_run",
        "native_niagara_binding": "not_run", "verse_compile": "not_run",
        "fortnite_mobile_profile": "not_run", "cooked_memory": "not_run",
        "enabled_for_native_activation": False,
        "glb_sha256": glb_hash, "presentation_sha256": sha(presentation_bytes),
        "camera_visibility": "instigator_only",
        "npc_visibility": "everyone_replaceable_npc_binding",
        "lease": "trusted_owner_and_generation_checked_before_each_cue",
        "cleanup": "stop_all_owned_camera_audio_vfx_npc_tracks_before_canonical_abort",
        "reduced_motion": {"static_camera_distance_cm": 900, "fov_deg": 55,
                           "camera_shake": False, "screen_flashes": 0,
                           "non_color_cues": True, "captions": True},
        "lod_design_caps_unmeasured": presentation["lod_design_caps_unmeasured"],
        "clips_ms": handoff.CLIP_MS, "plate_tracks": plates,
        "audio_caption_bindings": presentation["bindings"],
        "row_count": len(rows), "rows": rows,
        "editor_contract": [
            "CSV is an edit decision list, not a native Sequencer import format",
            "Two separate sequences: owner camera/audio and Everyone NPC plates",
            "Actual rig/Character Definition import, Niagara/Verse binding and native tests required",
            "Visual timing never authorizes damage, owner privileges or NPC possession",
        ],
    }
    return plan, stream.getvalue().encode("utf-8")

def expected(root):
    plan, csv_data = compile_tracks(root)
    return {JSON_NAME: (json.dumps(plan, indent=2, sort_keys=True) + "\n").encode("utf-8"),
            CSV_NAME: csv_data}

def build(root):
    files = expected(root)
    for name, data in files.items():
        (root / name).write_bytes(data)
    manifest = {"schema_version": 1, "source_only": True,
                "uefn_import": "not_run",
                "files_sha256": {name: sha(data) for name, data in sorted(files.items())}}
    (root / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def validate(root):
    try:
        files = expected(root)
        problems = [name + " content drift" for name, data in files.items()
                    if (root / name).read_bytes() != data]
        manifest = json.loads((root / MANIFEST_NAME).read_text(encoding="utf-8"))
        if (manifest.get("schema_version") != 1
                or manifest.get("source_only") is not True
                or manifest.get("uefn_import") != "not_run"
                or manifest.get("files_sha256") != {
                    name: sha(data) for name, data in sorted(files.items())}):
            problems.append("manifest provenance/status drift")
        return problems
    except (OSError, ValueError, TypeError, KeyError, IndexError, struct.error) as exc:
        return ["sequencer source failed closed: " + str(exc)]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if not args.validate_only:
        build(args.output)
    failures = validate(args.output)
    for failure in failures:
        print("ERROR: " + failure, file=sys.stderr)
    if failures:
        return 1
    print("PASS: 26 plate tracks, 130 plate keys, 10 camera keys, 6 cue rows")
    print("Native Sequencer, Niagara, Verse, mobile and cooked memory: NOT RUN")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
