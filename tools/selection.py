"""Deterministic nonempty proof selection with a declared runtime bound."""

from dataclasses import dataclass
import logging
import re

LOGGER = logging.getLogger(__name__)


@dataclass
class ProofSelection:
    """A bounded case selection and its internal execution deadline."""

    case_set: str | None = None
    shard: str | None = None
    budget_seconds: float = 120
    deadline: float = 0


def select_cases(manifest, case_set=None, shard=None, budget=120):
    """Return exact selected registrations or a reason to subdivide."""
    LOGGER.debug("Entering select_cases")
    if (
        not isinstance(budget, (int, float))
        or isinstance(budget, bool)
        or not 0 < budget <= 120
    ):
        return [], ["proof budget must be greater than zero and at most 120 seconds"]
    cases = [
        case
        for case in manifest["cases"]
        if case_set in (None, "all") or case.get("case_set", "all") == case_set
    ]
    if shard is not None:
        if not isinstance(shard, str) or not re.fullmatch(
            r"[1-9][0-9]*/[1-9][0-9]*", shard
        ):
            return [], ["shard must be I/N with positive coordinates"]
        part, count = (int(value) for value in shard.split("/"))
        if part > count or count > 64:
            return [], ["shard coordinates exceed supported bounds"]
        cases = cases[part - 1 :: count]
    if not cases:
        return [], ["empty case-set/shard selection"]
    if sum(case["timeout_seconds"] for case in cases) > budget:
        return [], ["selected shard exceeds declared budget; subdivide it"]
    return cases, []
