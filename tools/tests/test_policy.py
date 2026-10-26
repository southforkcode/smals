"""Evidence claims must follow actual capability, not hopeful labels."""

import json
import unittest

from tools.audit import audit_receipt
from tools.tests import test_proof

from tools.evidence_policy import assess_case


class EvidencePolicyTests(unittest.TestCase):
    """Keep logical/source/artifact proof separate from native qualification."""

    def test_host_and_source(self):
        """Supported host-backed scopes remain available without native credit."""
        for scope in ("host", "source"):
            decision = assess_case({"scope": scope})
            self.assertTrue(decision["available"])
            self.assertFalse(decision["native_conforming"])
            self.assertEqual(decision["scope"], scope)

    def test_host_cannot_be_native(self):
        """Neither family nor exact-profile labels elevate host execution."""
        for scope in ("native-family", "exact-profile"):
            decision = assess_case(
                {"scope": scope, "profile": "i8080a", "engine_kind": "independent"}
            )
            self.assertFalse(decision["available"])
            self.assertFalse(decision["native_conforming"])
            self.assertEqual(decision["classification"], "nonconforming")

    def test_synthetic_is_nonconforming(self):
        """A synthetic engine is never disguised as native proof."""
        decision = assess_case(
            {"scope": "exact-profile", "backend": "native", "engine_kind": "synthetic"}
        )
        self.assertEqual(decision["classification"], "nonconforming")
        self.assertFalse(decision["available"])

    def test_unavailable_and_invalid(self):
        """Missing adapters and unknown semantic tags remain explicit failures."""
        for case in (
            {"backend": "unavailable"},
            {
                "backend": "native",
                "scope": "exact-profile",
                "engine_kind": "independent",
            },
            {"scope": "imaginary"},
            {"scope": []},
            {"engine_kind": None},
            {"engine_kind": "imaginary"},
        ):
            self.assertFalse(assess_case(case)["available"])

    def test_artifact_requires_checked_bytes(self):
        """Artifact scope requires an actual independent byte expectation."""
        self.assertFalse(assess_case({"scope": "artifact"})["available"])
        case = {
            "scope": "artifact",
            "artifacts": [{"path": "image.bin", "sha256": "0" * 64}],
        }
        self.assertTrue(assess_case(case)["available"])
        self.assertFalse(assess_case(case)["native_conforming"])

    def test_collector_and_auditor_bound_scope(self):
        """Actual receipts carry scope and altered native flags are rejected."""
        fixture = test_proof.ProofTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.manifest["cases"][0]["scope"] = "artifact"
        receipt = fixture.collect()
        self.assertTrue(receipt["passed"], receipt["errors"])
        self.assertEqual(
            audit_receipt(fixture.root, "FIXTURE", fixture.root / "proof"), []
        )
        receipt["cases"][0]["native_conforming"] = True
        (fixture.root / "proof/receipt.json").write_text(
            json.dumps(receipt), encoding="utf-8"
        )
        self.assertTrue(audit_receipt(fixture.root, "FIXTURE", fixture.root / "proof"))
        fixture.manifest["cases"][0]["scope"] = "exact-profile"
        rejected = fixture.collect("native")
        self.assertFalse(rejected["passed"])
        self.assertEqual(rejected["cases"][0]["classification"], "nonconforming")
        self.assertFalse((fixture.root / "native/case-0.stdout").exists())
        fixture.manifest["cases"][0].update(backend="native", engine_kind="independent")
        unavailable = fixture.collect("unavailable")
        self.assertFalse(unavailable["passed"])
        self.assertEqual(unavailable["cases"][0]["classification"], "unavailable")
