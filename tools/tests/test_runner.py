"""Observable behavior of the bounded native case registry."""

import os
from pathlib import Path
import subprocess
import unittest

RUNNER = Path(os.environ.get("SMIL_TESTS", "build/smil/smil_tests")).resolve()


def invoke(*args):
    """Capture the actual native runner status and evidence text."""
    return subprocess.run(
        [str(RUNNER), *args], capture_output=True, text=True, check=False
    )


class RunnerTests(unittest.TestCase):
    """Cases discriminate fixture success from runner errors."""

    def test_deterministic_seed(self):
        """The same input seed reproduces its observation."""
        first = invoke("--case", "command.reject", "--seed", "17")
        second = invoke("--case", "command.reject", "--seed", "17")
        self.assertEqual(first.returncode, 0)
        self.assertEqual(first.stdout, second.stdout)
        self.assertIn(
            "seed=17 input=invalid.17 expected=reject observed=reject", first.stdout
        )

    def test_inverted_expectation(self):
        """A wrong oracle cannot pass and retains reproduction input."""
        result = invoke("--case", "version", "--seed", "7", "--invert")
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "seed=7 input=0.1.0 expected=reject observed=accept", result.stdout
        )

    def test_selection_bounds(self):
        """No empty or truncated selection can pass."""
        for args in [("--case", "missing"), ("--case", ""), ("--limit", "1")]:
            with self.subTest(args=args):
                result = invoke(*args)
                self.assertEqual(result.returncode, 2)
                self.assertIn("selection", result.stderr)
                self.assertEqual(result.stdout, "")

    def test_bad_options(self):
        """Reject malformed or unbounded options before execution."""
        for args in [
            ("--unknown",),
            ("--case",),
            ("--seed", "x"),
            ("--seed", "1x"),
            ("--seed", "-1"),
            ("--seed", "18446744073709551616"),
            ("--limit", "0"),
            ("--limit", "33"),
        ]:
            with self.subTest(args=args):
                self.assertEqual(invoke(*args).returncode, 2)

    def test_seed_boundaries(self):
        """Both valid unsigned seed boundaries execute selected cases."""
        for seed in ["0", "18446744073709551615"]:
            result = invoke("--case", "version", "--seed", seed, "--limit", "1")
            self.assertEqual(result.returncode, 0)
            self.assertIn(f"seed={seed}", result.stdout)
