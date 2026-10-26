# SMIL Modules and Published Interfaces

- Specify exact module ownership, explicit visibility, and nominal type identity across compilation units.
- Define reproducible interface fingerprints and import locks.

## Sources

- [Guide — Modules, Interfaces, and Static Linking](../docs/Guide_SMIL.md#modules-interfaces-and-static-linking), especially Module Headers, Visibility, Nominal Identity, Compatibility Fingerprints, and Serialized Types/Constants.
- [Source grammar](0001_source_syntax.md), [types](0002_types_and_storage.md), [canonical JSON](0011_checked_reference_profiles.md), and [object transport](0013_objects_and_static_linking.md).

## Requirements

| KEY | Requirement |
| --- | --- |
| MOD-001 | A module shall be the unit of source ownership, separate compilation, and lifecycle registration. Its publishable source shall begin with one explicit nonempty NUL-free UTF-8 identity string, before target/imports. Identity shall compare exact decoded scalar sequences, without case/path/Unicode normalization, filename inference, or version-range resolution. |
| MOD-002 | Version 1 shall have one independently generated object per module identity. Multiple implementation fragments shall be combined and checked before object publication. Two selected implementations with the same identity shall be an error even with matching exports. Distinct library versions shall require distinct module identities. |
| MOD-003 | Build configuration shall map each import identity to an exact interface/implementation. Imports shall precede other module items and shall only expose verification interfaces; importing shall neither execute code nor initialize storage. |
| MOD-004 | Import aliases shall be unique ordinary-name qualifiers; self-import and repeated aliases shall be rejected. Multiple different aliases of one provider shall denote the same entities. Qualifiers shall form a separate namespace and shall not be shadowed within `alias::member` by local type names. |
| MOD-005 | Imports shall expose only the provider's explicit exports through the chosen qualifier, with no unqualified injection, transitive exposure, wildcard, public rename, or re-export. A client naming another owner's export shall import that owner directly. |
| MOD-006 | All local definitions shall be private unless explicitly exported by `export type Name`, `export $name`, or `export @name`. Each export shall name a current-module definition; unresolved function declarations, duplicate exports, wrong-kind selections, and imported entity re-exports shall be rejected. An exported alias may refer to an imported type while retaining its identity. |
| MOD-007 | A local function declaration shall describe a function owned by this module and shall not search other modules by spelling. Imported symbols shall use their pinned qualified declarations and shall not be redeclared locally as the same entity. Ambient native/global name lookup shall not apply. |
| MOD-008 | Source symbol keys shall be canonical JSON triples `[module_identity, namespace, local_name]`, with namespaces `type`, `constant`, or `value` and function/global kind separately recorded. Aliases/sigils shall not become part of canonical names. Private machine labels shall use `aux` and have no source export/address. |
| MOD-009 | Definitions shall be unique by canonical key/kind. Weak/common/tentative definitions, first-definition wins, interposition, COMDAT, and implicit native-name fallback shall be absent. Selected required function declarations shall resolve to exactly one compatible definition. |
| MOD-010 | Imported globals shall expose actual type, space, mutability, and initialization mode. Clients shall not strengthen rights, redeclare mutability, or treat a not-ready immutable dynamic object as a compile-time value. |
| IDN-001 | Module record identity shall be `["record", module_identity, "module", declaration_name]`; function-local identity shall be `["record", module_identity, "function", owning_function_name, declaration_name]`. Imported records shall retain their owner's identity; local records shall not escape module contracts. |
| IDN-002 | Compatibility shall resolve transparent aliases, compare integers/pointers/callables structurally, retain record nominal identities and authoritative fields, and include callable order/attributes/variadic/raised/ABI properties. Matching record layout alone shall not establish equality. |
| IDN-003 | A published interface shall include the complete finite type graph reachable through its exports, including pointer fields, private module-level records in the public closure, callable/raised types, and constant values. Version 1 shall have no implicit opaque-record boundary. |
| IDN-004 | Each nominal owner shall supply authoritative descriptors. Imported snapshots shall match the selected owner and shall not replace a missing owner. Comparison/key construction shall stop at nominal references to avoid infinite expansion; alias/by-value cycles shall remain invalid. |
| IDN-005 | Cyclic source imports shall be permitted when their finite interface closure resolves consistently. Such cycles shall neither imply lifecycle edges nor waive missing providers. Interface payloads shall not recursively embed provider digests; direct locks shall be separate. |
| IFC-001 | `smil.interface.v1` shall contain format, canonical logical payload, `interface_sha256`, and optional nonsemantic `notes`. Payload shall include module identity, target, export table, complete public type graph, normalized exported constants, and byte-sorted unique `requires_modules` foreign owners. |
| IFC-002 | Interface digest shall be canonical-JSON SHA-256 under REF-003. Exports shall sort by canonical `[namespace,name]` UTF-8 bytes. Bodies, private data outside the public closure, paths, timestamps, diagnostics, and build notes shall be excluded. Owner requirements shall not be lifecycle edges or recursively embedded digests. |
| IFC-003 | An unbound interface shall record `target:null` and deferred ABI token `default`. A bound interface shall record exact profile ID/digest, shared-contract digest, and resolved component IDs, resolving defaults and layout constants. Machine linking shall not accept an unbound fingerprint in place of a bound one. |
| IFC-004 | Source verification shall consume build-pinned identity-to-interface/digest mappings. Objects shall lock the exact bound digest of every direct import, including type-only/constant-only imports, plus foreign owners introduced by expanded public graphs/constants. Added locks shall not add source qualifiers. |
| IFC-005 | A selected link shall match every locked whole-interface digest. Changes to exported values/types/storage/effects/profile shall invalidate old locks; private body changes with identical canonical interfaces shall not require client recompilation, but the build shall still pin/check the changed object digest. Digests shall not imply provider trust. |
| IFC-006 | Type labels shall derive from sorted canonical keys: integer `["integer",N]`, pointer `["pointer",space,pointee_key]`, record nominal identity, and callable key with ordered typed/attributed parameters/results, variadic flag, optional raised key, and ABI. Keys shall use no provisional label/runtime ID. |
| IFC-007 | Public type labels shall be `t` plus a zero-padded decimal ordinal of at least six digits beginning at one. Private types shall continue in sorted private-key order. Equal keys shall have one descriptor; conflicting definitions for one nominal key shall be rejected. |
| IFC-008 | Final catalogs shall distinguish a function-reference representation from its synthesized `["signature",callable_key]` and normal carrier `["tuple",ordered_result_keys]`. The borrowed `varargs` token shall not be an exported/storable descriptor. Private runtime carriers shall use exact contract-tagged runtime descriptors and shall not appear in source exports/ordinary globals. |
| IFC-009 | Exports shall record namespace, spelling, kind, type label, and value only for named constants; globals shall additionally record mutability/space/initialization mode. Alias exports shall point to resolved descriptors rather than create nominal types. |
| IFC-010 | Constant transport shall use the closed tagged forms below. Named-constant/alias references shall be expanded before publication. Expressions shall use only permitted constant operations, ordered arguments and valid paths, with unused argument/path arrays empty. |
| IFC-011 | Bound exported constants shall reduce to integer/null/record/address/function forms; remaining expressions shall indicate incomplete binding. Address forms shall retain root allocation/path through checked-pointer relocation, not become arbitrary numeric addresses. |
| IFC-012 | Public symbolic pointer/function constants shall reference explicitly exported target symbols of their owner. Exporting a constant shall not export a private target automatically. Private object initializers may reference owned private symbols; runtime-returned values may still identify private entities. |
| IFC-013 | Interface JSON shall reject invalid UTF-8/non-scalar strings, duplicate keys, floats, unknown semantic fields/enums/versions, and unresolved required contracts. Optional tool notes shall be confined to `notes`. Exact closed field shapes shall require the companion schema identified in [0000](0000_smil.md#unavailable-normative-inputs). |

## Constant wire forms

IFC-010 incorporates this table; type references are descriptor labels.

| Tag | Required contents |
| --- | --- |
| `integer` | Type and lowercase `0x` bits padded to exactly `ceil(N/4)` hex digits, with unused high bits zero. |
| `null` | Data-pointer or callable type; profile encoding applied later. |
| `record` | Actual nominal record type and ordered constant fields. |
| `address` | Pointer type, canonical global key, field-index path, canonical signed decimal extra byte offset. |
| `function` | Exact callable type and canonical function key. |
| `expression` | Result type, allowed opcode, ordered type arguments/operands, and applicable field path. |

## Required conformance observations

| Case | Required outcome |
| --- | --- |
| Provider imported under two aliases | Identical canonical symbols and nominal types. |
| Two same-layout records from different modules | Distinct nominal types. |
| Consistent mutually importing interfaces with recursive pointer records | Finite valid closure, no digest recursion. |
| Private symbol access or public address constant naming private target | Diagnostic. |
| Dependency interface changed versus private body only changed | Stale import lock rejected versus client interface remaining compatible with new object pin. |
| Identical source names with different owning module IDs | Distinct keys; no ambient collision. |
