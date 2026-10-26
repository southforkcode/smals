# Development efficiency policy update

User-authorized process change: targeted affected-case validation and cached builds by default; one post-merge smoke on unchanged inputs; a full safety checkpoint every tenth primary step; a rolling ten-increment average below five minutes elapsed. Original timings/estimates remain unchanged. Correctness, requirement evidence, quality gates, branch integration and safe cleanup remain mandatory. Fully verified work is not reopened merely to repair a time estimate; incomplete material obligations remain open. No product code or tests are removed.

Sources: the user’s process/cadence/five-minute instructions; project contributors, AGENTS.md, plans/00_delivery_and_evidence.md, plans/PLAN.md and plans/README.md. Step 22 was interrupted before implementation; its next attempt resumes after this process task. Historical overruns (including B013’s 1062 seconds) remain visible and are calibration failures, not within-budget claims.

Validation: structural/link/consistency checks plus a consolidated current-input full safety checkpoint; raw logs under temp/evidence/efficiency-checkpoint/. This process receipt is separate from product increments and does not close any specification requirement.

Preserved baseline for primary steps 12–21, including child/resume costs: 9168 elapsed seconds / 10 = 916.8 seconds per primary step. The target is not yet achieved. No historical duration or original estimate was reduced.

## Full checkpoint observation

All three hosts passed: macOS and separate Linux ARM64/x64 each ran seven native CTest cases and all 50 Python tests once, full default build quality gates, and the inventory audit (435 open, zero verified). Linux x64 is emulated. Docker/Colima engine and immutable smals-proof image IDs/toolchain pins are those recorded in B008; exact commands/logs and current input hashes are under temp/evidence/efficiency-checkpoint/. Windows is untested. Coverage reporting is not yet implemented (planned step 23); no quantitative coverage result is claimed. Next cadence checkpoint: primary step 30, sooner if risk/failures warrant.

The reusable scripts/checkpoint.sh wrapper passed bash syntax and actual macOS execution; deliberate CMake exit 7 propagates without continuing. Linux underlying full commands were executed independently; wrapper control-flow checks use each Linux Bash separately. No product behavior is changed.
