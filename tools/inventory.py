"""Seed exact requirement authorities without awarding behavioral verification."""

import hashlib
import json
import logging
from pathlib import Path
import re

from tools.audit import audit_requirement, scope_authority
from tools.proof import digest, read_json

LOGGER = logging.getLogger(__name__)


def authority_catalog(root):
    """Read exact table cells and reject duplicate normative keys."""
    LOGGER.debug("Entering authority_catalog")
    entries, errors = {}, []
    for path in sorted((root / "specs").glob("[0-9][0-9][0-9][0-9]_*.md")):
        for match in re.finditer(
            r"^\| ([A-Z][A-Z0-9]*-\d{3}) \| (.*?) \|$",
            path.read_text(encoding="utf-8"),
            re.M,
        ):
            key, text = match.groups()
            if key in entries:
                errors.append(f"duplicate normative requirement: {key}")
            scopes = scope_authority(root, key)
            if not scopes:
                errors.append(f"missing minimum scope authority: {key}")
            entries[key] = {
                "schema": "smals.requirement.v1",
                "key": key,
                "spec_path": str(path.relative_to(root)),
                "spec_sha256": digest(path),
                "text": text,
                "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "required_scopes": scopes,
            }
    return entries, errors


def initial_entry(authority):
    """Preserve every normative word in conservative unreviewed obligations."""
    LOGGER.debug("Entering initial_entry: %s", authority["key"])
    groups = re.split(r"(?<=\.)\s+(?=[A-Z`])|;\s+", authority["text"])
    return {
        **authority,
        "state": "open",
        "reviewed": False,
        "clause_basis": "Conservative sentence/semicolon seed groups; "
        "semantic clause review required before closure.",
        "obligations": [
            {
                "id": f"clause.{index + 1}",
                "text": text,
                "scopes": authority["required_scopes"],
                "evidence": [],
            }
            for index, text in enumerate(groups)
        ],
    }


def case_link_errors(root, link):
    """Reject orphan increment/case mappings without requiring pending receipts."""
    LOGGER.debug("Entering case_link_errors")
    if (
        not isinstance(link, dict)
        or not {"increment", "case_id", "scope", "kind", "receipt"} <= link.keys()
    ):
        return ["malformed obligation case link"]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", link["increment"]):
        return ["unsafe increment link"]
    manifest, error = read_json(
        root / "plans/verification/increments" / f"{link['increment']}.json"
    )
    if (
        error
        or not isinstance(manifest, dict)
        or manifest.get("increment") != link["increment"]
        or not any(
            case.get("id") == link["case_id"] for case in manifest.get("cases", [])
        )
    ):
        return ["orphan increment/case mapping"]
    return []


def obligation_errors(root, entry):
    """Check complete text/scope representation and all declared case links."""
    LOGGER.debug("Entering obligation_errors")
    obligations = entry.get("obligations")
    if not isinstance(obligations, list) or not obligations:
        return ["missing obligation inventory"]
    errors, remaining, identifiers, scopes = [], entry["text"], set(), set()
    for item in obligations:
        if (
            not isinstance(item, dict)
            or not {"id", "text", "scopes", "evidence"} <= item.keys()
            or not item["text"]
            or item["text"] not in entry["text"]
            or not item["scopes"]
        ):
            errors.append("malformed clause obligation")
            continue
        if item["id"] in identifiers:
            errors.append("duplicate clause ID")
        identifiers.add(item["id"])
        scopes.update(item["scopes"])
        remaining = remaining.replace(item["text"], "", 1)
        for link in item["evidence"]:
            errors.extend(case_link_errors(root, link))
    if remaining.strip(" \t\n.;") or not set(entry["required_scopes"]) <= scopes:
        errors.append("obligation inventory omits authority text or scopes")
    return errors


def entry_errors(root, authority, entry):
    """Keep authority fields exact and verification explicitly supported."""
    LOGGER.debug("Entering entry_errors")
    if not isinstance(entry, dict) or any(
        entry.get(key) != value for key, value in authority.items()
    ):
        return ["requirement authority text/digest/scopes changed"]
    if entry.get("state") not in ("open", "partial", "verified") or not isinstance(
        entry.get("reviewed"), bool
    ):
        return ["invalid requirement state/review marker"]
    errors = obligation_errors(root, entry)
    if entry["state"] == "verified":
        errors.extend(audit_requirement(root, entry["key"], replay_case=False))
    return errors


def seed_inventory(root: Path, expected_count=435):
    """Create absent seeds; preserve existing evidence byte-for-byte."""
    LOGGER.debug("Entering seed_inventory")
    root = root.resolve()
    try:
        entries, errors = authority_catalog(root)
        if len(entries) != expected_count:
            errors.append(
                f"expected {expected_count} authorities, found {len(entries)}"
            )
        if errors:
            return errors
        directory = root / "plans/verification/requirements"
        directory.mkdir(parents=True, exist_ok=True)
        for key, authority in entries.items():
            path = directory / f"{key}.json"
            if path.exists():
                entry, error = read_json(path)
                errors.extend(
                    [error] if error else entry_errors(root, authority, entry)
                )
            else:
                path.write_text(
                    json.dumps(initial_entry(authority), ensure_ascii=False, indent=2)
                    + "\n",
                    encoding="utf-8",
                )
        return errors
    except (OSError, ValueError, TypeError, KeyError) as error:
        return [f"inventory seed failed: {error}"]


def audit_inventory(root: Path, expected_count=435):
    """Return observed inventory counts and errors, never verification credit."""
    LOGGER.debug("Entering audit_inventory")
    root = root.resolve()
    summary = {"total": 0, "open": 0, "verified": 0}
    try:
        entries, errors = authority_catalog(root)
        paths = {
            path.stem: path
            for path in (root / "plans/verification/requirements").glob("*.json")
        }
        summary["total"] = len(paths)
        if len(entries) != expected_count or paths.keys() != entries.keys():
            errors.append("missing/extra requirement keys or orphan manifests")
        for key in sorted(paths.keys() & entries.keys()):
            entry, error = read_json(paths[key])
            if error:
                errors.append(error)
                continue
            invalid = entry_errors(root, entries[key], entry)
            errors.extend(f"{key}: {error}" for error in invalid)
            summary["open"] += entry.get("state") == "open"
            summary["verified"] += entry.get("state") == "verified" and not invalid
        return summary, errors
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        return summary, [f"inventory audit failed: {error}"]
