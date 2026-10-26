"""Tamper and closure checks against independently generated proof fixtures."""

import hashlib
import copy
import json
import unittest

from tools.audit import audit_receipt, audit_requirement, timing_errors
from tools.tests import test_proof


class AuditTests(unittest.TestCase):
    """Bind command observations rather than editable summaries."""

    def setUp(self):
        """Create a real passing proof with isolated inputs."""
        self.fixture = test_proof.ProofTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.receipt = self.fixture.collect()
        self.out = self.root / "proof"

    def save(self, receipt):
        """Write a deliberate mutation without changing raw observations."""
        (self.out / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")

    def test_untouched(self):
        """A complete untouched receipt audits successfully."""
        self.assertEqual(audit_receipt(self.root, "FIXTURE", self.out), [])

    def test_tampered_summary(self):
        """An editable passed flag cannot hide a wrong observed status."""
        self.fixture.manifest["cases"][0]["expected_exit"] = 1
        receipt = self.fixture.collect("failed")
        receipt["passed"] = True
        failed = self.root / "failed"
        (failed / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
        self.assertTrue(audit_receipt(self.root, "FIXTURE", failed))

    def test_log_integrity(self):
        """Missing and altered logs/records are rejected."""
        for name in ("build.stdout", "case-0.stderr", "case-0.json"):
            with self.subTest(name=name):
                path = self.out / name
                original = path.read_bytes()
                path.write_text("tampered", encoding="utf-8")
                self.assertTrue(audit_receipt(self.root, "FIXTURE", self.out))
                path.unlink()
                self.assertTrue(audit_receipt(self.root, "FIXTURE", self.out))
                path.write_bytes(original)

    def test_metadata_tamper(self):
        """Tool, target, revision/tree and source mutations fail."""
        for change in ("tool", "target", "tree", "command"):
            receipt = copy.deepcopy(self.receipt)
            if change == "tool":
                receipt["tools"]["cmake"]["sha256"] = "0" * 64
            elif change == "target":
                receipt["targets"] = ["other"]
            elif change == "tree":
                receipt["tree"] = "0" * 40
            else:
                receipt["cases"][0]["argv"] = ["other"]
            self.save(receipt)
            self.assertTrue(audit_receipt(self.root, "FIXTURE", self.out), change)
        self.save(self.receipt)
        (self.root / "CMakeLists.txt").write_text("changed", encoding="utf-8")
        self.assertTrue(audit_receipt(self.root, "FIXTURE", self.out))

    def test_work_timing(self):
        """Missing/reversed work clocks fail; active duration stays unknown."""
        for change in ("missing", "reversed", "elapsed"):
            receipt = copy.deepcopy(self.receipt)
            work = receipt["work_timing"]
            if change == "missing":
                del work["started_at_utc"]
            elif change == "reversed":
                work["ended_at_utc"] = "2026-10-25T23:59:59Z"
            else:
                work["elapsed_seconds"] = 99
            self.save(receipt)
            self.assertTrue(audit_receipt(self.root, "FIXTURE", self.out), change)
        self.assertEqual(dict(self.receipt["work_timing"])["active_seconds"], "unknown")

    def test_spec_digest(self):
        """Changed normative bytes invalidate a receipt."""
        specs = self.root / "specs"
        specs.mkdir()
        path = specs / "0000_probe.md"
        path.write_text("original", encoding="utf-8")
        self.fixture.collect("spec-proof")
        path.write_text("changed", encoding="utf-8")
        self.assertTrue(audit_receipt(self.root, "FIXTURE", self.root / "spec-proof"))

    def test_explicit_closure(self):
        """A reviewed synthetic obligation needs both actual case kinds and scope."""
        text = "Probe shall accept 42 and reject 41."
        (self.root / "specs").mkdir()
        (self.root / "specs/0000_probe.md").write_text(
            f"| TEST-001 | {text} |\n", encoding="utf-8"
        )
        self.fixture.manifest["cases"].append(
            {
                "id": "reject",
                "kind": "negative",
                "argv": [
                    "{python}",
                    "-c",
                    "import sys; print('rejected'); sys.exit(1)",
                ],
                "timeout_seconds": 5,
                "expected_exit": 1,
                "stdout_contains": ["rejected"],
            }
        )
        self.assertTrue(self.fixture.collect("closure-proof")["passed"])
        requirement = {
            "schema": "smals.requirement.v1",
            "key": "TEST-001",
            "spec_path": "specs/0000_probe.md",
            "text": text,
            "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "reviewed": True,
            "state": "open",
            "required_scopes": ["host"],
            "obligations": [
                {
                    "id": "clause.1",
                    "text": text,
                    "scopes": ["host"],
                    "evidence": [
                        {
                            "receipt": "closure-proof/receipt.json",
                            "increment": "FIXTURE",
                            "case_id": case,
                            "kind": kind,
                            "scope": "host",
                        }
                        for case, kind in [
                            ("value", "positive"),
                            ("reject", "negative"),
                        ]
                    ],
                }
            ],
        }
        path = self.root / "plans/verification/requirements/TEST-001.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(requirement), encoding="utf-8")
        before = path.read_bytes()
        self.assertEqual(audit_requirement(self.root, "TEST-001"), [])
        self.assertEqual(path.read_bytes(), before)
        self.assertTrue(
            list((self.root / "temp/evidence/closure").glob("*/replay.json"))
        )
        for change in ["review", "evidence", "scope", "clause"]:
            changed = copy.deepcopy(requirement)
            if change == "review":
                changed["reviewed"] = False
            elif change == "evidence":
                changed["obligations"][0]["evidence"] = []
            elif change == "scope":
                changed["required_scopes"].append("exact-profile")
            else:
                changed["obligations"][0]["text"] = "Probe"
            path.write_text(json.dumps(changed), encoding="utf-8")
            self.assertTrue(audit_requirement(self.root, "TEST-001"), change)

    def test_timing_annotations(self):
        """Validate in-progress/complete bounds and explicit measurements."""
        base = {"started_at_utc": "2026-10-26T00:00:00Z"}
        self.assertEqual(timing_errors(base), [])
        self.assertTrue(timing_errors({**base, "outcome": "completed"}))
        self.assertTrue(timing_errors({"started_at_utc": "invalid"}))
        self.assertTrue(timing_errors({**base, "active_seconds": 1}))
        self.assertEqual(
            timing_errors(
                {**base, "active_seconds": 1, "measurement_basis": "fixture"}
            ),
            [],
        )
