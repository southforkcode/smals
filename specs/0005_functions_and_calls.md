# SMIL Functions and Callable Transfers

- Define logical signatures, direct/indirect calls, typed variadics, and exceptional outcomes.
- Preserve explicit invocation lifetimes and prohibit hidden nonlocal CFG transfers.

## Sources

- [Guide — Functions](../docs/Guide_SMIL.md#functions), including Function References, Variadic Functions, Typed Exceptional Transfers, and Nonlocal Exits.
- [CFG/SSA](0006_control_flow_and_ssa.md), [ABI contracts](0010_targets_layout_and_abi.md), and [lifecycle](0014_program_lifecycle.md).

## Requirements

| KEY | Requirement |
| --- | --- |
| FUN-001 | A function shall be module-level and have an ordered fixed parameter list, optional final variadic marker, ordered normal results, optional ABI clause, and optional single raised-payload type. Definitions shall contain one or more basic blocks; functions shall not nest. |
| FUN-002 | Repeated declarations and the unique definition shall agree after alias resolution on parameter/result types/order, variadic status, raised type, resolved ABI, and effective extension attributes. Empty result lists shall produce no special void value. |
| FUN-003 | Entry parameters shall match the fixed signature plus exactly one final `[varargs]` parameter for a variadic definition. ABI carriers/extension/result areas shall not add logical entry parameters. Signature entries shall contain types/attributes rather than SSA binders. |
| FUN-004 | Direct `call` shall accept only a function symbol with a non-raising callable contract. Fixed arguments and result bindings shall match exact ordered types/counts; produced results shall all bind fresh SSA identifiers. |
| FUN-005 | Calls shall create distinct invocations and permit recursion. Normal completion shall resume at the next operation; terminal faults and program exit shall not return. Calls may affect accessible storage unless a stronger effect contract is established. Existing SSA values shall remain unchanged. |
| FUN-006 | All argument/result passing shall preserve logical by-value values and result lifetimes, including aggregates and hidden physical carriers. Block argument transfer shall not count as a call. |
| FUN-007 | `return` shall terminate the invocation with exactly its normal result list and expire its locals. A record result shall be one result, distinct from multiple scalar results. Returning a pointer shall not extend its target lifetime. Infinite execution shall not waive block-termination rules. |
| FUN-008 | `fnptr` compatibility shall include ordered parameter/result types, effective attributes, variadic marker, resolved ABI, and raised type. Implicit callable-contract conversion shall be rejected; adaptation shall require a wrapper. |
| FUN-009 | `fnaddr @f` shall require a function declaration and produce a non-null reference with its complete callable contract. A bare function symbol shall remain a direct target rather than an ordinary value. Typed callable null shall be permitted. |
| FUN-010 | Function references shall be distinct from data pointers, have profile-defined representation/null/equality/entry sequences, and permit matching typed storage, record inclusion, argument/result transfer, and copying without representation loss. |
| FUN-011 | `fn_eq` and `fn_ne` shall require matching callable contracts and return complementary `i1` results by resolved function identity, with null equal only to null. Distinct wrappers shall remain distinct; descriptors, trampolines, and code folding shall preserve identity. |
| FUN-012 | `call_indirect` shall follow direct-call argument/result rules and require a non-raising contract. Null/invalid target shall fault with `invalid_call` before entering the callee or reserving its execution resources. Foreign references shall be proven/checked compatible or rejected. |
| FUN-013 | Data-pointer casts/conversions/arithmetic/comparisons and field selection shall reject function-reference values. Function targets shall remain available for the instance lifetime; numeric code-address forging, implicit closures, and dynamic unloading shall not be supported. |
| VAR-001 | A variadic signature shall place `...` last in its parameter list, possibly with no fixed parameters. Results shall not be variadic. Additional explicit values shall keep their exact SMIL types without default promotions. |
| VAR-002 | A variadic entry pack shall be an immutable borrowed SSA value owned by its invocation. It may pass through that function's block parameters but shall not be stored, addressed, embedded in records, returned, raised, or passed as an ordinary function argument. Aliases shall retain these restrictions. |
| VAR-003 | `va_count [iM] pack` shall return the unsigned additional-argument count or fault with `invalid_variadic_access` if it does not fit. `va_is [T] pack index` shall return one only for an existing exact-type argument and zero for absent/wrong-type indices. |
| VAR-004 | `va_get [T] pack index` shall return a complete exact-T value or fault with `invalid_variadic_access` for an absent/wrong-type index. T shall be an ordinary supported value type. All indices shall use their complete unsigned value without masking/narrowing; retrieval shall not advance a cursor. |
| VAR-005 | Every pack operation shall require a live owning invocation; expired packs shall fault with `invalid_variadic_access`. A final `...%pack` expansion shall be allowed only once, last in a variadic call, after all explicitly supplied fixed arguments and any explicit additional values. |
| VAR-006 | Pack forwarding shall deliver a separate callee-scoped pack with unchanged source types/values and shall not extend pointee lifetimes or borrow expired storage. A target shall separately advertise static variadic calls, typed receipt, and runtime forwarding. |
| VAR-007 | Foreign untyped varargs receipt/forwarding shall require an explicit type-information ABI/adapter. Native `va_list` recognition alone shall not establish compatibility; missing support shall be diagnosed. |
| EXC-001 | `raises([E])` shall declare exactly one complete ordinary payload type and shall participate in all callable compatibility. Omission shall prohibit propagation; `varargs` shall not be a payload. |
| EXC-002 | `raise value` shall require the function's exact E, terminate its invocation exceptionally, expire its locals, and have no intrafunction successor or normal result. Payload pointers shall retain existing lifetimes. |
| EXC-003 | `invoke`/`invoke_indirect` shall require a raising callable and terminate their block with explicit normal and exceptional edges. Plain calls shall reject raising contracts even if an invocation is proven to return normally. |
| EXC-004 | The normal invoke edge shall supply ordered callee results followed by written edge operands; the exceptional edge shall supply one E followed by written edge operands. Each complete edge shall exactly match its destination parameters. |
| EXC-005 | Invoke outcome values shall have no source SSA binding and shall become available only as destination parameters on their selected edge. Explicit edge operands shall be available at the source terminator. Both edges shall participate in reachability/dominance, including shared destinations. |
| EXC-006 | A caller handling its exception edge shall need no raised effect unless it itself propagates using `raise`. Reraising shall be an ordinary explicit payload transfer with no hidden exception object or resume state. |
| EXC-007 | Physical exceptional outcomes shall use ABI-defined discrimination/carriers/ownership and shall read only the selected outcome's carrier. Unsupported combinations shall be diagnosed. Native unwinding shall not be an implicit requirement. |
| EXC-008 | Frontends shall express required normal/exceptional cleanups as explicit CFG operations. SMIL shall not infer destructors, automatic cleanup stacks, native handler searches, or second-exception policies. |
| EXC-009 | Terminal faults and user traps shall not be caught by `invoke`. Foreign exceptions shall cross only a defined adapter translating to E; an unexpected exception at a non-raising boundary shall be contained and terminate with `invalid_foreign_transfer`, or the interface shall be rejected when enforcement cannot be established. |
| EXC-010 | Cross-invocation nonlocal exits shall use cooperative typed propagation with explicit intervening exceptional edges. Dynamically selected target markers shall be validated for lifetime and membership in the same agent's active chain before use; equality alone shall not establish validity. |
| EXC-011 | Ordinary calls shall not hide raw `setjmp`/`longjmp`, returns-twice semantics, saved-stack restoration, cross-agent stack transfers, or entry into expired invocations. Such interfaces shall be adapted to cooperative transfers or rejected. |

## Required conformance observations

| Case | Required outcome |
| --- | --- |
| Matching logical signature but different ABI/raised/variadic attribute | Incompatible declaration/reference. |
| Null indirect target with exhausted stack | `invalid_call`, without entering a callee. |
| Out-of-bounds `va_is` versus `va_get` | Zero versus `invalid_variadic_access`. |
| Large unsigned variadic index whose low machine bits are valid | Full index used; no masked retrieval. |
| Forwarded typed pack | Exact ordered values/types preserved in a distinct live callee pack. |
| Invoke normal/exceptional outcomes and explicit trailing operands | Only selected prefix delivered; all destination bindings simultaneous. |
| Returned local pointer, including one inside a raised record | Target expires at invocation completion. |
| Terminal divide fault inside an invoked function | Instance terminates; exceptional destination is not selected. |
