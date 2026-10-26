"""Check script/tool formatting and lint with the selected interpreter."""

import argparse
import logging
from pathlib import Path
import subprocess
import sys

LOGGER = logging.getLogger(__name__)


def run_checks(root: Path, fix: bool = False) -> int:
    """Apply nonempty Python acceptance; return process failures as values."""
    LOGGER.debug("Entering run_checks: root=%s fix=%s", root, fix)
    files = sorted(
        str(path)
        for directory in (root / "scripts", root / "tools")
        for path in directory.rglob("*.py")
    )
    if not files:
        LOGGER.error("No Python files under scripts/ or tools/ in %s", root)
        return 1
    black_args = [] if fix else ["--check", "--diff"]
    commands = (
        [sys.executable, "-m", "black", *black_args, *files],
        [sys.executable, "-m", "pylint", "--persistent=n", *files],
    )
    for command in commands:
        try:
            status = subprocess.run(command, check=False).returncode
        except OSError as error:
            LOGGER.error("Cannot invoke %s: %s", command[2], error)
            return 1
        if status != 0:
            LOGGER.error("%s rejected Python inputs: exit %s", command[2], status)
            return status
    return 0


def main() -> int:
    """Parse tool options and return the acceptance status."""
    LOGGER.debug("Entering main")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--fix", action="store_true")
    args = parser.parse_args()
    return run_checks(args.root, args.fix)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
