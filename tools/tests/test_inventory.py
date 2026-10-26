"""Independent source-authority and orphan-mapping inventory fixtures."""

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.inventory import audit_inventory, seed_inventory


class InventoryTests(unittest.TestCase):
    """Keep exact authority and initial open status visible."""

    def setUp(self):
        """Create two normative rows and independently assigned minimum scopes."""
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.root)
        (self.root / "specs").mkdir()
        (self.root / "plans").mkdir()
        self.text = "The probe shall preserve café; it shall reject zero."
        (self.root / "specs/0000_probe.md").write_text(
            f"| TEST-001 | {self.text} |\n", encoding="utf-8"
        )
        (self.root / "specs/0001_other.md").write_text(
            "| TEST-002 | The probe shall return 42. |\n", encoding="utf-8"
        )
        (self.root / "plans/11_requirement_matrix.md").write_text(
            "| [TEST-001](../specs/0000_probe.md) | fixture | H | audit |\n"
            "| [TEST-002](../specs/0001_other.md) | fixture | S / H | audit |\n",
            encoding="utf-8",
        )
        self.directory = self.root / "plans/verification/requirements"

    def test_exact_open_seed(self):
        """Exact Unicode authority survives and nothing becomes verified."""
        self.assertEqual(seed_inventory(self.root, 2), [])
        entry = json.loads((self.directory / "TEST-001.json").read_text())
        self.assertEqual(entry["text"], self.text)
        self.assertEqual(
            entry["text_sha256"], hashlib.sha256(self.text.encode()).hexdigest()
        )
        self.assertEqual(entry["state"], "open")
        self.assertFalse(entry["reviewed"])
        self.assertTrue(entry["obligations"])
        self.assertTrue(all(not clause["evidence"] for clause in entry["obligations"]))
        summary, errors = audit_inventory(self.root, 2)
        self.assertEqual(errors, [])
        self.assertEqual(summary, {"total": 2, "open": 2, "verified": 0})
        before = {
            path.name: path.read_bytes() for path in self.directory.glob("*.json")
        }
        self.assertEqual(seed_inventory(self.root, 2), [])
        self.assertEqual(
            before,
            {path.name: path.read_bytes() for path in self.directory.glob("*.json")},
        )

    def test_missing_extra_and_changed(self):
        """Missing keys, orphan manifests and altered authority fail."""
        self.assertEqual(seed_inventory(self.root, 2), [])
        path = self.directory / "TEST-001.json"
        original = path.read_bytes()
        path.unlink()
        self.assertTrue(audit_inventory(self.root, 2)[1])
        path.write_bytes(original)
        orphan = self.directory / "TEST-999.json"
        orphan.write_bytes(original)
        self.assertTrue(audit_inventory(self.root, 2)[1])
        orphan.unlink()
        (self.root / "specs/0000_probe.md").write_text(
            "| TEST-001 | Altered. |\n", encoding="utf-8"
        )
        self.assertTrue(audit_inventory(self.root, 2)[1])
        self.assertTrue(seed_inventory(self.root, 2))
        self.assertEqual(path.read_bytes(), original)

    def test_duplicate_authority(self):
        """Two definitions of a requirement cannot seed an inventory."""
        (self.root / "specs/0001_other.md").write_text(
            "| TEST-001 | Duplicate. |\n", encoding="utf-8"
        )
        self.assertTrue(seed_inventory(self.root, 2))

    def test_orphan_case(self):
        """A mapping must resolve an actually registered increment/case."""
        self.assertEqual(seed_inventory(self.root, 2), [])
        path = self.directory / "TEST-001.json"
        entry = json.loads(path.read_text())
        entry["obligations"][0]["evidence"] = [
            {
                "increment": "FIXTURE",
                "case_id": "known",
                "kind": "positive",
                "scope": "host",
                "receipt": None,
            }
        ]
        path.write_text(json.dumps(entry), encoding="utf-8")
        registered = self.root / "plans/verification/increments/FIXTURE.json"
        registered.parent.mkdir(parents=True, exist_ok=True)
        registered.write_text(
            json.dumps(
                {
                    "schema": "smals.increment.v1",
                    "increment": "FIXTURE",
                    "targets": ["fixture"],
                    "build_dir": "build",
                    "inputs": ["specs/*.md"],
                    "cases": [
                        {
                            "id": "known",
                            "argv": ["{python}", "-c", "print(42)"],
                            "timeout_seconds": 1,
                            "expected_exit": 0,
                            "stdout_contains": ["42"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(audit_inventory(self.root, 2)[1], [])
        before = path.read_bytes()
        self.assertEqual(seed_inventory(self.root, 2), [])
        self.assertEqual(path.read_bytes(), before)
        entry["obligations"][0]["evidence"][0]["case_id"] = "missing"
        path.write_text(json.dumps(entry), encoding="utf-8")
        self.assertTrue(audit_inventory(self.root, 2)[1])

    def test_unearned_verified_flag(self):
        """A hand-edited verified flag earns no verified count."""
        self.assertEqual(seed_inventory(self.root, 2), [])
        path = self.directory / "TEST-001.json"
        entry = json.loads(path.read_text())
        entry["state"] = "verified"
        path.write_text(json.dumps(entry), encoding="utf-8")
        summary, errors = audit_inventory(self.root, 2)
        self.assertTrue(errors)
        self.assertEqual(summary["verified"], 0)
