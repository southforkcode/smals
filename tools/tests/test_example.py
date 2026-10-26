"""Explicit unavailable boundaries for a complete example module."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CLI = Path(os.environ.get("SMIL_CLI", ROOT / "build/smil/smil")).resolve()


class ExampleTests(unittest.TestCase):
    """Commands state their actual boundary without publishing artifacts."""

    def test_stage_expectations(self):
        """Every registered stage is recognized but explicitly unavailable."""
        expectations = json.loads((ROOT / "examples/commands.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            for item in expectations["commands"]:
                with self.subTest(stage=item["stage"]):
                    result = subprocess.run(
                        [str(CLI), item["stage"], str(ROOT / expectations["input"])],
                        cwd=directory,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, item["exit"])
                    self.assertEqual(result.stdout, "")
                    self.assertEqual(result.stderr.count("error[CAP001]"), 1)
                    self.assertIn(f"] {item['phase']} ", result.stderr)
                    self.assertIn(
                        f"{item['stage']} stage is unavailable", result.stderr
                    )
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_missing_input(self):
        """CLI shape errors do not masquerade as unavailable stages."""
        for args in [("verify",), ("verify", ""), ("nonsense", "input")]:
            result = subprocess.run(
                [str(CLI), *args], capture_output=True, text=True, check=False
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("error[CLI001]", result.stderr)
