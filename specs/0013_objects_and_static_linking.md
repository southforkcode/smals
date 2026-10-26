# SMIL Objects, Static Linking, and Images

- Specify deterministic relocatable object/library/link transport and checked relocation.
- Preserve ownership, complete runtime closure, lifecycle metadata, and final image provenance.

## Sources

- [Guide — Modules, Interfaces, and Static Linking](../docs/Guide_SMIL.md#modules-interfaces-and-static-linking) and [Relocation and Linked-Image Contract](../docs/Guide_SMIL.md#relocation-and-linked-image-contract).
- [Module/interface identity](0012_modules_and_interfaces.md), [reference profiles](0011_checked_reference_profiles.md), [execution metadata](0009_checked_execution.md), and [lifecycle](0014_program_lifecycle.md).
- [Unavailable closed schemas/private contracts](0000_smil.md#unavailable-normative-inputs).

## Requirements

| KEY | Requirement |
| --- | --- |
| OBJ-001 | `smil.object.v1` shall consist of a JSON descriptor and raw section blobs containing one owner module ID, bound target, embedded interface, all direct import locks/types/definitions/sections/references/relocations/continuations/runtime requirements/lifecycle nodes/user faults, and the checked execution metadata required by MET-001. |
| OBJ-002 | Each section shall record a unique local section ID, kind (`code`, `rodata`, `data`, `runtime`, or `metadata`), alignment, exact u32 byte length, relative blob path, and SHA-256 of exact bytes. No host structure packing/endian/compression/implicit zero-fill/executable relocation expression shall be inferred. Zero bytes for a reserved dynamic global shall not initialize it. |
| OBJ-003 | Descriptor paths shall be relative to the containing descriptor, use `/`, and reject absolute paths, backslashes, empty components, `.`/`..`, and symlink escapes. Descriptor digests shall cover canonical JSON; blob/segment digests shall cover exact bytes. Section sizes/positions shall be unsigned u32. |
| OBJ-004 | Relocation addends shall be canonical signed decimal strings without plus, leading zeros, or negative zero. All evaluation shall use mathematical integers. Unknown semantic fields/enums/formats/contracts, duplicate JSON keys, floats, malformed UTF-8, and non-scalar strings shall be errors; nonsemantic notes shall remain confined to `notes`. |
| OBJ-005 | Definitions shall record canonical key/kind/type as applicable, export visibility, section/offset/extent/alignment, and global space/mutability/initialization mode. A constant global shall carry its constant tree; a dynamic global shall have null tree and exactly one matching lifecycle node. Named source constants shall not be allocated definitions. |
| OBJ-006 | Functions shall locate their first instruction in code; globals shall identify distinct nonoverlapping allocations in data/rodata with exact bound type layout. Aux code/pool/metadata definitions may overlap an enclosing function extent. All section bounds/alignment shall be checked; relocated constant bytes shall encode their recorded logical initializer. |
| OBJ-007 | Every emitted semantic dependency shall have an explicit edge, including calls, fnaddr, global access, address constants, helpers, types, and machine labels. Relocations shall imply their targets; other dependencies shall be separate edges from the containing definition. Disassembly shall not substitute for missing producer metadata. |
| OBJ-008 | Cross-module references shall obey exports/import locks. Ordinary aux/section/continuation labels shall remain module-private. A cross-module aux helper shall require a validated runtime contract/binding, exact callable descriptor/opcode/ordered type and integer arguments. Specialization shall use symbolic type keys until final IDs. |
| OBJ-009 | Version 1 shall retain all definitions/sections of selected modules, including lifecycle-only content. Equal bytes shall not coalesce distinct addressable globals; linker code folding/definition coalescing shall be absent. Any later elimination extension shall prove all roots/edges/lifecycle/runtime dependencies and recompute catalogs/placement. |
| REL-001 | Relocations shall record kind, destination section/offset, target namespace/key, signed addend, and applicable PC anchor, slice/full-address domain, bitfield, pointer-construction, or callable information. Inapplicable optional slots shall be null rather than ignored extensions. |
| REL-002 | Targets shall distinguish canonical symbol keys, consuming-object type labels, continuation triples `[module,function,label]`, exact profile region keys, and `[module,section]` keys. Regions shall authorize pointers only when the profile establishes their associated storage/device identity. Private machine references shall not fabricate source pointers. |
| REL-003 | Every relocation shall follow the normative encoding table below, validate the full mathematical expression before extraction/encoding, and fit its destination bytes/field. Overflow, invalid target kinds, missing records, illegal masks, and unsupported relocations shall be diagnostics rather than dropped/truncated entries. |
| REL-004 | A PC anchor shall be an explicit position in a consuming-object section, allowing its end. Slice extraction shall require an explicit full-address domain. A bitfield shall specify signedness, bit count, destination bit offset, optional anchor, and positive power-of-two scale; the full expression shall be exactly divisible by scale and fit before insertion. |
| REL-005 | Relocation write masks shall not overlap except for disjoint bitfields in one instruction word. Branch relaxation/veneers shall occur before object publication or under an explicit link-time contract repeating placement, metadata, capacity, and relocation checks. |
| REL-006 | CHECKED_PTR shall retain root global/region, pointer type, field path, requested rights, and signed byte delta; validate real subobjects/full allocation extent including allowed one-past; and encode actual root ID, offset, coordinate, and intersected rights without wrapping. It shall not allocate another object. |
| REL-007 | FNREF shall require exact callable type and zero addend. ID32/RAW_ENTRY32 shall also require zero addend. ID32 shall name type/object/function/continuation namespace; RAW_ENTRY32 shall be private function/code-entry metadata, not permission for numeric source code pointers. |
| CAT-001 | After resolution/retention, canonical type keys and function keys shall be sorted by unsigned UTF-8 bytes of canonical JSON and assigned IDs from one. Continuation triples shall use that ordering; global canonical keys shall receive IDs from 16 with monitor 1 reserved. IDs shall not be stable source constants. |
| CAT-002 | Every ID-bearing location shall be rewritten/tracked, including helper specializations, callable signatures, statically materialized packets/descriptors, object root types, function refs, and lifecycle records. No provisional numeric ID shall be embedded untracked; profile-fixed constants shall be the explicit exception. Layout/ABI fingerprints shall be validated before byte writes. |
| LNK-001 | `smil.library.v1` shall map unique exact module identities to relative object paths, canonical object digests, and bound interface digests. It shall package providers rather than create a new definition namespace. `smil.link.v1` shall pin exact target, roots, available libraries, explicitly included modules, canonical entry, and additional retained keys. |
| LNK-002 | Roots and `include_modules` shall select modules unconditionally; every selected object's import locks shall recursively select exact providers until finite closure. Provider ambiguity/duplicate ownership shall fail. Selection shall be independent of input order and shall include type-only/constant-only imports. Unselected library entries shall contribute no lifecycle/code effects. |
| LNK-003 | Executable reference links shall explicitly select/pin runtime module `smil.rt.checked.packet.v2` like other inputs. A data-only fixture may omit it but shall not become executable without runtime and entry. No hidden host runtime shall be substituted. |
| LNK-004 | The designated canonical entry shall exist and satisfy the selected environment contract, for reference profiles local name `smil_main`, default-ABI fixed `() -> ([i32])`, non-raising. It may be private; retained-key designation shall neither export it nor conflict with equal private names in other modules. Every additionally retained key shall exist. |
| LNK-005 | All selected descriptors/blob digests/import locks/target identities shall validate; imported exports and authoritative type closure shall resolve; each required source/runtime symbol shall have one compatible definition. Checks shall apply to all selected content even if it might later be optimized away. |
| LNK-006 | The mandatory runtime shall bind each required private entry to its same-spelled aux definition with token `<contracts-id>#<entry-name>` and exact raw carriers/default packet ABI. `bootstrap`, `initialize`, `dispatch`, `request_exit`, `drain_callbacks`, and `fault` shall always exist; operation-dependent entries/helper specializations shall close. Contract `never` shall imply no result entries and nonreturning behavior. |
| LNK-007 | Runtime aux `bootstrap_entry` shall be an untyped first-native-entry shim establishing reserved context/initial packet before entering typed bootstrap with image metadata. It shall not be source callable. Native foreign code shall require an explicit checked adapter published as a conforming `smil.object.v1`; native container readers shall require a separate transport contract. |
| LNK-008 | The selected lifecycle graph shall resolve/validate before execution, retaining every selected node regardless of call reachability. Dependency on an unselected module's node shall be an error, not implicit archive discovery. |
| LNK-009 | Sections/catalogs/globals/native/software/runtime/callback/tracking storage shall fit aligned permitted regions and exact declared capacities/ID ranges. A capacity shall not silently expand into another region. Static failure shall be a diagnostic before a final executable image is published. |
| LNK-010 | After complete contract/closure/lifecycle/placement/catalog checks and checked relocations, linking shall emit final raw segments and image metadata. A target header edit shall not retarget machine objects; dependent code/layout/interfaces shall be regenerated. |
| LIFM-001 | Every dynamic global/startup declaration shall contribute one lifecycle record with the fields below. Constant globals shall have no nodes. Global definitions/nodes shall agree one-to-one; actual factory/hook/callback contracts and supported ABI shall validate, with callback ABI obtained from its own descriptor. |
| LIFM-002 | `after` strings shall remain absolute program-wide IDs, not alias-rewritten/module-prefixed names. Prerequisites shall be unique and byte-sorted. Duplicate nodes, missing dependencies, self-dependencies, and cycles shall fail before startup. |
| LIFM-003 | Final `initialization_plan` shall use Kahn's topological order choosing the byte-smallest ready decoded UTF-8 ID, contain complete resolved records with final object/action/signature/callback/type IDs, and retain dependency IDs for validation. A serialized node shall not authorize duplicate initialization. |
| IMG-001 | The `smil.ref.image.v1` descriptor shall retain required top-level format/profile/digests/entry/segment/initialization/user-fault fields and contain catalogs `types`, `objects`, `functions`, `continuations`, `modules`, and `link`. Provenance shall reside within catalogs rather than silently changing profile digests. |
| IMG-002 | Module records shall pin selected interface/object digests. One link record shall pin link-manifest digest, exact component IDs, and contract `smil.link.v1`. Complete interface/type descriptors shall remain available for validation; retained target runtime tables shall agree with host descriptors. |
| IMG-003 | Catalog type references shall be ordered field IDs for records/tuples, one pointee ID for pointers, one signature ID for function refs, and empty for integer/runtime carriers. Signatures shall separately carry parameter/result/raised references. Inapplicable nullable fields shall be null, arrays empty, and variadic false. |
| IMG-004 | Internal signatures shall have no stored value (representation/allocation zero, alignment one). Empty result tuples shall occupy zero bytes, unlike source empty records. Runtime-private descriptors shall carry exact runtime-contract identity. |
| IMG-005 | User fault identifiers shall be deduplicated/sorted bytewise and assigned IDs from 65536, preserving built-in IDs. Final catalogs/plans shall contain final IDs rather than local labels. |
| IMG-006 | Before entry, the loader shall validate selected module/object/contract identities, segment byte digests/region bounds, catalog references/entries/signatures, and regenerated topological order, then install already linked segments and transfer in the required CPU/native-stack state to bootstrap. Failed checks shall prevent execution rather than become catchable runtime faults. |
| IMG-007 | The loader shall perform no symbol resolution, nominal merging, relocation, constructor discovery, or factory execution as a loading expression. Off-device validation/install shall be permitted for small monitors when exact target state/segments remain the same. Host-only metadata shall not be charged as RAM; actual runtime tables shall be placed/charged. |

## Relocation encoding

REL-003 incorporates these encodings.

| Kind | Required evaluation/encoding |
| --- | --- |
| ABS8/16/32 | Full address plus addend, unsigned width check, target-endian storage. |
| SLICE8/16 | Validate complete address/domain, then select the stated significance slice. |
| PCREL8/16/32 | Target plus addend minus explicit PC anchor, signed width check, target-endian storage. |
| CHECKED_PTR | Validated allocation-relative construction in the 16-byte pointer encoding. |
| FNREF | Function ID plus exact signature ID in eight bytes. |
| ID32 | Nonzero final ID in the explicitly named namespace. |
| RAW_ENTRY32 | Normalized native-entry coordinate; native translation occurs at transfer. |
| BITFIELD32 | Checked scaled signed/unsigned expression inserted into a contiguous field in a four-byte target-endian instruction word, preserving other bits. |

## Lifecycle wire fields

LIFM-001 incorporates these fields.

| Field | Required contents |
| --- | --- |
| `id`, `kind`, `owner_module` | Exact initialization string, `global` or `startup`, owning module ID. |
| `object` | Owned global key for global nodes; null for startup. |
| `action`, `after`, `shutdown` | Canonical factory/hook key, unique sorted prerequisite IDs, canonical callback key or null. |
| `result_type`, `raises_type`, `abi` | Global result label or null for startup; action raised label or null; exact resolved action ABI. |

## Required conformance observations

| Case | Required outcome |
| --- | --- |
| Provider/library order permuted | Same selected closure, catalog identities, and initialization order. |
| Duplicate provider, stale import, private foreign aux access, missing owner/helper/runtime | Link diagnostic. |
| Escaping/malformed path, wrong raw digest, relocation overflow/overlap/scale | Diagnostic before image publication. |
| Symbolic cross-module field pointer or function reference | Exact exported identity, rights/type, final IDs, and relocation preserved. |
| Startup-only included module | Retained node executes in graph order without dummy callable export. |
| Missing/cyclic node or mismatched callable/ABI/effect | Diagnostic before any initializer. |
| Smallest-target capacity exceeded | Diagnostic for fixed image requirements; no wrapping placement. |
| Corrupt final image/catalog/provenance/plan | Loader rejects before native bootstrap. |

Conformance shall cover little- and big-endian images and at least two profiles with different layouts. A declaration match alone shall not establish machine-byte/runtime conformance.
