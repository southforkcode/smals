"""Prevent logical or synthetic evidence from acquiring native conformance."""

import logging

LOGGER = logging.getLogger(__name__)
SCOPES = frozenset({"source", "host", "artifact", "native-family", "exact-profile"})


def decision(scope, classification, available, reason=""):
    """Describe the current supported evidence boundary explicitly."""
    LOGGER.debug("Entering evidence decision")
    return {
        "scope": scope,
        "classification": classification,
        "available": available,
        "native_conforming": False,
        "reason": reason,
    }


def backend_decision(scope, backend):
    """No native execution adapter is qualified at this implementation stage."""
    LOGGER.debug("Entering backend_decision")
    if backend == "unavailable":
        return decision(scope, "unavailable", False, "backend unavailable")
    if backend == "native":
        return decision(
            scope, "unavailable", False, "no qualified native execution adapter"
        )
    if scope in ("native-family", "exact-profile"):
        return decision(
            scope, "nonconforming", False, "host evidence cannot satisfy native scope"
        )
    return None


def assess_case(case):
    """Classify actual capability; declarations alone never qualify a profile."""
    LOGGER.debug("Entering assess_case")
    scope = case.get("scope", "host")
    backend = case.get("backend", "host")
    engine = case.get("engine_kind", "host-model")
    if (
        not all(isinstance(value, str) for value in (scope, backend, engine))
        or scope not in SCOPES
        or backend not in ("host", "native", "unavailable")
        or engine not in ("host-model", "independent", "synthetic")
    ):
        return decision(
            scope, "invalid", False, "unknown evidence scope/backend/engine kind"
        )
    if engine == "synthetic":
        return decision(
            scope,
            "nonconforming",
            False,
            "synthetic engines provide no conformance evidence",
        )
    blocked = backend_decision(scope, backend)
    if blocked:
        return blocked
    if scope == "artifact" and not case.get("artifacts"):
        return decision(
            scope,
            "unavailable",
            False,
            "artifact scope requires independently checked artifact bytes",
        )
    return decision(scope, "host-model", True)
