"""Fail-closed tests for 13-region Omnigod mobile presentation admission source."""
from __future__ import annotations
import copy
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import build_omnigod_mobile_admission as m


def save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def wav(duration_ms: int, seed: int) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as sound:
        sound.setnchannels(1)
        sound.setsampwidth(2)
        sound.setframerate(16000)
        sound.writeframes(struct.pack("<h", seed) * (16 * duration_ms))
    return buf.getvalue()


def fake_png(seed: int) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + struct.pack(">II", 256, 256) + bytes([seed])


def fixture(root: Path) -> tuple[Path, ...]:
    arsenal, cinematic = root / "arsenal", root / "cinematic"
    arsenal.mkdir()
    cinematic.mkdir()
    regions = [f"REG-{i:03}" for i in range(1, 14)]
    world = root / "world.json"
    policy = root / "policy.json"
    fusion = root / "fusion.json"
    save(world, {"regions": [{"id": x} for x in regions]})
    save(policy, {"required_world_regions": regions,
                  "strategy": "full_universe_source_before_playable_prototype",
                  "no_codex_in_automation": True})
    save(fusion, {"forms": [{"id": x, "enabled_for_native_activation": False}
                             for x in ("FUS-001", "FUS-002")],
                  "identity": {"enabled_by_default": False},
                  "runtime": {"max_simultaneous_fusions": 1}})
    files = {}
    abilities = []
    events = []
    for i in range(1, 13):
        ident = f"SFA-{i:03}"
        image = f"textures/{ident}.png"
        caption = f"captions/{ident}.vtt"
        audio = f"audio/{ident}.wav"
        files[image] = fake_png(i)
        files[caption] = f"WEBVTT\n\n[{ident} warning]\n".encode()
        files[audio] = wav(900, i)
        abilities.append({"id": ident, "shape": f"unique_shape_{i}",
                          "texture": image, "caption": caption,
                          "presentation_hold_ms": 1100})
        events.append({"ability_id": ident, "role": "base_warning",
                       "start_ms": 0, "end_ms": 900, "audio": audio,
                       "caption": caption, "caption_text": f"[{ident} warning]",
                       "requested_visibility": "instigator_only",
                       "source_only_not_hit_authorization": True})
    for idx, ident in enumerate(("SFA-002", "SFA-005"), 1):
        audio = f"audio/{ident}_accent.wav"
        files[audio] = wav(300, 20 + idx)
        events.append({"ability_id": ident, "role": "accent", "start_ms": 300,
                       "end_ms": 600, "audio": audio,
                       "caption": f"captions/{ident}.vtt",
                       "caption_text": f"[{ident} warning]",
                       "requested_visibility": "instigator_only",
                       "source_only_not_hit_authorization": True})
    for name, data in files.items():
        path = arsenal / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    manifest = {
        "schema_version": 1, "source_only": True, "fusion_mode": "FUS-001",
        "native_uefn_import": "not_run", "native_niagara_binding": "not_run",
        "native_verse_compile": "not_run", "enabled_for_native_activation": False,
        "fuse_titan_FUS002_enabled": False, "event_not_damage_or_hit_receipt": True,
        "region_ids": regions, "cleanup_triggers": list(m.CLEANUP),
        "ability_count": 12, "audio_event_count": 14, "unique_shape_count": 12,
        "lod_design_caps_unmeasured": [
            {"tier": "near", "max_distance_cm": 2500, "max_particles": 80, "max_systems": 2},
            {"tier": "mid", "max_distance_cm": 6000, "max_particles": 24, "max_systems": 1},
            {"tier": "far", "max_distance_cm": 12000, "max_particles": 0, "max_systems": 0}],
        "accessibility": {"reduced_flash_screen_flashes": 0},
        "abilities": abilities, "events": events,
        "files": [{"path": name, "bytes": len(data), "sha256": m.sha(data)}
                  for name, data in sorted(files.items())]}
    save(arsenal / "arsenal_presentation_manifest.json", manifest)
    rows = []
    tracks = []
    for phase, duration in (("Activating", 4000), ("Separating", 3000)):
        for i in range(13):
            tracks.append({"sequence": phase, "node": f"Prototype_Plate_{i}"})
            for t in range(5):
                rows.append({"sequence": phase, "time_ms": t * (duration // 4),
                             "role": "npc_plate_translation", "visibility": "everyone_npc_sequence"})
        for t in range(5):
            rows.append({"sequence": phase, "time_ms": t * (duration // 4),
                         "role": "owner_camera_dolly", "visibility": "instigator_only"})
    for phase in ("Activating", "Activating", "Separating"):
        for role in ("owner_audio_cue", "owner_caption"):
            rows.append({"sequence": phase, "time_ms": 0, "role": role,
                         "visibility": "instigator_only"})
    assert len(rows) == 146
    sequence = {"schema_version": 1, "source_only": True, "mode": "FUS-001",
                "native_uefn_import": "not_run", "native_sequencer_binding": "not_run",
                "native_niagara_binding": "not_run", "verse_compile": "not_run",
                "enabled_for_native_activation": False,
                "camera_visibility": "instigator_only", "row_count": 146,
                "rows": rows, "plate_tracks": tracks,
                "clips_ms": {"Activating": 4000, "Separating": 3000}}
    save(cinematic / "sequencer_track_handoff.json", sequence)
    (cinematic / "sequencer_track_handoff.csv").write_text("source_only,not_native\n")
    save(cinematic / "sequencer_track_manifest.json", {
        "source_only": True, "uefn_import": "not_run", "files_sha256": {
            name: m.sha((cinematic / name).read_bytes())
            for name in ("sequencer_track_handoff.json", "sequencer_track_handoff.csv")}})
    return arsenal, cinematic, world, policy, fusion


class MobileAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.inputs = fixture(self.root)
        self.out = self.root / "out"

    def tearDown(self):
        self.temp.cleanup()

    def test_full_source_coverage_and_build_validation(self):
        m.build(self.out, *self.inputs)
        self.assertEqual(m.validate(self.out, *self.inputs), [])
        plan = json.loads((self.out / m.OUTPUTS[0]).read_text())
        self.assertEqual((plan["row_count"], plan["stress_case_count"]), (546, 78))
        self.assertEqual(plan["presentation_count"], 14)
        self.assertEqual(len(plan["region_ids"]), 13)
        self.assertFalse(plan["enabled_for_native_activation"])
        self.assertEqual(plan["cooked_memory_mib"], "not_run")

    def test_deterministic_export(self):
        self.assertEqual(m.expected(*self.inputs), m.expected(*self.inputs))

    def test_budget_overload_drops_effect(self):
        req = lambda ident, tier, voices: {"id": ident, "tier": tier,
                "peak_audio_voices": voices, "mode": "FUS-001",
                "lease_valid": True, "generation": 1, "owner_scope": "trusted_owner"}
        outcome = m.admit([req("SFA-001", "near", 1), req("SFA-011", "near", 1),
                           req("SFA-012", "near", 1)])
        self.assertEqual(len(outcome["accepted"]), 2)
        self.assertEqual(outcome["used"]["particles"], 80)
        self.assertEqual(len(outcome["rejected"]), 1)

    def test_overlap_audio_budget(self):
        req = lambda ident: {"id": ident, "tier": "near", "peak_audio_voices": 2,
                             "mode": "FUS-001", "lease_valid": True,
                             "generation": 1, "owner_scope": "trusted_owner"}
        result = m.admit([req("SFA-002"), req("SFA-005")])
        self.assertEqual(len(result["accepted"]), 1)
        self.assertEqual(result["used"]["audio_voices"], 2)

    def test_untrusted_lease_rejected(self):
        for field, value in (("lease_valid", False), ("generation", 0),
                             ("owner_scope", "anonymous"), ("mode", "FUS-002"),
                             ("id", "SFA-999")):
            req = {"id": "SFA-001", "tier": "near", "peak_audio_voices": 1,
                   "mode": "FUS-001", "lease_valid": True, "generation": 1,
                   "owner_scope": "trusted_owner"}
            req[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                m.admit([req])

    def test_far_is_caption_only(self):
        req = {"id": "SFA-011", "tier": "far", "peak_audio_voices": 1,
               "mode": "FUS-001", "lease_valid": True,
               "generation": 1, "owner_scope": "trusted_owner"}
        result = m.admit([req])
        self.assertEqual(result["used"]["systems"], 0)
        self.assertEqual(result["rejected"][0]["reason"], "far_noncolor_hud_fallback_only")

    def test_mutated_audio_rejected_even_if_manifest_rehashed(self):
        path = self.inputs[0] / "audio/SFA-001.wav"
        data = path.read_bytes()
        path.write_bytes(data[:-2])
        manifest_path = self.inputs[0] / "arsenal_presentation_manifest.json"
        manifest = json.loads(manifest_path.read_text())
        for item in manifest["files"]:
            if item["path"] == "audio/SFA-001.wav":
                item["bytes"] = len(path.read_bytes())
                item["sha256"] = m.sha(path.read_bytes())
        save(manifest_path, manifest)
        self.assertTrue(m.validate(self.out, *self.inputs))

    def test_forged_native_success_rejected(self):
        path = self.inputs[1] / "sequencer_track_handoff.json"
        plan = json.loads(path.read_text())
        plan["native_uefn_import"] = "verified"
        save(path, plan)
        self.assertTrue(m.validate(self.out, *self.inputs))

    def test_region_scope_drift_rejected(self):
        path = self.inputs[2]
        world = json.loads(path.read_text())
        world["regions"].pop()
        save(path, world)
        self.assertTrue(m.validate(self.out, *self.inputs))

    def test_fusion_gate_rejected(self):
        path = self.inputs[4]
        contract = json.loads(path.read_text())
        contract["forms"][1]["enabled_for_native_activation"] = True
        save(path, contract)
        self.assertTrue(m.validate(self.out, *self.inputs))

    def test_manifest_provenance_mutation_rejected(self):
        m.build(self.out, *self.inputs)
        path = self.out / "mobile_presentation_manifest.json"
        manifest = json.loads(path.read_text())
        manifest["native_uefn_import"] = "verified"
        save(path, manifest)
        self.assertTrue(m.validate(self.out, *self.inputs))

    def test_cinematic_owner_visibility_rejected(self):
        path = self.inputs[1] / "sequencer_track_handoff.json"
        sequence = json.loads(path.read_text())
        sequence["rows"][-1]["visibility"] = "everyone"
        save(path, sequence)
        self.assertTrue(m.validate(self.out, *self.inputs))


if __name__ == "__main__":
    unittest.main()
