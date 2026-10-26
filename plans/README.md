# SMIL Implementation Plan

Use [PLAN.md](PLAN.md) to execute this work by number: “do step 1”, “do step 2”, and so on. It orders every increment by dependencies and provides the central completion checklist and evidence links. Update it alongside the detailed increment after each completed step.

Follow the repository [agent development process](../AGENTS.md) for requirements analysis, design, test-first implementation, simplicity review, retesting, documentation, evidence, and completion updates. Every step uses a feature/bug branch and is complete only after merging into `main`, verifying the merged result, and safely deleting the merged local branch; routine human review is not required. Build-host guidance covers macOS first, Linux x64 and ARM64 container execution, and Windows x64 with its unavailable local validation explicitly recorded. Record non-material discoveries as deferred plan work; keep material acceptance obligations in the current step or its prerequisite children.

Implement the [15 effective specifications](../specs/README.md) through small, observable increments. The plan covers all **435 requirement keys**, the checked runtime/toolchain, and all **38 reference CPU/mode profiles**. It contains **1,943 indexed increments**, including individual requirement audits and exact-profile qualification shards. Current completion and evidence are recorded in PLAN.md; step 1 is complete.

Each increment targets **10 minutes of active agent work**, with a **15-minute hard stop** and evidence-driven subdivision when the estimate is wrong. Every row has dependencies, a narrow deliverable, a runnable demonstration/pass condition, and requirement links. The size/evidence policy is in [00](00_delivery_and_evidence.md); repeated work is explicitly expanded rather than hidden in a large “implement backend” task.

## Documents

| Document | Purpose |
| --- | --- |
| [PLAN.md](PLAN.md) | Numbered execution sequence and central progress checklist for every increment. |
| [00_delivery_and_evidence.md](00_delivery_and_evidence.md) | Timebox, next-ready selection, proof receipts, requirement closure, staleness and visible advancement. |
| [01_foundation_and_contracts.md](01_foundation_and_contracts.md) | Build/evidence baseline and missing normative contract controllers. |
| [02_source_and_verification.md](02_source_and_verification.md) | Token/grammar increments, types, callable verification, CFG and SSA. |
| [03_execution_memory_and_lifecycle.md](03_execution_memory_and_lifecycle.md) | Arithmetic, host execution, memory/pointers, checked events/resources, devices and lifecycle. |
| [04_binding_interfaces_and_linking.md](04_binding_interfaces_and_linking.md) | Target binding, interface fingerprints, objects, relocations, static linking and loading. |
| [05_runtime_helpers_and_lowering.md](05_runtime_helpers_and_lowering.md) | Physical packet/frame contracts, native checked runtime algorithms and compiler lowering. |
| [06_expanded_contract_and_integration_slots.md](06_expanded_contract_and_integration_slots.md) | Every missing record/profile, runtime guard/entry, section placement and source-opcode integration slot. |
| [07_native_family_increments.md](07_native_family_increments.md) | Separate instruction-form and native transport increments for 12 CPU families. |
| [08_exact_profile_qualification.md](08_exact_profile_qualification.md) | Separate 16-increment empirical qualification for each of 38 exact profiles. |
| [09_cross_layer_and_release.md](09_cross_layer_and_release.md) | Cross-layer behavior, digest prerequisite split and final evidence aggregation. |
| [10_requirement_closure.md](10_requirement_closure.md) | One bounded closure audit per requirement, with clause-level empirical evidence. |
| [11_requirement_matrix.md](11_requirement_matrix.md) | All 435 keys mapped to implementation work, evidence scopes and closure IDs. |
| [12_dependency_groups.md](12_dependency_groups.md) | Exact ALL-* membership, task inventory and nominal compute estimate. |
| [13_specification_baseline.md](13_specification_baseline.md) | Raw spec-file digests for plan/evidence drift detection. |

## Execution entry and early value

0.0 **Create feature branch — B001**, then complete the build/evidence prerequisites. The first useful results are a real verified module, an executable checked host demonstration, deterministic separate compilation/linking, then a small native i8080a image and an early mc6800 big-endian counterpart. Shared runtime algorithms and primitive encoders precede profile-specific qualification. Select ready work by dependency receipts, not by reading file order as a serial schedule.

Most increments contribute to one or more requirements; only a fully evidenced `A-<KEY>` closes a requirement. Source-only requirements can close early. Cross-layer/native requirements wait for all applicable layers. No schema validation, mocked device, host interpreter or sibling CPU receipt counts as native conformance.

## Known contract gates

The specs name absent profile, linking and execution companion bundles. The plan has explicit recovery/adoption slots for their unknown exact layouts, signatures, maps, fault IDs, schemas and digests. Source and synthetic host-model work proceeds independently. Real binary interoperability and affected target claims remain blocked until normative authority resolves; this plan neither invents historical digests nor silently changes the specs. The blocker is part of the plan, not a reason to omit the remaining implementation work.

No implementation, branch creation, dependency installation or tests have been executed by writing this plan. The commands and code paths are specified work to be created in early increments. Plan validation checks document structure, requirement coverage and dependency consistency only.
