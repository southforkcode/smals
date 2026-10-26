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

Target 10 minutes of active work, with the plan's hard stop at 15 minutes. Include analysis, editing, builds, tests, review, and evidence capture in that budget. If the work does not fit, leave it incomplete and add bounded child increments using the stable numbering rules in `PLAN.md`. Never renumber existing integer steps or hide unfinished work behind a checked box.

## Branch and merge discipline

- Before each step, inspect the working tree and current branch. Preserve unrelated changes. Start from the current `main` and check out `feature/step-<N>-<short-description>`, or `bug/step-<N>-<short-description>` for a bug fix being handled separately from feature implementation. Use a unique suffix if a branch name already exists. If the step's purpose is to establish a different named feature branch, that branch satisfies this rule.
- Record the step's code, tests, design/architecture changes, other affected documentation, and immediate evidence on that branch in focused commits. Do not accumulate several numbered steps on one long-lived feature branch. A blocked or split step remains open; retain its branch and committed partial work with an explicit status instead of merging it as complete.
- After tests, simplicity review, and documentation pass, bring the branch up to date with `main`, resolve any conflicts without discarding other work, and rerun the affected checks. Merge it into `main` and verify the resulting state there. Keep this integration and verification inside the increment's time budget; if they cannot finish, record a bounded continuation and leave the step open.
- Record the feature/bug branch, work commit IDs, integration commit ID, and post-merge evidence. Update the central and detailed completion records only after the merge and verification succeed. Commit final status/evidence bookkeeping so completion is durable; that bookkeeping must not introduce untested implementation changes.
- After a successful merge and post-merge verification, switch to `main` and delete the merged local feature/bug branch with the safe merged-branch deletion command (`git branch -d <branch>`). Record cleanup in the completion evidence. Do not force-delete an unmerged branch or remove a blocked step's work. Clean up a remote branch only when the remote publication workflow is explicitly authorized; local branch cleanup does not imply pushing. A step remains open until required local branch cleanup succeeds.
- Proceed through ordinary commits, conflict resolution, self-review, and merging without requesting routine human review. Use the specifications, plans, project standards, and accepted engineering practices to make implementation decisions. Seek human input only for an exceptional issue that cannot be resolved within that authority, such as a material unresolved contract conflict or a necessary destructive action affecting unrelated work. Follow actual tool permission requirements when they apply. Merging locally does not itself request remote publication or pushing.

## Development loop

1. **Analyze the requirements.** Identify the applicable specification keys, expected behavior, boundaries, failure conditions, and the increment's acceptance criteria. Check existing implementations and tests for reusable behavior. Resolve material ambiguity before claiming an implementation is correct.

2. **Create or update the design.** Before implementation, record the necessary approach, interfaces, data flow, invariants, and integration points in the relevant design or architecture document under `docs/`. Link to the governing requirements and summarize meaningful tradeoffs. Update architecture documentation when module boundaries, dependencies, representations, or shared contracts change. An existing concise section is sufficient; routine changes already covered by a current design do not need a new document. State when no design change is needed. When replacing an established design, preserve its prior revision and publish a complete replacement according to `CODE_STANDARDS.md`; maintain working links and the document index.

3. **Write the behavioral tests first.** For code behavior, add the smallest meaningful positive and negative/boundary cases before changing the implementation. Derive expected values, diagnostics, and effects from the requirements or an independent oracle. Run the new cases and observe failure for the intended behavioral reason. A missing tool, unselected test, or broken fixture is not that failure. For a regression, reproduce the bug first. For documentation-only or other changes without executable behavior, use appropriate structural, link, schema, or configuration validation instead of artificial unit tests.

4. **Implement until the tests pass.** Make the smallest coherent change satisfying those cases and the complete acceptance criteria. Reuse existing modules and follow project standards, including errors as values and required formatters/linters. Do not weaken requirements, remove necessary checks, or change expected results merely to accommodate the implementation. Add cases when implementation exposes an untested obligation.

5. **Review for simplicity and repetition.** Review the diff against the requirements and design. Remove unnecessary branches, indirection, dead code, and copied logic. Extract a small shared function or abstraction where repeated behavior has the same semantics and change together; give it a clear responsibility and test its callers. Do not introduce speculative frameworks or merge superficially similar code with different contracts. Check failure paths, lifetimes, resource accounting, and observable effects where relevant.

6. **Retest and fix.** After implementation and refactoring, rerun the new cases, affected regression tests, and required formatting/lint checks. Cover changed implementation branches as required by project standards. Broaden testing when shared behavior or unresolved failures justify it. Fix failures and repeat the loop within the timebox; a refactor is not finished until its affected behavior is retested. Record unavailable checks as missing evidence, never as passing.

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
- **Verification:** commands/cases and observed pass/failure outcomes, with durable evidence links.
- **Integration:** feature/bug branch, work commits, integration commit on `main`, post-merge verification, and safe local branch cleanup result.
- **Documentation:** relevant design/architecture and other document updates, or why none were needed.
- **Follow-up/progress:** recorded deferred IDs or blockers; completion state in both plan locations and the next step/action.

Do not claim tests or native target conformance that were not actually demonstrated. If a step is blocked or split, report the partial result, missing evidence, and the exact next bounded action, leaving its completion boxes open.
