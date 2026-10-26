# SMIL Checked Execution and Resource Semantics

- Define initialization, data-race, and resource failures as terminal events with deterministic intra-operation priority.
- Preserve the checked execution prefix and publish resource accounting with target-bound objects.

## Sources

- [Guide — Execution Violations, Resource Limits, and Optimization](../docs/Guide_SMIL.md#execution-violations-resource-limits-and-optimization).
- [Memory](0007_pointers_and_memory.md), [synchronization](0008_devices_and_atomics.md), [profiles](0011_checked_reference_profiles.md), and [objects](0013_objects_and_static_linking.md).

## Requirements

| KEY | Requirement |
| --- | --- |
| EXE-001 | `smil.execution.checked.v1` shall govern ordinary/unaligned/atomic access, local construction, calls, helpers, and lifecycle operations where applicable. Reached violations shall terminate without results, catchable payloads, cleanup, rollback of earlier effects, or later normal commits. |
| EXE-002 | Initialization shall belong to allocation representation, never SSA bits. A fresh uninitialized mutable local shall have no initialized representation bits even when recycled RAM contains an old value, zeroes, or debug fill. |
| EXE-003 | Successful integer initialization/store shall define every bit of its representation bytes, including cleared unused high bits, but not allocation padding. An interior integer view shall initialize only its own representation bytes in the selected byte order. |
| EXE-004 | Pointer/callable construction shall establish the complete matching value including required state. Record construction/store shall recursively establish logical fields only; empty records shall have no value-bit read requirements but still require a valid object position. |
| EXE-005 | An integer read shall require only its N logical bits in addressed byte order; pointer/callable reads shall require their complete typed representation; record reads shall require every leaf recursively. Missing required bits shall cause `uninitialized_read` before any value escapes. Ignored high bits/padding shall not add read requirements. |
| EXE-006 | A successful load shall not initialize storage. Masking, discarding, extracting a sibling field, comparison, or a later overwrite shall not repair an invalid earlier read. A typed copy shall validate its source before exposing any copied value/destination effect. |
| EXE-007 | Not-ready/finalized globals shall select their lifecycle fault before initialized-bit checks. External regions and foreign output contracts shall explicitly establish entry/output initialization; a signature or unknown call alone shall not prove initialization. Unsupported boundaries shall require an adapter or rejection. |
| EXE-008 | Initialization proof/tracking shall match every permitted alias and integer view, reset per allocation lifetime, and remain private/bounded. At merges a definite-initialization proof shall use the intersection of incoming initialized sets; loops shall use a sound fixed point. May-alias stores shall establish only bytes proven written. |
| EXE-009 | A backend may use equivalent flags/bitmaps/type walkers/proofs; omitted tracking shall require a sound proof at every read. Private metadata operations shall not be source events/races but shall be synchronized and inaccessible through source pointers. Missing metadata shall never imply an initialized value. |
| EXE-010 | A memory footprint shall be the union of accessed leaf representation-byte ranges, excluding padding. A failed compare/exchange shall have a read-only footprint. Correct atomic accesses to one supported location shall not constitute a race with each other. |
| EXE-011 | Before committing each next memory event, an implementation shall detect a conflict with prior completed events by another agent when at least one access is non-atomic and no application happens-before ordering exists. The new access shall then cause `data_race` before exposing a result/effect. Future unexecuted accesses shall not count as violations. |
| EXE-012 | Race freedom shall be established by proof, enforcing an environment ownership discipline, or exact equivalent histories. Sampling, delayed reports, unsound eviction, last-writer-only histories, and private serialization without application ordering shall not satisfy the contract. |
| EXE-013 | Multi-agent validation shall coordinate observation, read/write histories, lifetime, and commitment, keyed by allocation identity and footprint. Prospective acquire edges shall derive from the actual observed write and become effective only on commit. History may be summarized/discarded only with proof preserving all future conflicts. |
| EXE-014 | Profiles shall account for every foreign/DMA/thread/interrupt participant able to touch shared ordinary storage. Reference single-agent profiles may prove the race predicate false only while excluding all such competitors. Enabling another agent shall require a separately versioned contract. |
| RES-001 | Failure to obtain any required execution resource shall cause `resource_exhausted`, not null, truncation, wrap, dropped registration/tracking, identity reuse, unchecked execution, or an implicit raised payload. Static impossible types/placements/fixed frames/startup capacity/catalog ranges shall instead be diagnosed at binding/linking. |
| RES-002 | A profile shall define capacity domains, bounds, accounting units, reservation points, and emergency reporting resources for stacks/frames/packets/work buffers, object/shadow/history metadata, helper scratch, callbacks, and finite counters. All size/addition/multiplication/rounding shall be checked mathematically before writing finite encodings. |
| RES-003 | Each operation shall preflight and reserve all required resources before its logical commit, including native pushes, helper entry, storage-requiring locks, software extensions, local identity/tracking, and dynamic packet sizes. Call target validation shall precede its reservations. |
| RES-004 | One operation's reservation shall be all-or-fault: failure shall not publish a local, enter a callee, append a callback, partially initialize storage, or perform a device transaction. Private tentative reservations may occur only without observable partial success or application allocation needed to undo them. |
| RES-005 | Lifecycle completion-callback capacity shall be reserved before its initializer action and committed only after successful action/value installation. Runtime-depth/history/registration-dependent failure shall occur at its reached checkpoint, without faulting an unexecuted path. |
| RES-006 | Terminal reporting shall use pre-reserved emergency state independent of the exhausted capacity. A profile unable to guarantee this shall reject the use. Host process death, power loss, hardware corruption, or breach of environment reservations shall not be misreported as conforming resource exhaustion. |
| RES-007 | Profile-mandated identity increments, live-object slot charges, and callback registrations shall be preserved even when their physical representation is optimized away. Backend-dependent frame/spill/work/tracking charges shall describe the actual published lowering. |
| RES-008 | Reference v2 locals shall reserve a half-open ID range only when `next_allocation_id + count` fits u32. `UINT32_MAX` shall be an exhausted next-counter sentinel, never a new local identity. Required increments and live-slot charges (including monitor/reserved globals) shall not be waived by dead-code elimination. |
| RES-009 | Different valid lowerings may have different physical exhaustion points, but changes shall preserve non-resource semantics and mandated accounting, regenerate the execution plan/digests/provenance, and obey ABI/lifetime/association constraints including inlining and tail calls. No portable fixed recursion depth shall be implied. |
| EXE-015 | Each reached operation shall select its fault using the ordered validation stages below before its commit. Guard fusion/motion shall preserve the same selected fault and prior observable prefix. Operand-producing operations shall execute earlier under CFG sequencing. |
| EXE-016 | Principal operation-domain checks shall precede storage checks; storage association/extent/view/alignment/rights/kind shall precede global readiness. Among failing global states within one operation, `global_not_initialized` shall precede `global_finalized`. |
| EXE-017 | `on_exit` state/agent checks shall precede callback target checks. Division shall check zero before quotient overflow and work allocation. User `trap` shall commit its identifier when reached without application allocation. |
| EXE-018 | Fixed validation/emergency scratch shall be pre-reserved to decide earlier stages from valid existing metadata. Helper allocation failure shall not preempt an earlier selected fault. New-history growth shall be stage 4; absent exact tracking shall never mean no race. |
| EXE-019 | Across agents, the environment shall select the next validation/commit event consistently with sequencing/synchronization/atomic order. The first terminal event shall close the instance and determine the reported fault; no later normal operation shall commit. Authorized in-flight external activity shall retain its device contract. |
| OPT-001 | Verification shall establish well-formedness/implementability, not absence of dynamic violations. Source-language undefined behavior, disabled sanitizers, pointee spelling, or ordinary signatures shall not grant additional optimizer assumptions. |
| OPT-002 | Removing/forwarding/merging/hoisting loads, divisions, pointer operations, or guards shall preserve or prove absent all applicable domain, readiness, initialization, race, synchronization, resource, and terminal-prefix effects. Proven reached failures may become their selected terminal event, never an impossible-path assumption. |
| OPT-003 | Record scalarization shall preflight the complete logical access before any result/write; access widening/splitting shall retain legal source footprints and neighboring independence. Multi-agent physical splitting shall not introduce conflicts. Logical preflight shall not imply aggregate atomicity. |
| OPT-004 | A dominating guard shall justify later uses only while its lifetime/readiness/ownership/alias facts remain stable. Unknown calls, permitted writes, concurrent actors, or lifecycle transitions shall invalidate facts as applicable. |
| MET-001 | Checked v2 objects shall carry one private `aux` definition named `execution_plan` in a metadata blob, canonical JSON format `smil.execution-plan.v1`, with runtime descriptor token `smil.execution.checked.v1#plan`. The linker shall validate ownership/contract/bounds and preserve required target tables. |
| MET-002 | The plan shall identify module, execution-contract digest, profile, and every defined function's complete frame size, callee-owned native reservation excluding nested callees, local shadow extent, and checked sites. Locals shall record declaration ordinal, canonical type key, offset/size, initial state, tracking choice, and bitmap offset/size. Sites shall record opcode, fixed costs, and runtime-dependent resource domains. |
| MET-003 | Plan function/type references shall use canonical keys, never provisional numeric IDs. Frame sizes shall include headers/locals/shadow/private work; `tracking_bytes` shall attribute already charged software/runtime bytes rather than create another pool. Dynamic amounts shall be computed by checked code, not an executable metadata expression language. |
| MET-004 | Published extents/reservations shall fit their regions and match emitted code. Single-agent profiles shall have zero synchronization/history charges; extra tracking shall fit existing limits without changing reserved-zero fields or private record layouts. A different multi-agent runtime shall define its own capacities/protocol/progress. |
| MET-005 | Published checked v1 identities/digests shall not be silently amended. Checked v2 shall select the stronger execution digest/runtime, preserve built-in fault IDs 1–13, add ID 14 for `uninitialized_read` and 15 for `data_race`, and retain user-ID base 65536. Exact-component linking shall reject old v1-bound objects in a v2 program. |

## Ordered validation stages

EXE-015 incorporates this order; inapplicable stages are skipped.

| Stage | Required result on failure |
| --- | --- |
| 1. Operation domain | Applicable arithmetic, callable, pack, lifecycle, pointer, storage, then readiness/finalization fault. |
| 2. Required initialized reads | `uninitialized_read`. |
| 3. Checked concurrency | `data_race` when existing history establishes an unordered conflict. |
| 4. All execution reservations | `resource_exhausted`, including inability to retain exact checking for the next commit. |
| 5. Commit | Publish the logical action/results and associated metadata/synchronization. |

## Required conformance observations

| Simultaneous conditions at one operation | Selected outcome |
| --- | --- |
| Invalid/null/expired access and missing initialized bits | `invalid_storage_access`; no metadata lookup through invalid association. |
| Valid access to reserved dynamic global | `global_not_initialized` before unwritten bits. |
| Unwritten read and conflicting history | `uninitialized_read`. |
| Proven conflict and insufficient new history/work capacity | `data_race`; otherwise precommit `resource_exhausted` when exact checking cannot continue. |
| Invalid indirect target and exhausted call stack | `invalid_call`. |
| Failed initialized compare/exchange and concurrent reads only | No write conflict introduced. |
| Read after partial integer write, on both byte orders | Written view succeeds; larger load needing unwritten value bits faults. |
| Frame reuse and physical registry/bitmap elimination | Fresh initialization state and mandatory logical accounting preserved. |

The term “execution plan” above names a required runtime metadata artifact already defined by the guide. It is not a development plan or task list.
