"""Independent process and artifact expectations for proof collection."""

import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from tools import proof

from tools.proof import ProofRequest, run_proof


class ProofTests(unittest.TestCase):
    """Use an isolated real CMake target and executable cases."""

    def setUp(self):
        """Create all fixture inputs independently of the runner."""
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.root)
        (self.root / "CMakeLists.txt").write_text(
            "cmake_minimum_required(VERSION 3.28)\n"
            "project(fixture NONE)\n"
            'add_custom_target(fixture COMMAND "${CMAKE_COMMAND}" -E echo built)\n',
            encoding="utf-8",
        )
        self.cmake = shutil.which("cmake")
        subprocess.run(
            [self.cmake, "-S", str(self.root), "-B", str(self.root / "build")],
            capture_output=True,
            check=True,
        )
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(
            ["git", "-C", str(self.root), "add", "CMakeLists.txt"], check=True
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-qm",
                "Fixture",
            ],
            check=True,
        )
        self.manifest = {
            "schema": "smals.increment.v1",
            "increment": "FIXTURE",
            "targets": ["fixture"],
            "build_dir": "build",
            "inputs": ["CMakeLists.txt"],
            "cases": [
                {
                    "id": "value",
                    "argv": [
                        "{python}",
                        "-c",
                        "from pathlib import Path; "
                        "Path('result.txt').write_bytes(b'42\\n'); print(42)",
                    ],
                    "timeout_seconds": 5,
                    "expected_exit": 0,
                    "stdout_contains": ["42\n"],
                    "artifacts": [
                        {
                            "path": "result.txt",
                            "sha256": hashlib.sha256(b"42\n").hexdigest(),
                        }
                    ],
                }
            ],
        }
        self.path = self.root / "plans/verification/increments/FIXTURE.json"
        self.path.parent.mkdir(parents=True)
        self.timing = self.root / "work.json"
        self.timing.write_text(
            json.dumps(
                {
                    "started_at_utc": "2026-10-26T00:00:00Z",
                    "ended_at_utc": "2026-10-26T00:00:01Z",
                    "elapsed_seconds": 1,
                    "active_seconds": "unknown",
                    "waiting_seconds": "unknown",
                }
            ),
            encoding="utf-8",
        )

    def collect(self, name="proof"):
        """Collect the currently specified cases."""
        self.path.write_text(json.dumps(self.manifest), encoding="utf-8")
        return run_proof(
            ProofRequest(
                self.root, "FIXTURE", self.root / name, self.cmake, 17, self.timing
            )
        )

    def test_good_and_reproducible(self):
        """Case effects and stable hashes repeat; work time is preserved."""
        first = self.collect()
        second = self.collect("second")
        self.assertTrue(first["passed"], first["errors"])
        self.assertEqual(first["source_hashes"], second["source_hashes"])
        self.assertEqual(
            first["cases"][0]["artifacts"], second["cases"][0]["artifacts"]
        )
        self.assertEqual(
            dict(first["work_timing"])["started_at_utc"], "2026-10-26T00:00:00Z"
        )
        self.assertEqual(dict(first["work_timing"])["elapsed_seconds"], 1)

    def test_wrong_exit_and_output(self):
        """A failing test or wrong observed value cannot pass."""
        for field, value in [
            ("expected_exit", 1),
            ("stdout_contains", ["wrong value"]),
        ]:
            with self.subTest(field=field):
                self.manifest["cases"][0][field] = value
                self.assertFalse(self.collect(field)["passed"])
                self.manifest["cases"][0][field] = (
                    0 if field == "expected_exit" else ["42\n"]
                )

    def test_timeout(self):
        """Real subprocess timeout remains nonpassing with partial output."""
        self.manifest["cases"][0].update(
            argv=[
                "{python}",
                "-c",
                "import time; print('started', flush=True); time.sleep(2)",
            ],
            timeout_seconds=0.1,
        )
        receipt = self.collect()
        self.assertFalse(receipt["passed"])
        self.assertTrue(receipt["cases"][0]["timed_out"])

    def test_empty_and_unavailable(self):
        """No selected cases or unavailable backend can be green."""
        self.manifest["cases"][0]["backend"] = "unavailable"
        self.assertFalse(self.collect("unavailable")["passed"])
        self.manifest["cases"] = []
        self.assertFalse(self.collect("empty")["passed"])

    def test_missing_artifact_and_build_failure(self):
        """Artifact absence and failed target construction both prevent proof."""
        self.manifest["cases"][0]["artifacts"][0]["path"] = "absent.txt"
        self.assertFalse(self.collect("missing")["passed"])
        self.manifest["targets"] = ["missing_target"]
        self.assertFalse(self.collect("build")["passed"])

    def test_missing_log(self):
        """A lost command log cannot produce a passed receipt."""
        original = proof.capture

        def lose_log(*args):
            record = original(*args)
            if args[2] == "case-0":
                (args[1] / record["stdout"]["path"]).unlink()
            return record

        with mock.patch("tools.proof.capture", side_effect=lose_log):
            receipt = self.collect()
        self.assertFalse(receipt["passed"])
        self.assertIn("missing or changed stdout log", str(receipt["errors"]))

    def test_fresh_output(self):
        """Stale output is refused rather than reused."""
        self.assertTrue(self.collect()["passed"])
        self.assertFalse(self.collect()["passed"])

    def test_artifact_mismatch(self):
        """An independent wrong hash fails even for an existing artifact."""
        self.manifest["cases"][0]["artifacts"][0]["sha256"] = "0" * 64
        self.assertFalse(self.collect()["passed"])

    def test_closed_schema(self):
        """Reject unsafe, ambiguous or unbounded registrations."""
        variants = [
            None,
            {},
            {**self.manifest, "schema": "unknown"},
            {**self.manifest, "targets": []},
            {**self.manifest, "build_dir": "../outside"},
            {**self.manifest, "inputs": [0]},
        ]
        for data in variants:
            self.assertTrue(proof.manifest_errors(data, "FIXTURE"))
        for change in [
            {"unexpected": True},
            {"id": "../bad"},
            {"argv": []},
            {"timeout_seconds": 121},
            {"expected_exit": "0"},
            {"backend": "native"},
            {"stdout_contains": [""]},
            {"artifacts": [{}]},
            {"stdout_contains": [], "artifacts": []},
        ]:
            changed = copy.deepcopy(self.manifest)
            changed["cases"][0].update(change)
            self.assertTrue(proof.manifest_errors(changed, "FIXTURE"), change)
        changed = copy.deepcopy(self.manifest)
        changed["cases"].append(changed["cases"][0])
        self.assertTrue(proof.manifest_errors(changed, "FIXTURE"))

    def test_external_boundaries(self):
        """Missing executables/inputs and malformed JSON remain failed values."""
        self.manifest["cases"][0]["argv"] = ["/nonexistent-proof-executable"]
        self.assertFalse(self.collect("executable")["passed"])
        self.manifest["inputs"] = ["missing.input"]
        self.assertFalse(self.collect("input")["passed"])
        self.manifest["inputs"] = ["../outside"]
        self.assertFalse(self.collect("escape")["passed"])
        self.path.write_text("{invalid", encoding="utf-8")
        request = ProofRequest(self.root, "FIXTURE", self.root / "json", self.cmake)
        self.assertFalse(run_proof(request)["passed"])
