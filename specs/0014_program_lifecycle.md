# SMIL Program Lifecycle

- Specify one-time global construction, deterministic startup dependencies, readiness, and initialization failure.
- Define callback registration, orderly shutdown, explicit exit, and finalization.

## Sources

- [Guide — Program Lifecycle](../docs/Guide_SMIL.md#program-lifecycle) and [Global Initialization and Program Entry](../docs/Guide_SMIL.md#global-initialization-and-program-entry).
- [Functions](0005_functions_and_calls.md), [checked execution](0009_checked_execution.md), [reference environment](0011_checked_reference_profiles.md), and [linked lifecycle metadata](0013_objects_and_static_linking.md).

## Requirements

| KEY | Requirement |
| --- | --- |
| LIFE-001 | Each program instance shall have an environment-owned coordinator and designated lifecycle agent, with states bootstrap, initializing, running, shutting_down, and terminated. Normal initialization shall proceed in that order; failed initialization shall proceed to shutdown then termination. A terminal fault may terminate directly from any state without orderly cleanup. |
| LIFE-002 | Bootstrap shall establish CPU/runtime/stacks, reserve all global allocations/final locations, apply relocations, and install every constant initializer before any SMIL initializer action. Constant globals shall then be ready. Instance initialization shall occur once, not on import, ordinary factory calls, or reentry. |
| LIFE-003 | `global ... [T] dynamic @factory init("id")` shall require one nonempty program-wide ID and a direct non-variadic zero-parameter factory returning exactly one T. The factory may declare one raised type. Optional `after` shall list prerequisites; optional shutdown shall be a supported-ABI fixed non-raising zero-parameter/zero-result function. |
| LIFE-004 | Dynamic-global allocation/subobjects shall exist before initialization, but contents shall remain unavailable until normal factory return and complete coordinator installation. No implicit zero or second preceding initializer shall exist. Installation shall publish complete value/readiness together and initialize immutable storage without authorizing ordinary writes. |
| LIFE-005 | Dynamic placement shall permit construction; unwritable ROM placement shall be rejected. By-value results/pointer-field lifetimes shall remain unchanged. Ready mutable globals shall permit ordinary writes; immutable globals shall not. |
| LIFE-006 | Address formation may identify a reserved not-ready global. Content loads/stores/atomics through any alias shall cause `global_not_initialized`, including its own factory attempting incremental writes to the published object. A read shall neither trigger lazy initialization nor discover dependencies. Checks may be omitted only with readiness proof. |
| LIFE-007 | A `startup "id" @action` shall identify a non-variadic zero-parameter/zero-result action, optionally raising, with an optional callback obeying LIFE-003. Coordinator-supported action/callback ABIs may differ; reference callbacks shall use default ABI. |
| LIFE-008 | Dynamic globals and startup hooks shall form one graph with unique nonempty exact decoded UTF-8 IDs and explicit `after` edges. Duplicate/missing/self/cyclic dependencies shall be diagnosed before action execution. Constant globals shall have no nodes. Imports, source order, and address references shall not infer edges. |
| LIFE-009 | Initializers shall run serially on the lifecycle agent. Among ready nodes, the coordinator shall choose the unsigned UTF-8 byte-smallest ID; a node shall run at most once. Factory success shall install its object before completing; hook success shall complete on normal return. |
| LIFE-010 | Callback capacity for a completion callback shall be reserved before its action. The callback shall be registered only after successful action/value installation; a raised outcome shall discard that reservation. Ordinary calls of those functions shall not complete nodes, reconstruct objects, or confer immutable-write privilege. |
| LIFE-011 | An action may access constant globals and dynamic globals already completed. Required construction order shall be expressed by explicit/transitive dependencies; accessing incomplete contents shall fault rather than recursively initialize them. Source-language total constructor order shall require graph edges; lazy once/reentry semantics shall require explicit lowering/contracts. |
| LIFE-012 | Application entry and callbacks/interrupt handlers that could observe incomplete globals shall remain gated until initialization completes. Any initialization-time asynchronous service shall have an environment contract preventing unrestricted access to incomplete state. |
| LIFE-013 | On complete initialization, the coordinator shall publish readiness with an environment-defined happens-before handoff and enter the designated fixed non-raising supported entry. No universal language main signature shall be assumed; reference profiles shall use RRT-004. |
| LIFE-014 | A factory/hook raised outcome shall fail its node without installing its object/registering its callback, retrying, continuing dependents, or entering the application. Its explicit exceptional CFG shall clean up its own partial resources; earlier committed callbacks shall drain in reverse registration order, then terminal `initialization_failed` shall be reported. |
| LIFE-015 | An initializer terminal fault/trap shall terminate immediately without a callback-drain promise. A later callback fault while handling initialization failure shall terminate that cleanup path; already completed external effects shall not be rolled back. Original typed failure payload reporting shall occur only through a declared environment interface. |
| LIFE-016 | `on_exit ref` shall append one callback entry with no result, require an authorized agent in running state, and require a valid non-null supported-ABI fixed non-raising zero-parameter/zero-result callable. Repeated registrations shall be distinct. Failed validity/capacity shall append nothing. |
| LIFE-017 | The environment shall define registration agents and a linearization order consistent with per-agent sequencing. Successful registration shall publish preceding ordinary writes to its eventual callback through a happens-before edge. Registration shall not capture locals or extend target lifetimes. |
| LIFE-018 | Normal designated-entry return or authorized lifecycle-agent `exit value` shall request orderly shutdown. `exit` shall require i32, terminate its block with no successors, and report that exact logical status; it shall not be a function return or catchable exception. Normal entry-result status mapping shall be defined by the environment. |
| LIFE-019 | Before draining, the coordinator shall enter shutting_down, prevent new application entry, quiesce every other agent capable of accessing finalizing globals, and establish happens-before from their completed effects to callbacks. An insufficient interrupt/thread/device protocol shall be unsupported. |
| LIFE-020 | Explicit exit shall abandon the invocation chain after quiescence and before callbacks, expiring its locals without implicit per-invocation destructors. Required source cleanups shall be expressed through cooperative returns/raises before exit. |
| LIFE-021 | The callback stack shall drain LIFO across initializer completions and runtime registrations. Each entry shall be removed before invocation and execute at most once. Multiple entries for the same function shall remain distinct; callbacks shall execute on the lifecycle agent. |
| LIFE-022 | A dynamic global shall remain ready during its completion callback, then become finalized on normal callback return. Later content access shall cause `global_finalized`; allocation/address formation shall remain available until termination. Callback naming shall grant no mutation rights to immutable contents. Other globals shall remain available until their own finalization or termination. |
| LIFE-023 | After callback drain, remaining global lifetimes shall end, state shall become terminated, and the environment shall report status/halt without restarting the instance or rerunning initialization. |
| LIFE-024 | Exit/registration outside running, unauthorized agents, and nested coordinator startup/shutdown shall cause `invalid_lifecycle_transition`. For registration, state/agent validation shall precede target validity, then reservation. Callback faults/traps shall abort further orderly shutdown. |
| LIFE-025 | Terminal arithmetic/pointer/storage/initialization/race/resource/call/pack/lifecycle violations and user traps shall bypass ordinary callback drain unless an explicitly defined failure path above already applies. No general cleanup/unwind promise shall be inferred. |
| LIFE-026 | Linking shall retain lifecycle functions/nodes, verify contracts/placements/agents/runtime support, and resolve the graph before execution. Readiness/finalized checks shall follow association through aliases and supported integer reconstruction. |
| LIFE-027 | Native constructor/destructor registries and foreign exceptions shall require an explicit adapter and coordinator ordering contract. Dynamic loading/unloading and instance restart shall require extensions rather than hidden effects of ordinary calls. |

## Required state transitions

| Event/state | Required next behavior |
| --- | --- |
| Bootstrap complete | Initializing, with all constant globals ready and dynamic contents unavailable. |
| All initialization nodes succeed | Publish readiness, running, enter application. |
| Initialization node raises | Drain earlier callbacks; terminate with `initialization_failed` unless cleanup itself faults. |
| Entry returns or authorized running exit | Quiesce, shutting_down, LIFO callbacks, terminated/status. |
| Terminal fault in any state | Terminated, without further normal commits or promised orderly cleanup. |

## Required conformance observations

| Case | Required outcome |
| --- | --- |
| Independent node IDs discovered in different file/library orders | Same byte-sorted ready-node order. |
| Address cycle between globals with no content dependency | Address formation permitted without an initialization cycle. |
| Self-factory accesses its published dynamic object's contents | `global_not_initialized` after prior storage-domain checks. |
| Failed node with optional callback | Its callback absent; earlier committed callbacks drained in reverse order. |
| Dependent/prerequisite callbacks plus later application registration | Application callback first, then dependent before prerequisite. |
| Repeated `on_exit` for one function | Separate once-per-entry callbacks. |
| Finalized global address versus content access | Address available; content faults with `global_finalized`. |
| Shutdown callback attempts registration/exit | `invalid_lifecycle_transition`; further drain not promised. |
| Callback retains abandoned local pointer after exit | Target expired before callback invocation. |
