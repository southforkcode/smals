# SMIL Target Binding, Data Layout, and ABI Contracts

- Define target selection and reproducible binding without development-host defaults.
- Specify deterministic storage and physical call-boundary obligations.

## Sources

- [Guide — Target Profiles and ABI Lowering](../docs/Guide_SMIL.md#target-profiles-and-abi-lowering).
- [Reference profiles](0011_checked_reference_profiles.md), [interface compatibility](0012_modules_and_interfaces.md), and [lifecycle](0014_program_lifecycle.md).

## Requirements

| KEY | Requirement |
| --- | --- |
| TGT-001 | A target profile shall be a versioned selection of CPU configuration, data layout, ABI, platform environment, and runtime interfaces. Each component identifier shall resolve to exactly one contract; incompatible changes shall receive a new version. CPU name alone shall not constitute a profile. |
| TGT-002 | A module shall contain at most one target directive, following its header when present and preceding imports/other items. Build selection may supply an omitted target; simultaneous source/build selections shall agree on the resolved contract or be rejected. Host layout/ABI shall not be silently selected. |
| TGT-003 | Unbound SMIL may undergo structural/type verification and target-independent transformations. Binding shall resolve required component contracts before any concrete size/offset computation, layout-dependent optimization, ABI lowering, or object generation. |
| TGT-004 | Target-bound serialized SMIL/objects shall record sufficient resolved contract identities/digests, CPU requirements, and exposed-interface information to reproduce and validate target-dependent decisions. Changing layout/ABI shall invalidate every dependent transformation rather than merely replace an identifier. |
| TGT-005 | A backend shall preserve logical widths/semantics using a legal native sequence or conforming helper, and diagnose unsupported behavior instead of narrowing or weakening it. Object generation shall require a complete lowering/runtime closure under the selected exact CPU mode/resources. |
| LAY-001 | Ordinary storage shall use eight-bit bytes and byte addressing. Each supported storable type shall have deterministic value encoding, representation size, required alignment, and allocation size. Sizes/offsets shall be mathematical byte quantities; alignments shall be positive powers of two; allocation shall be at least representation size and a multiple of alignment. |
| LAY-002 | Statically required unrepresentable/unallocatable layout or placement shall be diagnosed without wrapping. Dynamic execution-capacity failures shall follow [0009](0009_checked_execution.md). Aliases shall retain underlying layouts; SSA values shall have no storage byte order/alignment/padding. |
| LAY-003 | Integer iN shall have representation size `ceil(N/8)`, with profile-defined alignment/allocation. Loads shall decode low N bits and stores shall encode them while clearing unused high representation bits, without promises for allocation padding or writes to neighbors. |
| LAY-004 | Ordinary i1 shall have one-byte representation/allocation/alignment. Stores shall write byte zero or one; loads shall read only the low bit. Consecutive i1 fields shall not be implicitly bit-packed. Foreign Boolean encodings shall require explicit adaptation. |
| LAY-005 | Integer byte order shall be specified: little-endian places the least significant byte first; big-endian the most significant representation byte first. It shall not alter logical SSA bits/arithmetic or imply pointer/special-space encodings. Protocol order shall have its own definition. |
| LAY-006 | Ordinary nonempty records shall lay out fields in order from offset zero, align each field start to its alignment, reserve its allocation size, set record alignment to the maximum field alignment, and round final size up to that alignment for allocation. Representation shall end at the final field allocation before record tail padding. |
| LAY-007 | A record's field layout shall not vary with the space holding the record. Pointer-field spaces may affect field type layout. A special space unable to support the ordinary layout shall reject the aggregate rather than alter offsets. Bytewise padding comparison shall not imply logical record equality. |
| LAY-008 | A profile shall explicitly define or reject empty-record layout. Packed records, alignment overrides, and alternate addressable units shall require extensions. Queries, field accesses, initializer relocations, and every participating compiler/link stage shall use the same resolved layout. |
| SPC-001 | The `data` space shall be default for ordinary locals and omitted global space clauses. Each additional supported space shall have an explicit contract; mutability shall not override space permissions or imply ROM placement. Placement preferences such as zero-page need not create new spaces when ordinary pointers suffice. |
| SPC-002 | Each space contract shall define pointer encoding/size/allocation/alignment/null, bank/segment components, addressable objects/regions, rights/access kind, alias relationships, ordered space mappings, integer conversions/domains/reconstruction/round trips, normalized equality/one-past arithmetic, and supported device/atomic/agent/runtime behavior. |
| SPC-003 | One space shall have one pointer representation in the initial model. Incompatible near/far representations shall have distinct type identities. Different names shall not imply disjointness; unsupported names/mappings shall be rejected. |
| ABI-001 | Every profile shall select a default ABI and identify supported additional ABIs. Each ABI shall define deterministic supported-signature classification and diagnose unsupported signatures. Logical parameters/results shall remain unchanged by physical lowering. |
| ABI-002 | The ABI shall define ordered parameter/result/aggregate classification, register/stack splitting, indirect copies/result areas, narrow carriers/extensions/unspecified bits, frame/stack organization and ownership, cleanup/returns, preserved/clobbered/reserved resources, and required processor/bank state. |
| ABI-003 | The ABI shall additionally define helper interfaces/versions, function-reference representation/indirect transfers, additional-argument descriptors/receipt/forwarding, exceptional discrimination/carriers/ownership/adapters, lifecycle callback interfaces/agents, registration guarantees, and quiescence. |
| ABI-004 | Separate active invocations shall retain distinct logical objects. Hardware/software stack combinations and scratch/static reuse shall preserve recursion and advertised reentrancy. External interrupt/asynchronous entries shall establish/preserve required ABI state under explicit profile guarantees. |
| ABI-005 | Hidden indirect argument passing shall preserve immutable by-value SSA semantics. Results shall survive callee/packet expiry in caller-owned backing; callee local storage shall not back an ordinary returned value. Returned local pointers shall still expire. |
| ABI-006 | A function ABI clause shall select only an ABI supported by the bound profile; omission shall use the default. Declarations/definition and callable references shall agree on effective ABI/attributes. Direct/indirect calls shall inherit that contract without conflicting call-site overrides. |
| ABI-007 | Selecting a foreign ABI shall not change module storage layout. Different foreign layout shall require an explicit adapter or rejection. Private calling conventions may be introduced only with control/update of all affected callers/callees and preservation of external contracts. |
| ABI-008 | `signext`/`zeroext` shall apply only to supported integer signature entries and prescribe sign/zero extension where a wider physical carrier is used. They shall not alter logical integer widths, memory encodings, or insert logical body casts. Unsupported/non-integer/conflicting attributes shall be rejected. |
| ABI-009 | Compatibility shall compare resolved effective attributes, treating explicit spelling and an equivalent ABI default equally. Required foreign information absent from both signature/default shall be diagnosed. |
| CMP-001 | Linked interfaces shall agree on nominal identities/signatures/effects, storage/pointer/function layouts, space/conversion/device/atomic domains, ABI/attributes, helper/preservation/runtime/execution contracts, lifecycle coordinator metadata, relocation/object/environment constraints, and required CPU features. CPU names or pointer widths alone shall not establish compatibility. |
| CMP-002 | Known incompatible contracts shall be rejected unless an explicit adapter separates them. An initial exact-version layout/ABI policy shall not be relaxed without an explicit compatibility rule. Checked reference profiles shall use their stronger exact-component policy. |
| CMP-003 | Foreign objects shall have an explicitly declared interface/adapter contract; that declaration shall establish an interoperability assumption, not proof of the implementation. Optimization preferences shall not affect compatibility unless they change exposed representation/calling behavior, in which case metadata shall record the change. |
| ENV-001 | Before entry, the environment shall establish processor/runtime/stacks, final global locations/relocations, constant values, serial dynamic initialization, and gated application entry. Entry shall be designated, fixed-arity, non-raising, and supported by its ABI; normal results shall have a defined logical i32 status mapping. |
| ENV-002 | Initialization shall run once per instance under [0014](0014_program_lifecycle.md). Zero-fill shall implement an initializer only when its bytes encode that logical value. Immutable storage may reside in RAM or ROM when construction is supported. Installing values shall not authorize later immutable stores. |
| TGT-006 | Target validation shall check all supported type layouts/placements/relocations, constant/layout evaluation, spaces/conversions, access/device/atomic/unaligned implementations, callable/variadic/exceptional ABIs, lifecycle graphs/interfaces, execution digests/plans/tracking/emergency budgets, linked compatibility, and legal instruction/helper availability before object publication. |

## Required conformance observations

| Case | Required outcome |
| --- | --- |
| Source and build specify different resolved target | Diagnostic; no host fallback. |
| i12 ordinary storage | Two representation bytes; high four bits ignored on load and cleared on store. |
| Record `{i1,i1,i8,ptr}` with pointer size/alignment 2/1 | Offsets 0,1,2,3 and size 5 under the illustrative cap-one layout. |
| Same fields with pointer 4/4 and integer/record rules as stated | Offsets 0,1,2,4 and size 8, alignment 4. These examples do not define checked-profile pointers. |
| Target without native i64 divide | Equivalent expansion/helper or unsupported diagnostic; no reduced-width result. |
| Retarget specialized module by header edit alone | Rejected as insufficient regeneration of dependent decisions. |
