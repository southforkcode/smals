# Increment Size, Execution Rules and Empirical Evidence

Source: [effective specifications](../specs/README.md); [baseline digests](13_specification_baseline.md). Prepared 2026-10-26. Planning standards applied: user value (PRIN-1), maintainability (PRIN-4), incremental delivery (PRIN-5), repository [STANDARDS](../STANDARDS.md) and [CODE_STANDARDS](../CODE_STANDARDS.md). No standards-manifest version exists in this checkout; none is invented.

## Starting state and intended implementation

The repository has 435 requirements in 15 numbered specifications, an empty CMakeLists.txt, no implementation under src/, and no tests beyond README placeholders. Existing build/ files are not evidence of an implemented compiler. plans/ was empty. The plan adds C++23 core code, Python3.13 scripts/oracles using uv, and formatting/lint acceptance gates. It does not implement a high-level language frontend, new language extensions, or an unrequested native platform ABI.

Core modules have explicit boundaries: source/AST -> resolved typed IR -> verification -> optional host execution -> target binding -> portable checked runtime/kernel lowering -> machine object -> static link -> validated image -> exact CPU execution. C++ errors are values. Use conventional CFG, dominator, SCC, dataflow and topological-order algorithms where specified. Start conservatively with stack-slot SSA and packet calls; correctness and visible checked effects precede optimization. A third-party dependency needs a recorded rationale, pin, provenance and placement under thirdparty/ before use. No dependency is selected here based on an unverified claim of present tool availability.

## Atomic increment rule

Every checkbox row is one work increment, targeted at **10 minutes of active agent work**, with a **hard stop at 15 minutes**. The estimate includes reading relevant code/specs, reasoning, editing, building, demonstration, test analysis and evidence capture. It is an estimate to calibrate empirically, not a guarantee about unknown tooling/CPU work. At execution time:

1. Spend at most2 minutes identifying the exact dependency receipts, files, one changed behavior and discriminating witness.
2. Spend approximately5–7 minutes implementing that behavior using already-completed primitives.
3. Reserve2–3 minutes for the bounded build/test/demo and approximately1 minute to record evidence and status.
4. At minute10, if green evidence cannot fit in the remaining budget, stop broadening the change. Record the smallest coherent partial result, leave the parent checkbox open, and create numbered child increments with their own <=10-minute estimate, dependencies, witnesses and evidence.
5. Stop at 15 minutes even if the task is not complete. Record actual active time and the cause; do not check it off, waive evidence, or hide additional work in another task's test run. Resume only as a newly bounded child. All uncompleted parent obligations remain visible.

A large family/phase/dependency group is not an increment. Rows saying “one record/form/opcode” prohibit implementing the rest of that family in the same slot. A successful schema/controller row does not complete its explicitly enumerated children. Any new source operation, instruction addressing form, guard, or contract decision discovered during execution gets a stable child ID (`<parent>.1`, `.2`, ...), a concrete witness and the same ceiling. If a slot's assumption is false, update dependent estimates and the requirement matrix before continuing its branch of work.

Tool installation, independent ISA/engine research and missing-contract resolution can have external prerequisites. Each acquisition/research attempt is bounded; record blocked state instead of waiting indefinitely or claiming implementation. Unattended jobs may be sharded into <=120-second verification slices; their execution counts as active work when the agent is occupied. A long clean build or emulator corpus is split into named receipt-bearing child shards. An unbounded task cannot become acceptable merely by launching a background process.

## Picking the next increment

For “do step N” requests, use the stable numbered sequence and central completion checklist in [PLAN.md](PLAN.md). Execute only the selected increment, update both checklists and its evidence reference on completion, and stop before the next step. The ready-work guidance below applies when no numbered step is specified or when the user explicitly selects independent work around a recorded blocker.

Start with **0.0 Create feature branch (B001)**. Then choose the first useful ready increment whose prerequisite receipts are valid. Source and host-model work can proceed while binary-authority gates are blocked. The planned first native qualification is i8080a (`N05`), followed by mc6800 (`N03`) to establish small little- and big-endian paths early. Later CPU/mode work follows family readiness; no speculative delegation/parallel agent work is assumed.

Each increment table supplies its prerequisites, bounded change, empirical pass condition and requirements advanced. [Dependency groups](12_dependency_groups.md) expand every ALL-* label into exact conjunctive IDs. The documents are workstreams, not a rule to complete every row of one file before opening the next. In particular I011/I012 precede I006, contract child slots precede their consuming integration, and native family K04 may be implemented before K01 if the first selected profile needs it. Dependencies, rather than file order, govern readiness.

## Increment definition of done

Follow the repository [agent development process](../AGENTS.md): use a separate feature branch per step, or a bug branch for a separately handled bug fix; record the work there; self-review; merge into `main`; verify the merged result; and safely delete the merged local branch. Human review is needed only for exceptional issues outside the authority of the specifications, plans, standards, and accepted engineering practice. Integration, post-merge checks, and cleanup are part of the increment budget, not unbounded follow-up work. Apply the agent process's build-host matrix to relevant changes: macOS primary, Linux x64 and ARM64 container execution, and explicitly untested Windows x64 compatibility.

An increment is complete only when its narrow implementation is present, relevant formatter/linter and meaningful branch checks pass, the table's demonstration matches expected values/effects/diagnostics, affected regression shards are green, its feature/bug branch is merged into `main`, the merged result is verified, its merged local branch is safely deleted, and its receipt is verifiable. Update both completion checklists only after those conditions hold. A plan document, TODO, named helper, generated schema, successful compilation, process exit0 or screenshot is insufficient evidence of a behavioral requirement by itself.

For code behavior, write the new cases first and observe failure for the intended behavioral reason before implementing the fix. At least one positive and one discriminating negative/boundary case should exercise the new behavior, unless the row documents why one is inapplicable. Tests compare independently expected values/bytes/traces or a justified independent oracle. They do not merely call the same production function twice or snapshot its unchecked output. Retain the initial failing observation and subsequent passing evidence. A targeted wrong-result/guard mutation is useful when validating the harness or when the ordinary test-first failure does not establish the needed discrimination; it is not extra mandatory work for every increment. Documentation-only changes use appropriate validation instead of artificial behavioral tests.

Project branch coverage is checked for the newly changed implementation unit. Exceptions require an explicit technical explanation; debug assertions do not replace tests. Do not run unrelated all-target suites for every small edit. Rerun the affected dependency cone, and broaden only for a change with broader consequences. Infrastructure-only increments do not automatically close any spec requirement.

## Planned commands and receipts

The following commands **do not exist yet**. B002–B013 implement and test them before later tasks depend on them. In the bootstrap rows, record direct configure/build/CTest/formatter command output first, then ingest it through the runner once available. Every subsequent table row implicitly uses:

```sh
uv run python scripts/prove.py --increment <ID> --out temp/evidence/<ID>/<attempt>
uv run python scripts/audit_evidence.py --increment <ID>
```

The proof runner resolves `plans/verification/increments/<ID>.json`, builds only declared relevant targets, executes the registered CTest/CLI/oracle/emulator cases, and checks all expected outputs. No shell wildcard or successful empty selection can count as a passing test. A row's future implementation paths are proposals, not links to files that already exist. Sample direct commands are:

```sh
cmake -S . -B build/smil
cmake --build build/smil --target smil_tests
ctest --test-dir build/smil --output-on-failure -L <increment-ID>
```

Each receipt records increment/attempt, feature/bug branch, work commits, integration commit on `main`, post-merge verification, base/revision and relevant transitive source hashes, spec and contract digests, tool versions/hashes, exact argv/environment/seed/shard, input fixture IDs/digests, expected and actual values/bytes/diagnostics/effect traces, command exit status, timing, generated artifact hashes, changed-unit coverage and prerequisite receipt references. Native receipts additionally retain exact target/mode, independent engine/ISA provenance, image/segment/map digests, register/SP/canary observations and monitor transaction trace. Failed/blocked/timed-out/skipped cases remain explicitly nonpassing.

Keep durable evidence summaries in plan documents, normally `plans/evidence/<ID>.md`, and process-only obligation/runner mappings under `plans/verification/`. Raw logs/images/traces/inventories go under ignored `temp/evidence/`. Keep domain fixture expectations in `test/`; do not put plan status, step IDs, branch/commit receipts, or evidence statements in source/test code or comments. Summarize actual observations in the durable plan record and reference temporary raw artifacts when useful. A temporary artifact's absence is not proof that a check passed; retain sufficient observations and commands to understand and reproduce the result. A hand-edited “passed” field is never authoritative.

## Requirement closure is separate from task completion

Every requirement has one explicit closure row `A-<KEY>` in [10](10_requirement_closure.md) and a mapping in [11](11_requirement_matrix.md). A completed implementation increment is advancement; a requirement is closed only after **every clause** is supported in its actual applicable layers. Test manifests link each clause to concrete positive/negative/boundary cases and their evidence receipts. A broad requirement spanning memory, calling convention and native behavior cannot close on a lexer test.

Scopes in the matrix are minimum review scopes: S=source/static verification; H=host interpreter or deterministic checked-event model; A=bound interfaces/objects/linker/loader/contracts; N=exact native profile receipts. Where a requirement has no meaningful behavior at a listed conservative scope, the closure audit records a clause-level applicability rationale rather than fabricating a passing test. N requires the 38 exact-profile qualification receipts for the reference catalog; shared-family evidence alone is insufficient. For general multi-agent rules, H includes the deterministic multi-agent model while N proves the specified reference profiles exclude additional agents. No unprovided multi-agent native profile is claimed.

The closure command is:

```sh
uv run python scripts/audit_evidence.py --requirement <KEY> --closure
```

It rejects missing clauses/tests/fixtures, empty selections, skipped applicable cases, stale dependency evidence and host-only substitutions for native proof. Each audit also replays one small discriminating case within 120 seconds. If full scope is not ready, record partial progress and keep the requirement open; if there is missing implementation, add child work with its own evidence. Audits themselves do not contain an unbounded implementation task.

## Staleness and changes

Use planned -> in_progress -> completed_with_evidence states for increments; blocked and split are separate noncomplete states. Requirement state is open -> partial -> verified and may return to open/partial when evidence becomes stale. Completion checkboxes link to a receipt ID; requirements link to closure receipts. A later commit does not invalidate unrelated evidence automatically: verify the exact transitive source/contract/tool/fixture dependency hashes, or rerun the affected shards. A changed runtime/compiler relevant to all targets invalidates all affected native receipts, which are rerun as their existing bounded qualification shards, not hidden inside a final audit.

Spec amendments and missing authority decisions remain visible with provenance/version consequences. The plan does not silently supply missing published bytes or authorize incompatible mutation of versioned contracts. A draft can advance review; affected binary conformance stays blocked until a normative contract is recovered or an explicit revised contract is adopted. Static diagnostics for unresolved contracts remain useful completed behavior.

## Concrete demonstrations of advancement

| Observable result | Gate and required evidence |
| --- | --- |
| Trustworthy red/green build evidence | B013: controlled failing fixture cannot pass, bounded green case has raw logs/hashes. |
| Complete source accepted/rejected precisely | V021 and S021: valid branching module verifies, malformed source and nondominating use fail in the right phase. |
| Executable checked language behavior | Y011: actual host run returns known values/status; negative variant preserves prior output and stops without later cleanup. |
| Reproducible separate compilation/linking | L021: two modules with pinned interfaces produce deterministic catalogs/segments across order permutations and both byte orders. |
| First real small-machine program | N05-04: emitted i8080a native image bootstraps and reports33 on independent engine through exact monitor protocol. |
| Big-endian native counterpart | N03-04: mc6800 image reports the same logical result with correct different storage encoding. |
| One completely qualified target | N05-16 (then N03-16): every bounded native shard and contract/engine receipt validates; only this target is advertised. |
| One completely satisfied requirement | Any A-<KEY>: clause evidence plus applicable layers, with no borrowed completion from task counts. |
| All specified reference targets and requirements | FIN001:435 verified requirement keys,38 qualified exact profiles, no stale/blocked obligations. |

These gates are demonstrations/aggregations, not extra unbounded coding increments. Their constituent work is explicitly decomposed in the linked workstreams.
