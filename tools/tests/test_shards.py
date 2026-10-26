"""Selection, audit and deadline behavior of bounded proof shards."""

import copy
import json
import unittest

from tools.audit import audit_link, audit_receipt
from tools.proof import ProofRequest, ProofSelection, run_proof
from tools.selection import select_cases
from tools.tests import test_proof


class ShardTests(unittest.TestCase):
    """Use actual fixture commands and independently expected selected IDs."""

    def setUp(self):
        """Register three deterministic independently named fixture cases."""
        self.fixture = test_proof.ProofTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        base = self.fixture.manifest["cases"][0]
        self.fixture.manifest["cases"] = [
            {
                **copy.deepcopy(base),
                "id": name,
                "case_set": "quick" if name != "c" else "other",
            }
            for name in ("a", "b", "c")
        ]

    def collect(self, name, case_set=None, shard=None, budget=120):
        """Invoke a real selected proof in a fresh directory."""
        self.fixture.path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        request = ProofRequest(
            self.fixture.root,
            "FIXTURE",
            self.fixture.root / name,
            self.fixture.cmake,
            17,
            self.fixture.timing,
            selection=ProofSelection(case_set, shard, budget),
        )
        return run_proof(request)

    def test_subset_and_audit(self):
        """The auditor binds exactly the selected case and rejects other links."""
        receipt = self.collect("selected", "quick", "2/2")
        self.assertTrue(receipt["passed"], receipt["errors"])
        self.assertEqual([case["id"] for case in receipt["cases"]], ["b"])
        self.assertEqual(
            audit_receipt(self.fixture.root, "FIXTURE", self.fixture.root / "selected"),
            [],
        )
        errors, _ = audit_link(
            self.fixture.root,
            {
                "receipt": "selected/receipt.json",
                "increment": "FIXTURE",
                "case_id": "c",
                "kind": "positive",
                "scope": "host",
            },
        )
        self.assertTrue(errors)

    def test_disjoint_complete_partition(self):
        """Two shards cover the independently listed IDs exactly once."""
        left = self.collect("left", shard="1/2")
        right = self.collect("right", shard="2/2")
        self.assertTrue(left["passed"] and right["passed"])
        first = {case["id"] for case in left["cases"]}
        second = {case["id"] for case in right["cases"]}
        self.assertFalse(first & second)
        self.assertEqual(first | second, {"a", "b", "c"})

    def test_empty_and_invalid(self):
        """Empty, malformed and oversized shard coordinates never pass."""
        for index, args in enumerate(
            [
                ("missing", None),
                (None, "4/4"),
                (None, "0/2"),
                (None, "3/2"),
                (None, "1/0"),
                (None, "x"),
                (None, "1/65"),
            ]
        ):
            self.assertFalse(self.collect(f"invalid-{index}", *args)["passed"], args)

    def test_oversize(self):
        """Known excessive declared runtime requests explicit subdivision."""
        for case in self.fixture.manifest["cases"]:
            case["timeout_seconds"] = 70
        receipt = self.collect("oversize")
        self.assertFalse(receipt["passed"])
        self.assertIn("budget", str(receipt["errors"]))

    def test_runtime_bound(self):
        """An exhausted proof budget cannot produce green evidence."""
        for case in self.fixture.manifest["cases"]:
            case["timeout_seconds"] = 0.001
        self.assertFalse(self.collect("deadline", budget=0.01)["passed"])

    def test_invalid_budgets(self):
        """Unknown, nonpositive and excessive bounds are not valid selections."""
        for budget in (None, 0, -1, True, 121, float("nan")):
            self.assertTrue(select_cases(self.fixture.manifest, budget=budget)[1])
