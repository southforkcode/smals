"""Build and run one manifest into a direct proof receipt."""

import argparse
import json
import logging
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.proof import (  # pylint: disable=wrong-import-position
    ProofRequest,
    ProofSelection,
    run_proof,
)


def main() -> int:
    """Preserve work metadata while collecting bounded command evidence."""
    logging.debug("Entering prove main")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--increment", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--cmake", default=shutil.which("cmake"))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--work-timing", type=Path)
    parser.add_argument("--case-set")
    parser.add_argument("--shard")
    parser.add_argument("--budget-seconds", type=float, default=120)
    args = parser.parse_args()
    receipt = run_proof(
        ProofRequest(
            args.root,
            args.increment,
            args.out,
            args.cmake,
            args.seed,
            args.work_timing,
            selection=ProofSelection(args.case_set, args.shard, args.budget_seconds),
        )
    )
    print(json.dumps({"passed": receipt["passed"], "errors": receipt["errors"]}))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
