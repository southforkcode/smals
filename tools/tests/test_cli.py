"""Command boundary behavior of the built executable."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

CLI = Path(os.environ.get("SMIL_CLI", "build/smil/smil")).resolve()


class CommandTests(unittest.TestCase):
    """Check observable status, output and diagnostics."""

    def test_version(self):
        """Tool identity alone succeeds."""
        result = subprocess.run(
            [str(CLI), "--version"], capture_output=True, text=True, check=False
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "smil 0.1.0\n")
        self.assertNotIn("error[", result.stderr)

    def test_invalid(self):
        """A command error cannot publish its requested artifact."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "invalid.object"
            result = subprocess.run(
                [str(CLI), "invalid", "--output", str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr.count("error[CLI001]"), 1)
            self.assertIn(
                "command-line <command-line>:1:1 [0,7): "
                "expected --version or <parse|verify|bind|link|run> <input>",
                result.stderr,
            )
            self.assertFalse(output.exists())
