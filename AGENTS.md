# Agent Development Process

These instructions apply throughout this repository. Use a short, repeatable development loop and keep the amount of design, testing, and reporting proportional to the current increment.

## Project references

- [specs/README.md](specs/README.md): required behavior and contracts.
- [plans/PLAN.md](plans/PLAN.md): numbered execution order and central progress checklist.
- [plans/00_delivery_and_evidence.md](plans/00_delivery_and_evidence.md): increment limits, completion evidence, and requirement closure.
- [STANDARDS.md](STANDARDS.md) and [CODE_STANDARDS.md](CODE_STANDARDS.md): language, tooling, design, and code standards.

Specifications define what must hold; designs explain how it will hold; plans organize the work. Keep those responsibilities distinct. Read the relevant material and existing code before changing it. Preserve unrelated user work.

## Work one increment at a time

For “do step N,” resolve N in `plans/PLAN.md`, follow its link, and verify its prerequisites and evidence. Implement that increment and stop after reporting its result. Do not automatically start the next step.

Every step uses its own feature or bug branch and ends by merging its completed work into `main`. A tested change left on a branch is not a completed step. The initial branch-setup increment establishes this practice; it does not replace branch creation for subsequent steps.

Target a rolling ten-increment average below **five minutes elapsed per increment**, including analysis, implementation, validation, integration and bookkeeping. Preserve original plan estimates for comparison; this is the current execution target, not a rewrite of historical estimates. Spend about 30 seconds on scope/requirements, 2–3 minutes implementing, and reserve 1–2 minutes for checks and integration. Stop broadening at minute 3. At minute 5, either finish the bounded closeout or record the concrete remaining work and resume with a new attempt. Split material scope before coding when it cannot reasonably fit; use stable child IDs only for distinct deliverables, never paperwork-only timing repairs.

At 15 minutes stop new implementation. Correctness and required evidence remain gates: save incomplete work when they are missing. If implementation and required checks are already complete or a bounded verification is finishing, complete integration/cleanup, record the actual overrun and cause, and improve the next slice; do not reopen a verified merged increment solely because elapsed time exceeded the estimate. User-requested process work/interruptions get separate attempt notes. Do not infer active work from wall time or hide waits/overruns to meet the average. Never renumber existing integer steps or mark missing material obligations complete.

## Fast path and safety checkpoints

- Before changing code, name the changed behavior and smallest discriminating positive/negative cases. Reuse a current design; do not create another design or phase report when the existing one is sufficient.
- Run the changed-case set and affected dependency cone once after the final edit/refactor. Use registered case sets/CTest labels, cached build directories and qualified tools. Run required formatter/linter gates; broaden only for shared behavior, portability changes, failures or unresolved risk.
- After a conflict-free merge, compare implementation inputs and run one affected smoke/shard. Reuse the passing pre-merge regression/host evidence when its exact inputs/tools are unchanged. Rerun the full affected cone after a conflict or implementation change; never relabel stale evidence as current.
- Use one concise receipt/working note per increment. Automate branch/timing/hash/checklist mechanics where possible. Do not repeat raw logs or retell the process in several documents. Keep the required separate feature branch, merge, verification and safe local cleanup.
- Run a full safety checkpoint at each tenth completed **primary numbered step** (10, 20, 30, ...); children do not advance this cadence. Run one sooner for broad architecture/build changes or unresolved failures. The checkpoint runs the full applicable native test suite and all Python tool tests once, required quality/coverage gates, and the applicable supported Linux host matrix when relevant/available. Parallelize independent host checks with separate build/output directories. Windows remains explicitly untested unless actually executed.
- Reuse a recent full checkpoint only when its covered inputs/tools remain unchanged; otherwise run the due checkpoint. Record exact scope/results and its timing in the current receipt and central checkpoint log. A full checkpoint may take longer than an ordinary increment and still counts toward the rolling average. Preserve the safety signal rather than weakening tests to meet the target.

## Record development work timing

Measure the agent's work on the plan step, not the runtime or performance of the software being built. Capture a real UTC clock reading before requirements analysis or other work begins, and persist it in the step's plan evidence and the timing log in `plans/PLAN.md` as soon as the work branch is available. Capture the end when the attempt finishes or stops; a successful attempt includes analysis, design, test development, implementation, review, retesting, documentation, merge, post-merge verification, and branch cleanup. Write the final timing record with completion bookkeeping.

Use one record per attempt with step number, increment ID, attempt number, `started_at_utc`, `ended_at_utc`, `elapsed_seconds`, outcome, and evidence link. Use ISO 8601 UTC timestamps ending in `Z` and calculate elapsed seconds from those timestamps. An in-progress attempt has no end or elapsed value yet. Keep the step's original time estimate available for later plan analysis.

Record stopped, blocked, split, and unsuccessful attempts too. On resume, append another attempt instead of replacing the first start or counting a long inactive gap as continuous work. If pauses/waits or active-work duration are measured, record `waiting_seconds` and `active_seconds` separately with their measurement basis. Otherwise use `unknown`; never infer active compute time from elapsed wall time, tool durations, or commit timestamps. Explain material scope additions or interruptions briefly so later comparisons are interpretable.

Keep these timestamps and timing notes in plan documents, with raw clock observations under `temp/` if useful. Do not add software instrumentation, product metrics, timers in source/test code, or timing assertions to fulfill this process rule. For historical steps, backfill only supported observations and label their source and precision honestly; unknown times stay unknown.

## Branch and merge discipline

- Before each step, inspect the working tree and current branch. Preserve unrelated changes. Start from the current `main` and check out `feature/step-<N>-<short-description>`, or `bug/step-<N>-<short-description>` for a bug fix being handled separately from feature implementation. Use a unique suffix if a branch name already exists. If the step's purpose is to establish a different named feature branch, that branch satisfies this rule.
- Record the step's code, tests, design/architecture changes, other affected documentation, and immediate evidence on that branch in focused commits. Do not accumulate several numbered steps on one long-lived feature branch. Materially blocked or split work remains open; retain its branch and committed partial work. A measured time overrun alone does not invalidate fully verified behavior; record it rather than creating a bookkeeping-only child.
- After tests, simplicity review, and documentation pass, bring the branch up to date with `main`, resolve any conflicts without discarding other work, and rerun the affected checks. Merge it into `main` and verify the resulting state there. Reserve closeout time. If material implementation or required evidence cannot finish, record a bounded continuation and leave the step open; if only verified integration/bookkeeping remains, finish it and record the overrun under the fast-path policy.
- Record the feature/bug branch, work commit IDs, integration commit ID, and post-merge evidence. Update the central and detailed completion records only after the merge and verification succeed. Commit final status/evidence bookkeeping so completion is durable; that bookkeeping must not introduce untested implementation changes.
- After a successful merge and post-merge verification, switch to `main` and delete the merged local feature/bug branch with the safe merged-branch deletion command (`git branch -d <branch>`). Record cleanup in the completion evidence. Do not force-delete an unmerged branch or remove a blocked step's work. Clean up a remote branch only when the remote publication workflow is explicitly authorized; local branch cleanup does not imply pushing. A step remains open until required local branch cleanup succeeds.
- Proceed through ordinary commits, conflict resolution, self-review, and merging without requesting routine human review. Use the specifications, plans, project standards, and accepted engineering practices to make implementation decisions. Seek human input only for an exceptional issue that cannot be resolved within that authority, such as a material unresolved contract conflict or a necessary destructive action affecting unrelated work. Follow actual tool permission requirements when they apply. Merging locally does not itself request remote publication or pushing.

## Merge stories honor our predecessors

Put the engaging historical or positive story **only in the merge commit into `main`**. Keep feature/work commits, source comments, and completion-bookkeeping messages technical. Consolidate/squash the step's technical branch work into one focused implementation commit before integration when practical; keep final evidence bookkeeping separate when required. Preserve unrelated work and do not rewrite existing `main` history unless explicitly requested.

A merge story should prefer an important or overlooked moment in computer science that relates to the actual evidenced change. Credit the original people and collective work, retell the relevant idea accurately, and explain its connection to the integrated result. When there is no clear computer science connection, use a grounded human-history story about people working together for a shared good. Do not force a joke or invent a connection, quotation, priority claim, or historical detail. Verify uncertain facts.

Keep the merge message small: aim for three short paragraphs and never exceed eight for the whole message. Usually use one brief historical paragraph, one concrete change/why paragraph, and one validation/source paragraph. Every source used or referenced must pay homage to its original author or team: name and credit them when known, distinguish original work from later curators, and cite/link the work. If authorship is uncertain, say so. For collective repository material, credit project contributors and cite the governing document. We stand on the shoulders of giants; gratitude and technical explanation should both be specific.

Every commit still needs a descriptive technical explanation of what changed, why, and the resulting behavior or decision. Include relevant validation/limitations and material sources (requirement keys, specification paths, plans/designs, evidence receipts). A reader browsing `main` history should understand the integrated idea without the chat. A generic step number or branch name alone is insufficient; bookkeeping messages should explain which result they make durable.

## Development loop

1. **Analyze the requirements.** Identify the applicable specification keys, expected behavior, boundaries, failure conditions, and the increment's acceptance criteria. Check existing implementations and tests for reusable behavior. Resolve material ambiguity before claiming an implementation is correct.

2. **Create or update the design.** Before implementation, record the necessary approach, interfaces, data flow, invariants, and integration points in the relevant design or architecture document under `docs/`. Link to the governing requirements and summarize meaningful tradeoffs. Update architecture documentation when module boundaries, dependencies, representations, or shared contracts change. An existing concise section is sufficient; routine changes already covered by a current design do not need a new document. State when no design change is needed. When replacing an established design, preserve its prior revision and publish a complete replacement according to `CODE_STANDARDS.md`; maintain working links and the document index.

3. **Write the behavioral tests first.** For code behavior, add the smallest meaningful positive and negative/boundary cases before changing the implementation. Derive expected values, diagnostics, and effects from the requirements or an independent oracle. Run the new cases and observe failure for the intended behavioral reason. A missing tool, unselected test, or broken fixture is not that failure. For a regression, reproduce the bug first. For documentation-only or other changes without executable behavior, use appropriate structural, link, schema, or configuration validation instead of artificial unit tests.

4. **Implement until the tests pass.** Make the smallest coherent change satisfying those cases and the complete acceptance criteria. Reuse existing modules and follow project standards, including errors as values and required formatters/linters. Do not weaken requirements, remove necessary checks, or change expected results merely to accommodate the implementation. Add cases when implementation exposes an untested obligation.

5. **Review for simplicity and repetition.** Review the diff against the requirements and design. Remove unnecessary branches, indirection, dead code, and copied logic. Extract a small shared function or abstraction where repeated behavior has the same semantics and change together; give it a clear responsibility and test its callers. Do not introduce speculative frameworks or merge superficially similar code with different contracts. Check failure paths, lifetimes, resource accounting, and observable effects where relevant.

6. **Retest and fix.** After the final implementation/refactoring edit, run the new cases, affected regression tests, and required formatting/lint checks once; use the fast path above and the periodic full checkpoint cadence. Cover changed implementation branches as required by project standards. Broaden testing when shared behavior or unresolved failures justify it. Fix failures and repeat the loop within the timebox; a refactor is not finished until its affected behavior is retested. Record unavailable checks as missing evidence, never as passing.

7. **Reconcile documentation and evidence.** Update every document affected by the final change: design/architecture, usage examples, test expectations, requirement mappings, and plan details as applicable. Record newly discovered work as described below. Preserve exact commands, inputs/seeds, expected and observed outcomes, failures and subsequent passes, and relevant artifact hashes or traces. Keep durable evidence summaries in plan documents under `plans/`, and raw logs or temporary artifacts under ignored `temp/`. Use the plan's proof runner and receipts once implemented; before then, retain direct command/output evidence. A concise durable record with reproducible artifacts is sufficient; do not add another reporting system.

8. **Merge, verify, clean up, report, and mark completion.** Merge the step's feature/bug branch into `main` using the discipline above, verify the affected behavior on the merged result, and delete the merged local branch safely. Produce a concise report identifying the step/increment, behavior delivered, relevant requirement keys, design changes, branch/work/integration commits, cleanup result, checks run and their observed outcomes, evidence links, and any deferred work or blockers. Mark complete only after the acceptance criteria, review, retest, affected documentation, merge, post-merge verification, and local branch cleanup are satisfied. Check both the detailed increment and its numbered entry in `plans/PLAN.md`, add the evidence reference there, and update central progress counts and the next-step pointer. Include these updates in the final report. A requirement is verified only through its separate closure criteria; completing an increment does not automatically verify every requirement it advances.

Keep one brief working note or existing receipt for the loop rather than creating paperwork for each phase. The final report can reference that evidence instead of repeating raw logs.

## Keep process records out of product and test code

`src/` contains implementation code. `test/` contains behavioral tests, their support code, and domain fixtures. Neither directory is a home for planning, completion status, evidence reports, branch/commit records, agent working notes, or commentary claiming that a numbered step or requirement was proved. Do not add those statements to source/test comments or assertions. Ordinary assertions of required behavior and explanations of a test's technical purpose remain appropriate.

Keep requirement-to-case mappings and increment runner metadata under `plans/verification/`; keep durable evidence summaries in `plans/evidence/*.md` or the relevant plan document. Put raw command output, runtime traces, inventories, and intermediate proof files under ignored `temp/evidence/`. Plan documents should summarize their observations and link to the temporary artifacts as useful; temporary files are not tracked product inputs. Keep normal product fixtures in `test/`, and map their domain test IDs to steps externally rather than embedding plan IDs in test code.

## Build hosts and portability

The compiler/toolchain's build hosts are distinct from the CPUs and runtime environments targeted by generated SMIL programs. Use this host matrix when designing build configuration, dependencies, scripts, and platform-sensitive code:

| Build host | Development and verification policy |
| --- | --- |
| macOS | Primary development/build platform. Run the affected native build, tests, formatters, and linters here first. |
| Linux x64 (`linux/amd64`) | Supported host. Use a container to configure, build, and run the affected tests when build/platform-sensitive changes require Linux verification. |
| Linux ARM64 (`linux/arm64`) | Supported host. Use a separate container architecture to configure, build, and run the affected tests; one architecture's results do not certify the other. |
| Windows x64 | Supported host to preserve in code and build design. Windows builds cannot be tested in the current development environment; report them as untested and retain a documented build/test recipe for later Windows execution. |

Prefer portable CMake/C++ and explicit platform adapters. Avoid unconditional Apple-only APIs, shell utilities, paths, or compiler flags in shared build paths. Do not broaden the dependency set solely to abstract a hypothetical platform difference.

For changes affecting builds, platform adapters, filesystem/process behavior, or shared portability assumptions, exercise both Linux container architectures when an appropriate runtime is available. Record the engine, image/tag or digest, selected architecture, toolchain, exact commands, and actual test results. An image pull or cross-compilation alone is not execution proof; emulated execution is acceptable when explicitly identified. Missing container support or failed execution is missing evidence to record and address in a bounded plan increment, not a passing Linux check.

Use narrow macOS regression checks for routine platform-independent changes unless their scope or failures warrant the container matrix. Do not turn every small edit into an all-platform rebuild. Never claim Windows verification from Linux/container results. Record Windows validation as unavailable here, with the remaining obligation linked to the affected build work; seek actual Windows execution through a suitable environment when it becomes available.

## Newly identified work and deferral

Classify discoveries against the current increment's acceptance criteria:

- **Material work** is necessary for the current behavior to be correct, preserve required contracts, or produce valid completion evidence. Complete it within the increment or split the increment and add explicit prerequisite child work. Leave the original step open until its obligations are met.
- **Non-material work** can be deferred when the current acceptance criteria and required invariants still hold. Record it in the appropriate plan document with a stable increment/child ID, scope, reason for deferral, acceptance condition, dependencies, and a link from the current step or evidence. Update `plans/PLAN.md` so that work remains visible centrally, preserving existing step numbers and adjusting totals as needed. Report the deferral without expanding the current step unnecessarily.

If a discovery changes or exposes a gap in required behavior, also update the relevant specification or record the unresolved contract there, following its versioning rules, and update affected traceability/plan entries. Do not put implementation tasks into specifications, silently invent missing normative contracts, or relax an existing requirement to declare success. Work that only changes implementation need not change a specification.

A deferred improvement does not prevent completion when it is demonstrably outside the current obligations. Missing required correctness, tests, evidence, or documentation cannot be reclassified as an improvement to check off the step. No discovery should exist only in chat or as an untracked code TODO.

## Completion report format

Use a short report, scaled to the change:

- **Step/result:** numbered step and increment ID; delivered behavior or explicit incomplete status.
- **Work timing:** UTC start/end, elapsed duration, and separately measured active/waiting time or `unknown`; identify a stopped/resumed attempt when applicable.
- **Verification:** commands/cases and observed pass/failure outcomes, with durable evidence links.
- **Integration:** feature/bug branch, work commits, integration commit on `main`, post-merge verification, and safe local branch cleanup result.
- **Documentation:** relevant design/architecture and other document updates, or why none were needed.
- **Follow-up/progress:** recorded deferred IDs or blockers; completion state in both plan locations and the next step/action.

Do not claim tests or native target conformance that were not actually demonstrated. If a step is blocked or split, report the partial result, missing evidence, and the exact next bounded action, leaving its completion boxes open.
