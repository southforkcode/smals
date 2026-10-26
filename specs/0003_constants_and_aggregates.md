# SMIL Constant Evaluation and Aggregate Values

- Define complete record values, static field selection, and layout queries.
- Define constant evaluation and symbolic addresses without executing SMIL functions.

## Sources

- [Guide — Constant Initializers and Symbolic Addresses](../docs/Guide_SMIL.md#constant-initializers-and-symbolic-addresses), [Aggregate Values and Operations](../docs/Guide_SMIL.md#aggregate-values-and-operations), and [Constant Pointer Operations](../docs/Guide_SMIL.md#constant-pointer-operations).
- [Types](0002_types_and_storage.md), [memory](0007_pointers_and_memory.md), and [target layout](0010_targets_layout_and_abi.md).

## Requirements

| KEY | Requirement |
| --- | --- |
| AGG-001 | A record SSA value shall contain a complete defined value for every field. Pointer fields shall hold pointer values rather than copies of their target objects; construction/copy shall not dereference those targets. |
| AGG-002 | A field path shall be a nonempty list of zero-based nonnegative decimal indices. Each index shall select an existing field; each intermediate field shall resolve to an inline record. Empty, negative, out-of-range, dynamic, or pointer-traversing paths shall be statically rejected without wrapping indices. |
| AGG-003 | `record_make [R] (values)` shall require a record type and exactly one exact-type operand per field in declaration order. It shall produce one R value without addressable allocation. An empty record shall require an empty operand list. |
| AGG-004 | `record_get value field(path)` shall require a record value and return the selected field's type/value without storage access or source mutation. A pointer/global symbol shall not substitute for the record value. |
| AGG-005 | `record_set value field(path) replacement` shall require an exact selected-field type and return a new value with the source's nominal type, the selected field replaced, and every other field unchanged. It shall not mutate the source or storage. |
| AGG-006 | `field_addr p field(path)` for `ptr S [R]` shall return `ptr S [F]` for the selected F, using the resolved cumulative field offset. It shall preserve allocation identity, extent, lifetime, permissions, and address space without reading/initializing any field. |
| AGG-007 | A `field_addr` base shall identify the start of a live actual R subobject. Null, expired, one-past, address-only, wrong-type, and non-boundary bases shall cause `invalid_pointer_operation` before a result. An uninitialized actual R object shall be a valid base. |
| AGG-008 | A typed record load shall read every logical leaf and produce one complete record. Any required uninitialized value bits shall cause `uninitialized_read` before any result. Loading a partial record and subsequently extracting a written field shall still fault at the load. |
| AGG-009 | A complete record store shall establish all field values recursively. A field store shall initialize only that field, including its complete inline descendants. Sibling fields and padding shall not acquire initialization through that store. |
| AGG-010 | Record access shall validate all affected ranges, permissions, readiness, initialized reads, and other applicable stages before exposing a result or changing a destination field. It shall preserve embedded pointer/callable representation state and shall not imply aggregate atomicity or aggregate MMIO. |
| AGG-011 | Record/integer allocation padding shall not be logical value data; typed loads shall not require its initialization and typed stores shall not promise its contents/preservation. Inline immutability shall not recursively make pointed-to objects immutable. |
| AGG-012 | `sizeof [iM] [T]` shall return allocation size, `alignof [iM] [T]` required alignment, and `offsetof [iM] [R] field(path)` cumulative inline offset, all in bytes. They shall require supported layouts, use the same layout as storage access, and perform no runtime memory access. |
| AGG-013 | Layout results shall be nonnegative mathematical quantities fitting the unsigned result width. Invalid paths shall be rejected structurally; unsupported layouts and unrepresentable results shall be rejected at binding without truncation. Unbound numeric results shall remain unresolved. |
| CST-001 | A constant initializer shall be a typed scalar/null, named constant, global symbolic address, function-address expression, complete record initializer, recursive record-zero initializer, or permitted constant expression. It shall have the required resolved type with no implicit conversion or content load. |
| CST-002 | `[R { fields }]` shall supply every exact-type field once in order, with actual nested nominal types and no omitted defaults. It shall construct a value without separate storage. Outside local declaration initializers its components shall all be constants. |
| CST-003 | `[R zero]` shall recursively construct integer-zero fields, typed data/callable null fields, and inline record-zero fields. Recursion shall stop at references and allocate no targets. It shall require a record type and shall not mean zeroing representation/padding bytes. |
| CST-004 | Local record initializers shall recursively accept already available values and constants under TYP-013. Ordinary runtime record construction shall use `record_make`; local syntax shall not permit loads, calls, later SSA values, or SSA operands in parenthesized constant expressions. |
| CST-005 | Parenthesized constant operations shall have no SSA binding and shall be limited to the operations in the allowed-operation table below. Every operand shall itself be constant; optimization knowledge shall not make an SSA operand a constant expression. |
| CST-006 | Constant operands shall evaluate eagerly in written order, including every record component even when a later operation extracts only one field. A fault in any required operand shall cause static rejection; no lazy/short-circuit evaluation shall be inferred. |
| CST-007 | Integer/record constant evaluation shall use runtime typing and mathematical semantics, including modular overflow. Layout-independent expressions may evaluate unbound; layout/encoding-dependent expressions shall remain symbolic until binding. |
| CST-008 | Required constant evaluation shall produce a defined value without any arithmetic/pointer fault. Failure shall be a compilation or binding diagnostic, with no startup execution, substitute value, or runtime fault-handler invocation. |
| CST-009 | A symbolic global address shall depend on its declaration/type, not its initializer contents. Named-constant dependencies, including all nested/eager operands, shall be acyclic; cyclic symbolic addresses between distinct globals shall remain permitted. |
| CST-010 | Constant `field_addr` shall retain an identified global allocation and actual inline subobject selection through binding and relocation, including its space and immutable restrictions. Null/numeric bases and casts fabricating a different record shall be rejected. |
| CST-011 | Symbolic `ptr_offset` shall remain within the identified allocation's bound extent and supported relocation model. Symbolic `ptr_diff` shall use the same allocation and a representable signed difference; no final link address shall be required to compute that difference. |
| CST-012 | Constant pointer equality shall be accepted only when its result is decidable without unresolved final placement, including null comparisons or positions of one allocation. A comparison depending on adjacency of distinct globals shall be rejected as a constant expression. |
| CST-013 | Constant `addrspacecast` shall require a supported symbolic mapping/relocation preserving association and restrictions. A runtime-only mapping shall not suffice. Constant `ptrcast` shall retain ordinary same-space representation requirements. |
| CST-014 | Constant `ptrtoint`/`inttoptr` shall require complete numeric evaluation under the bound profile without unresolved final global addresses. Symbolic integer-address relocations, arbitrary arithmetic on unresolved addresses, and arbitrary linker-side expression evaluation shall be rejected. |
| CST-015 | Constant `fnaddr` shall identify a declared function without executing its body. Constant `fn_eq`/`fn_ne` shall require resolved function identity independent of unresolved interposition/placement. Code/data casts and numeric code-address constants shall remain unsupported. |
| CST-016 | Verifiers shall reject invalid record operand kinds/counts/types, replacements, initializers, field paths, known immutable subobject stores, and unsupported constant operations. A statically invalid field path shall not be deferred as a runtime pointer fault. |

## Allowed constant operations

CST-005 incorporates this closed set. All are single-result forms; operand-specific restrictions still apply.

| Category | Operations |
| --- | --- |
| Integer | `add`, `sub`, `mul`, `neg`, `udiv`, `urem`, `sdiv`, `srem`, `xor`, `and`, `or`, `not`, `shl`, `lshr`, `ashr`, `cmp`, `sext`, `zext`, `trunc` |
| Aggregate/layout | `record_make`, `record_get`, `record_set`, `sizeof`, `alignof`, `offsetof` |
| References | `fnaddr`, `fn_eq`, `fn_ne`, `ptrcast`, `field_addr`, `ptr_offset`, `ptr_diff`, `ptr_eq`, `ptr_ne`, `addrspacecast`, `ptrtoint`, `inttoptr` |

Loads, stores, allocations, calls, control flow, MMIO, atomics, fences, and pair-result carry/overflow operations are excluded even if a particular use has no observable memory effect.

## Required conformance observations

| Case | Required outcome |
| --- | --- |
| Replace an inline nested field | New record differs only at that path; old record unchanged. |
| `field(2, 0)` where field 2 is a pointer | Static rejection, without implicit dereference. |
| Store one of two fields, then load whole record | `uninitialized_read`; loading the stored field directly succeeds. |
| Record zero with nonzero target null encoding | Typed nulls installed using that encoding. |
| Constant `srem [i8] [i8 -128] [i8 -1]` | Zero; no quotient-overflow fault. |
| Eager record component faults but extracted sibling is valid | Constant initializer rejected. |
| Mutually referencing global addresses versus mutually dependent named values | Address cycle accepted; value cycle rejected. |
