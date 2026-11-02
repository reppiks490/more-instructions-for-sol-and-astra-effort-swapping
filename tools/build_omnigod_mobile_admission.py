#!/usr/bin/env python3
"""Compile a bounded, source-only Omnigod presentation admission/LOD handoff.

Reads actual generated audiovisual bytes and Sequencer edit-decision source.
Never binds devices, authorizes damage, grants ownership or claims native UEFN.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import wave

TIERS = {"near": (1, 40, 2500), "mid": (1, 24, 6000), "far": (0, 0, 12000)}
POOL = {"systems": 2, "particles": 80, "audio_voices": 2,
        "near_effects": 2, "mid_effects": 1, "far_effects": 0}
MODES = ("Activating", "Separating")
CLEANUP = ("owner_revoked", "generation_changed", "cancelled", "actor_despawned",
           "region_unloaded", "separation", "logout")
OUTPUTS = ("mobile_presentation_admission.json", "mobile_presentation_admission.csv")
FIELDS = ("region", "presentation", "tier", "max_distance_cm", "systems", "particles",
          "peak_audio_voices", "hold_ms", "fallback", "visibility")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def safe_file(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError("unsafe source asset path")
    relative = Path(name)
    if relative.is_absolute() or any(x in (".", "..", "") for x in relative.parts):
        raise ValueError("unsafe source asset path")
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
        raise ValueError(f"missing or escaped source asset: {name}")
    return resolved


def peak(events: list[dict]) -> int:
    endpoints = []
    for event in events:
        start, end = event["start_ms"], event["end_ms"]
        if (type(start) is not int or type(end) is not int or start < 0 or end <= start):
            raise ValueError("invalid source audio event timing")
        endpoints.extend(((start, 1), (end, -1)))
    active = maximum = 0
    for _, change in sorted(endpoints):  # end (-1) before start (+1)
        active += change
        if active < 0:
            raise ValueError("negative audio event concurrency")
        maximum = max(maximum, active)
    if active:
        raise ValueError("unclosed audio event")
    return maximum


def load_inputs(arsenal_dir: Path, cinematic_dir: Path, world: Path,
                policy: Path, fusion: Path) -> tuple[dict, dict, list[str], dict]:
    a = read_json(arsenal_dir / "arsenal_presentation_manifest.json")
    s = read_json(cinematic_dir / "sequencer_track_handoff.json")
    sm = read_json(cinematic_dir / "sequencer_track_manifest.json")
    topology, universe, f = read_json(world), read_json(policy), read_json(fusion)
    regions = [r["id"] for r in topology["regions"]]
    if (len(regions) != 13 or len(set(regions)) != 13
            or regions != universe.get("required_world_regions")):
        raise ValueError("full 13-region canonical topology/policy drift")
    if (universe.get("strategy") != "full_universe_source_before_playable_prototype"
            or universe.get("no_codex_in_automation") is not True):
        raise ValueError("universe-first or zero-Codex policy drift")
    forms = {x["id"]: x for x in f.get("forms", [])}
    if (set(forms) != {"FUS-001", "FUS-002"}
            or any(x.get("enabled_for_native_activation") is not False for x in forms.values())
            or f.get("identity", {}).get("enabled_by_default") is not False
            or f.get("runtime", {}).get("max_simultaneous_fusions") != 1):
        raise ValueError("fusion native/authority gate drift")
    if (a.get("source_only") is not True or a.get("fusion_mode") != "FUS-001"
            or a.get("enabled_for_native_activation") is not False
            or a.get("fuse_titan_FUS002_enabled") is not False
            or a.get("native_uefn_import") != "not_run"
            or a.get("native_niagara_binding") != "not_run"
            or a.get("native_verse_compile") != "not_run"
            or a.get("event_not_damage_or_hit_receipt") is not True
            or a.get("region_ids") != regions
            or a.get("cleanup_triggers") != list(CLEANUP)):
        raise ValueError("unsafe arsenal source/native/cleanup claim")
    if (a.get("ability_count") != 12 or a.get("audio_event_count") != 14
            or a.get("unique_shape_count") != 12):
        raise ValueError("incomplete arsenal source")
    lod = a.get("lod_design_caps_unmeasured", [])
    if [(x.get("tier"), x.get("max_distance_cm"), x.get("max_particles"),
         x.get("max_systems")) for x in lod] != [
            ("near", 2500, 80, 2), ("mid", 6000, 24, 1), ("far", 12000, 0, 0)]:
        raise ValueError("arsenal LOD ceiling drift")
    if a.get("accessibility", {}).get("reduced_flash_screen_flashes") != 0:
        raise ValueError("flash accessibility contract drift")
    files = a.get("files", [])
    if len(files) != 38 or len({x["path"] for x in files}) != 38:
        raise ValueError("expected 38 unique original audiovisual files")
    file_map = {}
    for item in files:
        data = safe_file(arsenal_dir, item["path"]).read_bytes()
        if len(data) != item["bytes"] or sha(data) != item["sha256"]:
            raise ValueError("arsenal audiovisual bytes/hash drift: " + item["path"])
        if item["path"].endswith(".png"):
            if not data.startswith(b"\x89PNG\r\n\x1a\n") or data[16:24] != (256).to_bytes(4, "big") * 2:
                raise ValueError("invalid original PNG header/dimensions")
        file_map[item["path"]] = data
    for ext, count in ((".png", 12), (".wav", 14), (".vtt", 12)):
        members = [data for name, data in file_map.items() if name.endswith(ext)]
        if len(members) != count or len({sha(data) for data in members}) != count:
            raise ValueError("duplicate or incomplete original source: " + ext)
    abilities = a.get("abilities", [])
    if ([x.get("id") for x in abilities] != [f"SFA-{i:03}" for i in range(1, 13)]
            or len({x.get("shape") for x in abilities}) != 12):
        raise ValueError("arsenal ability identity/shape drift")
    events = a.get("events", [])
    if len(events) != 14:
        raise ValueError("arsenal event count drift")
    peaks = {}
    for ability in abilities:
        ident = ability["id"]
        matching = [e for e in events if e.get("ability_id") == ident]
        if not matching or len(matching) > 2:
            raise ValueError("missing/duplicated ability events: " + ident)
        if (ability.get("texture") not in file_map
                or ability.get("caption") not in file_map):
            raise ValueError("missing ability texture/caption")
        caption = file_map[ability["caption"]].decode("utf-8")
        if not caption.startswith("WEBVTT\n\n"):
            raise ValueError("invalid WebVTT header")
        for e in matching:
            if (e.get("requested_visibility") != "instigator_only"
                    or e.get("source_only_not_hit_authorization") is not True
                    or e.get("audio") not in file_map
                    or e.get("caption") != ability["caption"]
                    or e.get("caption_text") not in caption
                    or e["end_ms"] > ability["presentation_hold_ms"]):
                raise ValueError("unsafe or unbacked audio/caption event: " + ident)
            with wave.open(io.BytesIO(file_map[e["audio"]]), "rb") as wav:
                if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, 16000):
                    raise ValueError("unsupported original audio encoding")
                if wav.getnframes() != 16 * (e["end_ms"] - e["start_ms"]):
                    raise ValueError("original PCM duration drift")
        peaks[ident] = peak(matching)
        if peaks[ident] > POOL["audio_voices"]:
            raise ValueError("single ability exceeds voice pool")
    if (s.get("schema_version") != 1 or s.get("source_only") is not True
            or s.get("mode") != "FUS-001"
            or s.get("native_uefn_import") != "not_run"
            or s.get("native_sequencer_binding") != "not_run"
            or s.get("native_niagara_binding") != "not_run"
            or s.get("verse_compile") != "not_run"
            or s.get("enabled_for_native_activation") is not False
            or s.get("camera_visibility") != "instigator_only"
            or s.get("row_count") != 146 or len(s.get("rows", [])) != 146
            or len(s.get("plate_tracks", [])) != 26
            or s.get("clips_ms") != {"Activating": 4000, "Separating": 3000}):
        raise ValueError("unsafe or incomplete 13-plate cinematic source")
    roles = Counter(row.get("role") for row in s["rows"])
    if roles != {"npc_plate_translation": 130, "owner_camera_dolly": 10,
                 "owner_audio_cue": 3, "owner_caption": 3}:
        raise ValueError("incomplete or unknown cinematic track roles")
    plate_tracks = [(x.get("sequence"), x.get("node")) for x in s["plate_tracks"]]
    if len(set(plate_tracks)) != 26 or {x[0] for x in plate_tracks} != set(MODES):
        raise ValueError("duplicate or missing mechanical plate track")
    for row in s["rows"]:
        phase = row.get("sequence")
        if (phase not in MODES or type(row.get("time_ms")) is not int
                or not 0 <= row["time_ms"] <= s["clips_ms"][phase]):
            raise ValueError("invalid cinematic source row")
        if row.get("role") == "npc_plate_translation":
            if row.get("visibility") != "everyone_npc_sequence":
                raise ValueError("NPC plate leaked into owner-only sequence")
        elif row.get("visibility") != "instigator_only":
            raise ValueError("owner cinematic cue leaked to everyone")
    for name in ("sequencer_track_handoff.json", "sequencer_track_handoff.csv"):
        data = safe_file(cinematic_dir, name).read_bytes()
        if sm.get("files_sha256", {}).get(name) != sha(data):
            raise ValueError("cinematic EDL/CSV hash drift")
    if sm.get("uefn_import") != "not_run" or sm.get("source_only") is not True:
        raise ValueError("cinematic source manifest native status drift")
    return a, s, regions, peaks


def admit(requests: list[dict]) -> dict:
    """Offline, fail-closed admission snapshot; NOT a Verse or Niagara runtime."""
    used = {"systems": 0, "particles": 0, "audio_voices": 0, "near": 0, "mid": 0}
    accepted, rejected = [], []
    allowed = {f"SFA-{i:03}" for i in range(1, 13)} | {"FUS-001-" + x for x in MODES}
    for r in requests:
        if (r.get("id") not in allowed or r.get("mode") != "FUS-001" or r.get("lease_valid") is not True
                or type(r.get("generation")) is not int or r["generation"] <= 0
                or r.get("owner_scope") != "trusted_owner"
                or r.get("tier") not in TIERS or not isinstance(r.get("id"), str)):
            raise ValueError("untrusted/stale source admission request")
        tier = r["tier"]
        systems, particles, _ = TIERS[tier]
        voices = r["peak_audio_voices"] if tier != "far" else 0
        if type(voices) is not int or voices < 0 or voices > POOL["audio_voices"]:
            raise ValueError("invalid peak audio voice request")
        if tier == "far":
            rejected.append({"id": r["id"], "reason": "far_noncolor_hud_fallback_only"})
            continue
        if (used[tier] >= POOL[tier + "_effects"]
                or used["systems"] + systems > POOL["systems"]
                or used["particles"] + particles > POOL["particles"]
                or used["audio_voices"] + voices > POOL["audio_voices"]):
            rejected.append({"id": r["id"], "reason": "bounded_pool_or_voice_exhausted"})
            continue
        used[tier] += 1
        used["systems"] += systems
        used["particles"] += particles
        used["audio_voices"] += voices
        accepted.append(r["id"])
    return {"accepted": accepted, "rejected": rejected, "used": used}


def compile_plan(arsenal_dir: Path, cinematic_dir: Path, world: Path,
                 policy: Path, fusion: Path) -> tuple[dict, bytes]:
    a, s, regions, peaks = load_inputs(arsenal_dir, cinematic_dir, world, policy, fusion)
    presentations = [{"id": x["id"], "hold_ms": x["presentation_hold_ms"],
                      "peak_audio_voices": peaks[x["id"]], "source": x["texture"],
                      "fallback_caption": x["caption"]} for x in a["abilities"]]
    presentations += [{"id": "FUS-001-" + phase, "hold_ms": s["clips_ms"][phase],
                       "peak_audio_voices": 1,
                       "source": "sequencer_track_handoff.json#" + phase,
                       "fallback_caption": "owner_caption_required"} for phase in MODES]
    rows = []
    for region in regions:
        for p in presentations:
            for tier, (systems, particles, distance) in TIERS.items():
                rows.append({"region": region, "presentation": p["id"], "tier": tier,
                             "max_distance_cm": distance, "systems": systems,
                             "particles": particles,
                             "peak_audio_voices": p["peak_audio_voices"] if systems else 0,
                             "hold_ms": p["hold_ms"],
                             "fallback": "noncolor_hud_and_caption" if tier == "far" else "on_budget_visual_audio_caption",
                             "visibility": "owner_camera_separate_from_everyone_npc" if p["id"].startswith("FUS-") else "owner_audio_world_noncolor_warning"})
    cases = []
    for region in regions:
        samples = [
            ("two_near", [("SFA-001", "near", 1), ("SFA-011", "near", 1)]),
            ("near_plus_mid", [("FUS-001-Activating", "near", 1), ("SFA-001", "mid", 1)]),
            ("three_near", [("SFA-001", "near", 1), ("SFA-011", "near", 1), ("SFA-012", "near", 1)]),
            ("two_mid", [("SFA-001", "mid", 1), ("SFA-003", "mid", 1)]),
            ("voice_collision", [("SFA-002", "near", 2), ("SFA-005", "near", 2)]),
            ("far_fallback", [("SFA-011", "far", 1)]),
        ]
        for name, sample in samples:
            requests = [{"id": ident, "tier": tier, "peak_audio_voices": voice,
                         "mode": "FUS-001", "lease_valid": True, "generation": 1,
                         "owner_scope": "trusted_owner"} for ident, tier, voice in sample]
            cases.append({"region": region, "case": name, **admit(requests)})
    if len(rows) != 13 * 14 * 3 or len(cases) != 13 * 6:
        raise ValueError("incomplete region/ability/phase coverage")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    plan = {
        "schema_version": 1, "source_only": True, "native_uefn_import": "not_run",
        "native_niagara_binding": "not_run", "native_sequencer_binding": "not_run",
        "native_verse_compile": "not_run", "fortnite_mobile_profile": "not_run",
        "cooked_memory_mib": "not_run", "enabled_for_native_activation": False,
        "form": "FUS-001", "FUS_002_enabled": False,
        "scope": "all_13_regions_all_12_abilities_both_fusion_phases",
        "region_ids": regions, "presentation_count": len(presentations),
        "row_count": len(rows), "stress_case_count": len(cases),
        "source_provenance": {
            "arsenal_manifest_sha256": sha((arsenal_dir / "arsenal_presentation_manifest.json").read_bytes()),
            "sequencer_handoff_sha256": sha((cinematic_dir / "sequencer_track_handoff.json").read_bytes()),
            "world_topology_sha256": sha(world.read_bytes()),
            "universe_policy_sha256": sha(policy.read_bytes()),
            "fusion_contract_sha256": sha(fusion.read_bytes())},
        "unmeasured_design_pool_per_loaded_region": POOL,
        "per_effect_lod_design": {tier: {"systems": v[0], "particles": v[1],
                                          "max_distance_cm": v[2]} for tier, v in TIERS.items()},
        "admission": "trusted_owner_and_current_generation_required_before_each_event",
        "audio": "peak overlapping PCM events count against two-voice pool; drop secondary visuals rather than damage logic",
        "cleanup": list(CLEANUP),
        "on_cleanup": "stop_owner_camera_audio_subtitles_and_npc_plates_before_canonical_abort; release_all_region_slots",
        "accessibility": {"noncolor_hud": True, "captions": True,
                          "reduced_flash_screen_flashes": 0, "reduced_motion_static_camera": True,
                          "touch_readability_native_test_required": True},
        "runtime_limitations": ["This is an offline admission model, not an installed Verse scheduler",
                                "Do not interpret presentation denial as a gameplay hit/receipt denial",
                                "Region unload and owner/generation revocation must atomically release slots",
                                "All 840+ entity packages and 13 regions remain source-first"],
        "presentations": presentations, "rows": rows, "stress_cases": cases,
    }
    return plan, stream.getvalue().encode("utf-8")


def expected(*inputs: Path) -> dict[str, bytes]:
    plan, csv_data = compile_plan(*inputs)
    return {OUTPUTS[0]: (json.dumps(plan, sort_keys=True, indent=2) + "\n").encode(),
            OUTPUTS[1]: csv_data}


def build(output: Path, *inputs: Path) -> None:
    files = expected(*inputs)
    output.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (output / name).write_bytes(data)
    (output / "mobile_presentation_manifest.json").write_text(
        json.dumps({"schema_version": 1, "source_only": True, "native_uefn_import": "not_run",
                    "files_sha256": {k: sha(v) for k, v in sorted(files.items())}},
                   sort_keys=True, indent=2) + "\n", encoding="utf-8")


def validate(output: Path, *inputs: Path) -> list[str]:
    try:
        files = expected(*inputs)
        problems = ["generated source drift: " + name for name, data in files.items()
                    if (output / name).read_bytes() != data]
        manifest = read_json(output / "mobile_presentation_manifest.json")
        if manifest != {"schema_version": 1, "source_only": True,
                        "native_uefn_import": "not_run",
                        "files_sha256": {k: sha(v) for k, v in sorted(files.items())}}:
            problems.append("manifest hash/native-status drift")
        return problems
    except (OSError, ValueError, KeyError, TypeError, IndexError, wave.Error,
            UnicodeError, json.JSONDecodeError) as exc:
        return ["mobile presentation source failed closed: " + str(exc)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arsenal", type=Path, required=True)
    parser.add_argument("--cinematic", type=Path, required=True)
    parser.add_argument("--world", type=Path, default=Path("content/world/world_topology.json"))
    parser.add_argument("--policy", type=Path, default=Path("content/implementation/universe_first_policy.json"))
    parser.add_argument("--fusion", type=Path, default=Path("content/sovereign/fusion_integration_contract.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    inputs = (args.arsenal, args.cinematic, args.world, args.policy, args.fusion)
    if not args.validate_only:
        build(args.output, *inputs)
    failures = validate(args.output, *inputs)
    for failure in failures:
        print("ERROR:", failure, file=sys.stderr)
    if failures:
        return 1
    print("PASS: 546 LOD admission rows, 78 regional stress cases, 38 source files verified")
    print("Native UEFN, Verse, Niagara, Sequencer, Fortnite mobile and cooked memory: NOT RUN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
