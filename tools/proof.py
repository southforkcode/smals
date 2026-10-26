"""Collect bounded command evidence from explicit increment manifests."""

from dataclasses import dataclass, replace
import hashlib
import json
import logging
from pathlib import Path
import re
import subprocess
import sys
import time

LOGGER = logging.getLogger(__name__)


@dataclass
class ProofRequest:
    """Explicit inputs for one bounded proof collection."""

    root: Path
    increment: str
    out: Path
    cmake: str
    seed: int = 0
    work_timing: Path | None = None


def digest(path: Path) -> str:
    """Hash exact file bytes."""
    LOGGER.debug("Entering digest: %s", path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path):
    """Translate external JSON/filesystem errors into a diagnostic value."""
    LOGGER.debug("Entering read_json: %s", path)
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, ValueError) as error:
        LOGGER.error("Cannot read JSON %s: %s", path, error)
        return None, str(error)


def manifest_errors(data, increment):
    """Reject malformed, empty, unbounded or ambiguous registrations."""
    LOGGER.debug("Entering manifest_errors")
    required = {"schema", "increment", "targets", "build_dir", "inputs", "cases"}
    if (
        not isinstance(data, dict)
        or not required <= data.keys()
        or data.keys() - required
    ):
        return ["manifest fields must match the closed schema"]
    if data["schema"] != "smals.increment.v1" or data["increment"] != increment:
        return ["manifest version/increment mismatch"]
    if not all(
        isinstance(data[key], list) and data[key]
        for key in ("targets", "inputs", "cases")
    ):
        return ["targets, inputs and case selection must be nonempty"]
    if (
        not isinstance(data["build_dir"], str)
        or Path(data["build_dir"]).is_absolute()
        or ".." in Path(data["build_dir"]).parts
    ):
        return ["build directory must be relative to the project"]
    if not all(
        isinstance(item, str) and item
        for key in ("targets", "inputs")
        for item in data[key]
    ):
        return ["target/input names must be nonempty strings"]
    identifiers = [case.get("id") for case in data["cases"] if isinstance(case, dict)]
    errors = [error for case in data["cases"] for error in case_errors(case)]
    if len(identifiers) != len(set(str(item) for item in identifiers)):
        errors.append("case IDs must be unique")
    return errors


def case_errors(case):
    """Validate one case's identity, invocation and execution bounds."""
    LOGGER.debug("Entering case_errors")
    allowed = {
        "id",
        "argv",
        "timeout_seconds",
        "expected_exit",
        "stdout_contains",
        "stderr_contains",
        "artifacts",
        "backend",
        "kind",
    }
    if (
        not isinstance(case, dict)
        or not {"id", "argv", "timeout_seconds", "expected_exit"} <= case.keys()
        or case.keys() - allowed
    ):
        return ["case fields must match the closed schema"]
    if not isinstance(case["id"], str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9_.-]*", case["id"]
    ):
        return ["case ID must be a safe name"]
    if (
        not isinstance(case["argv"], list)
        or not case["argv"]
        or not all(isinstance(arg, str) for arg in case["argv"])
    ):
        return ["case argv must be nonempty"]
    if (
        not isinstance(case["timeout_seconds"], (int, float))
        or isinstance(case["timeout_seconds"], bool)
        or not 0 < case["timeout_seconds"] <= 120
        or not isinstance(case["expected_exit"], int)
        or isinstance(case["expected_exit"], bool)
    ):
        return ["case status/timeout must be bounded"]
    return expectation_errors(case)


def expectation_errors(case):
    """Require independent output expectations and a declared backend."""
    LOGGER.debug("Entering expectation_errors")
    if case.get("backend", "host") not in ("host", "unavailable") or case.get(
        "kind", "positive"
    ) not in ("positive", "negative", "boundary"):
        return ["unavailable backend: no adapter is registered"]
    for key in ("stdout_contains", "stderr_contains"):
        if not isinstance(case.get(key, []), list) or not all(
            isinstance(item, str) and item for item in case.get(key, [])
        ):
            return ["output expectations must be nonempty strings"]
    artifacts = case.get("artifacts", [])
    if not isinstance(artifacts, list) or not all(
        isinstance(item, dict)
        and set(item) == {"path", "sha256"}
        and isinstance(item["path"], str)
        and isinstance(item["sha256"], str)
        and re.fullmatch(r"[0-9a-f]{64}", item["sha256"])
        for item in artifacts
    ):
        return ["artifacts require relative paths and exact SHA-256 expectations"]
    if (
        not case.get("stdout_contains")
        and not case.get("stderr_contains")
        and not artifacts
    ):
        return ["each case needs an independent output or artifact expectation"]
    return []


def execute(root, argv, timeout):
    """Translate process status, OS failure and timeout into observation data."""
    LOGGER.debug("Entering execute: %s", argv)
    started = time.monotonic()
    data = {"argv": argv, "cwd": str(root), "timed_out": False}
    try:
        result = subprocess.run(
            argv,
            cwd=root,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        data.update(
            exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr
        )
    except subprocess.TimeoutExpired as error:
        data.update(
            timed_out=True,
            exit_code=None,
            stdout=error.stdout or "",
            stderr=error.stderr or "",
        )
    except OSError as error:
        LOGGER.error("Cannot execute %s: %s", argv[0], error)
        data.update(exit_code=None, stdout="", stderr=str(error))
    data["elapsed_seconds"] = time.monotonic() - started
    return data


def capture(root, out, name, argv, timeout):
    """Persist exact output and a hashed command record."""
    LOGGER.debug("Entering capture: %s", name)
    record = execute(root, argv, timeout)
    for stream in ("stdout", "stderr"):
        path = out / f"{name}.{stream}"
        value = record[stream]
        path.write_text(
            (
                value.decode("utf-8", errors="replace")
                if isinstance(value, bytes)
                else value
            ),
            encoding="utf-8",
        )
        record[stream] = {"path": path.name, "sha256": digest(path)}
    path = out / f"{name}.json"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return {**record, "record": {"path": path.name, "sha256": digest(path)}}


def capture_errors(out, record):
    """Require intact command JSON and both streams at finalization/audit."""
    LOGGER.debug("Entering capture_errors")
    errors = []
    for key in ("record", "stdout", "stderr"):
        metadata = record.get(key)
        if not isinstance(metadata, dict) or set(metadata) != {"path", "sha256"}:
            errors.append(f"malformed {key} metadata")
            continue
        path = (out / metadata["path"]).resolve()
        if (
            not path.is_relative_to(out.resolve())
            or not path.is_file()
            or digest(path) != metadata["sha256"]
        ):
            errors.append(f"missing or changed {key} evidence")
    return errors


def evaluate_case(root, out, case, record):
    """Derive acceptance from actual status/log bytes and independent expectations."""
    LOGGER.debug("Entering evaluate_case: %s", case["id"])
    errors = []
    if record["timed_out"] or record["exit_code"] != case["expected_exit"]:
        errors.append("case timed out or returned an unexpected exit status")
    for stream in ("stdout", "stderr"):
        path = out / record[stream]["path"]
        if not path.is_file() or digest(path) != record[stream]["sha256"]:
            errors.append(f"missing or changed {stream} log")
            continue
        content = path.read_text(encoding="utf-8")
        if not all(value in content for value in case.get(f"{stream}_contains", [])):
            errors.append(f"{stream} does not contain required output")
    artifacts = {}
    for item in case.get("artifacts", []):
        path = (root / item["path"]).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            errors.append("missing artifact or path outside project")
        else:
            artifacts[item["path"]] = digest(path)
            if artifacts[item["path"]] != item["sha256"]:
                errors.append("artifact digest differs from independent expectation")
    return errors, artifacts


def expand_argv(case, root, build, seed):
    """Replace only explicit proof tokens, preserving all other literal text."""
    LOGGER.debug("Entering expand_argv")
    tokens = {
        "{root}": str(root),
        "{build}": str(build),
        "{python}": sys.executable,
        "{seed}": str(seed),
    }
    argv = []
    for value in case["argv"]:
        for token, replacement in tokens.items():
            value = value.replace(token, replacement)
        argv.append(value)
    return argv


def input_hashes(root, patterns):
    """Hash the declared transitive inputs, refusing paths outside the workspace."""
    LOGGER.debug("Entering input_hashes")
    hashes = {}
    for pattern in patterns:
        if Path(pattern).is_absolute() or ".." in Path(pattern).parts:
            return {}, "input path escapes project"
        for path in sorted(root.glob(pattern)):
            if path.is_file():
                resolved = path.resolve()
                if not resolved.is_relative_to(root):
                    return {}, "input symlink escapes project"
                hashes[str(path.relative_to(root))] = digest(path)
    return hashes, None if hashes else "no declared source inputs exist"


def input_metadata(request, manifest, receipt):
    """Bind source/spec/work inputs without deriving work time from commands."""
    LOGGER.debug("Entering input_metadata")
    root = request.root
    receipt["source_hashes"], error = input_hashes(root, manifest["inputs"])
    if error:
        return [error]
    receipt["spec_hashes"] = {
        str(path.relative_to(root)): digest(path)
        for path in sorted((root / "specs").glob("[0-9][0-9][0-9][0-9]_*.md"))
    }
    if request.work_timing:
        receipt["work_timing"], error = read_json(request.work_timing)
        if error:
            return [error]
    return []


def git_metadata(request, receipt):
    """Capture committed revision/tree identity separately from input hashes."""
    LOGGER.debug("Entering git_metadata")
    root, out = request.root, request.out
    for name, argv in (
        ("revision", ["git", "rev-parse", "HEAD"]),
        ("tree", ["git", "rev-parse", "HEAD^{tree}"]),
    ):
        record = capture(root, out, name, argv, 10)
        receipt["commands"].append(record)
        if record["exit_code"] != 0:
            return [f"cannot identify git {name}"]
        receipt[name] = (
            (out / record["stdout"]["path"]).read_text(encoding="utf-8").strip()
        )
    return []


def selected_tools(build, cmake):
    """Read actual configured tool paths for collection and independent audit."""
    LOGGER.debug("Entering selected_tools")
    tools = {"cmake": cmake, "python": sys.executable}
    cache = build / "CMakeCache.txt"
    if cache.exists():
        for line in cache.read_text(encoding="utf-8").splitlines():
            if re.match(
                r"(CMAKE_CXX_COMPILER|SMIL_CLANG_FORMAT|SMIL_CLANG_TIDY|SMIL_UV):", line
            ):
                tools[line.split(":", 1)[0]] = line.split("=", 1)[1]
    return tools


def tool_metadata(request, manifest, receipt):
    """Record selected compiler/format/lint/interpreter tool identities."""
    LOGGER.debug("Entering tool_metadata")
    root, out, cmake = request.root, request.out, request.cmake
    build = (root / manifest["build_dir"]).resolve()
    tools = selected_tools(build, cmake)
    receipt["tools"] = {}
    for name, executable in tools.items():
        path = Path(executable).resolve() if executable else Path("/unavailable")
        if not path.is_file():
            return [f"tool unavailable: {name}"]
        record = capture(root, out, f"tool-{name}", [str(path), "--version"], 10)
        receipt["commands"].append(record)
        if record["exit_code"] != 0:
            return [f"tool version failed: {name}"]
        receipt["tools"][name] = {
            "path": str(path),
            "sha256": digest(path),
            "version": (out / record["stdout"]["path"]).read_text(encoding="utf-8")
            + (out / record["stderr"]["path"]).read_text(encoding="utf-8"),
        }
    return []


def run_cases(request, manifest, receipt):
    """Build declared targets and evaluate each registered case."""
    LOGGER.debug("Entering run_cases")
    root, out, cmake, seed = request.root, request.out, request.cmake, request.seed
    build = (root / manifest["build_dir"]).resolve()
    errors = []
    record = capture(
        root,
        out,
        "build",
        [
            str(Path(cmake).resolve()),
            "--build",
            str(build),
            "--target",
            *manifest["targets"],
        ],
        120,
    )
    receipt["commands"].append(record)
    if record["timed_out"] or record["exit_code"] != 0:
        return ["declared build target failed or timed out"]
    for index, case in enumerate(manifest["cases"]):
        if case.get("backend", "host") == "unavailable":
            receipt["cases"].append({"id": case["id"], "unavailable": True})
            errors.append(f"backend unavailable for {case['id']}")
            continue
        record = capture(
            root,
            out,
            f"case-{index}",
            expand_argv(case, root, build, seed),
            case["timeout_seconds"],
        )
        observed_errors, artifacts = evaluate_case(root, out, case, record)
        receipt["cases"].append(
            {
                **record,
                "id": case["id"],
                "artifacts": artifacts,
                "errors": observed_errors,
            }
        )
        errors.extend(f"{case['id']}: {item}" for item in observed_errors)
    return errors


def collect(request, receipt):
    """Collect a closed registration through explicit boundary checks."""
    LOGGER.debug("Entering collect: %s", request.increment)
    path = request.root / "plans/verification/increments" / f"{request.increment}.json"
    manifest, error = read_json(path)
    if error:
        return [error]
    errors = manifest_errors(manifest, request.increment)
    if errors:
        return errors
    receipt.update(
        manifest_path=str(path.relative_to(request.root)),
        manifest_sha256=digest(path),
        targets=manifest["targets"],
        seed=request.seed,
    )
    errors = input_metadata(request, manifest, receipt)
    if errors:
        return errors
    errors = git_metadata(request, receipt)
    if errors:
        return errors
    errors = tool_metadata(request, manifest, receipt)
    if errors:
        return errors
    return run_cases(request, manifest, receipt)


def run_proof(request: ProofRequest):
    """Write a failed or passed receipt; never reuse a nonempty output directory."""
    LOGGER.debug("Entering run_proof: %s", request.increment)
    request = replace(request, root=request.root.resolve(), out=request.out.resolve())
    out, increment = request.out, request.increment
    receipt = {
        "schema": "smals.proof.v1",
        "increment": increment,
        "passed": False,
        "errors": [],
        "commands": [],
        "cases": [],
        "work_timing": None,
    }
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", increment):
        receipt["errors"] = ["invalid increment identifier"]
        return receipt
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        receipt["errors"] = ["output directory must be fresh and empty"]
        return receipt
    try:
        out.mkdir(parents=True, exist_ok=True)
        receipt["errors"] = collect(request, receipt)
        for record in [*receipt["commands"], *receipt["cases"]]:
            if not record.get("unavailable"):
                receipt["errors"].extend(capture_errors(out, record))
        receipt["passed"] = not receipt["errors"]
        (out / "receipt.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
        )
    except (OSError, ValueError, TypeError) as error:
        LOGGER.error("Proof collection failed: %s", error)
        receipt["errors"].append(str(error))
        receipt["passed"] = False
    return receipt
