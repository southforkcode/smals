"""Read-only verification of proof observations and clause evidence."""

from datetime import datetime
import hashlib
import logging
from pathlib import Path
import re
import subprocess
import tempfile

from tools.evidence_policy import assess_case
from tools.selection import select_cases
from tools.proof import (
    capture,
    capture_errors,
    digest,
    evaluate_case,
    expand_argv,
    input_hashes,
    manifest_errors,
    read_json,
    selected_tools,
)

LOGGER = logging.getLogger(__name__)


def work_bounds_errors(work):
    """Check copied UTC bounds independently of work-duration annotations."""
    LOGGER.debug("Entering work_bounds_errors")
    if not isinstance(work, dict) or not isinstance(work.get("started_at_utc"), str):
        return ["missing work start timestamp"]
    try:
        if not work["started_at_utc"].endswith("Z") or (
            work.get("ended_at_utc") is not None
            and not work["ended_at_utc"].endswith("Z")
        ):
            return ["work timestamps must be UTC Z timestamps"]
        start = datetime.fromisoformat(work["started_at_utc"])
        if work.get("ended_at_utc") is None:
            return (
                ["completed work is missing its end timestamp"]
                if work.get("outcome") == "completed"
                else []
            )
        elapsed = (datetime.fromisoformat(work["ended_at_utc"]) - start).total_seconds()
        return (
            ["work end/elapsed does not match ordered UTC bounds"]
            if elapsed < 0 or elapsed != work.get("elapsed_seconds")
            else []
        )
    except (ValueError, TypeError, AttributeError) as error:
        return [f"invalid work timestamp: {error}"]


def timing_errors(work):
    """Never infer active/waiting work from elapsed wall time."""
    LOGGER.debug("Entering timing_errors")
    errors = work_bounds_errors(work)
    if errors:
        return errors
    for key in ("active_seconds", "waiting_seconds"):
        value = work.get(key, "unknown")
        if value != "unknown" and (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or value < 0
            or not work.get("measurement_basis")
        ):
            errors.append(
                "measured active/waiting work needs a nonnegative value and basis"
            )
    return errors


def command_errors(out, record):
    """Bind receipt fields to hashed raw command records and streams."""
    LOGGER.debug("Entering command_errors")
    errors = capture_errors(out, record)
    if errors:
        return errors
    stored, error = read_json(out / record["record"]["path"])
    if error:
        return [error]
    if (
        any(stored.get(key) != record.get(key) for key in stored)
        or not {
            "argv",
            "cwd",
            "exit_code",
            "timed_out",
            "elapsed_seconds",
            "stdout",
            "stderr",
        }
        == stored.keys()
    ):
        return ["command observation differs from hashed command JSON"]
    if (
        not isinstance(stored["elapsed_seconds"], (int, float))
        or stored["elapsed_seconds"] < 0
    ):
        return ["invalid command duration"]
    return []


def dependency_errors(root, manifest, receipt):
    """Recompute transitive source/spec/tool and committed baseline identity."""
    LOGGER.debug("Entering dependency_errors")
    sources, error = input_hashes(root, manifest["inputs"])
    errors = [error] if error else []
    if sources != receipt["source_hashes"]:
        errors.append("stale or changed source dependencies")
    specs = {
        str(path.relative_to(root)): digest(path)
        for path in sorted((root / "specs").glob("[0-9][0-9][0-9][0-9]_*.md"))
    }
    if specs != receipt["spec_hashes"]:
        errors.append("stale or changed specification dependencies")
    revision = receipt["revision"]
    if not isinstance(revision, str) or not re.fullmatch(
        r"[0-9a-f]{40}(?:[0-9a-f]{24})?", revision
    ):
        errors.append("invalid revision identity")
    else:
        tree = subprocess.run(
            ["git", "rev-parse", "--verify", f"{revision}^{{tree}}"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", revision, "HEAD"],
            cwd=root,
            capture_output=True,
            check=False,
        )
        if (
            tree.returncode
            or ancestry.returncode
            or tree.stdout.strip() != receipt["tree"]
        ):
            errors.append("revision/tree does not identify the recorded ancestor")
    tools = selected_tools(
        root / manifest["build_dir"], receipt["tools"]["cmake"]["path"]
    )
    if tools.keys() != receipt["tools"].keys():
        errors.append("configured tool selection differs from receipt")
    for name, executable in tools.items():
        path = Path(executable).resolve()
        entry = receipt["tools"].get(name, {})
        if (
            not path.is_file()
            or entry.get("path") != str(path)
            or entry.get("sha256") != digest(path)
        ):
            errors.append(f"changed or unavailable tool: {name}")
    return errors


def observation_errors(root, out, manifest, receipt):
    """Re-evaluate commands and declared case expectations, ignoring summary flags."""
    LOGGER.debug("Entering observation_errors")
    errors = []
    commands = receipt["commands"]
    for record in commands:
        errors.extend(command_errors(out, record))
        if (
            record["exit_code"] != 0
            or record["timed_out"]
            or record["cwd"] != str(root)
        ):
            errors.append("required metadata/build command failed or has wrong cwd")
    if errors:
        return errors
    by_name = {record["record"]["path"]: record for record in commands}
    for key in ("revision", "tree"):
        record = by_name.get(f"{key}.json")
        if (
            not record
            or (out / record["stdout"]["path"]).read_text(encoding="utf-8").strip()
            != receipt[key]
        ):
            errors.append(f"unbound {key} command observation")
    for name, tool in receipt["tools"].items():
        record = by_name.get(f"tool-{name}.json")
        if not record or record["argv"] != [tool["path"], "--version"]:
            errors.append(f"unbound tool observation: {name}")
        elif tool["version"] != (out / record["stdout"]["path"]).read_text(
            encoding="utf-8"
        ) + (out / record["stderr"]["path"]).read_text(encoding="utf-8"):
            errors.append(f"tool version differs from observation: {name}")
    build = (root / manifest["build_dir"]).resolve()
    expected_build = [
        receipt["tools"]["cmake"]["path"],
        "--build",
        str(build),
        "--target",
        *manifest["targets"],
    ]
    if not by_name.get("build.json") or by_name["build.json"]["argv"] != expected_build:
        errors.append("build did not select the declared targets")
    return [*errors, *case_observation_errors(root, out, manifest, receipt)]


def case_observation_errors(root, out, manifest, receipt):
    """Validate all selected case identities and independently expected effects."""
    LOGGER.debug("Entering case_observation_errors")
    errors = []
    build = (root / manifest["build_dir"]).resolve()
    if [item.get("id") for item in receipt["cases"]] != [
        item["id"] for item in manifest["cases"]
    ]:
        return [*errors, "missing, extra or reordered registered cases"]
    for case, record in zip(manifest["cases"], receipt["cases"]):
        classification = assess_case(case)
        if not classification["available"] or record.get("unavailable"):
            errors.append("unavailable backend is not passing evidence")
            continue
        if any(record.get(key) != value for key, value in classification.items()):
            errors.append(
                "evidence scope/classification differs from actual capability"
            )
        errors.extend(command_errors(out, record))
        if record["argv"] != expand_argv(case, root, build, receipt["seed"]) or record[
            "cwd"
        ] != str(root):
            errors.append("case argv/cwd differs from registration")
        observed, artifacts = evaluate_case(root, out, case, record)
        errors.extend(observed)
        if artifacts != record["artifacts"]:
            errors.append("artifact observations differ from receipt")
    return errors


def receipt_registration(root, increment, receipt):
    """Validate registration identity once before auditing dependent observations."""
    LOGGER.debug("Entering receipt_registration")
    manifest_path = root / "plans/verification/increments" / f"{increment}.json"
    manifest, error = read_json(manifest_path)
    if error:
        return None, [error]
    errors = manifest_errors(manifest, increment)
    if errors:
        return None, errors
    if (
        receipt["schema"] != "smals.proof.v1"
        or receipt["increment"] != increment
        or receipt["manifest_path"] != str(manifest_path.relative_to(root))
        or receipt["manifest_sha256"] != digest(manifest_path)
        or receipt["targets"] != manifest["targets"]
    ):
        return None, ["receipt manifest/target identity mismatch"]
    selected, errors = select_cases(
        manifest,
        receipt["selection"]["case_set"],
        receipt["selection"]["shard"],
        receipt["budget_seconds"],
    )
    if errors:
        return None, errors
    return {**manifest, "cases": selected}, []


def audit_receipt(root, increment, out):
    """Return diagnostics; malformed external metadata cannot become a pass."""
    LOGGER.debug("Entering audit_receipt: %s", increment)
    root, out = root.resolve(), out.resolve()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", increment):
        return ["invalid increment identifier"]
    receipt, error = read_json(out / "receipt.json")
    if error:
        return [error]
    try:
        manifest, errors = receipt_registration(root, increment, receipt)
        if not errors:
            errors.extend(timing_errors(receipt["work_timing"]))
            if not 0 <= receipt["proof_elapsed_seconds"] <= receipt["budget_seconds"]:
                errors.append("proof runtime exceeds the selected bound")
            errors.extend(dependency_errors(root, manifest, receipt))
            errors.extend(observation_errors(root, out, manifest, receipt))
        return errors
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as failure:
        LOGGER.error("Malformed receipt metadata: %s", failure)
        return [f"malformed receipt metadata: {failure}"]


def requirement_text(root, key, spec_path):
    """Bind exact text to its unique effective numbered specification file."""
    LOGGER.debug("Entering requirement_text: %s", key)
    declared = (root / spec_path).resolve()
    matches = []
    for path in sorted((root / "specs").glob("[0-9][0-9][0-9][0-9]_*.md")):
        match = re.search(
            rf"^\| {re.escape(key)} \| (.*?) \|$",
            path.read_text(encoding="utf-8"),
            re.M,
        )
        if match:
            matches.append((path.resolve(), match[1]))
    return matches[0][1] if len(matches) == 1 and matches[0][0] == declared else None


def scope_authority(root, key):
    """Read minimum scopes independently from the central traceability matrix."""
    LOGGER.debug("Entering scope_authority: %s", key)
    path = root / "plans/11_requirement_matrix.md"
    if not path.exists():
        return None
    match = re.search(
        rf"^\| \[{re.escape(key)}\]\([^)]*\) \| [^|]* \| ([^|]+) \|",
        path.read_text(encoding="utf-8"),
        re.M,
    )
    names = {"S": "source", "H": "host", "A": "artifact", "N": "exact-profile"}
    return [names[item.strip()] for item in match[1].split("/")] if match else []


def audit_obligations(root, requirement):
    """Require reviewed clause coverage, actual case identities and explicit scopes."""
    LOGGER.debug("Entering audit_obligations")
    errors, replay = [], None
    obligations = requirement["obligations"]
    if (
        not requirement.get("reviewed")
        or not obligations
        or len({item["id"] for item in obligations}) != len(obligations)
    ):
        return [
            "clause inventory must be nonempty, unique and explicitly reviewed"
        ], None
    for item in obligations:
        if (
            not item["text"]
            or item["text"] not in requirement["text"]
            or not item["scopes"]
        ):
            errors.append("missing clause text or required scope")
        links = item["evidence"]
        for scope in item["scopes"]:
            if not any(link["scope"] == scope for link in links):
                errors.append(f"missing clause scope: {scope}")
        if not {"positive", "negative"} <= {link["kind"] for link in links}:
            errors.append("clause requires positive and negative evidence")
        for link in links:
            linked_errors, linked_replay = audit_link(root, link)
            errors.extend(linked_errors)
            replay = replay or linked_replay
    remainder = requirement["text"]
    for item in obligations:
        remainder = remainder.replace(item["text"], "", 1)
    if remainder.strip(" \t\n.;"):
        errors.append("clause inventory omits authoritative requirement text")
    if not set(requirement["required_scopes"]) <= {
        scope for item in obligations for scope in item["scopes"]
    }:
        errors.append("required requirement scopes omitted by clause inventory")
    return errors, replay


def audit_link(root, link):
    """Bind one obligation link to an intact receipt and supported case scope."""
    LOGGER.debug("Entering audit_link")
    errors = []
    out = (root / link["receipt"]).resolve().parent
    if not out.is_relative_to(root):
        errors.append("receipt link escapes project")
        return errors, None
    errors.extend(audit_receipt(root, link["increment"], out))
    receipt, failure = read_json(out / "receipt.json")
    if failure:
        return errors, None
    manifest, failure = read_json(root / receipt["manifest_path"])
    cases = (
        []
        if failure
        else [
            case
            for case in manifest["cases"]
            if case["id"] == link["case_id"]
            and case["id"] in {item["id"] for item in receipt["cases"]}
        ]
    )
    if (
        not cases
        or link["case_id"] not in {item["id"] for item in receipt["cases"]}
        or link["kind"] != cases[0].get("kind", "positive")
        or not assess_case(cases[0])["available"]
        or link["scope"] != assess_case(cases[0])["scope"]
    ):
        errors.append(
            "missing case, mismatched case kind or unsupported evidence scope"
        )
    elif (
        timing_errors(receipt["work_timing"])
        or receipt["work_timing"].get("ended_at_utc") is None
    ):
        errors.append("closure requires completed development work bounds")
    else:
        return errors, (cases[0], manifest, receipt)
    return errors, None


def replay_observation(root, replay):
    """Retain a bounded replay's raw logs under ignored evidence storage."""
    LOGGER.debug("Entering replay_observation")
    case, manifest, receipt = replay
    output = root / "temp/evidence/closure"
    output.mkdir(parents=True, exist_ok=True)
    out = Path(tempfile.mkdtemp(dir=output))
    record = capture(
        root,
        out,
        "replay",
        expand_argv(case, root, root / manifest["build_dir"], receipt["seed"]),
        case["timeout_seconds"],
    )
    errors, _ = evaluate_case(root, out, case, record)
    return errors


def audit_requirement(root, key, replay_case=True):
    """Validate every explicit obligation and replay one small discriminating case."""
    LOGGER.debug("Entering audit_requirement: %s", key)
    root = root.resolve()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", key):
        return ["invalid requirement identifier"]
    requirement, error = read_json(
        root / "plans/verification/requirements" / f"{key}.json"
    )
    if error:
        return [error]
    try:
        text = requirement_text(root, key, requirement["spec_path"])
        if (
            requirement["schema"] != "smals.requirement.v1"
            or requirement["key"] != key
            or text != requirement["text"]
            or hashlib.sha256(text.encode()).hexdigest() != requirement["text_sha256"]
        ):
            return ["requirement authority text/digest mismatch"]
        scopes = scope_authority(root, key)
        if scopes is not None and scopes != requirement["required_scopes"]:
            return ["requirement scopes differ from minimum scope authority"]
        errors, replay = audit_obligations(root, requirement)
        if not errors and replay_case:
            errors.extend(replay_observation(root, replay))
        return errors
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as failure:
        return [f"malformed requirement evidence: {failure}"]
