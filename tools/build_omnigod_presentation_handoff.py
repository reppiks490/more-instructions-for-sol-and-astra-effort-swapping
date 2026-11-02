#!/usr/bin/env python3
"""Deterministic, source-only captions and timed UEFN presentation handoff.

No native UEFN devices, animations, or gameplay effects are created by this tool.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import wave

sys.path.insert(0, str(Path(__file__).resolve().parent))

CLIP_MS = {"Activating": 4000, "Separating": 3000}
TRACKS = {"Activating": "AEON_FUS001_Fusion_Preview",
          "Separating": "AEON_FUS001_Separation_Preview"}
CAPTION_PATHS = {"Activating": "captions/fusion_owner.vtt",
                 "Separating": "captions/separation_owner.vtt"}
TEXT = {"eclipse_begin": "[Eclipse pulse — expanding ring]",
        "plates_lock": "[Armor plates lock — converging chevrons]",
        "separation_begin": "[Void separation — contracting ring]"}
EXPECTED_CUES = (("Activating", "eclipse_begin", 0, "expanding_ring", "audio/eclipse_subpulse.wav", 1300),
                 ("Activating", "plates_lock", 3100, "converging_chevrons", "audio/iron_plate_lock.wav", 480),
                 ("Separating", "separation_begin", 0, "contracting_ring", "audio/void_separation.wav", 1100))
SOURCE_FILES = ("omnigod_mechanical_motion.glb", "audio/eclipse_subpulse.wav",
                "audio/iron_plate_lock.wav", "audio/void_separation.wav")
GENERATED_FILES = ("captions/fusion_owner.vtt", "captions/separation_owner.vtt",
                   "presentation_handoff.json")


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def ms(seconds: object) -> int:
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
        raise ValueError("cue time must be numeric")
    result = round(seconds * 1000)
    if abs(seconds * 1000 - result) > 1e-6 or result < 0:
        raise ValueError("cue time must be nonnegative whole milliseconds")
    return result


def stamp(milliseconds: int) -> str:
    h, rest = divmod(milliseconds, 3600000)
    m, rest = divmod(rest, 60000)
    s, fraction = divmod(rest, 1000)
    return f"{h:02}:{m:02}:{s:02}.{fraction:03}"


def source_manifest(root: Path) -> tuple[dict, dict]:
    cue = json.loads((root / "cue_sheet.json").read_text(encoding="utf-8"))
    if (cue.get("schema_version") != 1 or cue.get("mode") != "FUS-001"
            or cue.get("enabled_for_native_activation") is not False
            or cue.get("native_uefn_import") != "not_run"
            or cue.get("npc_skeletal_rig") is not False):
        raise ValueError("unsafe source metadata or native success claim")
    rules = cue.get("binding_rules", {})
    if (rules.get("requires_authoritative_generation") is not True
            or rules.get("abort_cancels_all_cues") is not True
            or rules.get("cleanup_before_canonical_abort") is not True
            or rules.get("owner_sequence_visibility") != "Instigator_Only_no_replaceable_npc_binding"
            or rules.get("npc_replaceable_binding_visibility") != "Everyone_separate_sequence"):
        raise ValueError("missing authority/cancellation/visibility rules")
    accessible = cue.get("accessibility", {})
    if (accessible.get("reduced_flash") is not True
            or accessible.get("non_color_cues") is not True
            or accessible.get("screen_flash_count") != 0):
        raise ValueError("inaccessible presentation source")
    if cue.get("animations") != [TRACKS["Activating"], TRACKS["Separating"],
                                   "AEON_OMNI_DormantBreath_Preview"]:
        raise ValueError("unknown animation binding")
    entries = cue.get("files", [])
    if sorted(item.get("path") for item in entries) != sorted(SOURCE_FILES):
        raise ValueError("source inventory must contain the four generated assets")
    hashes = {"cue_sheet.json": digest((root / "cue_sheet.json").read_bytes())}
    for entry in entries:
        rel = entry["path"]
        content = (root / rel).read_bytes()
        if len(content) != entry.get("bytes") or digest(content) != entry.get("sha256"):
            raise ValueError(f"source checksum mismatch: {rel}")
        hashes[rel] = digest(content)
    return cue, hashes


def compile_plan(root: Path) -> tuple[dict, dict[str, str]]:
    cue, hashes = source_manifest(root)
    events = cue.get("cue_events", [])
    if len(events) != len(EXPECTED_CUES):
        raise ValueError("unknown cue count")
    bindings = []
    captions = {phase: [] for phase in CLIP_MS}
    for event, (phase, name, start, shape, wav, duration) in zip(events, EXPECTED_CUES):
        if (event.get("phase") != phase or event.get("name") != name
                or event.get("shape") != shape or event.get("audio") != wav
                or event.get("visibility") != "instigator_only"
                or ms(event.get("time_seconds")) != start):
            raise ValueError("unknown/out-of-order cue or unsafe visibility")
        with wave.open(str(root / wav), "rb") as sound:
            if (sound.getnchannels(), sound.getsampwidth(), sound.getframerate()) != (1, 2, 16000):
                raise ValueError(f"unsupported PCM metadata: {wav}")
            if sound.getnframes() != 16 * duration:
                raise ValueError(f"audio duration mismatch: {wav}")
        if start + duration > CLIP_MS[phase]:
            raise ValueError(f"cue exceeds phase boundary: {name}")
        binding = {"id": name, "canonical_phase": phase,
                   "animation": TRACKS[phase], "start_ms": start,
                   "end_ms": start + duration, "audio_source": wav,
                   "shape": shape, "caption": TEXT[name],
                   "caption_source": CAPTION_PATHS[phase],
                   "sequence_visibility": "Instigator Only",
                   "native_device_binding": "NOT_BOUND_EDITOR_REQUIRED"}
        bindings.append(binding)
        captions[phase].append(f"{stamp(start)} --> {stamp(start + duration)}\n{TEXT[name]}\n")
    subtitles = {CAPTION_PATHS[phase]: "WEBVTT\n\n" + "\n".join(rows)
                 for phase, rows in captions.items()}
    plan = {
        "schema_version": 1, "mode": "FUS-001",
        "status": "SOURCE_ONLY_NOT_IMPORTED_IN_UEFN",
        "native_uefn_import": "not_run", "verse_compile": "not_run",
        "launch_session": "not_run", "native_devices_bound": False,
        "input_asset_sha256": hashes,
        "presentation_roles": {
            "owner_camera_and_audio": "Instigator Only; never attach replaceable NPC binding",
            "npc_plate_motion": "Everyone; separate replaceable NPC sequence; requires skeletal retargeting"},
        "authority_requirements": {
            "source": "canonical_fusion_state_runtime_trusted_owner_generation_only",
            "start": "only after canonical BeginActivation and physical adapter admission",
            "per_event": "reject stale generation, wrong instigator, revocation or phase mismatch",
            "cleanup": "stop owned camera, audio, VFX and NPC presentation BEFORE canonical Abort/CompleteSeparation",
            "acknowledgment": "cue schedule alone NEVER confirms native success or gameplay damage",
            "duplicate_start": "reject; at most one owner presentation sequence"},
        "clips_ms": CLIP_MS,
        "lod_design_caps_unmeasured": cue["lod_policy"],
        "accessibility": {"audio_alternatives": list(subtitles),
                          "no_flash": True, "non_color_shape_cues": True,
                          "camera_shake_opt_out": True},
        "bindings": bindings,
        "release_gates": ["trusted_player_reference", "skeletal_fbx_rig",
                          "native_editor_bindings", "verse_compile",
                          "two_client_launch_session", "cooked_memory", "runtime_profile"]}
    return plan, subtitles


def build(root: Path) -> dict:
    plan, subtitles = compile_plan(root)
    for rel, content in subtitles.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    plan_bytes = (json.dumps(plan, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    (root / "presentation_handoff.json").write_bytes(plan_bytes)
    package = {"schema_version": 1,
               "source_only": True, "uefn_import": "not_run",
               "files_sha256": {rel: digest((root / rel).read_bytes())
                                for rel in GENERATED_FILES}}
    (root / "presentation_handoff_manifest.json").write_text(
        json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return package


def validate(root: Path) -> list[str]:
    errors = []
    try:
        expected_plan, expected_subtitles = compile_plan(root)
        expected = (json.dumps(expected_plan, indent=2, sort_keys=True,
                               ensure_ascii=False) + "\n").encode("utf-8")
        if (root / "presentation_handoff.json").read_bytes() != expected:
            errors.append("presentation handoff drift or unsafe native claim")
        for rel, expected_text in expected_subtitles.items():
            if (root / rel).read_text(encoding="utf-8") != expected_text:
                errors.append(f"caption timeline drift: {rel}")
        manifest = json.loads((root / "presentation_handoff_manifest.json").read_text(encoding="utf-8"))
        if (manifest.get("schema_version") != 1 or manifest.get("source_only") is not True
                or manifest.get("uefn_import") != "not_run"
                or set(manifest.get("files_sha256", {})) != set(GENERATED_FILES)):
            errors.append("incorrect presentation inventory/status")
        for rel in GENERATED_FILES:
            if manifest.get("files_sha256", {}).get(rel) != digest((root / rel).read_bytes()):
                errors.append(f"handoff hash mismatch: {rel}")
    except (OSError, ValueError, KeyError, TypeError, wave.Error, EOFError) as exc:
        errors.append(f"handoff failed closed: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if not args.validate_only:
        build(args.output)
    problems = validate(args.output)
    if problems:
        for problem in problems:
            print("ERROR: " + problem, file=sys.stderr)
        return 1
    print("PASS: deterministic owner captions, phase/audio sync, source provenance, no native success claims")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
