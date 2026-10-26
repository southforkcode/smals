# Timing retrospective and forward corrections

User-directed process review, begun 2026-10-26T13:57:43Z. Sources: project contributors’ [timing log](../PLAN.md#work-timing-log), completed-step receipts B002–B014, [agent process](../../AGENTS.md), and the user’s revised 5–10 minute goal. This supersedes the earlier below-five-minute goal; no historical estimate or result is rewritten.

## Observations

| Recorded primary range | Total seconds including retries/children | Mean minutes | Median minutes | Above 10 minutes |
| --- | --- | --- | --- | --- |
| 4–22 | 12,064 | 10.58 | 6.15 | 8/19 |
| 13–22 (latest ten completed) | 10,404 | 17.34 | 19.53 | 7/10 |

Computed from the timing table by grouping each decimal child with the integer parent and summing all attempts, including stopped attempts. No measured phase breakdown or active/waiting time exists. These totals include recorded interruptions; they exclude separately recorded ad-hoc process work, including the earlier 1,108-second process/checkpoint window and this review. They are not a complete estimate of all collaboration time. Primary step 23 is incomplete and excluded from completed-step statistics; its stopped attempt remains recorded.

Steps 4–9 were fast tool checks (276 seconds combined), unlike the later implementation/evidence work. B008.1 repaired a real all-command log-integrity gap; that remains necessary correctness work. B009/B009.1 show final lint/refactoring cost; check the affected quality gates early when adding tool modules. B012.1 was a historical timing-only closeout: preserve its record but do not repeat that pattern. B013/B014 receipts show broad host/quality/evidence work alongside overruns; the logs do not support attributing exact seconds to any phase. Existing checkpoint/reuse rules address duplicate checks without waiving evidence. The 435 requirement inventory entries remain open; foundation completion never implied conformance.

## Forward plan corrections

| Next ready work | Revised execution estimate and boundary | Acceptance / follow-up |
| --- | --- | --- |
| 23.1 / B015.1 | 5–10 elapsed minutes; shared logging and caller migration only; selectively reuse the retained scaffold | Exact JSON/escaping, invalid severity/sink behavior, one origin error, debug/release probes; no coverage infrastructure scope |
| 23.2 / B015.2 | 5–10 elapsed minutes; coverage option/checker and real incomplete/complete runs | Demonstrate uncovered rejection and full changed-unit outcomes; host evidence as applicable; split instrumentation and checker into real children before coding if prerequisites cannot fit |
| 23 / B015 closeout | 5–10 elapsed minutes after both children; validate combined acceptance and integration evidence | Keep parent open until all obligations pass; retained scaffold branch is cleaned up only after its work is integrated; do not merge failing scaffold |
| 24 / C001 | 5–10 elapsed minutes; inventory missing companion files and exact unresolved authority only | Existing per-file register acceptance stays binding; recovery/adoption remains in already planned contract increments, not this inventory |
| 25 / C002 | 5–10 elapsed minutes; extract authoritative grammar/opcode contract with provenance | Retain byte comparison/distinctness checks; no parser or invented contract expansion |

These forward estimates accompany the original row estimates; they are not measurements. Before S001, preflight UTF-8 decoding versus normalization/span scope and introduce distinct children if both cannot fit, preserving all rejection cases. Do not preemptively rewrite the remaining thousands of estimates. Existing numbered steps and normative contracts stay stable; B015’s new child deliverables are visible in both checklists. README and dependency inventory counts are reconciled to 1,948; prior totals remain identified as historical.

## Process adjustment and evaluation

AGENTS.md now requires a brief actual-versus-estimate note per attempt and an evidence-based process/near-term-plan review every ten primary steps, sooner after three >10-minute totals or a material split. Reuse the existing receipt; do not add per-phase paperwork. Reserve closeout time, reuse exact-input checks, and keep the full checkpoint cadence. Review the effect at step 30 (or earlier trigger), comparing the next ten-primary window and the same cost basis; do not claim an improvement until observed. Faster correct steps are welcome; 5 minutes is not a minimum time to spend.

Validation: `python3 temp/evidence/process-review/validate.py` passes all 1,948 indexed links and matching detailed completion states, local document links, timestamp arithmetic, latest-ten statistics, unchanged historical timing rows, unchanged implementation inputs and `git diff --check`. Raw result: `temp/evidence/process-review/validation.json`. This documentation-only change requires structural validation; no software tests are claimed. Integration and branch cleanup follow. No product code changes belong to this process revision. The incomplete B015 implementation remains on its retained branch.

## Integration and work timing

Technical work `324f34812acef8dc4e84b5fe77cbfd47d602eb55`; integration `96ceadd434964e3b3b0a1f452c674b728bd2385c` on main. Post-merge structural checks passed; safe local `git branch -d docs/review-step-timing-process` succeeded. The incomplete step-23 branch remains, as required; no remote changes.

Observed UTC window `2026-10-26T13:57:43Z`–`2026-10-26T14:02:06Z`; elapsed_seconds 263; active_seconds/waiting_seconds unknown/unknown. End observed after merge, verification and cleanup, before final timing bookkeeping. This is separately requested process maintenance, not completion of step 23. Next action: B015.1; next periodic review/checkpoint: primary 30 or earlier overrun trigger.
