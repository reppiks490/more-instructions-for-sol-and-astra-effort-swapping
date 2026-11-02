"""Real PCM audio source regressions for all 13 AEONFALL regions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import build_all_region_audio as source
import validate_all_region_audio as validator


class WholeWorldSoundSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.pack=Path(cls.tmp.name)/"audio"
        cls.meta=source.build(cls.pack)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_full_world_binary_audio_validation(self):
        self.assertEqual(validator.audit(self.pack),[])

    def test_three_actual_wav_files_for_every_region(self):
        self.assertEqual(self.meta["cue_count"],39)
        self.assertEqual(self.meta["region_count"],13)
        self.assertEqual(len(self.meta["files"]),39)
        self.assertEqual(
            {r["id"] for r in self.meta["regions"]},
            {f"REG-{i:03d}" for i in range(1,14)})
        for row in self.meta["regions"]:
            self.assertEqual([x["kind"] for x in row["sources"]],
                             ["ambient","danger","navigation"])
            for cue in row["sources"]:
                self.assertTrue((self.pack/cue["file"]).is_file())

    def test_source_audio_contains_nonempty_pcm_and_bounded_levels(self):
        for row in self.meta["regions"]:
            for cue in row["sources"]:
                path=self.pack/cue["file"]
                b,values=validator.parse_wav(path)
                self.assertEqual(len(values),source.frames_for(cue["kind"]))
                self.assertGreater(max(values)-min(values),500)
                self.assertLessEqual(max(abs(x) for x in values),19000)
                self.assertEqual(cue["metrics"]["peak_pcm"],
                                 max(abs(x) for x in values))

    def test_every_region_has_independent_sonic_signature(self):
        self.assertEqual(len({r["sonic_identity"] for r in self.meta["regions"]}),13)
        shas={c["sha256"] for r in self.meta["regions"] for c in r["sources"]}
        self.assertEqual(len(shas),39)

    def test_original_sound_does_not_use_external_samples(self):
        self.assertFalse(self.meta["external_samples_used"])
        self.assertTrue(self.meta["source_audio_only"])
        self.assertEqual(self.meta["origin"],
                         "original deterministic mathematical PCM synthesis")

    def test_explicit_native_and_mobile_limitations(self):
        self.assertEqual(self.meta["native_uefn_import"],"not_run")
        self.assertEqual(self.meta["native_audio_device_binding"],"not_run")
        self.assertEqual(self.meta["fortnite_mobile_playtest"],"not_run")
        self.assertFalse(self.meta["automatic_gameplay_triggers_implemented"])

    def test_deterministic_bytes_of_every_generated_wav(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"audio"
            self.assertEqual(source.build(target),self.meta)
            for file in self.meta["files"]:
                self.assertEqual((target/file["path"]).read_bytes(),
                                 (self.pack/file["path"]).read_bytes())

    def test_ambient_wave_loop_edges_are_bounded(self):
        for row in self.meta["regions"]:
            pcm=row["sources"][0]["metrics"]
            self.assertLessEqual(pcm["seam_delta_pcm"],700)
            self.assertGreater(pcm["rms_pcm"],200)

    def test_threat_cue_zero_envelope(self):
        for number in range(1,14):
            values=source.pcm(number,"danger")
            self.assertEqual(values[0],0)
            self.assertEqual(values[-1],0)

    def test_navigation_cue_zero_envelope(self):
        for number in range(1,14):
            values=source.pcm(number,"navigation")
            self.assertEqual(values[0],0)
            self.assertEqual(values[-1],0)

    def mutate(self,callback):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"audio"
            shutil.copytree(self.pack,dest)
            callback(dest)
            self.assertTrue(validator.audit(dest))

    def mutate_manifest(self,callback):
        def mutation(folder):
            path=folder/"manifest.json"
            item=json.loads(path.read_text(encoding="utf-8"))
            callback(item)
            path.write_text(json.dumps(item),encoding="utf-8")
        self.mutate(mutation)

    def test_false_native_import_claim_rejected(self):
        self.mutate_manifest(lambda p:p.__setitem__("native_uefn_import","passed"))

    def test_forged_mobile_playtest_rejected(self):
        self.mutate_manifest(lambda p:p.__setitem__("fortnite_mobile_playtest","passed"))

    def test_fake_npc_sound_trigger_binding_rejected(self):
        self.mutate_manifest(lambda p:p.__setitem__(
            "automatic_gameplay_triggers_implemented",True))

    def test_missing_regional_audio_file_rejected(self):
        self.mutate(lambda d:(d/"REG-012"/"REG-012_danger_original.wav").unlink())

    def test_forged_material_region_identifier_rejected(self):
        self.mutate_manifest(lambda p:p["regions"][4].__setitem__("id","REG-999"))

    def test_swapped_source_wav_rejected_even_with_forged_sha(self):
        def change(directory):
            f=directory/"REG-008"/"REG-008_ambient_original.wav"
            replacement=(directory/"REG-009"/"REG-009_ambient_original.wav").read_bytes()
            f.write_bytes(replacement)
            m=directory/"manifest.json"
            data=json.loads(m.read_text(encoding="utf-8"))
            new_hash=hashlib.sha256(replacement).hexdigest()
            data["regions"][7]["sources"][0]["sha256"]=new_hash
            for row in data["files"]:
                if row["path"]=="REG-008/REG-008_ambient_original.wav":
                    row["sha256"]=new_hash
                    row["bytes"]=len(replacement)
            m.write_text(json.dumps(data),encoding="utf-8")
        self.mutate(change)

    def test_truncated_pcm_header_rejected(self):
        self.mutate(lambda d:(d/"REG-010"/"REG-010_navigation_original.wav")
                    .write_bytes(b"RIFFbroken"))

    def test_forged_audio_loudness_metrics_rejected(self):
        self.mutate_manifest(lambda p:p["regions"][0]["sources"][1]
                             ["metrics"].__setitem__("peak_pcm",12))

    def test_declared_file_hash_mismatch_rejected(self):
        self.mutate_manifest(lambda p:p["files"][15].__setitem__("sha256","0"*64))


if __name__=="__main__":
    unittest.main()
