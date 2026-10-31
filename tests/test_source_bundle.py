from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile


SPEC = importlib.util.spec_from_file_location(
    "source_bundle", Path(__file__).resolve().parents[1] / "tools/build_source_bundle.py")
bundle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bundle)


class SourceBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        self.output = Path(self.temp.name) / "delivery.zip"
        self.git("init", "-q")
        self.git("config", "user.name", "Bundle test")
        self.git("config", "user.email", "bundle-test@example.invalid")
        (self.root / "source.verse").write_text("example := class:\n", encoding="utf-8")
        (self.root / "mesh.glb").write_bytes(bytes(range(256)))
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args])

    def test_exact_source_bytes_and_explicit_engine_evidence(self):
        result = bundle.build_bundle(self.root, self.output, "passed", "https://example.invalid/run")
        self.assertEqual(result["source_files"], 2)
        self.assertEqual(result["commit"], self.git("rev-parse", "HEAD").decode().strip())
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(archive.read("AEONFALL/mesh.glb"), bytes(range(256)))
            proof = json.loads(archive.read("AEONFALL/BUILD_PROVENANCE.json"))
            self.assertEqual(proof["source_checks"]["result"], "passed")
            self.assertEqual(proof["verse_engine_compile"], "not_run")
            self.assertEqual(proof["fortnite_launch_session"], "not_run")
        self.assertEqual(bundle.verify_bundle(self.output), result)

    def test_untracked_files_never_enter_archive(self):
        (self.root / "secret.env").write_text("untracked fixture", encoding="utf-8")
        bundle.build_bundle(self.root, self.output)
        with zipfile.ZipFile(self.output) as archive:
            self.assertNotIn("AEONFALL/secret.env", archive.namelist())
            self.assertFalse(any("/.git/" in name for name in archive.namelist()))

    def test_modified_indexed_file_is_rejected(self):
        (self.root / "source.verse").write_text("modified\n", encoding="utf-8")
        with self.assertRaisesRegex(bundle.BundleError, "bytes changed"):
            bundle.build_bundle(self.root, self.output)
        self.assertFalse(self.output.exists())

    def test_staged_uncommitted_change_is_rejected(self):
        (self.root / "source.verse").write_text("modified\n", encoding="utf-8")
        self.git("add", ".")
        with self.assertRaisesRegex(bundle.BundleError, "Index differs"):
            bundle.build_bundle(self.root, self.output)

    def test_missing_source_is_rejected(self):
        (self.root / "source.verse").unlink()
        with self.assertRaisesRegex(bundle.BundleError, "absent"):
            bundle.build_bundle(self.root, self.output)

    def test_indexed_symlink_is_rejected(self):
        (self.root / "alias.verse").symlink_to("source.verse")
        self.git("add", ".")
        self.git("commit", "-qm", "unsafe fixture")
        with self.assertRaisesRegex(bundle.BundleError, "unsafe indexed path"):
            bundle.build_bundle(self.root, self.output)

    def test_tampered_archive_bytes_are_rejected(self):
        bundle.build_bundle(self.root, self.output)
        with zipfile.ZipFile(self.output) as original:
            contents = {name: original.read(name) for name in original.namelist()}
        contents["AEONFALL/source.verse"] = b"tampered"
        with zipfile.ZipFile(self.output, "w") as archive:
            for name, data in contents.items():
                archive.writestr(name, data)
        with self.assertRaisesRegex(bundle.BundleError, "source hash differs"):
            bundle.verify_bundle(self.output)

    def test_duplicate_archive_names_are_rejected(self):
        bundle.build_bundle(self.root, self.output)
        with zipfile.ZipFile(self.output, "a") as archive:
            archive.writestr("AEONFALL/source.verse", b"duplicate")
        with self.assertRaisesRegex(bundle.BundleError, "duplicate names"):
            bundle.verify_bundle(self.output)


if __name__ == "__main__":
    unittest.main()
