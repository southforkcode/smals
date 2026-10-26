"""Behavioral checks for Python acceptance."""

import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tools.check_python import run_checks

CHECKER = pathlib.Path(__file__).resolve().parents[1] / "check_python.py"


class QualityTests(unittest.TestCase):
    """Check real formatter and linter effects."""

    def run_case(self, source, fix=False):
        """Run acceptance on an isolated script tree."""
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "scripts").mkdir()
            if source is not None:
                (root / "scripts" / "probe.py").write_text(source, encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    str(CHECKER),
                    "--root",
                    str(root),
                    *(["--fix"] if fix else []),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_valid(self):
        """A documented constant passes both tools."""
        result = self.run_case('"""A probe."""\n\nVALUE = 42\n')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_format_failure(self):
        """Actual unformatted code fails acceptance."""
        result = self.run_case('"""A probe."""\nVALUE=42\n')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("would reformat", result.stdout + result.stderr)

    def test_lint_failure(self):
        """An undefined name fails even when formatted."""
        result = self.run_case('"""A probe."""\n\nprint(missing_value)\n')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("undefined-variable", result.stdout + result.stderr)

    def test_empty(self):
        """Empty discovery cannot pass."""
        result = self.run_case(None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No Python files", result.stdout + result.stderr)

    def test_fix(self):
        """Fix mode corrects a format violation before lint."""
        result = self.run_case('"""A probe."""\nVALUE=42\n', fix=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("reformatted", result.stderr)

    def test_process_error(self):
        """OS invocation failures become actionable error values."""
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "tools").mkdir()
            (root / "tools" / "probe.py").write_text("VALUE = 42\n", encoding="utf-8")
            with mock.patch(
                "tools.check_python.subprocess.run",
                side_effect=OSError("not executable"),
            ):
                with self.assertLogs("tools.check_python", level="ERROR") as logs:
                    self.assertEqual(run_checks(root), 1)
                self.assertIn("Cannot invoke black: not executable", logs.output[0])
