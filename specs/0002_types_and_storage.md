# SMIL Types and Storage Entities

- Define type identity, literal values, scopes, and storage lifetimes.
- Distinguish SSA values, named constants, and mutable/immutable objects.

## Sources

- [Guide — Names, Types, and Literals](../docs/Guide_SMIL.md#names-types-and-literals), [Data Entities](../docs/Guide_SMIL.md#data-entities), and [Custom Data Types](../docs/Guide_SMIL.md#custom-data-types).
- [Source syntax](0001_source_syntax.md), [constants](0003_constants_and_aggregates.md), [memory](0007_pointers_and_memory.md), and [layout](0010_targets_layout_and_abi.md).

## Requirements

| KEY | Requirement |
| --- | --- |
| TYP-001 | `%name`, `$name`, `@name` in a value position, bare type names, profile-defined space names, and `^name` shall resolve respectively to function-local SSA, module constants, module functions/globals, types, spaces, and function-local blocks. Qualified imports shall follow [0012](0012_modules_and_interfaces.md). |
| TYP-002 | Type and value namespaces shall be separate. Functions and globals shall share one module value namespace and shall not have the same name. SSA and block names shall each be unique in their separate function namespaces; constants shall be unique per module; type binders shall be unique per type scope. |
| TYP-003 | Module types/constants/functions/globals and block labels shall permit forward references subject to resolution, dependency, and dominance rules. Repeated compatible function declarations shall be the only permitted repeated declarations of the same entity. |
| TYP-004 | `[T]` shall denote a type; a typed literal shall denote a value of its resolved type without creating addressable storage. Operation-specific typing shall determine operand/result types, with no implicit integer, record, pointer, or truncating conversion. |
| TYP-005 | `iN` shall represent an N-bit signless pattern for every positive mathematical width N in unbound SMIL. Individual operations shall select signed/unsigned interpretation. `i1` shall contain exactly the patterns zero and one. Target support limits shall be checked separately. |
| TYP-006 | A nonnegative `iN` literal shall be less than `2^N`; a negative literal shall be at least `-2^(N-1)` and encoded in N-bit two's complement. Out-of-range literals shall be rejected without truncation; `[i8 255]` and `[i8 -1]` shall have equal bits. |
| TYP-007 | Each SSA definition shall introduce a fresh immutable typed binding. Loop execution may produce new dynamic bindings from one static definition; it shall not permit identifier reassignment. SSA values shall have no SMIL-visible addresses or prescribed physical register. |
| TYP-008 | Function parameters shall be entry-block parameter definitions, rather than separate bindings in the signature. Operation and `alosf` results shall become available only after their definition; all uses shall satisfy [0006](0006_control_flow_and_ssa.md). |
| TYP-009 | Changing storage shall not change an SSA value previously loaded from it. Scope shall govern name visibility independently of the lifetime of the runtime binding/allocation. |
| TYP-010 | Each `alosf` shall declare one local object and produce `ptr data [T]`. It shall occur only after entry-local types and before ordinary entry operations, with no ordinary operations between local declarations. |
| TYP-011 | Each processed local declaration shall create a distinct allocation for its invocation, including recursive invocations. Its lifetime shall begin at declaration and end on return, raise, or abandonment. A retained pointer shall not extend that lifetime. |
| TYP-012 | Mutable `alosf` shall permit an optional initializer; absence shall establish uninitialized storage. Immutable `alosf` shall require a complete initializer and prohibit later writes through every alias. The resulting pointer shall remain an immutable SSA value in both cases. |
| TYP-013 | Local declarations shall initialize in declaration order using the exact object type. Initializer inputs shall be constants, entry parameters, earlier available declaration results, or complete nested local record initializers; the declaration's own result and later definitions shall be unavailable. No load, call, or arbitrary executable expression shall be implied. |
| TYP-014 | Local sizes/alignment shall follow the resolved layout and frame contract. Logical storage shall belong to the invocation frame; core declaration order alone shall not require physical order unless a selected ABI imposes it. |
| TYP-015 | Each global definition shall establish one distinct addressable object shared by referencing invocations until program termination. Invocation shall not recreate/reinitialize it. Its symbol shall have type `ptr S [T]`, with `data` selected when `space(...)` is omitted. |
| TYP-016 | Every mutable or immutable global shall have an explicit exact-type constant initializer or the dynamic-factory form in [0014](0014_program_lifecycle.md). Dynamic storage shall not receive an implicit zero value. Placement shall permit its required construction and access. |
| TYP-017 | Mutable globals shall permit subsequent valid writes; immutable globals and their inline subobjects shall prohibit subsequent writes through any alias. Construction by declaration/loader/coordinator shall not authorize ordinary immutable stores. |
| TYP-018 | Global allocation, content readiness, and finalization shall be distinct states. Content access shall follow lifecycle readiness rules; storage visibility/lifetime shall imply neither atomicity nor synchronization nor device semantics. |
| TYP-019 | `$name = const initializer` shall define one immutable typed value inferred from its constant initializer, without an addressable object or source-visible allocation. A pointer-valued constant shall not make its target immutable. |
| TYP-020 | Module-local types shall be visible throughout their module; function-local types shall be confined to the declaring function and shall not escape through any module declaration or function contract, directly or indirectly. Local types shall be static declarations, not new identities per invocation. |
| TYP-021 | A local type may shadow a module type; built-in type names shall not be redefined. Local type declarations shall precede all local storage declarations and shall allocate no storage. |
| TYP-022 | `@A = type [T]` shall be a transparent alias interchangeable with T after resolution, retaining T's layout and identity. Cycles consisting solely of transparent aliases shall be rejected. Aliasing `varargs` shall not make it storable or escapable. |
| TYP-023 | `ptr [T]` shall equal `ptr data [T]`. Address space and resolved pointee shall participate in pointer type identity; different spaces shall remain distinct even with equal encodings. Pointer width shall not be inferred from pointee width. |
| TYP-024 | Each record declaration shall create one nominal type with ordered zero-based fields. Equal field lists shall not make distinct declarations interchangeable. Aliases/imports shall preserve the originating identity. A record type declaration shall not create a value or object. |
| TYP-025 | Recursive type references shall be permitted only when every storage-containment cycle is broken by a data pointer or function reference. Direct/indirect by-value cycles shall be rejected. Callable signature references shall not count as inline storage fields. |
| TYP-026 | A record's name and later type declarations in its scope shall be available when resolving recursive definitions. Finite layout shall not imply that an object fits a particular target. |
| TYP-027 | Function symbols shall not be data pointers or ordinary function values. `fnaddr` shall construct callable references under [0005](0005_functions_and_calls.md); globals shall not be callable. |
| TYP-028 | A verifier shall reject duplicates, unresolved/wrong-kind names, missing required initializers, mismatched initializers/operands, invalid declaration placement, and unavailable SSA inputs. Known immutable stores shall be rejected even through transparent pointer derivations. Dynamic violations shall use the defined execution faults. |

## Required conformance observations

| Case | Required outcome |
| --- | --- |
| Two records with identical fields; an alias of either record | Records distinct; alias identical to its underlying record. |
| Self/mutual recursion through pointers; by-value recursive record; alias-only cycle | First accepted; latter two rejected. |
| Recursive calls with locals | Distinct live local objects; returning one invocation expires only its locals. |
| Reused physical bytes for an uninitialized local | New allocation starts uninitialized. |
| Immutable inline field reached through a cast/offset/space mapping | Mutation remains prohibited. |
| Address of `$constant` versus pointer-valued `$constant` used to access its target | Constant has no address; stored pointer value can identify its separately declared target. |
