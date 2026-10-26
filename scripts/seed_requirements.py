"""Create conservative open obligation seeds from exact normative authority."""

import argparse
import json
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.inventory import seed_inventory  # pylint: disable=wrong-import-position


def main() -> int:
    """Create only absent entries and preserve prior mapped evidence."""
    logging.debug("Entering seed main")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()
    errors = seed_inventory(args.root)
    print(json.dumps({"seeded": not errors, "errors": errors}))
    return 1 if errors else 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
