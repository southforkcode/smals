# SMIL Control Flow and SSA Verification

- Define explicit block transfers, simultaneous parameter bindings, and integer switch/trap behavior.
- Specify structural reachability and dominance independently of textual block order.

## Sources

- [Guide — Basic Blocks and Control Flow](../docs/Guide_SMIL.md#basic-blocks-and-control-flow) and [Control-Flow and SSA Verification](../docs/Guide_SMIL.md#control-flow-and-ssa-verification).
- [Functions](0005_functions_and_calls.md), [source grammar](0001_source_syntax.md), and [lifecycle](0014_program_lifecycle.md).

## Requirements

| KEY | Requirement |
| --- | --- |
| CFG-001 | Every block shall have a unique function-local label, ordered typed parameters (including an explicit empty list), and ordered operations ending in exactly one final terminator. Labels shall not be ordinary values/data pointers. |
| CFG-002 | The first block shall be entry, match the function signature, and have no incoming CFG edges. Other blocks may be reordered without changing explicit edge semantics; branches shall remain within the owning function and shall never target entry. |
| CFG-003 | Operations shall execute in textual block order subject to semantics-preserving transformation. There shall be no implicit fallthrough, implicit return/trap, hidden unwinding destination, or saved-stack successor. Arbitrary valid edges between non-entry blocks shall be permitted. |
| CFG-004 | Every incoming edge shall separately supply the destination's exact argument count/types. Explicit edge arguments shall be existing source-available values or valid statically evaluated constants, not nested executable operations. |
| CFG-005 | The selected edge's source bindings shall be captured before transfer; all complete destination parameters shall bind simultaneously. A swap edge shall not overwrite a source value during sequential parameter assignment. Dominating values may be used directly without forwarding through every block. |
| CFG-006 | `br` shall take its one explicit edge. `br_if` shall require `i1`, select its first edge for one and second for zero, and bind only the selected argument list. Edges to the same block shall remain separately checked. |
| CFG-007 | `switch [iN] selector default edge { cases }` shall require a matching iN selector, one default, and zero or more same-type constant cases evaluable by binding. Selection shall compare bit patterns, with no range/fallthrough semantics. |
| CFG-008 | Encoded switch cases shall be unique, including different signed/unsigned spellings of the same bits. Invalid/faulting cases shall be diagnosed. Zero cases shall transfer to default; all listed edges shall remain structural CFG edges even for constant selectors. |
| CFG-009 | `trap` shall require a decoded constant identifier beginning `user.` with nonempty suffix, have no results/successors, and terminate with that fault while preserving preceding effects and promising no cleanup. It shall not mean undefined `unreachable`. |
| CFG-010 | The closed terminator set shall be `br`, `br_if`, `switch`, `invoke`, `invoke_indirect`, `return`, `raise`, `trap`, and `exit`, with exactly their defined successors. No ordinary operation shall follow a terminator in its block. |
| CFG-011 | `call`/`call_indirect` and ordinary potentially faulting arithmetic/pointer/memory operations shall remain ordinary operations. Possible terminal events shall not create normal successor edges or exempt their blocks from an explicit terminator. |
| SSA-001 | Every block shall be structurally reachable from entry using both conditional/invoke edges and every switch/default edge regardless of proven selection. Canonical verified/emitted SMIL shall contain no unreachable block. |
| SSA-002 | A block A shall dominate B exactly when every entry-to-B CFG path includes A. Each block shall dominate itself and entry shall dominate all valid blocks. Dominance shall not depend on textual order or on ignoring a syntactically listed edge. |
| SSA-003 | A same-block operation/declaration result shall be used only after its definition. A cross-block result shall be used only where its defining block dominates the use block. An operation's own outputs shall be unavailable to its inputs. |
| SSA-004 | A block parameter shall be defined at block entry, available throughout that block, and available in another block only if its block dominates the other block. Loop reentry shall create new dynamic bindings without reassignment or another static definition. |
| SSA-005 | Explicit branch/switch/invoke edge arguments shall be uses at the source terminator, before destination binding. Invoke results/payloads shall be defined only by their corresponding destination parameters. |
| SSA-006 | A verifier shall resolve every referenced symbol, type, constant, block, and SSA name to the appropriate kind; enforce definition uniqueness; and enforce every operation's result count, exact types, static attributes, and availability. |
| SSA-007 | Verification shall enforce entry declaration ordering; callable effects/ABIs/attributes; record paths and initializer dependencies; pointer/device/atomic form restrictions; switch/trap validity; borrowed-pack ownership; and lifecycle signatures. Profile-dependent checks shall finish at binding and whole-program graph checks at linking. |
| SSA-008 | A value defined on only one incoming path shall not be used after a merge unless it dominates the use. A block parameter receiving an appropriate value from every incoming edge shall be the supported merge mechanism. |
| SSA-009 | Verification shall diagnose violations even in structurally reachable blocks whose edges are never selected for a particular constant input. Unexecuted ordinary faulting operations shall not cause runtime faults merely because verification examines them. |

## Required conformance observations

| Case | Required outcome |
| --- | --- |
| Two edges from one block to one destination with different operands | Both checked separately; only selected bindings used. |
| Source pair `(b,a)` transferred to next iteration's parameters `(a,b)` | Values exchanged simultaneously. |
| Entry backedge, cross-function edge, missing/followed terminator | Structural rejection. |
| Switch cases `[i8 -1]` and `[i8 255]` | Duplicate-case rejection. |
| Block reachable only by a constant-false branch or invoke exceptional edge | Structurally reachable and included in dominance. |
| Physically earlier definition in a nondominating block | Use rejected. |
| Loop-carried parameters and dominating entry operands | Valid with one static definition per SSA name. |
| Disconnected block after a transformation | Removed before canonical verification/emission. |
