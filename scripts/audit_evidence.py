"""Audit direct proof observations or explicit requirement closure evidence."""

import argparse
import json
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.audit import (  # pylint: disable=wrong-import-position
    audit_receipt,
    audit_requirement,
)


def main() -> int:
    """Select a receipt/requirement audit without mutating completion state."""
    logging.debug("Entering audit main")
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--increment")
    group.add_argument("--requirement")
    parser.add_argument("--closure", action="store_true")
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    if args.requirement:
        errors = (
            audit_requirement(args.root, args.requirement)
            if args.closure
            else ["requirement auditing requires --closure"]
        )
    else:
        candidates = sorted(
            (args.root / "temp/evidence" / args.increment).glob("proof-*/receipt.json"),
            key=lambda path: path.stat().st_mtime,
        )
        out = args.receipt or (
            candidates[-1].parent
            if candidates
            else args.root / "temp/evidence" / args.increment / "missing"
        )
        errors = audit_receipt(args.root, args.increment, out)
    print(json.dumps({"valid": not errors, "errors": errors}))
    return 1 if errors else 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
