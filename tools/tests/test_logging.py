"""Structured diagnostics preserve actionable errors at their origin."""

import json
import os
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
CLI = Path(os.environ.get("SMIL_CLI", ROOT / "build/smil/smil")).resolve()


class LoggingTests(unittest.TestCase):
    """All CLI log lines are structured and one origin explains rejection."""

    def test_rejection_records(self):
        """Invalid command returns one reason and named entry records."""
        result = subprocess.run(
            [str(CLI), "invalid"], capture_output=True, text=True, check=False
        )
        self.assertEqual(result.returncode, 1)
        records = [json.loads(line) for line in result.stderr.splitlines()]
        self.assertTrue(
            all(set(row) == {"level", "unit", "event", "message"} for row in records)
        )
        errors = [row for row in records if row["level"] == "error"]
        self.assertEqual(len(errors), 1)
        self.assertIn("error[CLI001]", errors[0]["message"])
        self.assertIn("expected --version", errors[0]["message"])
        self.assertEqual(errors[0]["unit"], "diagnostic")
        self.assertTrue(any(row["event"] == "entry" for row in records))
