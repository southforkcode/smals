# SMIL Pointers and Ordinary Memory

- Define object association, normalized address equality, checked byte arithmetic, and typed access.
- Preserve lifetime, initialization, and permissions through copies and explicit conversions.

## Sources

- [Guide — Pointers and Memory Access](../docs/Guide_SMIL.md#pointers-and-memory-access) and [Type Casts](../docs/Guide_SMIL.md#type-casts).
- [Aggregates](0003_constants_and_aggregates.md), [devices/atomics](0008_devices_and_atomics.md), [checked execution](0009_checked_execution.md), and [target contracts](0010_targets_layout_and_abi.md).

## Requirements

| KEY | Requirement |
| --- | --- |
| PTR-001 | A data pointer shall have a declared space and pointee type. A non-null associated pointer shall identify an allocation/external region, byte position, and applicable restrictions. Association may be implemented by proof or metadata but shall not be fabricated from arbitrary bits. |
| PTR-002 | Each live local allocation and each distinct global shall have distinct allocation identity. Inline fields shall share their root allocation identity/extent. Physical address reuse shall not revive an expired association. |
| PTR-003 | A profile-declared external region shall specify identity, extent, lifetime, permissions, access kind, and typed subobjects. A numeric address or address-space name alone shall establish none of these properties. |
| PTR-004 | For positive allocation size L, associated byte arithmetic shall permit positions `[0,L]`, with L one-past and never dereferenceable, including for empty-record access. For a supported zero-sized allocation, offset zero shall be its object position and only zero-delta arithmetic shall be permitted, without a distinct one-past position. |
| PTR-005 | A field derivation shall retain the enclosing allocation's bounds rather than restrict arithmetic to that field. Typed view rules shall still prohibit invented subobjects or crossing into another allocation. |
| PTR-006 | Pointer copies, casts, arithmetic, comparisons, and space mappings shall not initialize storage, extend lifetime, change underlying mutability, or increase permissions. Address-only pointers shall permit only contract-defined copy/comparison/conversion, not arithmetic, field selection, or access. |
| PTR-007 | Typed null shall never designate an object. Its logical value shall be usable unbound; stored encoding shall be supplied by the profile. Numeric zero shall not implicitly be null. |
| PTR-008 | `ptr_eq`/`ptr_ne` shall require matching resolved pointer types and return complementary `i1`. Null shall equal only null; non-null equality shall compare normalized address positions including required bank/segment components, independently of identity/rights. |
| PTR-009 | Equality shall not dereference or test target lifetime and shall remain defined for complete pointer values after expiration. Equal addresses shall not authorize substitution of different associations. No ordering of unrelated allocations shall be implied. |
| PTR-010 | `ptr_offset base delta` shall interpret the complete integer delta as signed two's complement, add it mathematically to a live associated position, and preserve pointer type/space/association/restrictions. It shall neither scale by pointee size nor truncate/wrap the delta. |
| PTR-011 | `ptr_offset` shall fault with `invalid_pointer_operation` for null (including plus zero), expired/address-only bases, out-of-extent results, or unrepresentable positions. One-past may move back in bounds; unaligned formation itself shall be permitted. |
| PTR-012 | `ptr_diff [iM] left right` shall require matching pointer types and two live positions in one allocation, including one-past; it shall return the signed byte difference `left_offset-right_offset` or fault if its signed iM range/domain is violated. Equal addresses of different allocations shall not suffice. |
| PTR-013 | `field_addr` shall satisfy AGG-006/007, including actual record boundary/type checks before any result. Null-base offset idioms shall be rejected as constant expressions or fault at runtime; layout-only selection shall use `offsetof`. |
| PTR-014 | `ptrcast [ptr S [U]] p` shall require the same space and compatible representation and change only the pointee view, retaining location, association, restrictions, and null/expired state. It shall not establish validity, alignment, type conversion, or new subobjects. |
| PTR-015 | `addrspacecast` shall require different spaces, equal resolved pointees, and an explicitly supported ordered profile mapping. Null shall map to typed destination null. A non-null source shall require a live associated location covered by that mapping. |
| PTR-016 | A successful space mapping shall preserve object/position and intersect source/destination permissions while translating representation. Out-of-domain/unrepresentable/expired/address-only inputs shall fault with `invalid_pointer_operation`. Unsupported pairs shall be binding errors. Converting back shall not restore attenuated rights or change access kind. |
| PTR-017 | `ptrtoint`/`inttoptr` shall be supported only for explicit ordered type-pair contracts defining widths/spaces, numeric domain/encoding, null mapping, association reconstruction, pointer and integer round trips, state dependence, and all runtime failures. Equal storage sizes shall not imply support. |
| PTR-018 | A promised non-null pointer round trip shall preserve the same live allocation, position, usable permissions, and representation state, not merely equal address bits. The contract shall cover or exclude one-past/adjacent ambiguity and require continued liveness. |
| PTR-019 | An integer round trip shall yield exact bits unless the contract specifies normalization. Integer SSA shall not carry hidden association history. Arithmetic on converted integers shall remain modular arithmetic, with no extension of reconstruction guarantees to changed values. |
| PTR-020 | An unsupported conversion form shall be rejected; a supported form outside its dynamic value domain shall cause `invalid_pointer_operation`. Successful address-only conversion shall not authorize subsequent access. |
| MEM-001 | `load [T] p` shall require p:`ptr S [T]`; `store p v` shall require v of p's resolved pointee type. Each access shall require live association, valid extent/type view/alignment, object/view/space/region permissions, matching access kind, and lifecycle readiness. Reads shall additionally require initialized value bits. |
| MEM-002 | Integer views shall fit wholly within one actual integer object's/leaf's representation bytes, including permitted smaller interior-byte views. They shall not span fields, include padding, or inspect data-pointer/function-reference encodings. Stores shall update only their requested integer representation bytes without changing declared type. |
| MEM-003 | Pointer/callable loads and stores shall target actual matching typed leaves. Record access shall target an actual object/subobject of that nominal record type. Equal byte layouts or a `ptrcast` shall not authorize reinterpretation of unrelated records/references. |
| MEM-004 | Integer views shall use the selected byte order and requested N-bit encoding. Typed stores shall clear unused high representation bits and preserve neighboring independently accessible values; loads shall ignore high bits outside N. Allocation padding shall not be interpreted. |
| MEM-005 | Different pointee types and space names shall not prove disjointness. Independence proofs shall use actual allocation/range relationships and explicit profile alias guarantees. |
| MEM-006 | Ordinary access expansion/combination shall preserve source footprints, validity, fault priority, initialization, and concurrency. It shall not add reads or read/modify/writes to neighboring independently accessible fields even if their eventual values would match. |
| MEM-007 | `load_unaligned`/`store_unaligned` shall be limited to ordinary integer views, with ordinary type/range/encoding/initialization/permission rules and byte alignment only. They shall reject records, pointers, callables, MMIO, and atomic forms. |
| MEM-008 | An unaligned access may split into byte accesses without atomicity/stable-snapshot promises, but shall not touch bytes outside its requested representation range. Native unaligned instruction availability shall not weaken ordinary aligned-access requirements. |
| MEM-009 | Invalid null/expired/unassociated/one-past/range/view/alignment/permission/access-kind accesses shall cause `invalid_storage_access` before the memory action. Aggregate preflight shall cover all affected fields before a write. Stage-selected readiness/initialization/race/resource faults shall follow [0009](0009_checked_execution.md). |
| MEM-010 | Verifiers shall reject statically known immutable-target/access-kind mismatches through aliases, field derivations, offsets, casts, and supported mappings. Invalid static paths/types/forms shall be diagnostics; otherwise supported execution-dependent invalid values shall use runtime faults. |
| MEM-011 | Checks may be omitted only when validity is established for every reached use. Missing runtime support shall cause rejection rather than unchecked host-language behavior. Potentially faulting unused pointer/access operations shall retain their terminal-event behavior. |

## Required conformance observations

| Case | Required outcome |
| --- | --- |
| i16 `0x1234` accessed as first i8 view | `0x34` little-endian; `0x12` big-endian. |
| i1 load from initialized byte `2` | Zero, not nonzero normalization. |
| i1 pointer delta with bit one | Signed -1 byte. |
| Form one-past, compare to adjacent start, dereference | Formation/equality permitted; dereference invalid; association not transferred. |
| Expired pointer compared after frame reuse | Address equality defined; arithmetic/access still invalid. |
| Byte arithmetic back to actual enclosing record boundary | Field selection allowed after a matching cast and remaining checks. |
| Integer view spans two fields or pointer bits | Invalid typed view. |
| Byte-aligned i16 view inside i32 at offset one | Unaligned form allowed; ordinary form requires layout alignment. |
| Read-only view mapped out and back | Write rights remain absent. |
