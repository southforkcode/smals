# Small Machine Intermediate Language (SMIL)

**SMIL** is a typed intermediate representation (IR) used by the compilers in this project. It uses static single assignment (SSA) for computation values and explicit operations for accessing storage.

Functions use a flat control-flow graph (CFG) composed of basic blocks. Control transfers explicitly between blocks, with block arguments providing values for block parameters.

SMIL separates the meaning of computations from their implementation using physical registers, machine instructions, and memory layouts.

Examples include function-body fragments that omit their enclosing function and block declarations. Separate examples do not share identifiers unless explicitly stated. Forms containing angle-bracket placeholders are explanatory templates, not SMIL source. Source Text, Lexical Rules, and Grammar below is the single authority for concrete source spelling and statement boundaries.

## Target Profiles and ABI Lowering

A **target profile** is a versioned contract selecting a CPU configuration, data layout, ABI, platform environment, and runtime interfaces.

The profile defines how logical SMIL values and operations are represented and implemented. It does not change their logical meaning. Constant layout queries and symbolic field-address initializers must use the same resolved contract as ordinary field access.

| Component | Defines |
| --- | --- |
| CPU configuration | Instruction set, processor variant, and enabled features |
| Data layout | Storage sizes, alignment, byte order, record layout, and data-pointer representations |
| ABI | Parameter/result passing, call-boundary state, preservation rules, and invocation-frame organization |
| Platform environment | Memory regions, object/executable formats, relocations, program entry, and startup obligations |
| Runtime interfaces | Required helpers and runtime state, with their signatures, ABIs, progress/reentrancy guarantees, and terminal-fault behavior |

A CPU name alone is not a complete target profile. Profiles may share components while differing in other components.

Concrete profiles are defined by versioned manifests and their normative component contracts. Concrete Reference Profiles below supplies an initial resolved catalog for small and early-modern CPUs. A component identifier must resolve to one specified contract. An incompatible change requires a new contract version. Profile definition and tested backend availability are separate facts.

### Target Selection and Binding

A module may select its target profile with a module-level directive after its module header, when present:

```SMIL
target "smil.ref.w65c02s.checked.v2"
```

This directive follows a module header when present and precedes imports, declarations, definitions, and exports. A module has at most one target directive. The identifier above selects the W65C02S checked reference contract proposed below; it does not assert that a backend has already implemented it.

The build configuration may select a profile when the source omits the directive. If both specify a profile, they must agree on the resolved contract. The toolchain must not silently select the development host's layout or ABI.

A module without a selected profile may be processed as **unbound SMIL**. Structural verification, logical typing, and transformations independent of layout or ABI may be performed in that form.

A module becomes **target-bound** when its profile and required component contracts have been resolved. Binding must occur before computing concrete field offsets or storage sizes, applying layout-dependent optimizations, or lowering interfaces to a physical ABI.

Object generation requires a target-bound module. Serialized target-bound SMIL and generated objects must record enough resolved contract information to reproduce and validate those decisions.

Changing the layout or ABI of a target-bound module requires invalidating and repeating every transformation that depended on the changed contract. Replacing a target identifier alone does not retarget an already specialized module.

A target's lack of a native instruction or native integer width does not change an operation's semantics. The backend may use equivalent expansion or a runtime helper. If the required behavior cannot be implemented, it must diagnose the unsupported requirement rather than silently narrow values or weaken semantics.

### Data Layout

The initial SMIL storage model uses eight-bit bytes and byte-addressable ordinary memory. Other addressable-unit models require an explicit extension.

For each supported storable type, the layout defines:

| Property | Meaning |
| --- | --- |
| Value representation | Encoding of the logical value in storage |
| Representation size | Bytes containing that encoding, excluding trailing allocation padding |
| Required alignment | Alignment required by an ordinary typed access |
| Allocation size | Space reserved for an object, including any required trailing padding |

Sizes and alignments are measured in bytes unless explicitly stated otherwise. Alignments are positive powers of two. Allocation size is at least the representation size and is a multiple of the required alignment.

Layout calculations use mathematical sizes and offsets, not wrapping SMIL integer arithmetic. A statically required layout or placement that the profile cannot represent or allocate must be diagnosed rather than wrapped. Runtime storage exhaustion requires separately specified execution behavior.

For ordinary accesses, a pointer must satisfy the pointee type's required alignment. Support for an unaligned machine instruction does not by itself relax this SMIL requirement. The explicit `load_unaligned` and `store_unaligned` integer forms relax this requirement to byte alignment under the rules in Pointers and Memory Access.

The layout must define deterministic rules for every type and integer width it supports. It may use formulas or size classes; it need not enumerate every width individually.

Aliased types retain the layout of their underlying type. SSA values themselves have no memory alignment, byte order, or allocation padding.

#### Integer Storage

For `iN`, the representation size is `ceil(N / 8)` bytes. Required alignment and allocation size are supplied by the profile.

The representation encodes the integer bit pattern without an independent signedness attribute. A typed integer load decodes the low N value bits. A typed store encodes those bits and clears unused high bits within the representation bytes.

Allocation padding outside those representation bytes is not part of the integer value. Ordinary typed loads do not interpret it, and typed stores do not promise particular padding-byte contents.

For example, `i12` requires two representation bytes. The four unused high bits do not contribute to the loaded value. The profile may reserve additional allocation padding to satisfy its alignment rules.

A typed store must not modify neighboring objects as a consequence of expansion into wider machine operations.

#### Boolean Storage

An SSA `i1` remains a one-bit value. In ordinary memory, `i1` has representation size one byte, allocation size one byte, and required alignment one byte.

A store writes byte `0` or `1`. A load takes the low bit of the byte and ignores its other bits.

Consequently, loading `i1` from a byte containing `2` produces `[i1 0]`. It does not perform a nonzero-to-true conversion. Such normalization requires an explicit comparison against zero.

Consecutive ordinary `i1` fields are not bit-packed. Packed representations require separately defined types or operations.

Foreign ABI Boolean encodings must be mapped explicitly where they differ from this representation.

#### Endianness

The data layout specifies the byte order of multi-byte ordinary integer representations.

Little-endian layout places the least significant byte at the lowest address. Big-endian layout places the most significant representation byte at the lowest address.

Endianness does not change SSA integer values, arithmetic, or the numbering of bits within a value.

Pointer encodings and special address spaces follow their explicitly specified representation rules; they must not be inferred from integer byte order alone.

Operations that read or write protocol-specific byte order require separate definitions rather than changing the module's ordinary data layout.

#### Record Layout

The ordinary record layout is computed in field order:

1. Begin with a current offset of zero.
2. Align the next field's offset to that field's required alignment.
3. Reserve that field's allocation size and advance the current offset.
4. Set record alignment to the maximum field alignment.
5. Round the final current offset up to record alignment to obtain record allocation size.

The record's representation size ends at the end of the final field's allocation. Tail padding, when required, increases allocation size to satisfy record alignment.

In the initial ordinary-record model, a type's field layout does not vary with the address space in which an object is stored. The spaces of pointer fields are part of their types and can affect layout. A special space unable to support the ordinary layout must reject that aggregate use rather than silently change its offsets.

Record padding is not part of the logical record value. A bytewise comparison of stored records does not automatically implement logical record equality.

Empty-record layout is not established by this algorithm; a profile must explicitly support it with a stated layout or reject it. Packed records and user-specified alignment overrides require separately specified forms.

For illustration, consider these two hypothetical layouts:

| Property | Small layout | Wider layout |
| --- | --- | --- |
| Integer byte order | Little-endian | Big-endian |
| `i1` allocation/alignment | 1 / 1 bytes | 1 / 1 bytes |
| `i8` allocation/alignment | 1 / 1 bytes | 1 / 1 bytes |
| `i16` allocation/alignment | 2 / 1 bytes | 2 / 2 bytes |
| Default data-pointer allocation/alignment | 2 / 1 bytes | 4 / 4 bytes |

Given:

```SMIL
@cstr = type [ptr [i8]]
@UserInfo = record { i1, i1, i8, cstr }
```

The small layout places fields at offsets `0, 1, 2, 3` with allocation size `5`. The wider layout places them at offsets `0, 1, 2, 4` with allocation size `8` and alignment `4`.

These examples illustrate layout rules. They are not the layouts of the checked reference profiles, whose complete pointer representation and ABI are specified below, and do not define established platform ABIs.

### Address Spaces and Pointer Representations

A pointer type includes an address-space identity and a pointee type:

```SMIL
[ptr data [i8]]
[ptr rom [i8]]
[ptr io [i8]]
```

The space name `data` identifies the profile's default ordinary data space. The existing form `ptr [T]` is shorthand for `ptr data [T]`; both denote the same type.

Names such as `rom` and `io` are illustrative additional spaces. A profile must explicitly define each non-default space it supports.

An address-space contract specifies:

- Pointer representation, representation size, allocation size, and alignment.
- Address encoding and any required bank, segment, or other representation components.
- Null-pointer encoding.
- Which objects or regions can be addressed.
- Access capabilities, ordinary/device region distinctions, and restrictions.
- Aliasing relationships and the exact ordered mappings supported by `addrspacecast`.
- Supported pointer/integer conversion rules, numeric domains, object reconstruction, and separate pointer and integer round-trip guarantees.
- Normalized pointer equality, one-past representation, and object-preserving arithmetic.
- Atomic widths/alignment, participating agents, device contracts, and required runtime support where applicable.

The initial model has one pointer representation per address space. Distinct near/far or other incompatible representations must have distinct type identities rather than silently changing the encoding of the same pointer type.

Different address-space names do not by themselves establish disjoint memory. A profile may define overlapping spaces, and optimizations must follow the declared aliasing rules.

An address-space cast is not an ordinary `ptrcast`. It uses the explicit `addrspacecast` operation and a profile-defined object-preserving mapping. Unsupported space names and conversion pairs must be rejected.

#### Object Address Spaces

Ordinary `alosf` objects belong to `data`, and their pointers have type `ptr data [T]`. The profile must provide a frame implementation whose local objects are addressable through that model.

A global storage declaration may name its address space:

```SMIL
@ordinary = global mutable [i16] [i16 0]
@lookup = global immutable [i16] [i16 42] space(rom)
```

The second declaration requires a profile supporting `rom` and that placement. Its symbol has type `ptr rom [i16]`. Omitting `space(...)` selects `data`.

Object mutability and address-space access permissions are independent requirements. A `mutable` declaration cannot override a space's prohibition on writes. An `immutable` object does not automatically belong to `rom`.

Fast-memory placement, including a zero-page allocation preference, does not require a distinct address space when the same ordinary pointers can address those objects.

Declaring an `io` pointer does not establish a device's transaction semantics. MMIO access width, side effects, splitting, and ordering use a named device access contract and the `mmio_*` operations. Ordinary `load` and `store` are prohibited for a region requiring MMIO, even through an alias in another space. A space may also contain ordinary regions when the profile explicitly identifies them as such.

#### Null Pointers

A null pointer is a distinguished typed pointer value that never designates an object:

```SMIL
$empty = const [ptr [i8] null]
$empty_rom = const [ptr rom [i8] null]
```

The second form requires a supported `rom` space.

The profile defines each space's stored null encoding. It need not be all-zero bytes.

A null pointer cannot be dereferenced. An integer value of zero is not implicitly a null pointer, and `inttoptr` maps zero to null only when the profile explicitly defines that behavior.

A null literal is encoded only after target binding. Its logical meaning does not depend on knowing that encoding during earlier transformations.

### ABI Contracts

An **ABI contract** defines how logical SMIL interfaces are represented at physical call boundaries.

Every target profile selects a default ABI and identifies other ABIs it supports. A concrete ABI must provide deterministic rules for all supported signatures and diagnose unsupported forms.

At minimum, an ABI specifies:

| Area | Required rules |
| --- | --- |
| Parameters | Ordered classification, register/stack assignment, splitting, and indirect passing |
| Results | Register assignment, splitting, and caller-owned result areas |
| Aggregates | Classification, copies, layout, and indirect representations |
| Narrow integers | Carrier widths, extension requirements, and unspecified carrier bits |
| Invocation frames | Stack/frame organization, alignment, growth, ownership, cleanup, and return-address handling |
| Preservation | Caller- and callee-preserved registers and reserved memory resources |
| Processor state | Required modes, bank state, and other call-boundary assumptions |
| Runtime interfaces | Helper signatures, conventions, reserved resources, and compatibility versions |
| Function references | Representation, indirect transfer sequence, and callable-contract compatibility |
| Variadic arguments | Fixed/additional argument classification, type descriptors, receipt, and forwarding |
| Exceptional outcomes | Outcome discrimination, normal-result/payload carriers, ownership, and foreign adapters |
| Lifecycle callbacks | Coordinator-to-callback interfaces, authorized agents, and quiescence/registration guarantees |

An ABI may use a hardware stack, a software stack, or a defined combination. SMIL's logical invocation frames do not require all locals and arguments to use the processor's hardware stack.

ABI lowering must preserve separate active invocations. Shared scratch storage and static frame reuse require preservation rules or proofs sufficient to maintain recursion and any advertised reentrancy guarantees.

A profile must state its interrupt and asynchronous reentry guarantees. If an external entry mechanism calls SMIL functions, that mechanism must establish and preserve the required ABI state.

#### Logical Signatures and Physical Interfaces

ABI lowering does not change a function's logical SMIL parameter or result types.

```SMIL
declare @compute([i64]) -> ([i64], [i1])
```

A small-machine ABI may split values, pass them through memory, or introduce hidden pointers. A wider-machine ABI may use registers. Both must deliver the same logical argument and result values.

A hidden indirect argument representation must preserve by-value semantics. It must not permit changes to the caller's immutable SSA value.

Result areas must remain valid in the caller after the callee returns. A callee's expired local storage cannot serve as the backing storage for an ordinary returned value. This does not make a logically returned pointer to a local object valid.

Block arguments remain internal CFG value transfers. They do not use the function-call ABI and do not create invocations.

#### ABI Selection

A function declaration or definition may select an ABI after its signature:

```SMIL
declare @foreign_emit([i8]) -> () abi("vendor.v1")
```

The identifier is illustrative and must resolve to an ABI supported by the selected target profile.

When the clause is absent, the profile's default ABI applies. All declarations and the definition of a function must agree on the resolved ABI and ABI-relevant attributes as well as the logical signature.

Direct calls inherit that contract from the callee declaration; indirect calls inherit the function-reference type's complete callable contract. A call site cannot independently select a conflicting ABI.

The selected ABI does not change the module's data layout. A foreign interface requiring a different storage layout must use an explicit adapter or be rejected.

An optimizer may introduce a private calling convention only when it controls and updates every affected caller and callee while preserving externally visible contracts.

#### Integer Extension Attributes

SMIL integer types are signless. A foreign ABI may nevertheless require a narrow integer argument or result to be sign-extended or zero-extended into a wider physical carrier.

These requirements may be expressed on integer signature entries:

```SMIL
declare @signed_external([i8] signext) -> ([i8] signext) abi("vendor.v1")
declare @unsigned_external([i8] zeroext) -> ([i8] zeroext) abi("vendor.v1")
```

`signext` requests extension by repeating the value's most significant bit. `zeroext` requests extension with zero bits where the ABI uses a wider carrier.

These attributes do not change the logical `i8` type. At function entry or after a call, the corresponding SSA value still contains exactly eight value bits.

They do not change ordinary memory representation or imply casts within the function body.

The ABI defines where these attributes apply and what omitted attributes mean. If a foreign interface needs information that cannot be determined from the signature and selected ABI, the required attributes must be supplied. Unsupported attributes, non-integer uses, and conflicting extension requests must be rejected.

Compatibility is checked using the resolved effective attributes. Spelling an attribute explicitly or obtaining the same effect from an ABI default does not by itself create a mismatch.

### Compatibility and Object Metadata

Separate compilation must preserve every interface property observable by another module.

Compatibility requires agreement on relevant:

- Nominal type identities and logical signatures, including variadic markers and raised-payload effects.
- Function-reference layouts, callable ABIs, exception carriers, and variadic-pack contracts.
- Lifecycle coordinator versions, initialization identifiers/dependencies, and callback contracts.
- Storage layouts, alignments, pointer representations, address spaces, and conversion mappings.
- Referenced device access contracts, shared-memory agent domains, atomic requirements, and pointer-fault runtime contracts.
- Function ABIs and effective parameter/result attributes.
- Reserved resources and runtime interface contracts.
- Object formats, relocations, and platform constraints.

Matching CPU names or pointer widths is insufficient. Different CPU feature requirements may coexist when the interfaces are compatible and the final execution environment supports every required instruction.

Target-bound SMIL and project-generated objects must record resolved layout, ABI, environment/runtime, CPU-requirement, and exposed-interface information sufficient for the project toolchain to validate compatibility.

The initial implementation may require exact equality of versioned layout and ABI contracts where they are shared. Relaxing that rule requires an explicit compatibility definition, not an assumption based on similar sizes.

The linker must reject known incompatible interfaces unless an explicit adapter separates them. It must not silently reinterpret records or substitute a different calling convention.

Foreign objects without SMIL metadata require an explicitly declared interface contract. Such a declaration supplies an interoperability assumption; it does not prove that the foreign implementation obeys it.

Optimization preferences such as code size versus speed do not ordinarily change compatibility. Any option that changes an exposed representation or calling convention must be reflected in the recorded contract.

### Global Initialization and Program Entry

The platform environment establishes storage and runtime state through the Program Lifecycle coordinator defined below. Bootstrap installs constant initializers and reserves dynamic-global storage; the initialization graph then completes every dynamic initializer and startup hook before application entry.

Its contract must ensure that:

1. Required processor modes, stacks, and runtime resources are established.
2. Global objects have valid final storage locations and required relocations.
3. Constant initializer values are installed before any initializer function runs.
4. Dynamic factories install complete values, including immutable globals, in dependency order.
5. Required callbacks and interrupt/application entry remain gated until readiness is published.
6. Control enters the designated fixed-arity, non-raising program-entry function using its declared ABI.

These are obligations rather than a mandatory bootstrap instruction sequence. A hosted loader may perform work that bare-metal startup performs explicitly. Initialization functions can observe only already-ready global contents; address formation may refer to reserved but not-yet-ready objects.

The environment defines the entry signature and ABI, maps its normal results to a logical `i32` exit status, and implements ordered shutdown and terminal-fault reporting. No particular `main` signature or host operating-system service is implied.

Initialization occurs once per program instance. Calling a factory or hook as an ordinary function does not repeat coordinator initialization or grant immutable-write privileges. Terminal faults do not resume ordinary execution, return substitute values, or implicitly run shutdown callbacks.

#### Initializer Representations

Both mutable and immutable global declarations require an explicit constant initializer or the explicit dynamic-factory form. A dynamic declaration does not acquire an implicit zero value.

A zero-valued initializer may use zero-filled storage only when zero bytes represent the required initialized value. This must not be assumed for null pointers or other profile-specific representations.

An immutable object may remain in ROM or be initialized in RAM. Immutability does not require either placement.

Installing an initializer is object construction performed by the loader or startup implementation. It is not an ordinary SMIL `store` and does not authorize later writes to an immutable object.

The startup implementation must install symbolic pointer initializers, including field addresses embedded in records, using the final target encoding and supported relocations. Record-zero initializers supply typed null pointer fields, which need not have all-zero encodings. Taking a symbol's address does not read that object's contents or create a runtime initialization dependency on those contents.

Program Lifecycle defines dynamic factories, startup hooks, dependency ordering, initialization failure, and shutdown callbacks. Source-language construction/destruction rules must be lowered to those explicit operations and registrations rather than inferred from record types.

### Target-Bound Validation

In addition to logical typing and CFG verification, target-bound validation must check:

- The profile and its component versions resolve.
- Source and build-selected contracts agree.
- Every required type has a supported representation.
- Object sizes, alignments, spaces, placements, and relocations are supported.
- Record initializers, symbolic pointer expressions, and layout queries resolve without type errors, invalid selections, constant-evaluation faults, or result-range errors.
- Pointee spaces, pointer comparisons/arithmetic, explicit conversion pairs, and pointer/integer conversion domains are supported.
- Device access contracts, atomic widths/alignment/agent domains, and unaligned-access lowering resolve.
- Pointer/storage validity, initialized-value reads, checked concurrency, and staged resource faults can be implemented through proofs, checks, or conforming runtime support.
- The execution-contract digest and per-object execution plans match the selected profile/runtime; all shadow/history/emergency storage is accounted for.
- Selected function ABIs, callable-reference representations, raised-result carriers, variadic receipt/forwarding, and effective attributes are consistent and supported.
- Switch constants are unique after encoding, and new terminator/edge typing is valid.
- Lifecycle factory/callback signatures, dependency graphs, placements, and coordinator transitions are supported.
- Required lowering rules or runtime helpers exist and preserve integer result, shift-count, flag, and arithmetic-fault semantics.
- Linked interfaces and runtime components are compatible.
- The environment can fulfill initialization and entry obligations.
- The selected manifest and normative contract digests validate, and the chosen backend supplies every required instruction/lowering/helper within that exact CPU mode and resource map.

A structurally valid unbound module may fail these checks for a particular target. Such failure must be diagnosed rather than changing its semantics.

## Concrete Reference Profiles

The initial profile set defines project-owned **checked reference environments** across small and early-modern processors. These are complete proposed compilation contracts, not claims that the corresponding backends, runtime libraries, or reference monitors have already been implemented.

The accompanying `smil_profiles_v2/` directory is part of this proposal:

| File | Purpose |
| --- | --- |
| `index.json` | Exact target identifiers, resolved manifest paths, and content digests |
| `profiles/*.json` | Fully expanded CPU/layout/ABI/environment/runtime selections for each target |
| `contracts.json` | Shared checked-pointer, packet, metadata, relocation, device, lifecycle, and helper contracts |
| `schema/target-profile.schema.json` | Closed top-level structural manifest schema |
| `validate_profiles.py` | Dependency-free structural and semantic consistency checks |

The JSON values and algorithms in this section jointly define checked reference-profile version 2, using the existing version-1 manifest transport. A profile contains no implied development-host choices. There is no inheritance at binding: family definitions are an authoring convenience, and each indexed file is fully resolved. Unknown top-level fields, unresolved contracts, invalid digests, and unknown target identifiers are rejected.

`smil.ref.<model>.checked.v2` is the target identifier for each model below. For example:

```SMIL
target "smil.ref.i8086.checked.v2"
```

The table's register/coordinate column gives native integer-register width and the permitted normalized address-coordinate width. It does not constrain SMIL integer widths. The alignment cap belongs to the project layout, not an assertion about a platform C ABI.

| Model suffix | Family contract | Register / address bits | Data layout | Incoming native packet location |
| --- | --- | --- | --- | --- |
| `mos6502` | `6502` | 8 / 16 | little, cap 1 | A:low8, X:high8 |
| `w65c02s` | `6502` | 8 / 16 | little, cap 1 | A:low8, X:high8 |
| `mc6800` | `6800` | 8 / 16 | big, cap 1 | X |
| `i8008` | `8008` | 8 / 14 | little, cap 1 | H:high6, L:low8 |
| `i8080a` | `8080` | 8 / 16 | little, cap 1 | H:high8, L:low8 |
| `i8085a` | `8080` | 8 / 16 | little, cap 1 | H:high8, L:low8 |
| `i8086` | `8086` | 16 / 20 | little, cap 2 | ES:DI |
| `i8088` | `8086` | 16 / 20 | little, cap 2 | ES:DI |
| `i80186` | `8086` | 16 / 20 | little, cap 2 | ES:DI |
| `i80286-real` | `8086` | 16 / 20 | little, cap 2 | ES:DI |
| `i80286-protected` | `286pm` | 16 / 24 | little, cap 2 | ES:DI |
| `i386dx` | `x86-32` | 32 / 32 | little, cap 4 | EAX |
| `i386sx` | `x86-32` | 32 / 24 | little, cap 4 | EAX |
| `i486sx` | `x86-32` | 32 / 32 | little, cap 4 | EAX |
| `i486dx` | `x86-32` | 32 / 32 | little, cap 4 | EAX |
| `i486dx2` | `x86-32` | 32 / 32 | little, cap 4 | EAX |
| `i486dx4` | `x86-32` | 32 / 32 | little, cap 4 | EAX |
| `pentium-p5` | `x86-32` | 32 / 32 | little, cap 4 | EAX |
| `pentium-mmx` | `x86-32` | 32 / 32 | little, cap 4 | EAX |
| `pentium-pro` | `x86-32` | 32 / 32 | little, cap 4 | EAX |
| `pentium-ii` | `x86-32` | 32 / 32 | little, cap 4 | EAX |
| `pentium-iii` | `x86-32` | 32 / 32 | little, cap 4 | EAX |
| `mc68000` | `m68k` | 32 / 24 | big, cap 2 | A0 |
| `mc68020` | `m68k` | 32 / 32 | big, cap 4 | A0 |
| `mc68030` | `m68k` | 32 / 32 | big, cap 4 | A0 |
| `mc68040` | `m68k` | 32 / 32 | big, cap 4 | A0 |
| `mc68060` | `m68k` | 32 / 32 | big, cap 4 | A0 |
| `ppc601` | `ppc32` | 32 / 32 | big, cap 4 | r3 |
| `ppc603` | `ppc32` | 32 / 32 | big, cap 4 | r3 |
| `ppc603e` | `ppc32` | 32 / 32 | big, cap 4 | r3 |
| `ppc604` | `ppc32` | 32 / 32 | big, cap 4 | r3 |
| `ppc604e` | `ppc32` | 32 / 32 | big, cap 4 | r3 |
| `ppc750` | `ppc32` | 32 / 32 | big, cap 4 | r3 |
| `ppc7400` | `ppc32` | 32 / 32 | big, cap 4 | r3 |
| `ppc970-32` | `ppc32` | 64 / 32 | big, cap 4 | r3 |
| `arm7tdmi` | `arm7` | 32 / 32 | little, cap 4 | r0 |
| `r3000` | `mips1` | 32 / 32 | big, cap 4 | r4/a0 |
| `sparcv8-flat` | `sparc8` | 32 / 32 | big, cap 4 | %o0 |

`ppc970-32` deliberately selects 32-bit execution on a processor with 64-bit registers. It is not a full 64-bit pointer or ELFv1/ELFv2 profile. Likewise, `i80286-real` and `i80286-protected` are separate execution contracts. A model name or clock-speed label never silently selects protected mode, a memory map, an ABI, or an optional instruction extension.

The 8008 has a finite hardware address stack; its reference ABI therefore uses software continuations rather than imposing that hardware nesting limit on SMIL recursion. Its input/output port numbering is also different from the 8080's. These hardware distinctions are documented in [Intel's 8008 manual](https://deramp.com/downloads/mfe_archive/050-Component%20Specifications/Intel/Microprocessors%20and%20Support/8008%20Family/i8008UM%20Nov%2073.pdf). The 8086's segment model is specified by [Intel's 8086 documentation](https://userpages.cs.umbc.edu/squire/8086-datasheet.pdf); its reference normalization below is a project choice.

MC68000 and later 68k variants do not form an unrestricted instruction-set-superset chain. The reference emission subset excludes optional or removed instructions, including `MOVEP`, `CAS`/`CAS2`, long multiply/divide, bitfield, floating-point, and MMU operations; byte-vector helpers provide their required SMIL behavior. CPU facts and implemented-instruction differences follow the [Motorola family reference](https://www.nxp.com/docs/en/reference-manual/M68000PRM.pdf) and [MC68060 manual](https://www.nxp.com/docs/en/data-sheet/MC68060UM.pdf).

The Intel 32-bit variants initially use the documented 80386 integer baseline, including on 486, Pentium, and P6 processors. MMX, SSE, x87, `CMOV`, `CMPXCHG8B`, and other later fast paths are not enabled merely by the model name. A versioned CPU component may enable additional verified instructions later. PowerPC profiles similarly use a common 32-bit integer subset with no implicit POWER-only, floating-point, or vector instructions. RISC profiles state delay-slot and execution-state restrictions explicitly.

These are reference boards/monitors, not Apple II, Commodore, SWTPC, CP/M, DOS, IBM PC BIOS, Amiga, AIX, Linux, or an existing platform C ABI. Porting to one of those environments requires a profile selecting its actual memory map, entry interface, devices, and foreign adapters. The model catalog is extensible without changing target-independent SMIL operations.

### Versioning, Binding, and Availability

Manifest format is `smil.target-profile.v1`. Shared contract format is `smil.reference-contracts.v2`; the shared contract identifier is `smil.ref.checked.contracts.v2`.

Content digests are SHA-256 over UTF-8 JSON with object keys sorted, no insignificant whitespace, unescaped non-ASCII characters, and no Unicode normalization. Array order is significant. Input JSON must reject duplicate keys. Floating-point JSON numbers are not used in these manifests. The index contains each profile digest; a profile contains the shared-contract digest. No digest includes itself.

Binding resolves the index entry, validates the manifest and shared contract, and records their identifiers and digests. The current checked profiles use exact resolved component identity for linking, including CPU and environment components. It does not infer compatibility merely because a later CPU can execute some earlier instructions. A future explicit instruction-subset compatibility rule can relax this conservatism.

Backend availability is separate from profile definition. A toolchain may advertise an indexed target as implemented only after its encoder, runtime closure, linker/loader contract, and conformance vectors pass. An unimplemented target produces a diagnostic, not code for a nearby CPU. The manifest's proposed status does not substitute for that gate.

### Supported Types and Layout Formulas

All reference profiles support every integer width `1 <= N <= 65535`, including widths that are not powers of two. This is a versioned implementation limit, not a change to unbound SMIL's positive-width type model. Wider types still present at binding are unsupported by this profile set.

For each integer, let B be `ceil(N / 8)` and C the profile's alignment cap:

```text
representation_size(iN) = B
alignment(iN) = largest power of two <= min(B, C)
allocation_size(iN) = round_up(B, alignment(iN))
```

The guide's integer byte order, low-N-bit decoding, high unused-bit clearing, and `i1` rules apply without alteration. Big-endian byte-vector arithmetic still numbers logical bits by significance, not by increasing memory addresses.

An `i64` divide on an 8008, 6800, 6502, or 8080 is therefore a supported operation implemented through expansion or a helper. Native operand width is not a type restriction. Actual object, frame, code, and temporary-storage requirements must still fit the board. A large supported type can fail placement or exhaust execution resources; a backend must not silently reduce its width.

The ordinary record-layout algorithm remains unchanged. An empty record is explicitly supported with representation size zero, allocation size one, and alignment one. Distinct live empty-record allocations consequently have real storage positions. Their padding byte has no logical value. Empty records can be passed and returned as complete values; a no-result tuple remains distinct and occupies no result payload.

Data/ROM/I/O pointer representations are 16 bytes, aligned to `min(C, 4)`. Function references are eight bytes with the same alignment. These sizes are deliberate consequences of the checked semantics; the earlier two-byte/four-byte pointer layouts remain illustrations, not these profiles' layouts.

### Checked Pointer Representation and Object Registry

Every data-pointer representation contains four target-endian unsigned 32-bit fields:

| Byte offset | Field |
| --- | --- |
| 0 | Allocation identity |
| 4 | Byte offset within that allocation |
| 8 | Cached normalized address coordinate |
| 12 | Effective rights: read bit 0, write bit 1; other bits zero |

Address space and pointee type come from the SMIL type. Null has all fields zero. An address-only data/ROM pointer has identity, offset, and rights zero and a nonzero cached address. No ordinary storage access or pointer arithmetic is authorized by an address-only value.

The cached coordinate permits defined equality of expired pointers without retaining an unbounded tombstone table. Equality checks typed null separately, then compares normalized coordinates. Dereference and object arithmetic instead require an occupied live registry entry with the same identity, consistent offset/address, sufficient rights, supported type view, and valid readiness.

The runtime registry uses the 48-byte records in `contracts.json`, stored immediately after its 128-byte context. Record fields are target-endian `u32` in the listed order. An identity of zero denotes an unused slot. Allocation identity 1 belongs to the monitor region; globals receive identities from 16 in qualified-symbol UTF-8 byte order. Each local declaration receives a fresh monotonically increasing identity on execution. Freeing a slot does not permit identity reuse. Exhausting the 32-bit identity counter faults.

Records give physical base, allocation size, root type, allowed spaces/rights, readiness, and owning frame. An allocation can be found by bounded linear scan of occupied slots; a conforming implementation can use another equivalent index. Returning, raising, or abandoning a frame expires all its local identities before storage is reused.

Registry, type catalogs, packets, native return stacks, and runtime-private temporaries are not ordinary registered objects. Guessing their native addresses with `inttoptr` cannot make them accessible. The protection is enforced by generated code/runtime checks; these small CPUs need not provide memory-protection hardware. Unchecked foreign writes are not an advertised interface.

Backend proofs may eliminate checks and avoid materializing unused pointer fields in private computations. Observable pointer storage and public call boundaries still obey the selected encoding. A thin-pointer or shadow-metadata alternative requires a different layout/runtime contract and must preserve the same IR faults and lifetimes.

### Pointer/Integer Domains and Address-Space Mappings

Let M be the manifest's minimum inspection integer width: 16 for the small 8-bit families and 32 for the other profiles. Both conversions support integer widths M through 65535, with no truncation. A value outside the accepted numeric domain causes `invalid_pointer_operation`.

| Space | `ptrtoint` mapping | `inttoptr` mapping |
| --- | --- | --- |
| `data`, `rom` | Cached normalized coordinate, zero-extended; typed null maps to zero | Zero maps to null. Otherwise resolve a uniquely containing live allocation's strict interior in that space, with canonical rights; an unregistered coordinate becomes address-only |
| `io` | Null maps to zero; monitor coordinate a, for `0 <= a <= 7`, maps to `a + 1` | Zero maps to null; 1 through 8 map to the monitor's corresponding associated position; other integers fault |

Data/ROM numeric domains are zero through the manifest's `data_rom_encoding_max`, including cached inspection of expired values. That does not preserve expired association through reconstruction. The I/O bias distinguishes the non-null register at coordinate zero from null without assuming a special CPU port number.

| Round trip | Exact guarantee |
| --- | --- |
| Data/ROM pointer to integer and back | Typed null, or a live strictly interior pointer uniquely mapped in that space with canonical object/space rights. Same identity, byte position, and usable rights are restored |
| Data/ROM integer to pointer and back | Every accepted numeric value, including an address-only result; exact bits, zero-extended to the selected width |
| I/O pointer to integer and back | Null and live monitor positions 0 through 7 with canonical rights |
| I/O integer to pointer and back | Exactly the accepted numeric domain 0 through 8 |

Pointer round-trip guarantees exclude one-past positions, expired allocations, and attenuated rights. An adjacent object's start may reconstruct a different identity from a one-past pointer with the same coordinate. An unregistered boundary reconstructs address-only. There is no silent recovery of provenance from arbitrary integer history.

`rom` contains constant-initialized immutable ROM objects. Those same objects are also addressable through a read-only `data` view. Both conversion directions preserve identity and coordinate; `data -> rom` faults for RAM objects. All conversions to or from `io` and another space are unsupported. This set of profiles does not expose device aliases through `data`.

A native coordinate does not necessarily equal a native address-register encoding. 8086 raw addresses use canonical `segment = physical >> 4`, `offset = physical & 15`; kernels recompute segments before an access could wrap. The 286 protected profile uses selector 0x08 for its 64-KiB code region and selectors `0x10 + 8*k` for sixteen 64-KiB data windows. MIPS uses an uncached KSEG1 native address for its low physical reference memory while packet fields and cached coordinates retain the normalized physical value. The manifests give these translations explicitly.

### Physical Call-Packet ABI

The default ABI is a project-owned packet convention. No fixed or additional logical value argument is passed directly in a native value register. The listed incoming register(s) carry a runtime-private native address of the call packet. Every normal result and exceptional payload also travels through that packet.

The caller reserves a packet in its software stack. It begins with the 64-byte header in `contracts.json`; all sixteen fields are target-endian `u32`. Packet-relative offsets are mathematical nonnegative offsets, not wrapping SMIL address arithmetic. Header magic is `0x534d494c`.

The header records the complete signature ID, fixed/additional argument counts, argument table, normal/exceptional payload locations, outcome, callee identity, caller frame, saved stack top, and optional software continuation. Reserved fields are zero. Packet alignment is the profile cap. A zero argument count uses argument-table offset zero.

Each argument-table entry occupies 16 bytes: type ID, payload offset, allocation size, and reserved zero. Entries appear in source argument order. Payloads follow the table, each rounded to its type's alignment and using the ordinary storage encoding. Padding in ABI payloads is set to zero. Arguments are copied by value and do not expose the packet as source-level storage.

After all argument payloads, the caller reserves one region aligned for both outcome types and large enough for the greater of the normal-result tuple and raised payload. The ordered result tuple uses the ordinary record field-layout rule without acquiring a source-visible nominal type. The normal and raised offsets name that same region when both exist. A nonexistent carrier has offset zero. Only the selected carrier may be read.

The callee writes the selected payload and then sets outcome 1 for normal completion or 2 for `raise`. Outcome 0 means pending. A non-raising signature cannot return outcome 2. Hardware flags and native return registers are not result carriers. Termination does not manufacture an outcome.

The callee validates the target/signature and packet before consuming it. Entry SSA values are reconstructed from matching descriptors. The caller copies the selected results into storage that survives packet release before restoring the saved software top. Hidden result backing must not refer to freed packet bytes.

`signext`/`zeroext` remain integer signature attributes. This ABI has no wider integer register carrier for logical values, so they request no additional physical widening. Unused representation bits retain their canonical zero encoding. Effective attribute identities still participate in callable compatibility.

The manifest lists all caller-clobbered and preserved native resources. No other native register carries a source-level preservation promise. CPU condition flags are not live logical values across calls. Hardware stack pointers and required processor modes must be restored on normal or raised return.

The 6502 ABI additionally reserves zero-page bytes 0x20 through 0x3f as call-clobbered native scratch. Neither application globals nor the monitor may assume preserved values there across a call. Other families use only their explicitly reserved runtime region for scratch.

### Invocation Frames and Native Return Mechanisms

Software frames grow upward within the manifest's dedicated region. Each has the 32-byte private header in `contracts.json`, followed by local objects in declaration order with required alignment, then backend temporary/spill/call-packet storage. The compiler computes or bounds each frame extent before it is reserved. Checked addition precedes reservation; overlapping the region boundary faults.

The native return stack is separate from addressable `alosf` storage. Native stack use must be preflighted before a call, push, or link-save frame; implicit hardware wrapping is never a conforming overflow response. The emergency portion specified in the manifest is unavailable to ordinary calls and is reserved for a nonreturning reporting path.

| Family | Native call/return rule |
| --- | --- |
| 6502 | `JSR`/`RTS`; S is a page-one postdecrement stack. Indirect transfer uses a validated dispatcher/trampoline without writable code |
| 6800 | `JSR`/`RTS`; SP postdecrements. Indirect calls may use generated function-ID dispatch that preserves the incoming X packet address |
| 8008 | No generated `CALL`, `RST`, or `RET`; save a linker-assigned continuation ID in the packet and use static jump dispatch for call and return |
| 8080/8085 | `CALL`/`RET`; SP predecrements. Function-ID dispatch avoids assuming that an indirect call can preserve H:L without a thunk |
| 8086 real / 286 protected | Far call and `RETF`; SS:SP uses checked 16-bit stack offsets. These modes have different code/data address translations |
| Intel 32-bit | Near call/return with four-byte return addresses; ESP alignment four |
| 68k | `JSR`/`RTS` and four-byte return addresses; A7 alignment two on MC68000 and four in later reference layouts |
| PowerPC | r1 alignment 16; reserve 16 bytes with previous r1 at offset zero and saved LR at offset four; restore before `blr` |
| ARM7 | ARM-state calls; reserve eight bytes, saved LR at offset zero; return to an ARM-state address |
| MIPS I | Reserve eight bytes with saved r31 at offset zero; honor branch and load delay slots; default fill is `NOP` |
| SPARC V8 flat | Keep the application register window fixed; reserve eight bytes with saved %o7 at offset zero; return via %o7+8 with a `NOP` delay slot |

For predecrement stacks, bootstrap SP is the region end rounded down to native alignment. For postdecrement stacks it is the last usable byte (or the corresponding S index). Bounds checks use the actual ISA convention, including implicit return-address writes. Link-register families reserve their stated save frame before another call can overwrite the incoming link.

Static function and continuation dispatch includes every retained callable/continuation target and checks IDs before selecting a branch. It does not require a computed-jump instruction or self-modifying code. Compiler-introduced kernel calls on the 8008 use the same software-return rule; the hardware stack limit is not bypassed by an undocumented runtime exception.

### Function References, Variadics, and Raised Results

A function reference contains a target-endian `u32` function ID followed by its exact callable signature/type ID. Null is the zero pair. Linker function records contain function ID, signature ID, normalized native entry coordinate, and reserved zero, each `u32`. Each ID resolves to one fixed target for the instance lifetime.

`fnaddr` constants and stored function values use function-ID relocations, not an assumed code/data-pointer equivalence. Before indirect entry the runtime checks both IDs against the function catalog, translates the entry coordinate to its native encoding, and dispatches. Foreign function pointers, C calling conventions, and dynamic code loading are not automatically supported by this private ABI.

All reference profiles support explicit variadic calls, typed receipt, and runtime pack forwarding. A borrowed pack identifies the owning live invocation's additional descriptor range. `va_is` compares exact logical type IDs; `va_get` checks the full unsigned index and type before copying a complete value; `va_count` checks its result width. Forwarding allocates another packet and copies the selected additional values/descriptors. It neither borrows expired packet bytes nor silently changes source types.

No profile advertises native C varargs receipt or forwarding. Those require an adapter with a defined type-information contract. Recognizing a machine `va_list` layout is insufficient.

`raises([E])` uses the packet's outcome tag and E carrier. The ABI introduces no native unwinding dependency. Both normal and exceptional completion expire the callee's local object identities before transfer to the caller's appropriate explicit edge. Source cleanups remain the frontend's CFG responsibility.

### Reference Monitor, Port I/O, and Device Contract

`smil.ref.monitor.v1` is the only predefined device contract in this set. It is an eight-register logical I/O region, not a claim about a UART chip. Its pointer coordinate is the logical register offset, independent of a CPU's port or memory address.

| Offset | Permitted transaction |
| --- | --- |
| 0 | Read one `i8`, always returns 1: transmitter ready |
| 1 | Write one `i8`, emits that byte once |
| 2, 3, 4, 5 | Write result bits 7:0, 15:8, 23:16, 31:24 respectively |
| 6 | Write command 1 to report orderly exit or 2 to report a terminal fault, then stop the instance permanently |
| 7 | Read one `i8`, always returns zero |

Result bytes are written in offset order 2, 3, 4, 5 before command 6. This explicit little-significance-first protocol is independent of ordinary target byte order. Other directions and widths, including `i1`, fault or are rejected when statically known. There is exactly one committed transaction per access, no widening, no posting, no DMA, and no device-shared ordinary region.

On 6502/6800 reference boards these registers use memory addresses starting at 0x7ff0. On 8008 they map reads at offsets 0/7 to input ports 0/1, and writes at offsets 1..6 to output ports 8..13. On 8080/8085/x86 they use isolated I/O ports starting at 0xf0, with only the permitted directions. Dynamic register selection on CPUs with immediate-only port instructions uses a checked finite dispatch, not an extra probing read.

68k, PowerPC, ARM7, MIPS, and SPARC reference environments expose synchronous monitor services. The manifest specifies the trap instruction and selector/offset/byte/result registers. Service selector 0 performs a read, 1 a write, and 2 a device fence. A successful service implements precisely the device transaction above, returns a read byte in its result register, and restores native SP and processor execution mode. Other caller-clobbered registers may change. Service instructions/trap entries are runtime implementation details, not catchable SMIL exceptional transfers.

The environment supplies these services as an exact, nonspeculative device interface. A physical monitor port must implement the required ordering with appropriate device mappings/barriers; an emulator may implement the transaction at service retirement. Unsupported monitor behavior is not excused by the CPU's ability to execute the trap instruction.

`mmio_fence` completes preceding synchronous monitor transactions and forms the compiler memory boundary. There are no DMA/shared-memory observers in this contract, so it promises no device access to application RAM. Adding a real UART, framebuffer, DMA engine, or shared-memory device requires another explicit device/environment contract. The `io` space remains distinct from ordinary registered memory.

### Atomic Agents, Alignment, and Progress

These reference environments have exactly one application agent, `main`. Application interrupts, asynchronous reentry, additional CPUs/threads, DMA mutation, and concurrent foreign callbacks are unsupported. Interrupt/NMI gating and processor modes are explicit environment requirements, not an inference from the CPU family. An environment exposing another agent does not conform to these profile versions.

All core integer atomic operations are supported for widths 1 through 65535 on actual live ordinary integer locations. Their alignment equals the ordinary declared type's alignment. A finite byte-vector sequence is indivisible with respect to this advertised agent set because there is no competing participant; it is not advertised as interrupt-safe or multiprocessor-atomic.

Helpers use no locks and complete in a finite number of steps for finite operands and sufficient reserved resources. This is a bounded nonblocking reference implementation guarantee, not a claim about a native lock-free bus instruction. `seq_cst` fences preserve the required compiler ordering; no unsupported modern fence opcode is emitted on an old CPU.

A later interrupt-capable or multiprocessor profile must provide its own agent set and interoperation rules for every atomic path. Reusing one of these profiles while merely enabling interrupts would violate its contract.

### Runtime Catalogs, Helpers, and Lifecycle Interfaces

Runtime catalogs have program-wide nonzero IDs. Integers, data-pointer types, function-reference types, records, internal result tuples, and callable signatures have distinct descriptor kinds. Transparent aliases share IDs. Nominal record references use their resolved program-wide identity and are not recursively expanded into an infinite type string.

For deterministic IDs, construct finite canonical JSON descriptor keys using resolved nominal identities and resolved ABI/attribute/effect selections. Structural references in these keys use structural keys or nominal identities, never provisional numeric type IDs. Sort their UTF-8 encodings and number from one. Global and function catalogs similarly sort fully resolved symbol identities. Continuation keys include the resolved function identity and compiler-emitted unique continuation label. IDs and catalogs are emitted together and validated before execution; their particular numeric values are not source-level constants.

The image descriptor contains each type's kind, width/count, representation/allocation sizes, alignment, field offsets and referenced type IDs; each signature's fixed/result type/attribute lists, variadic flag, and raised type; each global's placement, type, identity, permissions and readiness; and every function/continuation's native entry coordinate. The code generator may emit equivalent specialized type checkers and ROM lookup tables instead of parsing JSON at runtime. The sidecar remains sufficient to validate their agreement; ROM tables and IDs cannot silently diverge.

The reserved runtime region begins with the 128-byte context, then `object_slots * 48` registry bytes, then `callback_slots * 8` callback bytes. Remaining bytes are private runtime scratch. The manifests give all capacities and addresses. Wide integer work buffers and variable packets use preflighted software-stack temporary space, not an assumed unbounded scratch buffer.

`contracts.json` lists all ordered context, frame, object, packet, and helper fields. Runtime-private `Raw`, `FrameRaw`, counts, modes, and metadata IDs are backend types, not source `ptr` values and not an alternate way to forge an allocation association.

| Helper class | Required lowering contract |
| --- | --- |
| `smil.rt.int.<opcode>.n<N>.v1` | Core operand order and result tuple, exact N-bit semantics; signed/unsigned division guards and full shift-count handling |
| `smil.rt.ptr.<opcode>.t<TypeID>.v1` | Core pointer operand/result forms, registry/coordinate/rights and required conversion checks |
| `smil.rt.mem.<opcode>.t<TypeID>.v2` | Representation-aware access/copy; all required validity checks before effects; no neighbor writes |
| `smil.rt.atomic.<opcode>.n<N>.v2` | Exact core results/flags and seq_cst behavior within the single-agent domain |
| `smil.rt.va.<opcode>.t<TypeID>.v1` | Borrowed packet descriptors, unsigned indexing, exact types, safe copying/forwarding |
| `smil.rt.fn.<opcode>.v1` | Function/signature identity checks and native dispatch without writable trampolines |
| `smil.rt.life.v2` | Bootstrap, initialization, exit registration, orderly exit, callback drain, and terminal reporting |
| `smil.rt.init.<opcode>.v1` | Reset/check/mark exact initialized representation state; preserve staged validation and preflight shadow storage |

Each helper specialization has the core operation's logical operands/results, plus only the explicitly declared runtime-private annotations. Helper calls use the same physical packet convention and clobber rules. Allocation/access/dispatch/lifecycle private entry signatures are listed in `private_runtime_entries`. Their `never` result means a nonreturning native transfer, not a new source-level SMIL type.

A backend must supply a lowering closure for every operation it accepts: a native sequence, a generated helper specialization, or a linked conforming helper. A textual helper name is not an implementation. If a required helper is absent, object generation/linking fails. Native expansions must retain division/remainder edge cases, carry/borrow meanings, canonical stores, pointer state, and terminal events.

The only source program entry is `@smil_main() -> ([i32])`, with the default packet ABI, no variadic marker, and no raised effect. The coordinator installs constant values, executes the linked dependency plan, publishes readiness, invokes entry, and reports its returned i32 bits after orderly shutdown. Language-specific entry signatures need wrappers.

Only `main` may call `on_exit` or `exit`. Callback registration uses the fixed-capacity LIFO table and validates a non-null zero-parameter/zero-result, non-raising default-ABI function reference. Before invoking an initializer that has a completion callback, the coordinator reserves callback capacity; it commits that entry only after successful return/value installation. An exceptional initializer discards its reservation and drains previously committed callbacks as defined by Program Lifecycle.

Quiescence is concrete and simple: no other application agent or DMA engine can be active, and the environment keeps asynchronous application entry gated. Explicit `exit` expires abandoned local identities, resets software/native call state to the coordinator's reserved root context, and then invokes callbacks. A callback cannot resurrect expired stack objects. Terminal reporting uses no new packet allocation or ordinary native call, so stack exhaustion cannot recursively prevent reporting. Monitor traps may use architectural exception state and the pre-reserved emergency stack; this context is reserved before ordinary execution and does not require an allocation from an exhausted application stack.

Built-in fault IDs are fixed in `contracts.json`. User fault identifiers are assigned IDs starting at 65536 in UTF-8 identifier order and recorded in the image. A terminal path writes the fault ID to result registers 2..5 and command 2; orderly termination uses the exact i32 status and command 1. Neither path resumes or restarts the instance.

These profile successors implement the portable `smil.execution.checked.v1` rules below, including terminal `resource_exhausted` for capacity/counter/tracking failures and `uninitialized_read` for missing value bits. Static impossible placements are diagnostics; dynamic exhaustion never wraps, reuses an identity, or overwrites another frame. Their single-agent domain proves race freedom without a detector. The execution contract defines required fault priority, metadata accounting, and optimizer assumptions.

### Relocation and Linked-Image Contract

The profile's executable format is `smil.ref.image.v1`: a UTF-8 JSON descriptor plus fixed-placement raw binary segment files. The descriptor records format/profile/digests, entry function ID, segment addresses/lengths/digests/kinds, resolved catalogs, the initialization plan, and user fault IDs. Each segment must lie wholly within its permitted manifest region. Unmapped holes are not ordinary RAM. A conforming reference monitor establishes the declared CPU mode and native stack, then enters the image's native bootstrap.

For these reference images, all static relocations are applied before bootstrap observes values. There is no dynamic linking, rebasing, native OS executable ABI, or relocation-time execution of a factory. Constant ROM contains its final encoded values. Dynamic globals reside only in writable ordinary RAM.

| Relocation | Encoding and checks |
| --- | --- |
| `ABS8`, `ABS16`, `ABS32` | Full mathematical address plus addend; unsigned width check, then target-endian storage |
| `SLICE8`, `SLICE16` | Validate the complete address first, then extract the requested significance slice; no overflow hidden by truncation |
| `PCREL8`, `PCREL16`, `PCREL32` | Target plus addend minus an explicit PC-anchor address; signed width check before encoding |
| `CHECKED_PTR` | Resolved global/region identity, allocation-relative offset, normalized address, and intersected rights in the 16-byte format |
| `FNREF` | Function ID and exact signature ID in the eight-byte format |
| `ID32` | Nonzero resolved type/object/function/continuation ID with an explicit namespace |
| `RAW_ENTRY32` | Normalized function entry coordinate; transfer applies the native address translation |
| `BITFIELD32` | Checked scaled signed/unsigned expression inserted into an explicit contiguous instruction-field mask, preserving other bits |

Every relocation record identifies destination segment/byte offset, target namespace/key, and a mathematical signed addend. PC-relative records identify a segment-relative PC anchor explicitly; they do not assume that every CPU measures displacement from the same point. Slice records specify the significance shift.

A `BITFIELD32` record additionally specifies signedness, field bit count, destination bit offset, optional PC anchor, and power-of-two scale. Evaluate the full address/displacement, require exact divisibility by the scale, check the scaled value's field range, and insert its two's-complement bits into a four-byte target-endian instruction word. Invalid alignment/range or overlapping relocation fields are diagnostics. Local branch relaxation may replace an instruction sequence, but it must repeat affected range/placement checks.

`CHECKED_PTR` selects an actual allocated global/region subobject; its offset and final coordinate cannot wrap. Its recorded allocation ID does not create a second allocation. Code-address integer relocations into source pointer/integer values remain prohibited; `RAW_ENTRY32` is runtime-private function-catalog metadata.

Modules, Interfaces, and Static Linking below defines the machine-object/import/export transport and completes image provenance and lifecycle metadata. Those formats preserve these relocation records and resolved compatibility identities. A linker cannot claim this image contract by dropping a relocation it does not understand.

### Implementation Direction and Acceptance Vectors

Implement the checked runtime and packet lowering once as logical/backend services, then add the small native kernels for byte access, arithmetic, branches, call/return, and monitor transport. CPU encoders own instruction legality, native address translations, delay slots, and relocation fields. Frontends retain the same signless integers, records, SSA, and explicit CFG.

A practical first implementation order is 8080 or 6800, then 6502/8008, 8086/286, 68k, and the early-modern families. This is an implementation sequence, not a claim that the later manifests are already backends. Keep the reference packet ABI as an interoperation baseline; introduce faster register ABIs or native platform ABIs under distinct versioned identifiers after measuring them.

Before advertising a profile, verify at least:

- Non-native widths, including `i1`, `i3`, `i12`, `i24`, and `i64`, across arithmetic, shifts, division/remainder and carry/overflow.
- Both byte orders, empty/nested records, field offsets, checked pointer/function-reference copies, and constant relocations.
- Recursion, frame reuse, dangling-pointer equality versus invalid access, one-past boundaries, and failure before stack/table overflow.
- Packet offsets and preserved/clobbered resources, multi-result and exceptional outcomes, typed variadic receipt/forwarding, and indirect-target checks.
- Segmented-address boundary crossing, 8008 software-continuation depth, RISC delay slots, and instruction subsets on each named CPU.
- Exact device transaction counts, terminal fault/status reporting, deterministic startup order, failed initialization, and LIFO shutdown.

The accompanying validator checks manifest structure, digests, memory/metadata budgets, layout vectors, packet arithmetic, coordinate normalization, and catalog coverage. CPU execution and backend conformance require emulator or hardware runs once those implementations exist.

## Modules, Interfaces, and Static Linking

A **module** is the unit of source-level ownership, separate compilation, and lifecycle registration. A **program instance** is one statically linked selection of modules and its runtime state. Importing a module makes declared interfaces available to verification; it does not execute code or initialize storage.

This section defines explicit module identities and visibility, an interface transport (`smil.interface.v1`), a relocatable machine-object transport (`smil.object.v1`), library indexes (`smil.library.v1`), and a whole-program link manifest (`smil.link.v1`). It also specifies the metadata carried into the existing `smil.ref.image.v1` descriptor. These are proposed project formats, not an implementation of a linker or a platform object ABI.

### Module Headers and Imports

A complete, separately publishable module begins with its identity, followed by an optional target directive and its imports:

```SMIL
module "example.geometry.v1"
target "smil.ref.mc68020.checked.v2"

@Point = record { i16, i16 }
$unit = const [i16 1]

declare @translate([Point], [i16], [i16]) -> ([Point])

export type Point
export $unit
export @translate

func @translate([Point], [i16], [i16]) -> ([Point]) {
^entry(%p: [Point], %dx: [i16], %dy: [i16]):
    %x = record_get %p field(0)
    %y = record_get %p field(1)
    %nx = add [i16] %x %dx
    %ny = add [i16] %y %dy
    %result = record_make [Point] (%nx, %ny)
    return %result
}
```

A consumer imports that exact module identity under a local qualifier:

```SMIL
module "example.application.v1"
target "smil.ref.mc68020.checked.v2"
import "example.geometry.v1" as geo

@Position = type [geo::Point]
$step = const $geo::unit

func @smil_main() -> ([i32]) {
^entry():
    %p = record_make [Position] ([i16 3], [i16 4])
    %q = call @geo::translate(%p, $step, $step)
    return [i32 0]
}
```

A module identity is a nonempty UTF-8 string without NUL. Identity comparison uses exact Unicode scalar sequences encoded as UTF-8; no case folding, Unicode normalization, path canonicalization, or version-range interpretation is performed. The conventional `.v1` suffix is part of the identity, not a package resolver. Build configuration maps the identity to an exact interface and implementation. Filesystem location, timestamps, source filenames, and linker input order are not identities.

Every independently generated object owns exactly one module identity. Version 1 has one object per module; implementation splitting must first combine fragments into that module, with duplicate and type checks. Distinct library versions may coexist only under distinct module identities. Two implementations claiming the same identity in one selected program are an error even when their exported signatures happen to match.

An import alias is a module-local identifier, unique in the qualifier namespace. It is not a type, constant, value, or address-space name. Repeated aliases and self-imports are rejected. Multiple aliases for one provider are allowed and denote the same entities. Imports precede declarations, definitions, and exports. Export statements may otherwise occur anywhere among module items.

The initial portable spelling of an import alias or qualified member is `[A-Za-z_][A-Za-z0-9_]*`. `::` separates exactly one alias and one exported member; no whitespace occurs inside that qualified name. The sigil precedes the alias once: `@geo::translate`, `$geo::unit`, and bare `geo::Point` in a type expression. Function-local SSA and block names cannot be module-qualified. The complete source chapter below defines all remaining identifier and token rules; import qualifiers follow that same ordinary-name spelling.

Earlier examples without headers remain fragments or anonymous verification units. They do not acquire a filename-derived identity and cannot be published as interfaces or objects until given an explicit module identity. A module header precedes its target directive; the target directive still precedes imports and all declarations and definitions.

### Visibility, Exports, and Name Resolution

Every locally defined entity is private unless explicitly exported:

```SMIL
export type Point
export $unit
export @translate
```

`export type` selects the type namespace, `$` the named-constant namespace, and `@` the shared function/global-storage namespace. Each export names a definition owned by the current module. A compatible local function declaration may precede its definition, but exporting an unresolved declaration is an error. Version 1 has no implicit exports, wildcard imports, public renaming, or re-export statements. A public type alias may name an imported type and preserves that type's identity.

An import exposes only the provider's exports through the selected alias. It does not introduce unqualified names or transitively expose the provider's imports. A client needing to name another module's export imports that owner directly. Unqualified identifiers continue to resolve in their existing local/module namespaces; a function-local type may shadow a module type, but it cannot shadow a qualifier within `alias::member`.

A local `declare @f` describes a function owned by this module and does not search other modules for a matching spelling. Intermodule calls use an imported qualified symbol. Imports do not require or permit a second local function/global declaration for the imported entity; its authoritative declaration comes from the pinned interface. There is no ambient global namespace populated by linker discovery.

The canonical symbol key is the three-element JSON array `[module_identity, namespace, local_name]`, where the source namespaces are `type`, `constant`, and `value`. Function and global keys both use `value`; their symbol kind distinguishes them. Local spellings and aliases are resolved to this key before object emission. JSON arrays, rather than separator-concatenated strings, prevent ambiguous keys. Runtime-private machine labels use a separate `aux` namespace, are never source exports, and have no SMIL address by themselves. Ordinary `aux` labels are module-private; a declared runtime contract may separately authorize a particular helper binding across modules, without making it a source export.

Global/function definitions must be unique by canonical value key and have one kind. Local function declarations must all agree and have exactly one selected definition when required. Duplicate exports, type or constant definitions, mismatched declarations, unresolved imported members, and kind mismatches are diagnostics. There are no weak definitions, tentative/common storage, first-definition wins, symbol interposition, COMDAT selection, or implicit native-name fallback in these versions.

An imported global exposes its actual object type, space, and mutability. A client cannot redeclare mutable contents as immutable, strengthen rights, or change the object's initialization mode. Importing an immutable global is not permission to treat a not-yet-ready dynamic initializer as a compile-time constant.

### Nominal Identity and Interface Type Closure

A module-level record's nominal identity is `["record", module_identity, "module", declaration_name]`. A function-local record uses `["record", module_identity, "function", owning_function_name, declaration_name]`. Local records remain forbidden from escaping through module-level types, constants, storage declarations, or function contracts. An imported record keeps its originating identity; the importing module does not create a new record.

```SMIL
// Module "a.v1"
@Point = record { i16, i16 }
export type Point

// Separate module "b.v1"
@Point = record { i16, i16 }
export type Point

// In a consumer importing them as a and b:
@APoint = type [a::Point]
// APoint and a::Point are identical after alias resolution.
// b::Point is a different nominal type despite equal field layouts.
```

Transparent aliases disappear for compatibility checks. Exported alias spellings remain in the interface's export table so a consumer can resolve them, but do not create new nominal identities. Structural integer, pointer, and callable types compare recursively after alias resolution; records compare by identity and must also have consistent authoritative field definitions. Callable comparison includes parameter/result order, effective extension attributes, variadic status, raised type, and resolved ABI.

Interfaces contain the complete finite type graph reachable from exports, including record fields reached through pointers, raised payloads, function-reference types, and constant values. Private module-level records appearing in that closure are included by their real identities even if they have no separately exported type spelling. There is no opaque-record boundary in version 1; abstract handles can use an exported representation selected by the frontend, and a future opaque-type facility requires a separate contract.

A provider is authoritative for its owned nominal records. An interface may include imported record descriptors as snapshots, but they must match the selected owning provider's descriptors. An importer cannot supply a replacement definition for an owner absent from the selected module closure. Record comparison follows nominal references instead of recursively expanding them forever. By-value layout cycles and cyclic transparent aliases remain invalid; recursion broken by a pointer remains permitted.

Interfaces can be collected before verifying bodies, so mutually importing modules are permitted. Import cycles do not establish startup order and do not excuse missing owners. Interface digests do not recursively contain dependency digests, avoiding a hash cycle; the build lock and each object pin their direct providers separately.

### Compatibility Fingerprints and Recompilation

An interface has a logical payload containing its module identity, target selection, export table, complete public type graph, and normalized exported constant values. Its `requires_modules` lists the byte-sorted unique foreign owners referenced by that public graph or its symbolic constants; these are interface requirements, not lifecycle edges or recursively embedded interface digests. `interface_sha256` is the canonical-JSON SHA-256 of this payload, using the profile bundle's existing canonical JSON rules. The export table is sorted by the canonical JSON encoding of `[namespace, name]` in unsigned UTF-8 byte order; type labels and owner lists use the deterministic orders below. Implementation bodies, private definitions outside the public type/constant closure, paths, timestamps, diagnostics, and build notes are excluded.

An unbound interface has `target: null` and uses the explicit ABI token `default` where resolution is deferred. It supports structural checking and target-independent transformations. A target-bound interface records the exact profile ID/digest, shared-contract digest, and resolved component IDs; all defaults and layout-dependent constants are resolved before object generation. An unbound fingerprint is not an acceptable substitute for a bound fingerprint at machine linking.

Source verification uses a build-supplied map of module identities to interface payloads and their exact digests. Every generated object records the bound digest used for every direct import, including imports used only for types or constants. The compiler adds object import locks for foreign owners introduced when it expands imported public type graphs or symbolic constants; these locks authorize metadata references and select providers, but introduce no extra source-visible qualifier. A final link must select those exact bound interfaces. A changed exported constant, nominal definition, callable effect, storage declaration, or profile contract invalidates that match. Version 1 uses whole-interface fingerprints; accepting only a compatible subset of a changed interface is a possible future extension.

Changing a private implementation without changing the canonical interface does not require client recompilation. Changing a dependency's private implementation still requires checking its new object digest in the selected build lock. Digests establish content identity and consistency, not trust in a provider's code.

The object carries an interface-local type table extending the interface table with implementation types. Type labels are references, not runtime type IDs. They are deterministically assigned by sorting canonical type keys: an integer key is `["integer", N]`; a pointer key is `["pointer", space, pointee_key]`; a record key is its nominal identity; a callable key contains ordered parameter/result keys and attributes, variadic flag, raised key or null, and ABI. Structural expansion stops at record identities. At final catalog construction, the linker also synthesizes a distinct `["signature", callable_key]` descriptor for each callable contract and `["tuple", ordered_result_keys]` for its normal-result carrier; the function-reference representation points to that signature descriptor rather than conflating the two kinds. Public labels are `t` followed by a six-or-more-digit, zero-padded decimal ordinal starting at one; private labels continue in sorted private-key order. Neither provisional type labels nor runtime numeric IDs participate in these keys. Equal keys have one descriptor; conflicting descriptors for one nominal key are rejected.

### Interface and Object Transport

The accompanying `smil_linking_v2/schema.json` gives the closed record shapes. This section supplies cross-record semantics that JSON Schema alone cannot express. Unknown semantic fields, enum values, format versions, and required contracts are errors. Optional nonsemantic tool notes are confined to a `notes` object and excluded from the interface payload. Duplicate JSON keys, floats, invalid UTF-8, and non-scalar Unicode strings are rejected.

| Artifact | Required contents |
| --- | --- |
| `smil.interface.v1` | Format, canonical logical `payload`, its `interface_sha256`, optional nonsemantic `notes` |
| `smil.object.v1` | Owned module ID, exact bound target record, embedded interface, direct import locks, complete type table, definitions, sections, references, relocations, continuations, runtime requirements, lifecycle nodes, user-fault identifiers |
| `smil.library.v1` | Unique module entries with relative object paths, canonical object digests, and bound interface digests |
| `smil.link.v1` | Exact target record, root object entries, available library entries, explicitly included module IDs, qualified entry key, additional retained keys |
| `smil.ref.image.v1` | Existing fixed-placement segment files and descriptor, completed with linked catalogs, initialization plan, selected-object provenance, and validated target/contract identities |

An object is a JSON descriptor plus raw section blobs. A section records its unique module-local section ID, kind (`code`, `rodata`, `data`, `runtime`, or `metadata`), alignment, byte length, relative blob path, and SHA-256 of the raw bytes. Its size is exactly the file length. There is no implicit host-native structure packing, endianness, compressed code, zero-fill assumption, or relocation-time executable expression in this transport. A dynamic global's reserved bytes are not an initialized SMIL value, even if its blob contains zeroes.

All blob/object/library paths are relative to their containing descriptor, with `/` separators; empty components, `.`/`..`, absolute paths, backslashes, and symlink escapes are invalid. Descriptor digests cover canonical JSON; blob and final-image segment digests cover the exact bytes. Section sizes and positions are unsigned JSON integers within `u32`; relocation addends use canonical signed decimal strings without a leading plus, leading zeroes, or negative zero. Evaluation uses mathematical integers rather than host integer wrap.

Definitions record canonical key, kind, type label where applicable, export visibility, owning section, offset, extent, alignment, global mutability/space/initializer mode where applicable, and a `constant_value` tree for a constant global (null otherwise). Separate reference records give their complete dependency edges. Function definitions locate their first native instruction in `code`; global definitions locate one distinct allocation in `data` or `rodata`. Runtime-private `aux` definitions can describe code, pools, or metadata and may overlap an enclosing function extent; distinct globals may not overlap. The linker validates section bounds/alignment and each global's bound type layout. After relocation, a constant global's blob bytes must represent its recorded initializer under that layout; ordinary padding is not a logical field. A dynamic global has no constant tree and must have exactly one matching lifecycle node. Source constants are interface values, not allocated definition entries.

Every semantic dependency of emitted code or data must be represented: direct calls, function-address formation, global accesses, address constants, helper use, type descriptors, and machine-label references. A relocation implies its target dependency, and nonrelocating dependencies are recorded as reference edges from their containing definition. The linker checks the target against the selected module's export/private ownership rules and the consuming object's import locks. Runtime requirements record the exact contract token, binding key, callable descriptor, opcode if applicable, ordered type arguments, and ordered integer arguments. Type-specialized helper names use symbolic descriptor keys until final catalog assignment; a provisional numeric type ID is never baked into an untracked symbol. Only a validated runtime requirement permits a cross-module `aux` helper reference; arbitrary foreign `aux` access remains invalid. It cannot recover missing semantic edges merely by disassembling arbitrary machine bytes. Object producers are responsible for complete edges and exact machine-call contracts.

Version 1 conservatively retains all definitions and sections in every selected module. This preserves lifecycle effects and address identity without requiring an initial garbage collector. Reference edges remain mandatory for resolution, verification, future elimination, and helper closure. A later elimination pass may remove private definitions only after proving reachability from entry, retained exports/keys, every selected lifecycle node, constant/address references, and required runtime machinery, then recomputing catalogs and placement. It cannot drop a selected module's lifecycle node merely because no ordinary call reaches it.

Distinct addressable globals are never coalesced because their bytes match. Linker-level identical-code folding and definition coalescing are absent in version 1. Source optimizations within a module remain permitted when they preserve identities, faults, address equality, and exported contracts.

### Serialized Types and Constant Values

The wire `function` descriptor expresses a callable contract used by a function-reference value or function declaration; the final runtime catalog separately identifies its function-reference representation and synthesized signature. The type table uses tagged descriptors for integers (`bits`), pointers (`space`, `pointee`), records (`identity`, ordered `fields`), and callable references (ordered typed/attributed parameters and results, `variadic`, optional `raises`, and `abi`). The non-storable borrowed `varargs` token is not a public/exported value type. Runtime-private raw carrier types use a separate `runtime` descriptor with an exact helper-contract token; they cannot appear in source exports or ordinary globals.

Export entries record namespace, exported spelling, kind, type label, and a value only for named constants. Record aliases are represented by the resolved descriptor label. A global export additionally records mutability, space, and constant-versus-dynamic initialization; a function export's callable descriptor supplies its complete signature.

Constant trees use these forms:

| Tag | Fields and meaning |
| --- | --- |
| `integer` | Type label and lowercase hexadecimal bits, prefixed `0x` and padded to exactly `ceil(N/4)` digits; high unused bits zero |
| `null` | Pointer/callable type label; target encoding is applied later |
| `record` | Actual nominal record type label and ordered constant field trees |
| `address` | Pointer type label, canonical exported/owned global key, field-index path, and signed decimal additional byte offset |
| `function` | Exact callable type label and canonical exported/owned function key |
| `expression` | Result type label, permitted constant opcode, ordered type arguments, ordered constant operands, and field-index path if applicable |

Alias and named-constant references are expanded before publishing an interface. Expression fields follow the core operation's argument order and arity; unused field paths/type arguments are empty arrays. Only operations already permitted in constant expressions may appear. There is no general link-time evaluator or arbitrary integer arithmetic on unresolved symbol addresses. Bound exported constants reduce to integer/null/record/address/function forms; a remaining expression means binding is incomplete. Address trees retain their root allocation and selected path through binding and become supported checked-pointer relocations.

A public symbolic address/function constant must target an explicitly exported symbol of its owner so another module can validate its reference. Exporting a pointer constant does not export its referenced private definition automatically. Private constant initializers within an object can still reference that object's private symbols. A returned runtime pointer/function value may refer to a private entity; this restriction concerns static cross-module symbolic naming, not runtime value transfer.

### Relocation Records and Final Catalog Assignment

Relocation records preserve the existing profile relocation meanings. Each contains `kind`, destination section/offset, target namespace and key, signed-decimal addend, optional PC anchor, optional slice shift/full-address width, optional bitfield parameters, optional pointer construction information, and optional callable type label. Unused optional slots are null; they are not ignored extension points.

Targets distinguish `symbol`, `type`, `continuation`, `region`, and `section`. Symbol keys are canonical triples; type targets use the consuming object's descriptor label; continuation keys are `[module_identity, function_name, unique_label]`; region keys name an exact profile region contract; section keys are `[module_identity, section_id]`. Sections, continuations, and ordinary `aux` machine labels are module-private; explicitly contracted runtime bindings use the exception described above. They cannot bypass source visibility or fabricate an ordinary data pointer. A region pointer is permitted only for a profile-declared associated device/storage region such as the reference monitor.

`ID32` additionally records its ID namespace (`type`, `object`, `function`, or `continuation`). A type target maps to the final canonical type catalog; object and function targets map to the corresponding global/function entries. Built-in device object IDs come from the profile. `RAW_ENTRY32` accepts a function or runtime-private code entry. Raw absolute/PC-relative instruction relocations are runtime-private machine references, not permission to encode a source-level code pointer as an integer.

`CHECKED_PTR` includes its pointer type, root global/registered region, field path, and requested rights mask. The linker checks each field selection, adds the signed byte offset, validates the full root extent including permitted one-past formation, intersects rights, and writes the actual root allocation ID and normalized coordinate. The constant remains a pointer value, not a numeric-address constant. `FNREF` requires addend zero and the exact callable descriptor. `ID32` and `RAW_ENTRY32` likewise require addend zero; ordinary byte-address addends belong to address relocations.

PC anchors are explicit locations in the consuming object's sections and must lie within those sections, allowing the end position. Slice relocations require an explicit full-address domain before extraction. For `BITFIELD32`, width/least-significant-bit/scale/signedness determine the insertion mask and range; scale is a positive power of two. Relocation write masks must not overlap, except disjoint bitfields in the same instruction word. All destination bytes must be within a blob; truncation, unrepresentable fields, illegal target kinds, or missing records are diagnostics.

Object-local type labels and continuation/function/global references are symbolic until whole-program binding. After resolution and retention, type keys and qualified function keys are sorted by unsigned UTF-8 bytes of their canonical JSON encodings and assigned IDs starting at one. Continuations sort by their canonical triple encoding. Globals use the existing allocation-ID sequence starting at 16, ordered by the same canonical qualified-symbol encoding; monitor ID 1 stays reserved. This defines the phrase “qualified-symbol byte order” used by the reference runtime. IDs are never exported as stable source constants.

The linker rewrites every ID-bearing location, including helper specialization references, callable signatures, packets or descriptors materialized statically, object root types, function references, and lifecycle records. A producer may not embed an untracked provisional ID. Fixed-profile numeric constants such as the monitor's reserved ID are the explicit exception. Layout and ABI fingerprints remain attached through relocation and are checked before writing bytes.

### Library Selection and Whole-Program Linking

A library index is a map of exact module identities to object paths, canonical object digests, and interface digests. It is packaging, not another definition namespace. Root objects and `include_modules` select modules unconditionally. A complete executable link additionally selects the mandatory runtime module whose identity equals the selected runtime component ID (for these profiles, `smil.rt.checked.packet.v2`). Its object must be provided and pinned like any other input; it is not a hidden host library. A data-only object fixture need not itself include this runtime, but cannot become an executable until the runtime and an entry module are supplied. Then every object import lock of a selected module selects that provider, repeatedly until closure. A provider must be unique across the root/library candidates. Merely listing an unselected library module does not run its constructors or retain its code.

This differs deliberately from a left-to-right native archive scan: an import selects the provider even if used only for a type or constant, and every selected module contributes its lifecycle nodes. A module containing only startup effects can be selected with `include_modules`; it need not export a dummy function. Selection is independent of input order. Cyclic imports reach a fixed finite module set, while lifecycle cycles still fail.

The link manifest identifies one canonical entry function key. For the existing reference profiles, its local name is `smil_main` and its exact contract is default-ABI `() -> ([i32])`, fixed arity, no raised effect. It may be private because the build manifest designates it directly. Other modules' same-spelled private functions do not conflict. A build-retained symbol must exist; this option does not expose it as an ordinary cross-module source import.

A complete link performs these steps:

1. Validate all descriptors, raw blob digests, direct import locks, and exact selected profile/contract/component identities. Reject duplicate providers and unknown semantic requirements.
2. Compute selected import closure and resolve every imported export and referenced owner. Validate authoritative type graphs, logical/callable/storage contracts, and complete runtime/helper requirements, including modules selected only for lifecycle effects.
3. Check that each required source or runtime symbol has exactly one matching definition. The mandatory runtime module binds each profile `private_runtime_entries` name to its same-spelled `aux` definition under the shared contract token `<contracts-id>#<entry-name>`. Its callable descriptor records the listed raw carrier types and default packet ABI. The `bootstrap`, `initialize`, `dispatch`, `request_exit`, `drain_callbacks`, and `fault` entries are required even when no user object explicitly references them; operation-dependent frame/access/device entries and helper specializations must also close. A separate untyped `aux` symbol named `bootstrap_entry` occupies the image's first native entry. This raw entry shim establishes context and an initial packet from reserved storage, then enters `bootstrap` with the image-metadata carrier; it is not callable through a source function reference. A runtime entry whose listed result is `never` has no result entries and a nonreturning obligation enforced by its contract token. Missing bindings or mismatched runtime carriers fail the link. Foreign native code requires an explicit checked adapter and interface; an ELF/COFF symbol spelling alone is insufficient. This transport accepts only `smil.object.v1` inputs: adapter code/metadata must be published as a conforming project object under the selected profile, and native container readers require a separately specified adapter/transport contract.
4. Validate and merge lifecycle metadata, resolve every dependency identifier, and diagnose duplicate nodes, missing dependencies, or cycles. Produce the stable initialization plan below.
5. Retain version 1's full selected object content, assign canonical catalogs, and place aligned sections within allowed profile regions. Validate writable/ROM restrictions, total native/software/runtime capacity, global table capacity, catalog size, and ID ranges. A declared runtime capacity cannot be silently enlarged into another region.
6. Apply checked relocations. A backend needing branch veneers/relaxation must emit them before final object publication, or use an explicitly contracted link-time relaxation pass that repeats placement, metadata, relocation, and capacity checks. Failure to fit is a diagnostic.
7. Emit final raw segments and the validated image descriptor. Loader validation precedes bootstrap; no import lookup, nominal merging, relocation factories, or constructor discovery occurs during application execution.

The linker must check all selected input contracts even if an optimizer could later remove the offending code. Changing a target cannot be implemented by editing the object header; target-dependent lowering and layout must be regenerated. The reference-profile version-1 exact component policy governs these objects; any more permissive future CPU-subset rule must explicitly revise that compatibility policy.

### Serialized Lifecycle Metadata and Image Provenance

Every dynamic global and `startup` statement contributes one lifecycle record, independent of ordinary symbol visibility. It contains:

| Field | Meaning |
| --- | --- |
| `id` | Exact program-wide UTF-8 initialization identifier |
| `kind` | `global` or `startup` |
| `owner_module` | Identity of the declaring module |
| `object` | Owned global key for `global`; null for `startup` |
| `action` | Canonical factory/startup function key |
| `after` | Unique prerequisite IDs, in byte-sorted order |
| `shutdown` | Canonical callback key or null |
| `result_type` | Global object's type label for `global`; null for `startup` |
| `raises_type` | Action's declared raised type label or null |
| `abi` | Exact resolved action ABI ID |

The object definition and lifecycle record must agree one-to-one for each dynamic global. Constant globals have no lifecycle nodes. Factories/hooks and callbacks are checked against their actual callable descriptors, including zero arity, result/raised contracts, no variadic pack, and supported ABIs. The callback's own descriptor supplies its ABI; it is not assumed to equal the action's ABI. The existing reference packet profiles require their default ABI for these callbacks.

Imports establish no lifecycle dependencies. Strings in `after(...)` remain absolute program-wide initialization IDs; they are not prefixed by the declaring module or rewritten through aliases. Two selected modules using one ID conflict. A dependency on a node in an unselected module does not cause archive discovery: explicitly import/include that module. Missing dependencies are diagnosed.

The merged graph is processed by Kahn's algorithm, always choosing the ready ID first in unsigned UTF-8 byte order. The emitted `initialization_plan` contains the complete resolved node records in that order, with global object IDs, action function/signature IDs, shutdown function/signature IDs when present, and final type IDs. Dependency IDs remain available for loader validation. No serialized node is interpreted as permission to call an initializer twice.

The existing image's `catalogs` is completed with arrays named `types`, `objects`, `functions`, `continuations`, `modules`, and `link`. The first four carry the established runtime descriptors and canonical keys; `modules` carries each selected module's interface and object digests, while `link` carries one record with the link-manifest digest, exact resolved component IDs, and linker-contract version `smil.link.v1`. The wire schema lists exact catalog fields. Type `references` are ordered field IDs for records/tuples, one pointee ID for a pointer, one signature ID for a function reference, and empty for integers/runtime carriers; signature parameter/result/raised fields carry their own references. Inapplicable nullable fields are null, lists are empty, and `variadic` is false. An internal signature has no stored value (`representation = allocation = 0`, alignment one); an empty result tuple also occupies zero bytes, unlike a source empty record. Runtime-private descriptors identify their exact `runtime_contract`. Interface payloads and complete type descriptors remain available in the descriptor for validation; a loader may discard host-only tables after validating them if the required runtime tables remain in image memory.

The image descriptor keeps the existing required top-level fields; provenance is carried within `catalogs` so the reference-profile manifests and their digests do not change. The finalized plan carries integer IDs instead of object-local labels. Existing numeric fault IDs retain their meanings; selected user fault identifiers are deduplicated and sorted bytewise before assignment from 65536. Module digests, catalog references, region bounds, function entries/signatures, and the regenerated topological order are validated before execution. A failed image check prevents entry; it is not a catchable SMIL fault after startup.

The loader performs no symbol resolution or relocation. It installs already linked segments, validates profile state and metadata, and transfers to the existing native bootstrap. For targets whose monitor cannot parse JSON on-device, an off-device loader performs these checks before installing the same segments; the executing CPU still receives the exact selected profile state. Host-only descriptor size is not charged as target RAM, but every runtime table actually used by generated code must be placed and charged in the target map.

### Linking Verification and Initial Implementation Direction

Keep module resolution, type identity, compatibility checks, lifecycle planning, catalog assignment, and relocation evaluation independent of CPU encoders. The backend contributes legal machine bytes, native call/entry encodings, section/alignment requirements, and typed relocations under the chosen profile. The same module and linker semantics therefore apply to 8008/6800, segmented Intel, later 68k, PowerPC, and the other reference families.

Start with the explicit full-retention linker and deterministic JSON transport. Validate it with both endian orders and two profiles whose layouts differ before adding dead stripping, compressed object containers, native object adapters, or optimized helper specialization. Native ELF/COFF packaging can later carry this metadata if it preserves every required identity, edge, relocation, and lifecycle record. The [ELF linking model](https://gabi.xinuos.com/elf/03-sheader.html) and [LLVM linkage definitions](https://llvm.org/docs/LangRef.html#linkage-types) provide useful comparisons; SMIL's version-1 ownership and duplicate rules above are project choices.

Required conformance cases include alias-independent imports, equal-layout distinct records, recursive imported records, consistent cyclic imports, stale interface fingerprints, duplicate module/value ownership, private-symbol access, mismatched raised/variadic/ABI contracts, symbolic addresses across modules, relocation overflow/overlap, malformed paths/digests, provider-order independence, startup-only library modules, missing/cyclic lifecycle nodes, failed initialization, and capacity failures on the smallest targets. A source-level declaration match alone is insufficient evidence of valid machine bytes or a conforming runtime.

## Names, Types, and Literals

SMIL distinguishes the following categories of names:

| Form | Meaning |
| --- | --- |
| `%name` | Function-local SSA identifier |
| `$name` | Module-level named constant |
| `@name` in a value context | Module-level value symbol identifying a global storage object or function |
| `@name` in a type declaration | Declaration of a type name |
| Bare `name` in a type expression | Reference to a declared type |
| `@alias::name`, `$alias::name`, bare `alias::name` in a type expression | Imported exported value symbol, constant, or type under a local module qualifier |
| Bare `name` in an address-space context | Address space defined by the selected profile |
| `^name` | Function-local basic-block label |

Type names occupy a namespace separate from module-level value symbols. Consequently, a type and a global storage object or function may have the same spelling without identifying the same entity.

Functions and global storage objects share the module-level value-symbol namespace. A function and a global storage object cannot have the same name within a module.

A symbol’s declaration determines its category. A global storage symbol cannot be called as a function, and a function symbol cannot be used as a data pointer. Function values are constructed explicitly by `fnaddr`; `fnptr` is a distinct kind of callable reference.

SSA identifiers must be unique within their function. Block labels must also be unique within their function, in a separate namespace. Named constants must be unique within their module. Type names must be unique within their declaring type scope.

Repeated compatible function declarations are permitted, as described under Functions. Other duplicate definitions are rejected.

Module-level types, constants, global storage symbols, and functions may be referenced before their declarations. Block labels may also be referenced before their blocks appear in the text. Forward references remain subject to type, dependency, and dominance rules.

### Type Expressions

A bracketed type expression identifies a type without supplying a value:

```SMIL
[i16]
[byte]
[ptr [i8]]
```

A typed literal supplies both a type and a value:

```SMIL
[i16 100]
[i16 -512]
[i16 0xff00]
```

A literal is a value, not a storage object. It has no SMIL-visible address.

Record constants use `[R { <constant field values> }]` or the recursive shorthand `[R zero]`. Nonconstant record initializer components are permitted only in local storage declarations; ordinary runtime record construction uses `record_make`. These forms are defined under Constant Initializers and Symbolic Addresses.

Typed pointer null literals are also supported:

```SMIL
[ptr [i8] null]
[ptr rom [i8] null]
```

The second form requires a profile supporting `rom`. The type may also be a pointer alias. Function-reference types and aliases also admit a typed `null`, as defined under Function References and Indirect Calls. Numeric literals do not implicitly construct either kind of reference; `inttoptr` applies only to supported data pointers.

Operation signatures determine where type expressions and value operands appear:

```SMIL
%sum = add [i16] [i16 20] [i16 1]
%value = load [i16] %address
store %address %sum
```

Here, `add` and `load` specify their result types explicitly. `store` receives the destination address followed by the value to be written.

Some operations determine their result types from their signatures rather than an explicit result-type annotation. For example, integer comparisons produce `i1`, and call result types come from the called function’s signature.

Operand and result types must satisfy the individual operation’s typing rules. Equal operand widths are not a universal requirement. No implicit numeric conversion, pointer conversion, or truncation is performed.

Type compatibility is determined after resolving transparent aliases. Distinct nominal record types remain distinct.

### Integer Types and Literals

An integer type `iN` represents an N-bit value, where N is a positive integer. Its width is independent of the native integer width of the target machine.

Integer values are bit patterns. Operations determine whether those patterns are interpreted as signed or unsigned quantities.

The type `i1` has two bit patterns, `0` and `1`, and is used for Boolean results and conditions.

Integer literals may use decimal notation or hexadecimal notation with the `0x` prefix. For an `iN` literal:

- A nonnegative value must be less than `2^N`.
- A negative value must be at least `−2^(N−1)`.
- Negative values are encoded using their N-bit two’s-complement representation.
- Out-of-range values are rejected rather than implicitly truncated.

For example, `[i8 255]` and `[i8 -1]` identify the same eight-bit pattern. An operation’s signedness determines how that pattern is interpreted.

These literal rules do not establish the behavior of arithmetic operations. Each operation specifies its own result and exceptional conditions. The integer division, shift, and explicit overflow rules apply uniformly across profiles; native machine behavior does not override them.

## Data Entities

A **data entity** is either an immutable value or an addressable storage object containing a value. Each data entity has a scope that determines where its name may be referenced.

Scope is distinct from lifetime. Scope governs name visibility; lifetime governs the existence of a particular runtime binding or storage object.

SSA values are defined exactly once within the function’s static representation. Storage objects may have mutable or immutable contents. Modifying a storage object does not change any SSA value previously loaded from it.

These classifications do not assign values to physical registers. Storage declarations may impose storage requirements, such as membership in a stack frame, while leaving physical offsets and instruction selection to the backend.

| Entity | Scope | Mutability | Addressable? | Lifetime or extent | Notes |
| --- | --- | --- | --- | --- | --- |
| SSA value | Function, subject to availability rules | Defined exactly once | No | Per dynamic binding within an invocation | Operation or declaration result, or block parameter |
| Local storage object | Function | Contents mutable or immutable, as declared | Yes | Owning function invocation | Separate instance per invocation |
| Global storage object | Module; accessible elsewhere through import and export rules | Contents mutable or immutable, as declared | Yes | Program execution | Shared by referencing function invocations |
| Named constant | Module; accessible elsewhere through import and export rules | Immutable | No | Compile-time or symbolic link-time definition | Does not establish a storage object |

Function symbols and type names identify declarations; they are not storage objects.

### SSA Values

An **SSA value** is an immutable, typed value introduced by:

- An operation or local storage declaration result.
- A block parameter.

Function parameters are the parameters of the entry block. They are not separate SSA definitions in the function signature.

Each SSA binding uses an identifier that has not previously been defined within the function. Its type cannot subsequently change, and its identifier cannot be reassigned.

An operation result is introduced by binding the result to a fresh SSA identifier:

```SMIL
%t0 = add [i16] [i16 1024] [i16 -512]
// %t0 holds the i16 value 512.

%t1 = or [i16] %t0 [i16 0x2]
// %t1 holds the i16 value 514.
// %t0 still holds 512.
```

Redefining an existing identifier is rejected:

```SMIL
%t0 = add [i16] [i16 1024] [i16 -512]

// Rejected: %t0 already has a definition.
%t0 = or [i16] %t0 [i16 0x2]
```

“Defined exactly once” refers to the function’s static representation. It does not mean that an operation executes only once.

An operation inside a loop may execute repeatedly and produce a different runtime value on each iteration. Each execution produces the corresponding dynamic result without introducing another static definition of the identifier.

Block parameters similarly receive new dynamic bindings each time their block is entered.

An SSA value has no SMIL-visible address. Its identifier does not prescribe a physical register or memory location.

#### Value Availability

An SSA value’s function-wide name does not make it available at every point in that function.

An operation result is available only where its definition dominates its use. Within its defining block, the result is available only after the defining operation.

A local storage declaration’s pointer result follows the same ordering rule.

A block parameter is defined at the beginning of its block. It is available throughout that block and in blocks dominated by its block.

Entry-block parameters are available from function entry. Because the entry block dominates every block in a valid function, these parameters may be used throughout the function.

The complete verification rules appear under Control-Flow and SSA Verification.

### Local Storage Objects

A **local storage object** is an addressable storage object declared in a function’s entry declaration region.

Each function invocation has a separate instance of every local storage object, including recursive invocations. Calling a function again does not reuse the logical objects of an invocation that is still active.

Local storage declarations precede ordinary executable operations in the entry block. They cannot appear in another block or after ordinary operations have begun.

The entry block cannot be a branch destination. Consequently, its declaration region is processed once per invocation and cannot be re-entered through a loop backedge.

Storage is reserved in the invocation’s logical stack frame using the target ABI's frame implementation, which may use a hardware stack, a software stack, or a combination. Declaration order does not require the backend to allocate objects in that physical order.

The lifetime of an object begins when its declaration is processed and ends when the owning invocation ends. Its storage is released when the function returns.

Pointers to local storage objects may be passed to other functions while the owning invocation remains active. Returning or otherwise retaining such a pointer does not extend the object’s lifetime. It must not be dereferenced after the owning invocation ends.

#### Declaration and Initialization

An `alosf` declaration specifies the object’s type and whether its contents are mutable:

```SMIL
%ptr = alosf mutable [<type>]
%ptr = alosf mutable [<type>] <initializer>
%ptr = alosf immutable [<type>] <initializer>
```

The declaration produces an SSA pointer of type `ptr data [<type>]`, equivalently `ptr [<type>]`. Local objects belong to the profile's default ordinary data space.

The initializer must have the declared object type. It may be a constant initializer, another value available at the declaration, or a complete local record initializer whose components recursively meet those rules. Available values include entry-block parameters and pointer results from earlier local declarations. No ordinary runtime operations, loads, or calls are implicitly executed inside an initializer.

Declarations are initialized in declaration order. Ordinary executable operations cannot be placed between local storage declarations.

A **mutable local storage object** permits subsequent writes through `store`. Without an initializer, its contents are uninitialized. Record fields may be initialized individually through field pointers; a whole-record load requires every logical field to be initialized. Padding is not a logical field.

An **immutable local storage object** requires an initializer. Initialization establishes its contents as part of the declaration. Subsequent writes are prohibited, including writes through any alias of its address.

Mutability applies to the object’s contents. The pointer produced by `alosf` remains an immutable SSA value in both cases.

```SMIL
func @increment([i16]) -> ([i16]) {
^entry(%initial: [i16]):
    %counter_ptr = alosf mutable [i16] %initial
    %step_ptr = alosf immutable [i16] [i16 1]

    // Ordinary executable operations follow the declarations.
    %counter = load [i16] %counter_ptr
    %step = load [i16] %step_ptr
    %next = add [i16] %counter %step
    store %counter_ptr %next

    // %counter retains its previously loaded value.
    return %next
}
```

The following examples violate declaration or access rules:

```SMIL
%limit_ptr = alosf immutable [i16] [i16 100]

// Rejected: a direct write to this immutable object is prohibited.
store %limit_ptr [i16 200]
```

```SMIL
// Rejected: an immutable object requires an initializer.
%limit_ptr = alosf immutable [i16]
```

```SMIL
%counter_ptr = alosf mutable [i16] [i16 0]

// Rejected: the SSA identifier already has a definition.
%counter_ptr = alosf mutable [i16] [i16 1]
```

The sizes, alignments, and offsets of local objects follow the applicable data-layout contract. The frame may contain padding and other backend-managed storage.

For example, an `i16` object and an `i8` object contain 24 bits of value data, but their contribution to the frame allocation may be larger.

### Global Storage Objects

A **global storage object** is an addressable storage object declared outside any function. Each definition establishes one object shared by all function invocations that reference it.

Global storage allocations are established during bootstrap. Their initialized contents become ready through constant installation or a dynamic factory before application entry. Initialization functions can run earlier under the readiness rules in Program Lifecycle. Allocation lasts until program termination; finalization can remove content-access permission during orderly shutdown.

A global declaration specifies whether the object’s contents are mutable:

```SMIL
@name = global mutable [<type>] <initializer>
@name = global immutable [<type>] <initializer>
@name = global mutable [<type>] <initializer> space(<address space>)
@name = global immutable [<type>] <initializer> space(<address space>)
```

All forms require an explicit initializer. A constant initializer must have the object’s declared type and satisfy the constant-initializer rules. The alternative `dynamic @factory init("id")` form, with optional dependency and shutdown clauses, is defined in Program Lifecycle. An omitted address-space clause selects `data`. Explicit spaces must support the object and the construction/access requirements of its selected initialization form.

A **mutable global storage object** permits subsequent writes through `store`.

An **immutable global storage object** receives its contents through its initializer. Subsequent writes are prohibited, including writes through any alias of its address.

A global storage symbol identifies its object’s address and has pointer type `ptr <address space> [<type>]`. For the default `data` space this is equivalently `ptr [<type>]`. The symbol is not an SSA temporary. Executing a function does not recreate or reinitialize the object.

```SMIL
@counter = global mutable [i16] [i16 0]
@limit = global immutable [i16] [i16 100]
```

Given those declarations, a function may access the objects as follows:

```SMIL
%counter = load [i16] @counter
%limit = load [i16] @limit

%next = add [i16] %counter [i16 1]
store @counter %next

// Previously loaded SSA values remain unchanged.
```

Updates to mutable global storage persist after the modifying function returns. Subsequent accesses observe those updates according to the applicable memory and concurrency rules.

The following examples are rejected:

```SMIL
// Given the immutable @limit declaration above:
store @limit [i16 200]
// Rejected: @limit identifies an immutable object.
```

```SMIL
// Rejected: a global declaration requires an initializer.
@limit = global immutable [i16]
```

```SMIL
@counter = global mutable [i16] [i16 0]

// Rejected: duplicate definition in the module-level value namespace.
@counter = global mutable [i16] [i16 1]
```

Object sizes and alignments follow the module’s data-layout contract. The backend, object format, and linker determine final placement while preserving that contract.

Global storage lifetime and visibility do not imply atomic access or synchronization. Shared ordinary storage uses the explicit atomic and happens-before rules below. A global definition establishes ordinary storage, not a device register; device regions are established by the environment and are accessed through their contracts.

### Named Constants

A **named constant** is an immutable, typed value declared outside any function.

Unlike a storage object, a named constant has no SMIL-visible address and requires no allocation or deallocation. Operations use its value directly.

A constant declaration has the following form:

```SMIL
$name = const <initializer>
```

The constant’s type is the type of its initializer. A named constant is defined exactly once; its type and value cannot subsequently change. Its value may be a complete record, a symbolic field address, or the result of a permitted constant expression; none of these forms introduces an addressable object for the constant itself.

```SMIL
$step = const [i16 1]
$limit = const [i16 100]
$maximum = const $limit
```

Given those declarations, constants may be used directly within a function:

```SMIL
%next = add [i16] [i16 20] $step
// %next holds the i16 value 21.

%above_limit = add [i16] $limit $step
// %above_limit holds the i16 value 101.
```

The following examples are rejected:

```SMIL
$limit = const [i16 100]

// Rejected: duplicate named constant definition.
$limit = const [i16 200]
```

```SMIL
$limit = const [i16 100]

// Rejected: an i16 value is not a storage address.
store $limit [i16 200]
```

```SMIL
// Rejected: a named constant requires an initializer.
$limit = const
```

An immutable global storage object and a named constant both have fixed values, but only the storage object has a SMIL-visible address.

A pointer-valued constant may be used to access the object it identifies. The constant’s immutability does not make that object immutable.

The backend may materialize a constant using an immediate operand, registers, or memory. These implementation choices do not give the named constant a SMIL-visible address.

### Constant Initializers and Symbolic Addresses

A **constant initializer** describes a value without executing function-body operations.

The supported forms are:

- A typed scalar literal or typed null pointer.
- A reference to another named constant.
- The symbolic address of a global storage object in its declared space.
- A typed function-reference null or a `fnaddr` constant expression identifying a declared function.
- A complete record initializer whose components are constant initializers.
- A recursive record-zero initializer.
- A constant expression using the permitted operations below.

The initializer must have the declared or inferred value type. No implicit field conversion, nominal record conversion, or pointer conversion is performed.

```SMIL
@counter = global mutable [i16] [i16 0]
$counter_address = const @counter
// Type: ptr [i16].
```

The compiler can determine the addressed object without knowing its final numeric address. The linker resolves its representation according to the target profile and object-format rules.

Taking an object's address does not read its contents. Loading a global's contents, including an immutable global's contents, is not a constant-initializer operation.

#### Record Initializers

A record initializer has the following form:

```SMIL
[<record type> { <field initializers> }]
```

Fields are supplied exactly once in declaration order. The field count and types must match the record. No omitted-field defaults are implied.

The initializer constructs a value; it does not introduce an addressable object. A global or local declaration using that value separately establishes storage.

```SMIL
@Point = record { i16, i16 }
@Config = record { Point, i1, ptr [i8] }

$origin = const [Point { [i16 0], [i16 0] }]

@configuration = global immutable [Config] [Config {
    $origin,
    [i1 1],
    [ptr [i8] null]
}]
```

These definitions establish a named Point value and an immutable Config object. They do not allocate a separate Point object for `$origin`.

A nested initializer must identify its actual record type. Matching field lists of another nominal type do not suffice.

#### Recursive Record-Zero Initializers

`[R zero]` supplies a complete value for a record R:

- Integer fields receive their all-zero value bit patterns.
- Data-pointer fields receive a typed null in their declared address space.
- Function-reference fields receive a typed null of their callable type.
- Inline record fields are initialized recursively.

```SMIL
@Point = record { i16, i16 }
@Node = record { i16, ptr [Node] }

$origin = const [Point zero]
@empty_node = global mutable [Node] [Node zero]
```

Recursion stops at pointer fields; the initializer does not allocate pointed-to objects.

`zero` denotes these logical field values, not a command to clear every representation byte. Pointer null encodings and record padding follow the selected profile.

The shorthand requires a record type. Integer zero already uses `[iN 0]`, and pointer null uses its typed null literal.

#### Local Record Initializers

An `alosf` initializer may use the same record form with component values available at that declaration, including entry-block parameters and earlier local pointer results.

Such an initializer is evaluated as part of the declaration. It does not insert an ordinary operation statement into the entry declaration region.

Given a module-level Point type with two `i16` fields:

```SMIL
func @snapshot([i16], [i16]) -> ([Point]) {
^entry(%x: [i16], %y: [i16]):
    %slot = alosf immutable [Point] [Point { %x, %y }]

    %value = load [Point] %slot
    return %value
}
```

Each component is a value already available, a constant initializer, or a nested local record initializer. Arbitrary runtime operation expressions, loads, and calls are not allowed inside these initializers.

The declaration's own result is not available to its initializer. Initializers cannot refer to later local SSA definitions.

Initialization establishes every inline field before an immutable object becomes available for subsequent access. No later field store is permitted.

Outside local declaration initializers, record forms used as value operands must be constant. Runtime record construction within ordinary code uses `record_make`.

#### Constant Expressions

A constant expression is parenthesized operation syntax with no SSA result binding:

```SMIL
$step = const (add [i16] [i16 2] [i16 3])
$wrapped = const (add [i8] [i8 255] [i8 1])
$negative = const (cmp slt [i8 -1] [i8 0])
```

These values are respectively `[i16 5]`, `[i8 0]`, and `[i1 1]`.

Value operands may be literals, named constants, symbolic addresses where the operation permits them, nested record constants, or other constant expressions.

Every value operand must be constant; function-local SSA identifiers are prohibited in a constant expression, even when an optimizer could prove their values.

The initial constant-expression language permits only the following single-result operations:

| Category | Permitted operations |
| --- | --- |
| Integer arithmetic | `add`, `sub`, `mul`, `neg`, `udiv`, `urem`, `sdiv`, `srem` |
| Integer bitwise and shifts | `xor`, `and`, `or`, `not`, `shl`, `lshr`, `ashr` |
| Integer comparison | `cmp` with its defined integer predicates |
| Integer conversion | `sext`, `zext`, `trunc` |
| Record values | `record_make`, `record_get`, `record_set` |
| Function references | `fnaddr`, `fn_eq`, `fn_ne` when resolved function identity suffices |
| Symbolic pointer operations | `ptrcast`, `field_addr`, `ptr_offset`, `ptr_diff`, `ptr_eq`, `ptr_ne`, `addrspacecast` subject to the constant-pointer restrictions |
| Layout queries | `sizeof`, `alignof`, `offsetof` |
| Numeric pointer conversions | `ptrtoint`, `inttoptr` when fully evaluable under the selected profile |

An operation absent from this table is not a constant-expression operation merely because it has no memory side effects.

Loads, stores, calls, allocations, control-flow operations, MMIO, atomics, fences, and multi-result carry/overflow operations are not permitted. This excludes ordinary and explicit unaligned accesses alike. There is no compile-time execution of arbitrary SMIL functions.

All operands are evaluated eagerly in written order. Construction of a record requires every component value, including when a surrounding expression later extracts only one field. There is no short-circuit or lazy constant-expression form.

#### Evaluation and Target Binding

Integer and record-value expressions use the same mathematical and typing rules as their ordinary operation forms. Wrapping integer arithmetic remains wrapping during constant evaluation; overflow does not become an implicit diagnostic.

Expressions independent of layout and pointer encoding may be evaluated while unbound. Layout queries and profile-dependent casts remain symbolic until binding.

After target binding, layout queries must produce supported, representable numeric results. The requested result width is part of the expression, so an unrepresentable `sizeof`, `alignof`, or `offsetof` result is rejected.

A constant expression must produce a defined value without an arithmetic or pointer fault. For example:

```SMIL
// Rejected: constant evaluation cannot produce a value.
$invalid = const (udiv [i8] [i8 1] [i8 0])

// Legal: the remainder edge case is defined.
$remainder = const (srem [i8] [i8 -128] [i8 -1])
```

This is a requirement of the constant-expression form. An ordinary executable division with constant operands retains the previously defined runtime fault behavior.

A failed constant evaluation does not run startup code, install a substitute value, or invoke a runtime fault handler during compilation. It is a compile-time diagnostic, or a binding-time diagnostic when the failure depends on the profile.

#### Symbolic Field Addresses and Numeric Pointer Conversions

A constant `field_addr` selects an existing inline subobject of a declared global storage object. Its base may be a direct symbol, a named constant identifying that symbol or one of its record subobjects, or a permitted expression preserving that object association and selection validity.

Given the Config declaration above:

```SMIL
$enabled_address = const (field_addr @configuration field(1))
// Type: ptr [i1].

$x_address = const (field_addr @configuration field(0, 0))
// Type: ptr [i16].
```

The result retains the global object's address space and applicable immutability restrictions. These expressions do not read the initializer or current contents of `@configuration`.

An address expression may remain a symbol-plus-field selection until layout binding, then become a symbol-plus-byte-offset relocation. The target environment must support its final representation or diagnose the unsupported initializer.

A constant `field_addr` cannot use null or an arbitrary numeric address as a substitute for an identified global record object. A `ptrcast` does not fabricate a different set of record subobjects.

Constant `ptrcast` uses the same space and representation rules as its runtime form. It does not create an address or access permission.

In the initial constant language, `ptrtoint` and `inttoptr` require numeric encodings and mappings that can be fully resolved during target binding. They must not require a global's unresolved final link address. Unsupported mappings or required pointer state are diagnosed.

Arithmetic on unresolved linker-dependent integer addresses, symbolic integer-address relocations, and arbitrary linker-side expression evaluation are not part of this initial language. Ordinary symbolic pointer initializers remain supported.

#### Dependencies and Cyclic Addresses

Named constants may reference later constant declarations, but their value dependencies must be acyclic. Dependencies include all nested initializer and expression operands, not only fields eventually extracted.

```SMIL
$first = const (add [i16] $second [i16 1])
$second = const [i16 10]
// Legal.
```

```SMIL
$first = const (add [i16] $second [i16 1])
$second = const $first
// Rejected: cyclic constant-value dependency.
```

An object's symbolic address depends on its declaration and type, not on evaluating its initializer. Cyclic address references between global objects are therefore permitted:

```SMIL
@Node = record { i16, ptr [Node] }

@first = global mutable [Node] [Node { [i16 1], @second }]
@second = global mutable [Node] [Node { [i16 2], @first }]
```

Both objects can be allocated and their pointer fields relocated without reading either object's contents.

Global references through imported declarations remain subject to the module, type-identity, and relocation contracts.

Function-address constants use `(fnaddr @function)` and do not evaluate the function body. `fn_eq`/`fn_ne` constant evaluation requires resolved identity without unresolved interposition or placement. A function reference is not a data pointer; numeric code-address expressions and code/data casts remain unsupported.

### Storage Access and Validation

A storage access must identify a live object, remain within its permitted extent, and satisfy the applicable type, alignment, initialization, and mutability requirements.

Immutability applies to an object regardless of which pointer is used to reach it. It is a SMIL semantic requirement and does not require physically write-protected memory.

A compiler must reject violations of the static rules established here, including:

- Duplicate definitions or unresolved names.
- Missing required initializers.
- Operand or initializer type mismatches.
- Invalid uses of unavailable SSA values.
- Invalid placement of local declarations.
- Cyclic constant-value dependencies.
- Stores to objects statically known to be immutable, including inline record subobjects and targets preserved through `ptrcast`, `ptr_offset`, `field_addr`, or `addrspacecast`.
- Statically known access-kind mismatches, invalid field paths, or unsupported memory-operation forms.

Access violations may also depend on execution, such as a read from uninitialized storage, use of an expired pointer, or a write to an immutable object through an indirectly obtained alias.

These access requirements do not imply that every violation can be detected statically. Pointers and Memory Access defines terminal faults for invalid pointer formation and runtime lifetime, extent, typed-view, alignment, access-kind, and permission violations. Execution Violations, Resource Limits, and Optimization defines their terminal fault policies, staged validation, and optimizer obligations; these accesses do not introduce undefined behavior.

## Custom Data Types

Custom data types may be declared at module scope or in a function’s entry declaration region.

A module-level type name may be referenced throughout the module and may be exported for import by other modules.

A function-local type name may be referenced only within its declaring function. It must not be exposed directly or indirectly through a module-level declaration or function signature.

Local type declarations precede local storage declarations. They do not execute at runtime and do not create a new type on each function invocation.

A local type name may shadow a module-level type name. Two type declarations in the same type scope may not have the same name. Built-in type names cannot be redefined.

Type declarations do not allocate storage or create runtime values. The scope of a type name does not determine the lifetime of objects having that type.

### Type Aliases

The `type` keyword declares a transparent alias for an existing type:

```SMIL
@byte = type [i8]
@word = type [i16]

$NUL = const [byte 0]
$HIMASK = const [word 0xff00]
```

An alias and its underlying type are interchangeable wherever a type is required. No conversion is necessary between them.

Aliases do not introduce distinct type identities. Cycles involving only alias definitions are rejected:

```SMIL
@First = type [Second]
@Second = type [First]
// Rejected: cyclic alias definitions.
```

### Pointer Types

A pointer type identifies the type of object addressed by its value:

```SMIL
@cstr = type [ptr [i8]]
```

Here, `cstr` is an alias for a pointer to an `i8` object in `data`. It is equivalent to `ptr data [i8]`.

An explicit address space is part of the pointer type:

```SMIL
@rom_byte_ptr = type [ptr rom [i8]]
```

This declaration requires a profile supporting `rom`. Pointers in different spaces are distinct types, even if their sizes match, and are not implicitly interchangeable.

The pointer’s representation, size, alignment, and applicable address-space behavior follow the target profile and data-layout contract. Pointer width is not inferred from the width of the pointee type.

The alias does not establish a string length, null-termination requirement, or access permission.

A pointer value does not extend the lifetime of the object it identifies. Object mutability and access requirements still apply.

### Record Types

The `record` keyword declares a record containing an ordered sequence of fields:

```SMIL
@UserInfo = record { i1, i1, i8, cstr }
```

Given the `cstr` alias above, fields `0` and `1` have type `i1`, field `2` has type `i8`, and field `3` has type `cstr`. Fields are identified by zero-based position.

Each record declaration introduces a distinct type. Two separately declared record types are not interchangeable merely because their field types match.

An alias of a record retains that record’s identity. Importing a record type also preserves its original identity; an import does not create a new record declaration.

A record may be used as an SSA value or as the type of a storage object. Declaring the record type does not create either.

An SSA record value is immutable. Computing a record with a changed field produces a new SSA value. Modifying a field in an addressable record object is a storage operation subject to that object’s mutability rules.

#### Record Layout

Record layout follows the algorithm and allocation-size rules in Target Profiles and ABI Lowering. All participating frontend, optimization, backend, and linking stages must use that same resolved contract.

Field order is preserved in memory. Field offsets, alignment, padding, and total storage size are determined consistently by that contract. Consecutive `i1` fields are not implicitly bit-packed. `field_addr` and `offsetof` must use these same offsets, including for nested paths.

An SSA record value does not itself have byte order or padding. Those properties apply when the value is represented in storage or passed through an interface that prescribes a representation.

Modules exchanging stored records must use compatible type identities and data-layout contracts. Matching field lists alone do not establish compatibility.

#### Recursive Records

A record’s name is available within its own definition. Type declarations may also reference later type declarations in the same scope.

A record must have a finite storage size. Every recursive containment cycle must pass through a data pointer or function reference rather than requiring direct containment of another complete instance. Types mentioned in a callable signature are not inline fields of its function-reference representation.

```SMIL
// Legal: recursion passes through a pointer.
@Node = record { i16, ptr [Node] }
```

```SMIL
// Legal: mutually recursive references pass through pointers.
@Left = record { ptr [Right] }
@Right = record { ptr [Left] }
```

```SMIL
// Rejected: direct containment would require infinite storage.
@Invalid = record { i16, Invalid }
```

```SMIL
// Rejected: indirect by-value containment requires infinite storage.
@First = record { Second }
@Second = record { First }
```

A valid finite record layout does not by itself guarantee that an object fits in a particular target’s available memory. Target resource limits are checked separately.

## Aggregate Values and Operations

The aggregate types established by this guide are records, including records containing other records by value. Arrays, unions, packed aggregates, and vector aggregates require separate definitions.

A record SSA value contains a defined value for every field. There are no uninitialized, omitted, or unspecified fields in a record SSA value.

A record containing pointer fields contains those pointer values, not copies of the objects they identify. Constructing or copying the record does not read or duplicate those objects.

### Field Paths

Record operations select fields using a nonempty, zero-based field path:

```SMIL
field(0)
field(1, 0)
```

Each index is a nonnegative decimal integer literal, not an SSA operand or a named constant. It is a structural attribute with no SMIL integer width.

Every index must be within the selected record's field count. All path components except the last must select a field whose type is itself a record.

Paths follow inline record fields only. They do not implicitly load or dereference pointer fields. Selecting a field of a pointed-to record requires explicit pointer retrieval and a separate access.

An empty path, negative index, out-of-range index, or traversal through a non-record type is rejected during structural/type verification. Indices are not truncated or wrapped.

### Record Construction

The `record_make` operation constructs one record SSA value:

```SMIL
%record = record_make [<record type>] (<field values>)
```

The record type may be a transparent alias of a record. The number and order of operands must match its fields. Every operand must have the corresponding field type after alias resolution.

Construction preserves the record's nominal identity. Matching field lists do not permit substitution of a separately declared record type.

Given:

```SMIL
@Point = record { i16, i16 }
```

A function-body fragment may construct a value as follows:

```SMIL
%point = record_make [Point] ([i16 20], [i16 30])
```

The result has type `Point`. Construction does not allocate addressable storage.

A record with no fields uses an empty operand list. Its storage or ABI use still requires the target profile to support that empty-record layout.

### Field Extraction

The `record_get` operation extracts one field value:

```SMIL
%field = record_get <record value> field(<indices>)
```

Its result type is the selected field's type. The source operand must be a record value, not a pointer to a record.

Given `Point` above:

```SMIL
%point = record_make [Point] ([i16 20], [i16 30])
%x = record_get %point field(0)
// %x has type i16 and holds 20.
```

Extraction does not load from storage and does not modify the source value. A global storage symbol cannot be supplied directly as the record operand; it identifies an address.

### Field Replacement

The `record_set` operation produces a new record value with one selected field replaced:

```SMIL
%updated = record_set <record value> field(<indices>) <replacement>
```

The replacement must have the selected field's type after alias resolution. The result retains the source record's type and nominal identity.

The selected field receives the replacement value. Every other field remains equal to its corresponding source field. The source value remains unchanged.

Given `Point` above:

```SMIL
%original = record_make [Point] ([i16 20], [i16 30])
%updated = record_set %original field(0) [i16 21]

%old_x = record_get %original field(0)
// 20.

%new_x = record_get %updated field(0)
// 21.
```

This is value construction, not a write to an existing object. No address or mutable storage is required.

### Nested Fields

Given `Point` above:

```SMIL
@TaggedPoint = record { i8, Point, ptr [Point] }
```

The following function-body fragment uses inline paths:

```SMIL
%position = record_make [Point] ([i16 20], [i16 30])
%tagged = record_make [TaggedPoint] (
    [i8 1], %position, [ptr [Point] null]
)

%x = record_get %tagged field(1, 0)
// i16 value 20.

%moved = record_set %tagged field(1, 0) [i16 25]
// A new TaggedPoint whose inline Point has x = 25.
```

`field(2)` selects the pointer value. `field(2, 0)` is rejected because the path would traverse a pointer rather than an inline record.

Parentheses and braces delimit aggregate operand and initializer lists; those lists may span lines.

### Field Addresses

The `field_addr` operation derives the address of a record field:

```SMIL
%field_ptr = field_addr <record pointer> field(<indices>)
```

The base must have type `ptr S [R]`, where R resolves to a record and S is its address space. If the selected field has type F, the result has type `ptr S [F]`.

The operation preserves the address space and derives the selected subobject from the base object. It does not perform a pointer/integer conversion or use wrapping integer arithmetic to compute an offset.

For valid inputs, the base identifies storage for the indicated record object or subobject. Its contents need not be initialized. The path selects an existing field within that record's extent.

`field_addr` does not read or write the record or initialize any field. It does not extend object lifetime or grant access permissions.

A field pointer retains the enclosing object's lifetime and applicable mutability restrictions. It does not identify a separately allocated object.

A null or expired base, a one-past position, or a base that does not identify an actual subobject of the indicated record type causes `invalid_pointer_operation` at `field_addr`. No pointer result is produced. The detailed rules are established in Pointers and Memory Access; layout-only calculations use `offsetof` rather than a null-base field-address expression.

The byte offset is determined by the selected profile's record layout. A backend must preserve bank, segment, and other pointer-representation components when implementing the calculation.

Given `Point` above:

```SMIL
func @assemble([i16], [i16]) -> ([Point]) {
^entry(%x: [i16], %y: [i16]):
    %slot = alosf mutable [Point]

    %x_ptr = field_addr %slot field(0)
    %y_ptr = field_addr %slot field(1)
    store %x_ptr %x
    store %y_ptr %y

    %complete = load [Point] %slot
    return %complete
}
```

The returned value is independent of `%slot`. Returning it does not keep the local object alive.

### Record Loads, Stores, and Partial Initialization

`load [R]` from a pointer to R produces a complete record SSA value. Every logical leaf field being read must be initialized, including fields of nested records. Pointer fields need initialized pointer values; loading them does not dereference their targets.

A whole-record load before every logical field is initialized violates the storage-access requirements. It does not produce a partially defined SSA record.

A `store` of a complete record value writes its field values into the destination and establishes their initialization. The destination must permit all affected writes.

A mutable record object may instead be initialized or updated through field pointers. Writing one field initializes that field, including all logical fields when the written value is itself a complete record. It does not initialize unwritten siblings.

Padding bytes are not logical fields. They need not be initialized before a typed record load, and record operations do not promise their preservation or particular contents.

Record copies preserve embedded pointer values and any representation state required by the profile. Raw byte-copy expansion is permitted only when it preserves that behavior and all access requirements.

Aggregate accesses do not imply atomicity. They may be split into valid field accesses in ordinary memory while preserving the specified fault behavior. This core does not provide aggregate MMIO or atomic transactions: use the explicitly supported integer operations and construct an SSA record separately when appropriate.

An immutable record object's inline subobjects cannot be modified after initialization, including through derived field pointers. This restriction does not recursively make objects reached through pointer fields immutable.

### Layout Queries

The following operations produce an integer result describing the selected data layout:

```SMIL
%bytes = sizeof [<integer type>] [<object type>]
%alignment = alignof [<integer type>] [<object type>]
%offset = offsetof [<integer type>] [<record type>] field(<indices>)
```

- `sizeof` returns allocation size in bytes, including allocation padding.
- `alignof` returns required alignment in bytes.
- `offsetof` returns the cumulative byte offset of the selected inline field.

The queried type must have a supported storage layout. `offsetof` uses the same structural path rules as record operations.

Results are nonnegative mathematical quantities encoded in the requested integer type. A quantity that does not fit its unsigned range is rejected; it is not truncated or wrapped.

The result type and field path can be checked while unbound. Numeric query results are resolved only after target binding. A target-bound layout query has no runtime memory access and can be materialized as a constant.

Given `Point` and `TaggedPoint` above:

```SMIL
%point_bytes = sizeof [i16] [Point]
%tagged_alignment = alignof [i16] [TaggedPoint]
%x_offset = offsetof [i16] [TaggedPoint] field(1, 0)
```

These queries do not read an object or extend any object's lifetime.

### Aggregate Validation

A verifier must reject:

- A non-record type supplied to `record_make`.
- Incorrect constructor operand counts or field types.
- A non-record value supplied to `record_get` or `record_set`.
- Invalid field paths or incorrectly typed replacements.
- A non-pointer or non-record pointee supplied to `field_addr`.
- A store to a known immutable record or inline subobject.
- An invalid aggregate initializer under the constant and local initializer rules.

Known immutable subobjects include `field_addr` derivations from immutable globals or immutable `alosf` objects, including symbolic constant addresses and other transparent pointer derivations that preserve those targets. General alias analysis is not required to detect every runtime violation; runtime permission violations use the specified access-fault policy.

Layout-query range errors and unsupported representations are checked at target binding.

## Pointers and Memory Access

Pointer operations describe locations and accesses independently of the machine instructions used to implement them. The core distinguishes ordinary storage, device transactions, and synchronized access to shared ordinary storage.

### Object Association and Extent

A pointer value has a declared address space and pointee type. A non-null pointer may additionally identify an allocation or a profile-declared external region, an offset within it, and the access restrictions carried by that association.

This **object association** is semantic information, sometimes called provenance. It need not occupy bits in every machine pointer. A compiler may establish it by proof, placement information, runtime metadata, or another conforming implementation.

Each `alosf` invocation creates distinct allocation identity. A global object has its own allocation identity. A record's inline fields are subobjects of its allocation, not separate allocations.

An external region used by foreign code or a device must have a profile/environment contract establishing its identity, extent, lifetime, permissions, access kind, and any typed subobjects. A numeric address alone does not establish those facts.

For an allocation of positive size L, pointer arithmetic may retain offsets in the inclusive interval `[0, L]`. Offset L is the **one-past** position. It may be compared or moved back into the allocation but cannot be dereferenced, including for an empty-record access. For a zero-sized allocation, when supported, the declared object position at offset zero may be used for its zero-sized typed operations. `ptr_offset` accepts only a zero delta for that allocation and preserves that object position; the core does not construct a separate one-past position for it.

Deriving a field pointer retains the enclosing allocation's extent and identity. It does not restrict subsequent byte arithmetic to that field, and does not grant permission to access another allocation. Typed access rules still restrict what may be read or written at the resulting position.

Allocation identity, initialization, mutability, and lifetime are not changed by copying a pointer, `ptrcast`, pointer arithmetic, a comparison, or an address-space conversion. An expired pointer does not become associated with a newly allocated object merely because storage addresses are reused.

A profile may support an **address-only pointer** produced by an explicit integer conversion. It can be copied, compared, or converted back where specified, but cannot be used for object arithmetic, field selection, or storage access until a separately defined operation or region mapping establishes a valid association. This core supplies no operation that fabricates allocation identity from arbitrary bits.

### Ordinary Typed Access and Aliasing

For `load [T] p`, p must have type `ptr S [T]`. For `store p v`, v must have its pointer operand's pointee type. Transparent aliases are resolved before these checks. A differently typed view therefore requires an explicit `ptrcast` before access.

An ordinary access also requires:

- A live associated object or external ordinary-storage region.
- A range within its extent and a valid typed view under the rules below.
- The required alignment, unless the explicit unaligned form is used.
- Permission for the access in the object, pointer view, address space, and region.
- Initialized value bits when reading, under the initialization rules.
- Ordinary memory whose access contract permits the operation.

The initial core permits the following views:

| Requested access | Permitted ordinary storage |
| --- | --- |
| Integer `iN` | An integer object or integer leaf field's representation bytes, including a smaller view at an interior byte position; the entire requested representation must fit within that one integer leaf |
| Pointer value | An actual data-pointer object or pointer leaf field of the same type after alias resolution |
| Function reference | An actual function-reference object or leaf field of the same callable type |
| Record R | An actual R object or inline R subobject, preserving its nominal type identity |

An integer view may change width, subject to bounds and alignment. It uses the selected layout's byte order and the accessed `iN` encoding. Such a store updates the underlying integer representation bytes; it does not change the object's declared type. Subsequent loads decode their own declared value widths from those bytes.

An integer view cannot span separate record fields, include allocation or record padding, or reinterpret pointer representation bytes. Record access is not a way to reinterpret an unrelated record with a coincidentally matching layout. Broader raw-buffer, representation-copy, union, and type-punning operations require separate definitions.

This restriction protects pointer state that is not represented by ordinary address bytes. Data pointers and function references are copied using their matching typed operations or record operations. Explicit pointer/integer conversions remain available only for data pointers under their profile contracts.

For example, given an `i16` object:

```SMIL
func @first_byte() -> ([i8]) {
^entry():
    %word = alosf mutable [i16] [i16 0x1234]

    %byte_ptr = ptrcast [ptr [i8]] %word
    %byte = load [i8] %byte_ptr
    return %byte
}
```

The result is `0x34` under a little-endian layout and `0x12` under a big-endian layout. Casting the pointer does not convert the stored integer.

Differing pointee types do not establish non-aliasing. In particular, the permitted integer views can overlap. Distinct address-space names also do not establish disjointness unless the profile says so. A backend must use the actual object/range relationships and explicit profile guarantees when proving independence.

An ordinary access cannot stand in for a device transaction or atomic operation merely because the machine instruction happens to be the same. Ordinary accesses may be removed, combined, or split only when the transformation preserves all required storage, fault, and concurrency behavior. Expansion must not introduce a write or read/modify/write to a neighboring independently accessible field, even when its value would be unchanged in a single-agent execution.

### Pointer Equality

Pointer equality uses a separate operation from integer `cmp`:

```SMIL
%equal = ptr_eq <left> <right>
%different = ptr_ne <left> <right>
```

The operands must have identical pointer types after alias resolution. Each operation returns `i1`. Compare different pointee views by first using `ptrcast` to a common pointee type; compare different spaces only after a supported explicit address-space conversion.

Two null values compare equal. Null compares unequal to every non-null location. Two non-null values compare equal when they denote the same normalized address position in that space, including the bank or segment components needed to distinguish locations. Raw encoding equality is sufficient only when the profile guarantees canonical encodings.

Object identity and access permissions do not participate in address equality. A one-past pointer can therefore compare equal to the start of an adjacent object without becoming usable for that object. Copying or substituting an equal-address pointer must preserve the association required by each use.

Equality itself does not dereference, require initialization of the pointed-to storage, or test lifetime. A defined pointer value may be compared after its object expires, but a true result does not restore validity. Profiles must preserve enough information to implement these comparisons; this is not permission to load an uninitialized pointer value.

`ptr_ne` is the logical complement of `ptr_eq`. Neither operation imposes a total ordering of unrelated objects. Integer comparison of converted addresses is not a portable substitute for these operations.

### Byte-Based Pointer Arithmetic

The core defines byte offsets rather than implicitly scaling by pointee size:

```SMIL
%advanced = ptr_offset <base> <byte delta>
%distance = ptr_diff [<integer result type>] <left> <right>
```

`ptr_offset` accepts any integer-width delta and interprets it as a signed two's-complement mathematical integer. It neither truncates the delta to a pointer width nor wraps it. For `i1`, delta `1` consequently means `-1`.

The result retains the base's pointer type, space, association, and restrictions. It adds the mathematical byte delta to the associated allocation offset. The base must be a live associated object position or its one-past position. The resulting offset must remain in `[0, L]` and be representable by that space's pointer model. Null plus zero is invalid, just as null plus any other delta is invalid.

`ptr_diff` requires matching pointer types and two live positions associated with the same allocation, including one-past positions. It returns `left_offset - right_offset` in bytes. The mathematical difference must fit the **signed** range of the requested integer result type. Different allocations are invalid even when their normalized addresses are equal.

Invalid bases, out-of-range results, an unrepresentable position, or an unrepresentable difference cause a pointer fault as defined below. These operations do not create an intermediate out-of-bounds pointer that can later be brought back into range.

Pointer arithmetic may produce an unaligned pointer; formation alone does not require the pointee's alignment. A subsequent access independently checks alignment and the selected typed view.

Given a live pointer `%word_ptr` to an `i16` object whose allocation size is two bytes:

```SMIL
%bytes = ptrcast [ptr [i8]] %word_ptr
%second = ptr_offset %bytes [i16 1]
%end = ptr_offset %bytes [i16 2]
%back = ptr_offset %end [i16 -2]
%length = ptr_diff [i16] %end %bytes
// %length is 2; %back addresses the original first byte.

// This operation faults if executed: offset 3 exceeds this allocation.
%outside = ptr_offset %bytes [i16 3]

// A load from %end is invalid even though forming %end was valid.
```

Element-based indexing must explicitly calculate a byte delta from the required layout stride. Ordinary wrapping integer multiplication is not a checked address calculation: the producer must prevent arithmetic overflow before supplying the delta. An unsigned source index exceeding the positive range of its current type must be widened with `zext` before it is used as a signed delta. Arrays and a dedicated checked indexing operation are separate extensions.

### Field-Address Validity

`field_addr` retains its established static path and result-type rules. At execution, its base must identify the beginning of a live actual subobject of the indicated record type. A pointer to uninitialized record storage is sufficient; no field contents are read.

Null, an expired association, a one-past position, an address-only pointer, an interior byte that is not the indicated record boundary, or a differently typed object reached through `ptrcast` is an invalid base. Even a zero-offset first field requires a valid base.

An invalid base causes a pointer fault at `field_addr`, before any result is produced. There is no null-base field-offset idiom; use `offsetof` for layout-only calculations.

Byte arithmetic may recover an actual enclosing record boundary within the same allocation. Casting that recovered pointer to its actual record type and then selecting a field is permitted. Casts and byte offsets cannot invent a different record's subobjects.

### Explicit Address-Space Conversion

```SMIL
%converted = addrspacecast [ptr <destination space> [T]] <source>
```

The source must be a pointer in a different space, with the same pointee type T after alias resolution. Pointee reinterpretation, if required, is a separate `ptrcast`.

The selected profile must define a mapping for the ordered source/destination space pair. Equal encoding sizes or overlapping numeric addresses do not imply that a mapping exists. An unsupported pair is rejected at binding.

A supported conversion maps a source null to the destination space's typed null. For a non-null source it preserves the same underlying object and byte position, translates representation components as necessary, and retains lifetime and object association. It does not read or copy the object.

A mapping may cover only a specified subset of locations. A non-null source must have a live object association, and a source location outside the mapping or an unrepresentable destination position causes a pointer fault. Converting an address-only or expired pointer is invalid. The destination view cannot grant permissions beyond those already held and those permitted by the destination space and region. Converting a read-only view back to another space does not restore write permission through that converted pointer.

Converting spaces cannot turn an ordinary-storage object into a device register, hide device side effects, or change a region's access kind. Aliasing and access contracts follow the object through both views.

For example, on a profile advertising a `rom`-to-`data` mapping:

```SMIL
@table_word = global immutable [i16] [i16 42] space(rom)

// Function-body fragment; requires the advertised mapping.
%mapped = addrspacecast [ptr data [i16]] @table_word
%value = load [i16] %mapped

// Rejected: the mapped view still identifies immutable storage.
store %mapped [i16 43]
```

### Explicit Unaligned Integer Access

```SMIL
%value = load_unaligned [iN] <pointer>
store_unaligned <pointer> <iN value>
```

These operations use the same pointee typing, bounds, integer-view, initialization, byte-order, and permission rules as ordinary integer `load` and `store`, but require only byte alignment.

They are restricted to ordinary integer storage views. Record values, pointer values, device regions, and atomic accesses are not accepted by these forms. Supporting unaligned pointer representations or aggregate accesses requires separate definitions.

The target may implement one operation with several byte accesses. No atomicity or stable snapshot is promised. Expansion must not access bytes outside the requested representation range or modify neighboring values. A target without an unaligned machine instruction may still support these operations through a conforming expansion or helper.

Assuming a profile with ordinary `i16` alignment two and a four-byte `i32` representation:

```SMIL
func @middle_word() -> ([i16]) {
^entry():
    %slot = alosf mutable [i32] [i32 0x11223344]

    %view = ptrcast [ptr [i16]] %slot
    %middle = ptr_offset %view [i16 1]
    %value = load_unaligned [i16] %middle
    return %value
}
```

The two accessed representation bytes are inside the same integer object. An ordinary `load [i16] %middle` would fail its alignment requirement under that profile.

### Device Regions and MMIO Transactions

A **device access contract** is a versioned profile/environment definition identifying a device region and its allowed observable transactions. It is separate from both the pointer's space name and the ordinary data layout. The `mmio_*` family also covers isolated port I/O and synchronous monitor-mediated device transactions where the profile defines them; a logical I/O coordinate need not be a physical memory address.

Each contract must specify:

- Region identity, extent, lifetime, pointer mappings, and authorized agents.
- Readable/writable locations, value widths, alignment, and register byte order.
- The exact bus transaction or prescribed sequence implementing each access, including address order, byte enables, and any prohibited splitting or widening.
- Read and write side effects, read-only and write-only registers, and reserved-bit requirements.
- Required ordering, completion meaning, permitted posting, barriers, and the ordinary-memory regions shared with the device.
- DMA/cache-coherence requirements and how external device activity interacts with the region.
- Bus-error and device-fault handling, including any partially completed transactions.

Contract identifiers used in source must resolve at binding and must be recorded in compatibility metadata. An `access(...)` clause selects a contract; it cannot authorize a pointer outside that contract's region.

```SMIL
%status = mmio_load [i8] <pointer> access("uart.registers.v1")
mmio_store <pointer> <i8 value> access("uart.registers.v1")
mmio_fence access("uart.registers.v1")
```

`mmio_load` and `mmio_store` accept integer values only. Pointer pointee type and value/result type must match. The operation's width must be explicitly supported by the device contract; there is no implicit narrowing, widening, or conversion between register encodings and logical `i1`.

When a contract supports a non-byte-multiple width, it must define a complete mapping between that width's value bits and the transaction bits, including ignored read bits and required written bits. Ordinary `iN` representation rules alone do not define a device transaction.

A successful operation performs exactly the transaction or sequence prescribed by its contract, once per dynamic execution. An unused MMIO load still performs the read. A device read may update the device as specified; the name `load` does not make it free of side effects.

An optimizer must not remove, duplicate, speculate, merge, or split these transactions in a way that changes that observable sequence. MMIO operations in one agent retain their textual execution order relative to other MMIO operations, including operations under different contracts. Contracts must provide a compatible implementation of that order. This does not make every access a completion barrier for ordinary memory or for device work.

`mmio_fence` is a full ordering and visibility boundary between earlier and later MMIO and ordinary-memory accesses in that contract's declared device/shared-memory domain. Earlier accesses must satisfy the contract's required visibility and completion conditions before later accesses may become observable in that domain. The profile must state the necessary hardware barriers, posting drains, and cache maintenance. It must reject this fence if those guarantees cannot be provided.

A fence does not wait for an independently running device operation or DMA transfer to finish. Completion must be established using the device's protocol. It does not synchronize CPU threads by itself, and an atomic fence does not substitute for this device-domain fence.

External device mutation of shared memory requires an explicit coherence and ownership protocol. The presence of a device access contract alone does not authorize ordinary loads to race with DMA, or make a CPU atomic instruction atomic with respect to a device.

MMIO contracts may be usable through `io`, `data`, or another supported space. Ordinary `load`, `store`, and their unaligned forms are prohibited for a region requiring MMIO, even through an alias in an ordinary-named space. `atomic_*` operations on such a region are also prohibited by this core; atomic device transactions need a separate device-specific operation and contract.

There is no generic `volatile` modifier in this core. A source language's volatile object must be lowered to a contract that actually provides its required observable accesses. Ordinary RAM requiring volatile access needs an explicitly defined extension; it must not be silently treated as ordinary optimizable storage.

For example, suppose a selected profile maps address `0xf001` into a live UART region and supports the named byte-access contract:

```SMIL
$status_register = const (inttoptr [ptr io [i8]] [i16 0xf001])

// Function-body fragment.
%first = mmio_load [i8] $status_register access("uart.registers.v1")
%second = mmio_load [i8] $status_register access("uart.registers.v1")
// Both reads occur, even if the register address is unchanged.
```

The numeric mapping and contract in this example are illustrative, not predefined SMIL platform behavior. Device regions are established by the environment; they are not ordinary initialized globals, and startup must not issue stores to device registers merely to implement global initialization.

### Atomic Access to Shared Ordinary Storage

The initial atomic core supports only **sequentially consistent** operations, spelled `seq_cst`. Relaxed, acquire-only, release-only, explicit synchronization scopes, and weak compare/exchange require later definitions.

```SMIL
%value = atomic_load [iN] <pointer> seq_cst
atomic_store <pointer> <iN value> seq_cst
%old = atomic_rmw add [iN] <pointer> <iN operand> seq_cst
%old, %success = atomic_cmpxchg [iN] <pointer> <expected> <desired> seq_cst
atomic_fence seq_cst
```

An atomic location is one actual ordinary integer object or integer leaf subobject. Its access width must equal that object's declared `iN` type after alias resolution. Integer reinterpretations, partial-width accesses, pointer values, records, unaligned forms, and MMIO are not atomic locations in this core.

All concurrent atomic accesses to a location use the same type and extent. Aliased pointer views do not create separate atomic locations. Atomic operations retain the ordinary integer value encoding, including canonical `i1` stores and unused high bits; any extra atomic alignment is an access requirement, not a different storage layout.

The profile must state supported widths, required atomic alignment, participating agents, and the memory regions where each operation is implementable. Existing `alosf` and global declarations do not request stronger-than-layout alignment. If a location cannot be shown or checked to satisfy an extra requirement, a conforming helper must handle it or that use must be rejected. Alignment syntax is a separate extension.

Each atomic access is indivisible with respect to every participating agent accessing the same location. The requirement applies to the logical value and representation state, even when its implementation uses more than one machine instruction.

`atomic_load` returns the current `iN` value. `atomic_store` replaces it. `atomic_rmw` accepts `xchg`, `add`, `sub`, `and`, `or`, or `xor`, returns the old value, and installs the corresponding new value as one indivisible action. Addition and subtraction wrap modulo `2^N`; the other operators use ordinary integer bitwise semantics. `xchg` installs its operand.

`atomic_cmpxchg` returns the observed old value and an `i1` success flag. Expected and desired operands have type `iN`. If the observed bits equal expected, it installs desired and returns success one. Otherwise it performs no write and returns success zero. Comparison is of the N logical value bits. The operation is strong: it cannot fail spuriously when the comparison matches.

For the atomic model, an **agent** is a thread, interrupt execution context, or other participant explicitly covered by the environment contract. Each agent's executed operations have the textual sequencing established by its CFG. Entry/exit, thread creation, and interrupt handoff provide additional ordering only where the environment explicitly defines it.

There is one total order of all `seq_cst` atomic accesses and fences across participating agents. It is consistent with each agent's sequencing and the happens-before relation defined below. For determining a location's values, extend that order with its initialization and any ordinary writes, consistently with happens-before. A load observes the most recent write to its location preceding it in this extended order. A read/modify/write observes the preceding value and installs its replacement at its single position in the order. Ordinary writes between atomic-use phases must be ordered relative to every conflicting access by happens-before; they are not ignored when determining subsequent atomic values.

Every atomic write has release semantics and every atomic read has acquire semantics. A read that observes a value from an atomic write synchronizes with that write. Successful compare/exchange and the other read/modify/write operations act as both read and write; failed compare/exchange acts as an acquiring read. **Happens-before** is the transitive closure of within-agent sequencing, these synchronization edges, and ordering edges explicitly supplied by the environment.

`atomic_fence seq_cst` participates in the total order and orders preceding and following ordinary-memory accesses in its agent. It does not read a location or create a cross-agent synchronization edge by itself. Publication still requires communication through an atomic location or an environment-defined synchronization event.

An object's initial value must be established before it is read or published to another agent. A shared ordinary non-atomic access is valid only when conflicting accesses are ordered by happens-before. Two accesses conflict when their storage ranges overlap and at least one writes. Unordered conflicting accesses with at least one non-atomic access constitute a **data race**, including an ordinary access racing with an atomic access. Non-overlapping integer fields can be independent, but an aggregate access also accesses its covered fields.

Execution Violations, Resource Limits, and Optimization below defines terminal uninitialized-read and data-race behavior, required validation stages, and optimizer obligations for these operations. Atomic writes can initialize a location; every atomic operation returning its old value must first read a complete initialized value.

For example, after startup initializes these objects and the environment makes them available to both agents:

```SMIL
@payload = global mutable [i16] [i16 0]
@ready = global mutable [i1] [i1 0]

func @publish() -> () {
^entry():
    store @payload [i16 42]
    atomic_store @ready [i1 1] seq_cst
    return
}

func @try_read() -> ([i16]) {
^entry():
    %ready = atomic_load [i1] @ready seq_cst
    br_if %ready, ^available(), ^waiting()

^available():
    %value = load [i16] @payload
    return %value

^waiting():
    return [i16 0]
}
```

With one publication and no subsequent payload writes, observing `%ready = 1` establishes the ordering needed to read `42`. This is a one-time publication example, not a reusable queue protocol.

A small target may implement an atomic operation with a critical section or helper only when it excludes every competing agent in the advertised domain and preserves required ordering. Masking a local interrupt does not exclude another CPU, a non-maskable interrupt, or a device. Every implementation used for the same location, including native instructions and helper paths, must interoperate to preserve indivisibility. Helpers must meet their advertised interrupt/reentrancy and progress contracts; a lock that can deadlock when interrupted by another user of that lock is not a conforming fallback.

No atomic operation is implicitly lock-free or wait-free. A profile must identify its progress guarantees and supported interrupt use. An unsupported requirement is diagnosed, not lowered to a tearing ordinary access. Optimizers may transform atomic operations only when all permitted observations, synchronization, and progress requirements are preserved.

### Pointer Faults and Access Failures

The following faults are defined terminal events:

| Condition | Fault kind |
| --- | --- |
| Invalid `ptr_offset`, `ptr_diff`, `field_addr`, or runtime address-space conversion | `invalid_pointer_operation` |
| Access through null, an expired or unassociated pointer, a one-past position, or an invalid range/view; invalid alignment or access permission | `invalid_storage_access` |

The second row includes writes to immutable objects through indirect aliases, ordinary accesses to MMIO-only regions, and accesses through a supported operation that fail its runtime region or alignment requirements. Unsupported static types, contracts, conversions, or operation forms are binding/verification errors instead.

A faulting operation produces no result and does not continue in its function or caller. It uses the same terminal execution mechanism as arithmetic faults, with the indicated fault kind. It is not undefined behavior, an exception edge, or a request for stack unwinding.

Pointer formation faults before returning a pointer. An invalid storage access faults before performing that access; an aggregate access must validate the ranges and permissions needed for all its fields before changing any field. A bus/device error after an authorized MMIO transaction begins follows the device contract's specified fault behavior and may have already caused device side effects.

Executions must preserve observable effects preceding a fault. An optimizer cannot discard a potentially faulting unused pointer calculation, move it onto a path that would not execute it, or assume that its faulting case is impossible merely because that case is invalid. A proof that an operation cannot fault permits normal elimination or motion subject to its other semantics.

A target may omit checks when validity is established. Otherwise it must supply conforming checks or runtime support, or diagnose an unsupported requirement. This can require substantial runtime metadata on a target whose raw pointers do not encode bounds or lifetime; the semantics do not require a particular pointer bit layout, and they do not permit silently falling back to unchecked host-language behavior.

Execution Violations, Resource Limits, and Optimization below defines uninitialized-read, data-race, and portable resource faults, plus operation-level validation priority. These extend this defined terminal-fault model without introducing undefined values or weakening pointer/access checks.

### Required Profile Guarantees for Pointer/Integer Conversion

Each supported ordered pointer/integer type pair must have an explicit contract. A profile must specify:

| Area | Required information |
| --- | --- |
| Support and domain | Allowed spaces and integer widths; accepted source values; rejected forms and runtime failure conditions |
| Encoding | Which address, bank, segment, tag, and other components map into integer bits; any width changes or discarded bits |
| Null | The numeric result of converting null and the integer values that map to null |
| Association | How conversion back resolves a live object or registered external region, or instead produces an address-only pointer |
| Pointer round trip | The exact pointer domain in which integer conversion and conversion back preserve location, association, permissions, and usability |
| Integer round trip | The exact integer domain and any normalization for conversion to a pointer and back |
| Representation state | Whether all required pointer state can be recreated; stable versus state-dependent mappings and their ordering requirements |

For a claimed pointer round trip, let q be the result of `inttoptr [ptr S [T]] (ptrtoint [iM] p)`, written here as mathematical composition rather than nested runtime syntax. For non-null p within the stated domain, q must identify the same live object and byte position with the same usable permissions as p. A true `ptr_eq q p` result alone is insufficient. The object must remain live between conversions, and the contract must state how ambiguous one-past/adjacent positions are handled or exclude them from the guarantee. If the guarantee includes null, its round trip must preserve typed null without requiring an object association.

For a claimed integer round trip, converting x to a pointer and back must yield exactly x, unless the contract explicitly defines a particular normalization. A masking or truncating mapping is not silently an exact round trip.

Integer values do not secretly carry pointer association in the core language. A claimed reconstruction guarantee must be implementable from the numeric value and the profile's defined mapping/environment state; it cannot depend on an undocumented pointer history attached to an otherwise ordinary integer SSA value.

A profile may provide a usable round trip for live interior pointers in a flat registered memory map, only address inspection for some other space, and no pointer/integer conversions at all for a capability-like space. Each case must be stated. Supporting `ptrtoint` does not imply support for `inttoptr` or for reconstruction of lost pointer state.

Conversions may have a partial value domain; executing a supported conversion outside that domain causes `invalid_pointer_operation`. A successful conversion to an address-only pointer remains subject to all restrictions on that value. Stable numeric inspection does not itself authorize dereferencing reconstructed bits.

Arithmetic on a converted integer is ordinary modular integer arithmetic. It is not object-preserving pointer arithmetic, and a reconstruction guarantee for an unchanged value does not extend to arbitrary arithmetic results. Use `ptr_offset` when the intended operation preserves an allocation association.

### Constant Pointer Operations

The initial constant-expression set additionally admits `ptr_eq`, `ptr_ne`, `ptr_offset`, `ptr_diff`, and `addrspacecast`, subject to all ordinary typing and validity rules and the following restrictions.

Symbolic arithmetic must retain an identified global allocation, remain within its bound layout extent, and be representable by supported relocations. A symbolic `ptr_diff` must use two positions of that same allocation; its offset difference can then be determined without a final link address. Constant `field_addr` still selects actual global record subobjects.

A constant pointer comparison must be decidable without an unresolved final address or unspecified placement. Comparisons between positions of the same identified allocation, or comparisons with known null/non-null values, can normally meet that requirement. A comparison whose answer depends on whether separate objects are adjacent cannot be used as a constant expression in this initial language.

A constant address-space conversion requires a supported symbolic mapping and relocation that preserve association and restrictions. A runtime-only conversion mapping is not a constant initializer. Numeric conversions retain their existing requirement of full evaluation at binding.

A pointer fault during required constant evaluation is a compilation or binding diagnostic, not a runtime fault. MMIO, ordinary/unaligned loads and stores, atomics, and fences are never constant-expression operations.

### Memory-Operation Verification

A verifier must check operand/result types, integer widths, static field paths, exact atomic location types when known, access clauses, and the required result counts. `ptr_eq` and `ptr_ne` return one `i1`; `ptr_diff` returns its declared integer type; `atomic_cmpxchg` returns `iN` followed by `i1`.

Binding resolves supported spaces, conversion pairs, object mappings, device contracts, atomic widths/agents/alignment, and required helpers. Known access-kind or immutable-target mismatches are rejected, including through transparent pointer derivations. A statically known invalid path is not accepted as a runtime pointer-fault case.

Execution-dependent invalid values in otherwise supported operations use the specified fault rules. Static analysis may diagnose a guaranteed runtime fault without reclassifying all constant faulting operands as malformed SMIL. Explicit constant expressions are different: required evaluation must succeed.

## Execution Violations, Resource Limits, and Optimization

SMIL operations either complete with their specified values/effects or perform a specified transfer or terminal fault. This core introduces no `undef`, `poison`, arbitrary-value read, or undefined-behavior escape for uninitialized storage, data races, or exhausted resources. A terminal violation is an observable execution event, including when the operation's normal result would be unused.

The portable execution contract is `smil.execution.checked.v1`. It establishes `uninitialized_read` and `data_race`, retains `resource_exhausted`, and defines the validation stages below. These faults do not become declared raised payloads, cannot be caught by `invoke`, and do not initiate orderly shutdown. Effects of earlier completed operations remain observable; the failing operation produces no SSA result and cannot resume.

This section applies to ordinary, explicit unaligned, and atomic memory operations, local construction, calls, runtime helpers, and lifecycle operations as applicable. Device transactions retain their separate access contracts. A malformed type, static field path, unsupported contract, invalid constant expression, or impossible static placement is still a verification/binding diagnostic, rather than a runtime fault-selection case.

### Initialized Storage and Complete SSA Values

Every SSA value is complete. Initialization state belongs to a storage allocation and its representation, never to an SSA bit pattern. There is no partially initialized SSA record or pointer, and no instruction that manufactures an uninitialized SSA operand.

A newly created mutable local object without an initializer has no initialized representation bits. Reusing the same physical frame bytes does not inherit initialization from an expired object. Zero-filled RAM, a debug fill pattern, or a compiler's incidental clearing of private storage does not constitute a SMIL initializer. Immutable locals still require explicit complete initializers.

A successful typed initializer or store establishes its complete value encoding. For an integer, this defines every bit in its representation bytes, including the unused high bits that canonical storage clears. It does not initialize allocation padding. An integer view at an interior byte position initializes only its own representation bytes, with the selected byte order. Pointer and function-reference initialization establish complete matching typed values, including any required association/representation state; integer views of their encodings remain forbidden.

A record initializer or store establishes its logical fields recursively. A field store establishes that field's representation but does not initialize its siblings. Record and integer allocation padding is not readable through the core's integer views and has no initialization requirement for typed value loads. An empty record has no value-bit reads; loading it still requires a live permitted typed object position.

The initialized-bit requirement of an integer load is its N logical value bits in the addressed representation and byte order. A pointer/function-reference load requires the complete matching value representation. A record load requires every logical leaf value, recursively. Ignored integer high bits and aggregate padding do not add requirements to that typed load. If any required bit is uninitialized, the operation faults with `uninitialized_read` before returning any value.

```SMIL
func @read_unwritten() -> ([i16]) {
^entry():
    %slot = alosf mutable [i16]
    %value = load [i16] %slot
    return %value
}
// On invocation: uninitialized_read at load; no result is returned.
```

The program above is well-typed. A compiler may warn or replace the reached load with an equivalent terminal fault; it cannot turn the function into a value-returning function or fault merely because the uncalled definition exists.

```SMIL
func @partially_write() -> ([i16]) {
^entry():
    %slot = alosf mutable [i16]
    %first_byte = ptrcast [ptr [i8]] %slot
    store %first_byte [i8 7]
    %byte = load [i8] %first_byte
    %whole = load [i16] %slot
    return %whole
}
// The byte load succeeds on either byte order.
// The i16 load faults: the other representation byte is still unwritten.
```

An uninitialized value cannot be made harmless by later masking, comparison, selecting another record field, discarding the load result, or overwriting the destination. In particular, loading a partial record and then extracting an initialized field still faults at the record load. Load that field directly when only its value is required.

A plain `store` and `atomic_store` need no previous initialized value at their destination. They may establish the first complete value when permissions and ordering permit. `atomic_load`, every `atomic_rmw` including `xchg`, and both outcomes of `atomic_cmpxchg` read the previous complete value and require it to be initialized. An unsuccessful compare/exchange does not initialize anything. A fence reads no object value. An authorized `mmio_load` obtains a complete value under its device contract; it does not consult an ordinary-storage initialization bitmap. Device transactions use their own ordering contract, while any DMA access to ordinary RAM must also be covered by the environment's ordinary-memory ownership/agent rules.

A successfully constructed global is fully initialized in its logical fields. A reserved dynamic global remains not ready until its complete factory result is installed. Access before readiness faults with `global_not_initialized`, and after finalization with `global_finalized`, before considering initialized bits. Loading an initialized pointer whose target has expired succeeds as a value load; later use of that pointer still obeys lifetime checks.

External ordinary-storage regions require a contract identifying the initialized byte ranges or complete typed values on entry and the updates performed by external producers. A foreign call must return complete declared values and establish initialization for any output region it claims to initialize. A signature alone does not establish output initialization. Unsupported or unverifiable boundaries require a conforming adapter or rejection; guessing that arbitrary external RAM is initialized is insufficient.

### Initialization Tracking and Proofs

Initialization is checked at the actual read, not deferred until the loaded value affects control flow. A backend can use definite-initialization proofs, per-leaf flags, byte-validity bitmaps, specialized type walkers, or equivalent mechanisms. The choice is private, but the result must match every permitted pointer alias and integer view.

Because current integer stores define whole representation bytes and integer views cannot access padding or pointer encodings, a per-byte validity bitmap plus typed pointer/function-reference construction state is sufficient for this core. A proof can remove all tracking for a local object whose complete initialization dominates every read. At CFG merges the statically known initialized set is the intersection of incoming sets; loop analysis must compute a sound fixed point. A store that might alias an object can add initialization only for bytes it is proven to define.

A successful load does not initialize the object or unrelated bytes. Passing an address to an unknown call does not prove that it was written. A complete typed copy reads its source first; it cannot propagate a hidden uninitialized marker. Whole-record accesses validate all their read requirements before publishing any field result or changing any destination field.

Private shadow-state accesses are not source-level reads and do not themselves create source data races. Their implementation must nevertheless be synchronized, bounded, and inaccessible through ordinary SMIL pointers. Tracking state is tied to allocation identity and reset on each new lifetime. Metadata exhaustion follows the resource rules; dropping tracking is never an allowed fallback.

### Data Races and the Checked Execution Prefix

A **memory footprint** is the union of representation-byte ranges of the integer, pointer, or function-reference leaves actually accessed. Record footprints are the union of covered leaves, excluding padding; integer subviews use their own representation-byte ranges. Two accesses conflict when footprints overlap and at least one actually writes. A failed compare/exchange is a read, not a write. Two properly typed atomic accesses to the same supported atomic location do not constitute a data race.

For accesses by different participating agents, an overlapping conflicting pair with at least one non-atomic access is a **data race** unless ordered by happens-before. The happens-before relation, release/acquire communication, and `seq_cst` order are those already specified under Atomic Access to Shared Ordinary Storage. Different wall-clock times, scheduling one thread after another, an implementation's internal lock, or the CPU's native memory ordering do not by themselves create an application happens-before edge.

The checked contract evaluates an execution as a prefix of completed memory events and synchronization events. Before committing the next access, it checks the access's actual read/write footprint against prior conflicting events by other agents. If a required happens-before ordering is absent, that access faults with `data_race` before its result or memory effects are committed. A possible future access that has not executed is not a violation yet. A read performed before any initialization can therefore fault with `uninitialized_read` without predicting a later writer.

A valid implementation may prove that a conflict cannot arise, enforce an environment ownership discipline that establishes the required ordering, or maintain exact equivalent runtime histories. Merely serializing a racy program behind a private instrumentation lock must still detect the missing application ordering. Sampling, “best effort” detection, history eviction without a sound summary, or reporting after an invalid result escapes is insufficient.

To enforce this rule, a multi-agent environment must coordinate validation, value observation, conflict history, and access commitment. It must retain enough read as well as write history, distinguishing allocation identities and byte ranges. A last-writer record alone misses a later write racing with an earlier reader. Safe summaries can discard history only when all relevant future agents are known to happen after it or an equivalent proof applies. Counter/history exhaustion faults before allowing an unchecked event.

Atomic release/acquire edges are based on the actual write observed, not just equal numeric values. An acquiring operation can use that prospective edge when validating its own event; the edge becomes effective only if the operation commits. Conditional atomic operations determine their actual write footprint using a private initialized-value observation protected by the validation protocol. That observation is not a result exposed to SMIL before the race check succeeds.

A profile advertising several agents must supply these enforcement/proof obligations together with its existing atomic progress, interrupt, and reentrancy contracts. The core adds no thread-creation or interrupt-control syntax. An unverified frontend “race-free” assertion is not a proof. Foreign participants or DMA writers cannot be omitted from the domain when they can touch shared ordinary storage; the profile must include and constrain them or reject that use.

The current reference profiles remain single-agent environments with asynchronous application interrupts, DMA, and foreign writers excluded. Their domain proves data-race freedom without a runtime detector or history buffer. Enabling another agent requires a separately versioned profile with the additional obligations above; it is not a flag that can be switched on after linking.

### Portable Resource Exhaustion

An operation that cannot obtain a required execution resource faults with `resource_exhausted`. This rule applies to every conforming profile, not only the checked reference boards. It does not return null, truncate values, wrap a counter, drop a callback, reuse a live identity, continue with unchecked memory, or implicitly convert failure into a raised payload. Recoverable allocation or bounded-counter operations require separately defined explicit operations; this core introduces none.

Resources include software/native stack and frame space, call packets, spill/work buffers, object/initialization/race metadata, helper scratch, callback entries, finite allocation or synchronization counters, and other profile-declared execution capacities. Existing logical widths and signatures are not reduced to fit. Static type/function/continuation catalog overflow is a link diagnostic, not a runtime counter event. Source-level dynamic allocation is still outside this core.

Profiles must identify capacity domains, bounds, accounting units, supported reservation points, and emergency reporting resources. Resource arithmetic is evaluated with checked mathematical addition/multiplication/rounding before any finite counter or address encoding is written. Required resources are validated and reserved before the associated operation commits its ordinary effects. Every native push, helper entry, runtime lock acquisition needing storage, and software-frame extension must be covered by a prior reservation or a proven bound; crossing a guard after corruption is not an implementation of the fault.

A local-object lifetime reserves its required semantic identity/registry accounting and any initialization tracking before the declaration becomes usable. A call validates its callable before reserving the packet/frame resources needed to enter it. Arguments already computed by earlier operations retain their effects. A lifecycle completion callback reserves its entry before the initializer action begins, then commits the callback only after successful completion as already specified.

A statically impossible section placement, oversized fixed frame, unsupported type, or insufficient fixed startup capacity is a binding/link diagnostic. If success depends on runtime depth, active objects, argument-pack size, execution counts, or registration history, a conforming execution either obtains the resources or faults at the relevant checkpoint. Static analysis may warn about an inevitably failing executed call; it does not make an ordinary unexecuted path execute a fault.

The resource reservation for one operation is all-or-fault: a failure does not partially initialize a local, publish a new object, enter a callee, append a callback, or perform a memory/device operation. Existing effects are not rolled back. Implementations may make private tentative reservations, but must not expose them as successful actions by another agent or require application allocation to undo them. The terminal gate prevents subsequent normal commits after failure.

Fault reporting uses pre-reserved emergency state and cannot itself depend on the exhausted capacity. Monitor traps may use their separately reserved architectural exception context. If a platform cannot guarantee a terminal path for an advertised resource domain, that profile/use is unsupported. Host process termination, physical power loss, arbitrary hardware corruption, and environmental breach of a promised memory reservation are outside this resource protocol; they are not silently relabeled as a conforming SMIL `resource_exhausted` event.

### Resource Accounting and Optimization

Resource behavior has two distinct kinds of accounting:

| Kind | Required rule |
| --- | --- |
| Profile-mandated semantic accounting | Preserve the specified identity increments, live-object slot charges, callback registrations, and other explicitly mandated events even when their physical representation can be optimized |
| Backend-dependent physical accounting | Charge the frames, spills, work buffers, native call state, and tracking storage actually selected by the published lowering plan |

For a fixed linked image and its execution plan, a checkpoint's reservations and failure condition are specified. An optimizer cannot assume success merely because exhaustion is exceptional or replace an executed exhausted reservation with unchecked writes.

Different conforming lowerings may consume different physical resources and therefore reach different resource limits. Register allocation, helper specialization, eliminating a proven-unneeded bitmap, or avoiding a spill can prevent physical exhaustion. These choices must be reflected in the new object/image plan and digest, while preserving non-resource values, effects, semantic accounting, and all other faults. There is no portable promise of one recursion depth across optimization levels or processor profiles.

The reference profiles require a fresh allocation ID for each processed local declaration and a slot charge for each live registered object, including the monitor and reserved globals. For v2, `next_allocation_id + count` must fit `u32` before assigning the half-open ID range `[next_allocation_id, next_allocation_id + count)`; `UINT32_MAX` is the exhausted next-counter sentinel and is not assigned as a new local ID. No arithmetic wraps to create that sentinel. Avoiding a physical registry entry by proof does not silently waive those logical charges. Global IDs and callback accounting retain their existing rules. Eliminating a required source-level allocation/registration solely to avoid its mandated exhaustion is not ordinary dead-code elimination under these profile versions.

Inlining or tail-call transformations must preserve object lifetimes, identity accounting, pointer association, and externally visible call contracts. They can alter physical frame usage only where the selected ABI allows the resulting implementation. A proof that a local address does not escape can help representation elimination, but is not permission to ignore mandated counters.

### Validation Order and Simultaneous Violations

Operand-producing operations execute first under ordinary CFG sequencing. There is no “simultaneous violation” between a load that produces an argument and a later call: a fault in the earlier load prevents the call entirely. Across separate operations in one agent, the first executed failing operation wins.

Within one operation, use the following ordered stages. A stage that does not apply is skipped:

| Stage | Checks and selected fault |
| --- | --- |
| 1. Operation domain | Arithmetic domain, callable/null/signature/pack/lifecycle validity, pointer association/lifetime/range/view/alignment/permissions/access kind, and global readiness/finalization; use the existing operation-specific fault |
| 2. Required initialized values | Every storage value that this operation reads; `uninitialized_read` |
| 3. Checked concurrency | Actual conflicting read/write footprint against the completed prefix and prospective synchronization; `data_race` |
| 4. Execution resources | All reservations necessary to commit this operation, with checked capacity/counter arithmetic; `resource_exhausted` |
| 5. Commit | Perform the specified logical action, make results available, and publish the associated metadata/synchronization |

Stage 1 first validates the operation's principal domain (`invalid_call`, `invalid_variadic_access`, `invalid_lifecycle_transition`, or `invalid_pointer_operation` for the respective operations). A memory operation then validates object association, extent, type view, alignment, rights, and access kind; failure is `invalid_storage_access`. Only after those succeed does an associated global's state select `global_not_initialized` or `global_finalized`. A not-ready global does not authorize a write through an immutable pointer or turn a device access into ordinary RAM access.

For `on_exit`, state and agent authorization are checked before the callback target, so an invalid lifecycle transition precedes `invalid_call` at that one registration. Division checks zero and then its applicable quotient-overflow case in stage 1, before helper/work-buffer reservations.

Within one stage, multiple failed checks with the same fault kind need no further ordering. If one aggregate operation can name several failing global states, `global_not_initialized` precedes `global_finalized`. Ordinary aggregate accesses share one enclosing allocation; this tie-break also covers helpers with several validated locations. Existing independent arithmetic faults remain unchanged: a division checks zero first; signed quotient overflow applies only to the nonzero `MIN_N / -1` case. User `trap` commits its explicit identifier when reached and requires no application allocation.

Examples of selected outcomes:

| Conditions at one operation | Result |
| --- | --- |
| Expired/null access and missing initialized bits | `invalid_storage_access`; no initialization metadata is read through the invalid association |
| Valid access to a not-ready dynamic global | `global_not_initialized`, before its intentionally unwritten contents are considered |
| Read needs unwritten bits and would also conflict with prior events | `uninitialized_read` |
| Initialized conflicting access and insufficient history/work capacity | `data_race` if the existing history proves the conflict; otherwise pre-commit `resource_exhausted` if exact checking cannot be maintained |
| Invalid indirect callable and an exhausted call stack | `invalid_call` |
| Uninitialized `atomic_cmpxchg` location | `uninitialized_read`; no comparison, update, or successful synchronization is published |
| Failed initialized compare/exchange concurrent only with another read | No conflicting write from that compare/exchange; other validity rules still apply |

Validation and commitment must be protected against check/use races and lifetime changes. Private reads needed for validation do not publish a result, perform a device transaction, initialize a value, or constitute a completed SMIL event. A backend can interleave or fuse guards only when it preserves the stage-selected fault for the same reached operation and commits no prohibited effects.

A conforming implementation pre-reserves sufficient fixed validation/emergency scratch to decide the earlier applicable stages using existing valid metadata. Resource failure cannot preempt a selected earlier-stage fault merely because a guard was lowered through an allocating helper. Growth needed to retain the next committed history belongs to stage 4; the existing history must remain exact until then. If those obligations cannot be implemented within a profile, binding fails. The implementation must not label missing tracking information “no race” or invent an initialization value.

Across agents, more than one operation may be eligible to fail. The environment selects one next validation/commit event consistent with sequencing, synchronization, and the atomic order. The first terminal event closes the program instance; its identifier is the reported fault. This cross-agent winner may differ between legal schedules. A scheduler choice cannot retroactively erase a completed effect. Already authorized external/device activity obeys its explicit in-flight transaction contract; no further normal SMIL operation commits after the terminal event.

Checks in this table apply before ordinary storage effects. Bus/device faults after an authorized physical transaction begins retain the existing device/hardware contract; no source guard can promise to undo an external transaction that has already occurred. Similarly, an initializer that raises follows its already defined cleanup path, and a subsequent cleanup fault terminates that later path; it does not replace the earlier completed history.

### Required Checks and Optimizer Assumptions

A successful verification or binding pass proves well-formedness and implementability, not that every dynamic execution is violation-free. Assertions about undefined behavior in a source language, sanitizers being disabled, integer signedness, pointer pointee spelling, and an ordinary function signature do not grant additional SMIL assumptions.

| Transformation | Required proof or preserved behavior |
| --- | --- |
| Delete an unused ordinary load | Preserve or prove absent its domain, initialization, race, and associated resource faults |
| Forward a preceding store into a load | Same live location/value bits, definite initialization, permissions/readiness, and no intervening aliasing or unordered conflicting event; preserve remaining checks |
| Hoist or speculate a load/division/pointer operation | No new fault on a path where the original would not execute; preserve ordering against prior effects/faults |
| Replace two loads with one | Prove both see the same value and that removing the second cannot hide a defined fault or synchronization event |
| Scalarize a record access | Validate all required fields before exposing any result or changing a destination field; preserve fault selection |
| Widen/split ordinary accesses | Keep the source footprint, legal views, initialization requirements, and independently accessible neighboring fields intact |
| Simplify atomic operations | Preserve read-versus-write effects, observed write identity, synchronization, races, SC order, and progress |
| Eliminate a guard/bitmap | Establish the corresponding invariant on every execution reaching the use, including joins, loops, calls, and aliases |

A successful guard can justify facts for the operations it dominates while the checked object, readiness, and ownership facts remain stable. An unknown call, concurrent actor, lifetime transition, or permitted aliasing write can invalidate those facts. Check motion across effects or faults requires a proof of the complete transformed prefix, not merely equal values on successful returns.

Unreachable CFG paths need no dynamic checks because they do not execute. Static structural requirements still apply to all blocks. When an executed operation is proven to fail, replacing it with its correctly selected terminal event is permitted; treating the path as impossible is not.

Logical aggregate preflight is not aggregate atomicity. A multi-agent implementation can split physical field accesses only while preventing newly introduced conflicting effects and preserving the checked event and fault semantics; safe ordinary implementations may consequently be stronger than a minimum bus transaction. Profiles still advertise atomic progress only for the explicit supported atomic operations.

### Versioned Runtime and Object Obligations

The earlier `.checked.v1` profile manifests selected resource faults but did not supply this initialization/race/priority contract. Their published identities and digests must not be silently changed. This proposal supplies `.checked.v2` successors for the same 38 CPU/mode combinations, referencing `smil.ref.checked.contracts.v2` and runtime component `smil.rt.checked.packet.v2`. CPU instruction selections, physical layouts, pointer/function encodings, packet ABI IDs, memory maps, and device protocols remain the same; all additional tracking storage is charged within the existing limits.

The new shared contract embeds the exact execution-contract reference/digest, adds built-in fault ID 14 for `uninitialized_read` and 15 for `data_race`, and preserves IDs 1 through 13 and the user-ID base 65536. Memory/atomic/initialization helpers implement the stages above. A build must regenerate target-bound interface/object digests when selecting a successor profile; an old v1-bound object is incompatible with a v2-bound program under the existing exact-component policy.

No new source operation or general allocation API is required. The existing interface/object/library/link/image container formats remain version 1: their bound target and shared-contract digests already distinguish the stronger semantics. Every v2 object additionally carries one private `aux` definition named `execution_plan`, located in a `metadata` blob whose canonical JSON format is `smil.execution-plan.v1`. Its runtime descriptor token is `smil.execution.checked.v1#plan`. The linker validates its contract/profile ownership and metadata bounds, and preserves the required target tables.

The execution plan identifies its module, execution-contract digest, profile, and each defined function's frame size, native-stack reservation, local shadow size, and checked reservation sites. Frame size includes the header, locals, shadow, and private work area. Native bytes include the callee-owned return linkage and maximum native temporary/frame use, excluding nested callees. Local records contain declaration ordinal, canonical type key, frame offset/size, initial-state flag, tracking choice, and bitmap offset/size. Type keys use the existing canonical type-key encodings; function keys are canonical value triples, not provisional numeric IDs. Each site names the lowered operation, fixed resource costs, and resource domains with runtime-dependent costs. `software_bytes` and `native_bytes` reserve physical stack capacity; slot/ID/callback counts reserve their existing pools. `tracking_bytes` attributes bytes already included in the relevant software/runtime storage charge, not a second independent or unbounded pool. The single-agent profiles have zero synchronization-tick/history cost. Future profiles must supply explicit capacities for any additional domains. The actual dynamic amounts are computed by the emitted checked code from values such as a forwarded argument pack; metadata is not an executable expression language. Published frame/shadow extents must fit and must match the emitted code. Resource-dependent optimizations regenerate the plan, blob digest, object digest, and final image provenance.

A v2 single-agent reference implementation can put compressed local initialization bitmaps after the frame's local objects, in its private temporary area. The existing frame header and object record are unchanged: `owning_frame_raw`, the frame's function ID, and compiler-emitted slot/shadow descriptors locate tracking state. Reserved-zero fields stay zero. Global readiness already proves complete global initialization; no per-byte global bitmap is needed for these profiles. Race-free single-agent execution requires no race history. The additional costs are therefore mostly local shadow bytes and their checks, with proof-based elimination available.

A future multi-agent profile must provide a different runtime component with the required histories, synchronized tracking/commit protocol, fault gate, and advertised progress guarantees. The execution contract defines that profile's obligations; it does not claim that the present 38 environments implement concurrency.

### Implementation and Conformance Direction

Start with definite-initialization analysis and a conservative local byte-validity fallback on one small little-endian and one big-endian target. Preserve existing arithmetic/pointer guards while introducing common validation stages. Add precise partial-integer and record-field cases before optimizing shadow storage. Existing single-agent targets can prove the race predicate false at binding.

The accompanying contract/plan schema and executable reference-model vectors cover fresh/reused local storage, partial-width writes in both byte orders, ignored integer high bits, empty/partially initialized records, atomic read/write distinctions, publication ordering, unordered and mixed atomic/ordinary conflicts, history retention, staged fault selection, resource preflight, and profile/digest migration. They are specification checks, not a compiler, production race detector, native runtime, or hardware validation.

These semantics intentionally require guards before values escape. For implementation comparisons, [Clang's MemorySanitizer documentation](https://clang.llvm.org/docs/MemorySanitizer.html) describes initialization instrumentation, and [LLVM's undefined-behavior manual](https://llvm.org/docs/UndefinedBehavior.html) documents its different `undef`/`poison` model. SMIL's rules above are its own mandatory contract, not a request to enable an optional sanitizer or inherit another IR's optimizer assumptions.

## Functions

A **function** is a module-level declaration with an ordered list of fixed parameter types, an optional variadic marker, an ordered list of result types, and an optional raised-payload type. A definition supplies basic blocks. Its complete callable contract includes its resolved ABI and effective signature attributes.

Functions are not nested within other functions.

### Signatures and Declarations

A function signature specifies parameter and result types:

```SMIL
declare @emit([i8]) -> ()
declare @increment([i16]) -> ([i16])
declare @split([i16]) -> ([i8], [i8])
```

Empty parentheses indicate an empty list. A function returning no values does not produce a special void value.

Signature entries contain types and any ABI extension attributes, not SSA bindings. Parameter names are introduced by the entry block of a definition. Attributes such as `signext` and `zeroext` do not change those SSA parameter types.

A declaration without a body permits calls to a function whose definition is supplied elsewhere.

Repeated declarations of the same function are permitted only when their logical signatures match after alias resolution and their resolved ABIs and effective ABI attributes agree. There may be at most one definition of a function within a module.

All declarations and the definition of a function must agree on fixed parameter/result types, the variadic marker, the optional raised-payload type, and the resolved physical-interface contract. An omitted ABI clause selects the profile's default ABI. Function-reference types use this same complete contract.

Function declarations and definitions share the module-level value-symbol namespace with global storage objects. A name cannot identify both a function and a global storage object.

### Definitions

A function definition has the following form:

```SMIL
func @name(<parameter types>) -> (<result types>) {
    <basic blocks>
}
```

For example:

```SMIL
func @increment([i16]) -> ([i16]) {
^entry(%value: [i16]):
    %next = add [i16] %value [i16 1]
    return %next
}
```

An optional `abi("identifier")` clause may follow the signature, then an optional `raises([T])` clause, before the opening brace. Declarations use the same order and rules.

The first block is the **entry block**. Its parameters match the fixed logical parameter list, with one final `[varargs]` pack parameter exactly when the signature is variadic. That pack is an explicit logical extension, not an ABI carrier. Physical extension, hidden result areas, and exception carriers introduce no other SMIL entry parameters.

Entry-block parameters are the function parameters. They introduce the only SSA bindings for those incoming values.

The entry block has no incoming CFG edges and cannot be a branch destination. Its label need not be spelled `^entry`; its position as the first block establishes its role.

Every function definition contains at least one block.

### Entry Declaration Region

The beginning of the entry block may contain:

1. Function-local type declarations.
2. Local storage declarations using `alosf`.

Ordinary executable operations follow these declarations.

Once a local storage declaration appears, no further local type declarations are permitted. Once an ordinary operation or terminator appears, no further local declarations are permitted.

Other blocks contain ordinary operations followed by a terminator. They cannot contain local type or `alosf` declarations.

### Calls

A direct call identifies a function symbol and supplies an ordered list of value arguments:

```SMIL
call @emit([i8 65])

%next = call @increment([i16 20])

%low, %high = call @split([i16 0x1234])
```

These examples assume the corresponding function declarations above.

For a fixed-arity function, argument count and types match its parameter list. A variadic function requires the fixed prefix plus explicitly typed additional arguments or a final pack expansion. Result count and types follow the result list. Ordinary `call` accepts only a non-raising callable contract; a raising callee requires `invoke`.

The call inherits the resolved ABI and effective attributes of the callee declaration. Extension attributes affect boundary lowering, not the types of the argument operands or returned SSA values.

Each produced result must be bound to a fresh SSA identifier. Result identifiers may remain unused.

`call` and `call_indirect` are ordinary operations. Normal return resumes at the next operation; a terminal fault or explicit program exit does not return. `invoke` and `invoke_indirect` instead terminate their block and transfer through one of their explicit continuation edges.

A call creates a distinct function invocation. Recursion is permitted.

Calls may affect accessible storage. An optimizer may assume more restrictive effects only when established by the function definition or a separately specified effect contract. Previously computed SSA values remain unchanged even when a call modifies storage from which they were loaded.

Parameter passing and result delivery are logical SMIL operations. The resolved ABI determines their physical implementation, including any use of registers, stack locations, copies, or hidden output pointers. These implementation details must preserve by-value semantics and result lifetimes as specified in Target Profiles and ABI Lowering.

The following sections define indirect and variadic calls, explicit typed exceptional transfers, and the cooperative nonlocal-exit policy. None adds an implicit transfer to an unlisted CFG destination.

### Returns

The `return` terminator ends the current invocation and supplies the function’s results:

```SMIL
return
return %value
return %first, %second
```

The number and types of returned values must match the function’s result list.

All return sites in a function must satisfy the same signature.

A returned record is one result of record type. It is distinct from a function returning several separate results. A function's optional `raises` clause does not add a normal result; exceptional completion uses `raise` and an invoking caller's exceptional edge.

Returning ends the lifetime of the invocation’s local storage objects. Returning a pointer to such an object does not extend that object’s lifetime.

A function is not required to reach a return dynamically. For example, a function may execute an infinite loop. Every block must nevertheless have a valid terminator.

### Function References and Indirect Calls

A **function reference** has type `fnptr`, with a complete callable contract:

```SMIL
@Unary = type [fnptr ([i16]) -> ([i16])]
@FallibleUnary = type [fnptr ([i16]) -> ([i16]) raises([i8])]
@ForeignUnary = type [fnptr ([i16] signext) -> ([i16] signext) abi("vendor.v1")]
```

The parameter/result types, variadic marker if any, effective ABI attributes, resolved ABI, and optional raised-payload type determine compatibility. Transparent aliases are resolved; nominal record identities are retained. Omitting `abi(...)` selects the profile's default ABI, including in a function-reference type. While unbound, that default remains unresolved.

The callable contract must agree exactly with the target function. There is no implicit conversion between different callable contracts, including between raising and non-raising functions. A wrapper function supplies any required adaptation.

`fnptr` is distinct from `ptr S [T]`. Its representation may be a code address, a banked address, or a descriptor; the profile defines its storage layout, null encoding, equality implementation, and call sequence. The initial model has one function-reference representation per resolved callable contract. It does not assume that code and data pointers have the same size or encoding.

```SMIL
%callback = fnaddr @increment
%next = call_indirect %callback([i16 20])

$increment_callback = const (fnaddr @increment)
$no_callback = const [Unary null]
```

`fnaddr` requires a function declaration and produces a non-null reference with that declaration's callable contract. A bare function symbol remains a direct-call target, not an ordinary value operand. `call_indirect` requires a non-raising callable contract and follows the same argument/result rules as `call`; raising functions use `invoke_indirect`.

`fn_eq` and `fn_ne` accept two references with the same callable contract and return `i1`. Null equals null and differs from every function reference. Non-null references compare by resolved function identity, including through different supported descriptors for that function. Distinct wrapper functions remain distinct identities. Code folding or trampoline lowering must preserve observable equality.

A function reference may be passed, returned, stored in a matching typed object, or included in a record. These copies preserve its complete callable representation. It is not accepted by `ptrcast`, `ptrtoint`, `inttoptr`, `addrspacecast`, `field_addr`, data-pointer comparisons, or byte arithmetic. Casting a pointer to storage containing a function reference does not authorize reading that representation as integers.

An indirect call through null or an invalid target causes terminal `invalid_call` before entering a callee. Unsupported callable representations are binding errors. A foreign interface supplying function references must establish a valid compatible target and representation; the backend must prove or check validity, or diagnose an unsupported interface. The core does not manufacture function references from numeric addresses.

Function targets remain available for the program instance's lifetime. Dynamic code unloading and closures with hidden environments are not implicit in `fnptr`. A closure is lowered explicitly as a record containing a function reference and an environment value, with the environment passed as a declared parameter.

### Variadic Functions and Argument Packs

A final `...` in the parameter list declares a variadic function. Results are never variadic. The fixed prefix may be empty:

```SMIL
declare @report([i16], ...) -> ()
declare @collect(...) -> ([i16])

// Fixed prefix followed by two explicitly typed additional arguments.
call @report([i16 7], [i8 2], [i16 300])
```

Every explicit argument already has its SMIL value type. There are no default argument promotions. A frontend targeting a C-style variadic ABI must perform the source language's integer promotions and any other required conversions explicitly before the call. The ABI defines classification and physical passing for the actual additional types, not a new interpretation of their logical values.

A variadic definition's entry block receives its fixed parameters followed by exactly one parameter of the special type `[varargs]`. That parameter represents the additional logical arguments and their type identities:

```SMIL
func @first_or_zero(...) -> ([i16]) {
^entry(%args: [varargs]):
    %matches = va_is [i16] %args [i16 0]
    br_if %matches, ^present(), ^absent()

^present():
    %first = va_get [i16] %args [i16 0]
    return %first

^absent():
    return [i16 0]
}
```

The argument pack is an immutable borrowed SSA value valid only in its owning invocation. It may flow through that function's block parameters. It cannot be stored, addressed, put in a record, returned, raised, or supplied as an ordinary function parameter. `[varargs]` is not a storable type and has no public layout or pointer representation.

| Operation | Meaning |
| --- | --- |
| `va_count [iM] pack` | Number of additional arguments as an unsigned-represented `iM`; faults if it does not fit |
| `va_is [T] pack index` | `i1` one if the index exists and its type equals T after alias resolution, otherwise zero |
| `va_get [T] pack index` | Complete value of type T at that index; faults for an absent or differently typed argument |

Indices may have any supported integer type and are interpreted as unsigned without masking or narrowing. Retrieval does not advance a cursor or modify the pack. A requested T must be a supported ordinary value type; it cannot itself be `varargs`. Pack accesses require a live owning invocation. Invalid retrieval, an expired pack, or an unrepresentable count causes terminal `invalid_variadic_access`.

A final `...%pack` in a variadic call expands a pack into additional arguments:

```SMIL
func @forward([i16], ...) -> () {
^entry(%tag: [i16], %args: [varargs]):
    call @report(%tag, ...%args)
    return
}
```

All fixed arguments must be supplied explicitly before the expansion. Explicit additional arguments may precede it. At most one expansion is allowed, it must be final, and the callee must be variadic. The source pack remains unchanged and live during the call; the callee receives its own invocation-scoped pack of logical values. Copying argument values does not extend the lifetime of their pointees.

The profile must separately advertise static variadic calls, typed-pack receipt by definitions, and runtime pack forwarding. It defines the descriptors or runtime interfaces needed to preserve type checking and complete values. Lack of a native variadic convention does not change the logical semantics; expansion or a helper is permitted.

An outbound foreign variadic declaration may use a supported native ABI. A SMIL variadic definition cannot claim compatibility with an incoming untyped foreign argument area unless an explicit adapter or ABI contract supplies the required type information. The toolchain must reject unsupported receipt/forwarding rather than silently discard `va_get` checking. ABI compatibility does not follow merely from recognizing a native `va_list` layout.

### Typed Exceptional Transfers

A function may declare one raised-payload type after its optional ABI clause:

```SMIL
declare @decode([i16]) -> ([i16]) raises([i8])
declare @foreign_decode([i16]) -> ([i16]) abi("vendor.v1") raises([i8])
```

The payload is one complete ordinary value; a record can carry several error fields. `varargs` is not permitted as a payload. Omission means that the function cannot propagate a SMIL exceptional result. All declarations, definitions, function references, and ABI metadata must agree on this effect.

The `raise` terminator ends the current invocation with its declared exceptional result:

```SMIL
raise <payload>
```

The payload type must equal the function's declared raised type. There are no normal results and no intrafunction successor. Its local storage lifetimes end just as on `return`. A pointer carried by the payload retains its existing association and does not extend its object's lifetime.

A raising callee is entered with an explicit terminator:

```SMIL
invoke @decode(%input) normal ^success() except ^failure()
invoke_indirect %decoder(%input) normal ^success() except ^failure()
```

The callee must declare `raises`. Plain `call` and `call_indirect` reject a raising callable contract, even when a particular invocation could be proven to return normally. A wrapper that handles all exceptional results can expose a non-raising contract.

Each `invoke` has two ordinary, explicit CFG edges:

- On normal return, the normal destination receives the callee's ordered result values, followed by the explicitly written arguments on that edge.
- On `raise`, the exceptional destination receives the single raised payload, followed by its explicitly written edge arguments.

Implicit result/payload values have no SSA names at the source terminator. They are introduced only as destination block parameters. Explicit edge arguments are existing values used at the source terminator and must dominate that use. Each edge's complete argument list must match its destination's parameter types and count.

```SMIL
func @decode_or_zero([i16]) -> ([i16]) {
^entry(%input: [i16]):
    invoke @decode(%input) normal ^success() except ^failure()

^success(%value: [i16]):
    return %value

^failure(%error: [i8]):
    return [i16 0]
}
```

The same block may receive invoke edges and ordinary branch edges when every complete incoming list agrees. If the two invoke edges target the same block, that block must accept both complete lists. No result is available on the wrong edge. Reachability and dominators include both edges, independently of whether the callee can be proven to raise.

The caller need not declare `raises` when it handles the exceptional edge. It declares an effect only when it can propagate a payload using its own `raise`. Reraising is simply `raise` of the received payload; there is no hidden in-flight exception object or `resume` state.

These are logical transfers through callers, not asynchronous interruption. A backend may use a tag/status plus result and payload carriers, explicit branches, or a compatible native mechanism. The ABI must define those carriers and ownership without reading a carrier for the outcome that did not occur. Unsupported combinations are diagnosed.

The frontend emits cleanup operations on normal and exceptional CFG paths where its source language requires them. SMIL does not infer destructors from types, retain an automatic cleanup stack, or search for native language handlers. A cleanup that itself raises follows its explicit CFG; source rules such as termination during a second exception must be emitted explicitly.

Arithmetic faults, pointer/access faults, `invalid_call`, `invalid_variadic_access`, user traps, and lifecycle faults are terminal events, not payloads catchable by `invoke`. Foreign exceptions require an explicit boundary adapter that translates them to a declared payload. An unexpected foreign exception at a non-raising boundary must be contained and cause terminal `invalid_foreign_transfer`; it must not unwind through ordinary SMIL frames. A proven non-throwing interface needs no such dynamic adapter. If the platform cannot establish or enforce the boundary contract, the interface is unsupported. Foreign `longjmp` must not skip SMIL frames through an ordinary call.

### Nonlocal Exits

Within one function, nonlocal source constructs such as `break` or an early return use ordinary CFG edges and block parameters. Across invocations, the supported model is **cooperative propagation** through typed `raise`/`invoke` paths. Every intervening invocation has an explicit exceptional edge and can perform its required cleanup before forwarding.

A frontend needing dynamically targeted exits may include an active target marker and a result in its payload, then test the marker in each handler. One possible representation is a pointer to a dedicated local `i1` marker, together with the result:

```SMIL
@ExitValue = record { ptr [i1], i16 }

func @leave_scope([ptr [i1]], [i16]) -> () raises([ExitValue]) {
^entry(%target: [ptr [i1]], %value: [i16]):
    %live_target = ptr_offset %target [i16 0]
    %payload = record_make [ExitValue] (%live_target, %value)
    raise %payload
}
```

The target invocation supplies the marker, handles a matching marker, and forwards other exits through its declared raised type. The zero offset checks that the marker's allocation is still live without reading it. Handlers must validate a received marker before comparing it with their own; pointer equality alone does not establish lifetime. Source lowering must also ensure that a target belongs to the same agent's active invocation chain. A foreign/live but unrelated target is not made a legal nonlocal destination by this encoding.

This representation is ordinary explicit code, not an implicit continuation capability. It does not capture SSA bindings or resume execution at a previously executed instruction. An expired marker faults under the pointer rules; reusing its old numeric address does not revive its association.

Raw `setjmp`/`longjmp`, stack restoration, returns-twice calls, cross-agent stack transfers, and jumps into a terminated invocation are not supported by this core. They cannot be declared as ordinary functions whose hidden effects bypass CFG or SSA rules. A foreign interface requiring those effects must be adapted to cooperative transfers or rejected. A future saved-continuation extension would need distinct syntax, lifetime, cleanup, and SSA rules.

## Basic Blocks and Control Flow

A **basic block** has a label, an ordered list of parameters, and an ordered sequence of operations ending in exactly one terminator.

```SMIL
^block_name(%first: [i16], %second: [i8]):
    <ordinary operations>
    <terminator>
```

A block without parameters still uses an empty parameter list:

```SMIL
^block_name():
    <ordinary operations>
    <terminator>
```

Block labels belong to the enclosing function. Branches cannot target blocks in another function.

Block labels are control-flow destinations, not ordinary values or data pointers.

### Execution Order

Within a block, operations execute in textual order, subject to transformations that preserve their specified behavior.

There is no implicit fallthrough between blocks. Executing the last ordinary operation does not transfer control to the next block in the file; the block’s terminator determines what happens next.

Only the first block’s position has entry semantics. Reordering other blocks without changing their contents or explicit edges does not change the function’s meaning.

The CFG is not restricted to structured `if` or loop forms. Arbitrary edges between non-entry blocks are permitted when they satisfy the rules in this guide.

### Block Parameters and Incoming Arguments

A non-entry block receives its parameter values from the incoming control-flow edge selected at runtime.

Each edge supplies an ordered argument list. The argument count and types must match the destination block’s parameters.

```SMIL
br ^merge([i16 21])

^merge(%value: [i16]):
    return %value
```

Branch arguments are values available at the source terminator. Argument lists do not contain nested executable operations. They may contain valid constant expressions, which are evaluated statically rather than when the edge is taken.

Explicit arguments are taken from the source’s current bindings before control transfers. An invoke additionally supplies its selected implicit result/payload prefix when the callee completes. All destination parameters are then bound simultaneously from the complete selected edge list.

For example, an edge passing `(%b, %a)` to parameters `(%a, %b)` exchanges the incoming values logically. It does not perform two sequential assignments that could overwrite one of the source values.

These bindings do not create addressable storage, imply a function call, or require physical stack operations. Their implementation is determined during backend lowering.

A value defined in a dominating block may be referenced directly. It does not have to be passed through every intervening block’s parameter list.

### Unconditional Branch

The `br` terminator transfers control to one destination:

```SMIL
br ^destination(<arguments>)
```

For example:

```SMIL
br ^done(%result)
```

An empty argument list is required when the destination has no parameters:

```SMIL
br ^continue()
```

### Conditional Branch

The `br_if` terminator selects between two outgoing edges:

```SMIL
br_if <condition>, ^true_destination(<arguments>), ^false_destination(<arguments>)
```

The condition must have type `i1`.

A condition value of `1` selects the first edge. A condition value of `0` selects the second edge. No other integer type is implicitly converted to a condition.

Only the selected edge transfers control and supplies parameter bindings.

The two edges may target the same block with different arguments:

```SMIL
func @choose([i1], [i16], [i16]) -> ([i16]) {
^entry(%condition: [i1], %first: [i16], %second: [i16]):
    br_if %condition, ^done(%first), ^done(%second)

^done(%answer: [i16]):
    return %answer
}
```

Incoming arguments belong to individual edges, not merely to predecessor blocks.

### Multiway Branches

`switch` is an integer terminator with one required default edge and zero or more cases:

```SMIL
switch [i8] %kind default ^unknown() {
    [i8 0]: ^zero(),
    [i8 1]: ^one()
}
```

The selector must have the annotated integer type. Every case is a constant value of that same type, fully evaluable by binding. Cases compare N-bit patterns; there is no signed ordering, range case, or fallthrough.

Encoded case values must be unique. For example, `[i8 -1]` and `[i8 255]` designate the same case and cannot both appear. An unsupported or faulting constant case is a diagnostic.

The matching case edge is taken, or the default if none matches. Edge operands use the ordinary branch-argument availability and type rules. Every listed edge participates in reachability and dominance, even when the selector is constant. Several cases may share a destination when their argument lists satisfy that block's parameters.

A backend may use comparisons, a decision tree, or a jump table, but the operation remains a flat CFG terminator with exactly these destinations. Zero cases means an unconditional transfer to the default edge.

### Explicit User Traps

```SMIL
trap "user.invalid_state"
```

`trap` requires a constant string identifier beginning with `user.` and having a nonempty suffix. The suffix identifies the user-defined fault within the linked program. It is a terminator with no CFG successors or results.

Execution causes a defined terminal fault using that identifier, preserves preceding observable effects, and does not return to a caller. It does not unwind, run automatic cleanups, or initiate orderly global shutdown.

The environment defines the reporting/termination mechanism; a backend cannot replace a trap with fallthrough, a return value, or an assumption that execution was impossible. SMIL does not introduce an `unreachable` terminator with undefined behavior. A source-level assertion that must be observable on failure uses an explicit branch to `trap`.

Trap identifiers, rather than source strings describing arbitrary expressions, form the stable reporting contract. Additional diagnostic payloads require a separate operation or an explicit reporting call before the trap.

### Terminators

The initial core defines these terminators:

| Terminator | CFG successors | Meaning |
| --- | --- | --- |
| `br` | One | Transfer control and arguments to a block |
| `br_if` | Two outgoing edges | Select an edge using an `i1` condition |
| `switch` | Default plus case edges | Select by an integer bit pattern |
| `invoke`, `invoke_indirect` | Normal and exceptional edges | Call a raising function and transfer its outcome |
| `return` | None | Return the function’s declared normal results |
| `raise` | None within this function | Propagate the declared exceptional payload to its invoking caller |
| `trap` | None | Cause a defined user terminal fault |
| `exit` | None | Request orderly program shutdown with an `i32` status |

Every block must contain exactly one terminator, which must be its final operation.

Ordinary operations cannot appear after a terminator within the same block.

`call` and `call_indirect` remain ordinary operations even when a particular callee execution does not return. `invoke` and `invoke_indirect` are terminators by definition.

The terminators above have only their specified successors. A missing terminator does not imply a return, exceptional transfer, or trap. Neither implicit unwinding nor saved-stack restoration creates hidden CFG edges.

Integer operations may raise terminal arithmetic faults, and pointer/memory operations may raise the terminal faults defined in Pointers and Memory Access. Such events terminate normal execution without introducing a normal successor edge. They do not make an otherwise ordinary operation a block terminator.

### Integer Comparisons

The `cmp` operation compares two integers and produces an `i1` result:

```SMIL
%condition = cmp <predicate> <left> <right>
```

Both operands must have the same integer type after alias resolution.

| Predicate | Meaning |
| --- | --- |
| `eq` | Equal bit patterns |
| `ne` | Unequal bit patterns |
| `ult`, `ule`, `ugt`, `uge` | Unsigned less than, less than or equal, greater than, greater than or equal |
| `slt`, `sle`, `sgt`, `sge` | Signed less than, less than or equal, greater than, greater than or equal |

Unsigned predicates interpret both operands as nonnegative integers. Signed predicates interpret both operands using two’s-complement representation.

A satisfied comparison produces `[i1 1]`; an unsatisfied comparison produces `[i1 0]`.

```SMIL
%negative = cmp slt [i8 -5] [i8 0]
// Result: [i1 1].

%unsigned_less = cmp ult [i8 -5] [i8 0]
// Result: [i1 0], because the left operand represents unsigned 251.
```

Data-pointer comparison uses `ptr_eq`/`ptr_ne`; function-reference comparison uses `fn_eq`/`fn_ne`. Floating-point comparison requires a separate definition.

### Loop-Carried Values

Loops use ordinary branches and block parameters. There is no separate loop variable assignment operation.

```SMIL
func @sum_to([i16]) -> ([i16]) {
^entry(%n: [i16]):
    br ^loop([i16 0], [i16 0])

^loop(%i: [i16], %sum: [i16]):
    %more = cmp ult %i %n
    br_if %more, ^body(), ^done(%sum)

^body():
    %next_i = add [i16] %i [i16 1]
    %next_sum = add [i16] %sum %i
    br ^loop(%next_i, %next_sum)

^done(%answer: [i16]):
    return %answer
}
```

Each entry to `^loop` supplies new dynamic bindings for `%i` and `%sum`.

The static definitions of `%next_i` and `%next_sum` each appear once, even though their operations may execute repeatedly.

This example sums the unsigned integers below `%n`, with the result reduced to 16 bits by wrapping addition.

## Control-Flow and SSA Verification

A function must satisfy structural, typing, reachability, and dominance requirements before it is valid SMIL.

### Structural Requirements

A verifier must check that:

1. Every referenced function, block, type, constant, and SSA identifier resolves to an appropriate declaration or definition.
2. Every SSA identifier has exactly one definition in its function.
3. Every block label is unique within its function.
4. The first block is the entry block and has no incoming CFG edges.
5. Entry-block parameters match the fixed signature prefix and include exactly one final `[varargs]` pack for a variadic function.
6. Every block ends in exactly one valid terminator.
7. Every branch destination belongs to the same function.
8. Every edge supplies the required number and types of arguments.
9. Every conditional branch condition has type `i1`.
10. Every direct/indirect call, invoke, return, and raise agrees with its callable contract. Declarations, definitions, and function references agree on variadic/raised effects, resolved ABIs, and effective attributes.
11. Local declarations occur only in the entry declaration region and in the required order.
12. Integer operations have the prescribed result counts and types, carry/borrow operands have type `i1`, and shift counts have a supported integer type. A literal zero divisor is an execution-fault condition, not a typing violation.
13. Record operands, constructor counts, field paths, replacement values, and derived pointer types satisfy their aggregate operation rules.
14. Constant expressions use only permitted forms and have acyclic value dependencies. Profile-dependent evaluation and range checks are completed at binding.
15. Pointer, unaligned, MMIO, atomic, and fence operations satisfy their operand/result typing and static contract rules. Required conversion mappings, access contracts, and supported atomic forms are resolved at binding.
16. Switch cases are constant, same-width, and unique after bit encoding; traps have valid identifiers; invoke edges, raised payloads, borrowed packs, and lifecycle operands obey their rules.
17. Lifecycle nodes and callbacks have valid signatures and unique identifiers, and linked initialization dependencies resolve without cycles.

Each outgoing edge is checked separately, including conditional, switch, and invoke edges that target the same block. An invoke edge includes its implicit result/payload prefix before its explicit operands. Only its destination parameters introduce those incoming SSA values.

For unbound SMIL, profile-dependent ABI and layout checks are deferred until target binding. A successful structural check does not imply that every target can implement the module.

### Reachability

Every block in a valid function must be reachable from the entry block through CFG edges.

Reachability is structural. Both conditional edges, every switch edge, and both invoke outcome edges are included even when their selection could be proven constant or impossible for a particular execution.

A block’s lack of execution on a particular input does not make it structurally unreachable.

Transformations may temporarily create unreachable internal blocks. Such blocks must be removed before the function is verified or emitted as canonical SMIL.

### Dominance

For reachable blocks, block A **dominates** block B when every CFG path from the entry block to B passes through A.

Each block dominates itself. The entry block dominates every block in a valid function.

An implementation may compute dominators using any algorithm producing this relation. One reference computation is:

```text
Dom(entry) = {entry}

Initially, for every other block B:
    Dom(B) = the set of all blocks

Repeatedly update every non-entry block B:
    Dom(B) = {B} union intersection(Dom(P) for each predecessor P)

Stop when no set changes.
```

Dominance is determined from the CFG, not the textual order of block definitions.

### SSA Use Requirements

For an operation or declaration result:

- If its use is in the defining block, the definition must occur before the use.
- If its use is in another block, the defining block must dominate the use block.
- An operation’s own results are not available to that operation’s operands.

For a block parameter:

- Its definition occurs at the beginning of its block.
- It is available throughout that block.
- It may be used in another block only when its defining block dominates that block.

An explicit branch, switch, or invoke-edge argument is a use at the source terminator. Its availability is checked there, before destination parameters are bound. Invoke results/payloads have no source SSA binding; they become destination parameters only on their corresponding edge.

A value computed on only one incoming path cannot be referenced directly after a merge unless its definition dominates that use:

```SMIL
func @invalid_merge([i1]) -> ([i16]) {
^entry(%condition: [i1]):
    br_if %condition, ^left(), ^right()

^left():
    %candidate = add [i16] [i16 20] [i16 1]
    br ^done()

^right():
    br ^done()

^done():
    // Rejected: ^left does not dominate ^done.
    return %candidate
}
```

The correction is to supply a value on every incoming edge and receive it through a block parameter:

```SMIL
func @valid_merge([i1]) -> ([i16]) {
^entry(%condition: [i1]):
    br_if %condition, ^left(), ^right()

^left():
    %candidate = add [i16] [i16 20] [i16 1]
    br ^done(%candidate)

^right():
    br ^done([i16 0])

^done(%answer: [i16]):
    return %answer
}
```

## Program Lifecycle

Each program instance has these coordinator states:

```text
bootstrap -> initializing -> running -> shutting_down -> terminated
                       \-> initialization failure -> shutting_down -> terminated
```

Terminal faults may transition directly from any state to termination without orderly shutdown. The environment owns the coordinator and the designated lifecycle agent. It must provide the runtime/ABI support advertised for these features; an unsupported lifecycle requirement is a binding error.

### Constant and Dynamic Global Initialization

Bootstrap establishes processor/runtime state, reserves all global allocations, applies required relocations, and installs every constant initializer before any SMIL initializer function executes. A global with a constant initializer is then ready.

A global may instead have an explicit dynamic initializer:

```SMIL
@Settings = record { i16, i1 }

declare @build_settings() -> ([Settings]) raises([i8])
declare @release_settings() -> ()

@settings = global immutable [Settings] dynamic @build_settings \
    init("app.settings") after("app.devices") shutdown @release_settings
```

The declaration above is one module item, continued across its physical newline by the explicit backslash. Initializer clauses do not implicitly continue a logical line. A dynamic initializer requires a direct function symbol, a nonempty program-wide initialization identifier supplied by `init(...)`, and a factory with no parameters and exactly one result matching the object's type. The factory may declare a raised-payload type. It is not variadic. The optional `shutdown` callback has no parameters, no results, no raised effect, and is not variadic.

The global's storage exists during bootstrap, but its contents remain unavailable until its factory returns normally and the coordinator installs the complete result. There is no implicit zero initializer for a dynamic global and no second SMIL initializer value preceding the factory result.

The coordinator's installation is object construction, not an ordinary `store`. It initializes immutable objects exactly once and makes the completed value available atomically with respect to lifecycle readiness. This is a publication/state guarantee, not a promise of a single machine-wide aggregate store. Ordinary application agents are not yet running.

A mutable dynamic global permits ordinary writes after it becomes ready. An immutable dynamic global permits none. A runtime placement must allow the coordinator to install the value; a ROM placement that cannot do so is rejected. Returned values preserve by-value semantics; pointer fields do not acquire longer lifetimes.

Address formation and symbolic address references may name a not-yet-ready global because its allocation and typed subobjects already exist. Ordinary loads, stores, atomic accesses, or other content accesses to it cause terminal `global_not_initialized`. This includes aliases and attempted writes from its own initializer. The factory constructs a result instead of incrementally writing the published object.

No lazy initialization is triggered by a read. The compiler must preserve readiness checks unless completion is established by the lifecycle graph or another valid proof. This global readiness check precedes the initialized-bit checks on ordinary local storage and other permitted reads defined in Execution Violations, Resource Limits, and Optimization.

### Startup Hooks and Dependency Order

A module may register a startup action that does not construct a particular global:

```SMIL
declare @start_devices() -> () raises([i8])
declare @stop_devices() -> ()

startup "app.devices" @start_devices shutdown @stop_devices
```

The action is a fixed-arity, zero-parameter, zero-result function; it may declare one raised-payload type. Its optional shutdown callback has the same non-raising zero-parameter/zero-result contract as a dynamic global's callback. Resolved ABIs may differ between hooks, provided the coordinator supports each interface.

Dynamic globals and `startup` declarations form one program-wide dependency graph. Each has a unique nonempty UTF-8 identifier. `after("id", ...)` names prerequisite initialization nodes; every name must resolve. A node cannot depend on itself, and cycles or duplicate identifiers are diagnosed before any startup action runs. Constant-initialized globals need no graph nodes because they are ready before the graph starts.

The coordinator repeatedly executes a ready node whose prerequisites have completed. If several nodes are ready, it chooses the identifier first in unsigned lexicographic UTF-8 byte order. It does not normalize identifiers or use module discovery, object-file order, source order, or linker input order as a tie-breaker. Dependencies, not spelling conventions, express semantically required ordering.

Initializers execute serially on the lifecycle agent. A successful factory installs its object before its node completes. A successful startup hook completes after its normal return. Its optional shutdown callback is registered only at that successful completion, after any global value installation. Each node runs at most once per program instance; calling its underlying function elsewhere does not change coordinator state or construct its global again.

A node may read constant-initialized globals and dynamic globals whose nodes are already complete. Use `after(...)`, including transitive dependencies, to establish required readiness. Dependencies are not inferred from function bodies: content-access validity is checked against actual readiness, and reading a still-incomplete global faults instead of discovering a prerequisite or recursively initializing it. Taking addresses can form cycles without creating a value-initialization cycle.

Callbacks and interrupt handlers that could observe application globals remain disabled or gated until initialization finishes. A startup hook may invoke its own helpers and use already-established device contracts. An initializer requiring asynchronous device service must use an environment contract that prevents those service callbacks from observing incomplete globals; it cannot publish unrestricted application entry early.

After every node completes, the coordinator publishes readiness to application agents with an environment-defined happens-before handoff and enters `running`. The designated program-entry function must have a fixed-arity, non-raising signature supported by the environment. A raising or variadic language entry point needs an explicit wrapper. No universal `main` signature is implied.

Source-language constructor order must be lowered to graph dependencies. Source declarations needing a total order must receive edges establishing that order; merely emitting them in source order is insufficient. Lazy function-static initialization requires an explicit guard/runtime lowering with its own once/reentry contract; an eager startup node is not automatically an equivalent replacement.

### Initialization Failure

If a factory or startup hook returns a declared raised payload, its node fails. A dynamic object's value is not installed and that node's shutdown callback is not registered. The coordinator does not retry, continue to dependent nodes, or enter the application.

The failing initializer is responsible for cleaning up its own partially acquired resources along its exceptional CFG before `raise`. Previously successful nodes are cleaned up by draining their registered callbacks in reverse registration order. After those callbacks finish, startup terminates with terminal `initialization_failed`; the environment may report the original typed payload through its declared runtime interface.

If an initializer instead executes a terminal fault or user trap, that terminal event applies immediately and does not promise orderly cleanup. If a shutdown callback faults while processing an initialization failure, that later fault terminates the cleanup path and no further callback is promised. External side effects already performed are not rolled back.

### Ordered Shutdown and Explicit Exit

During `running`, a program may register another zero-parameter, zero-result, non-raising, non-variadic function reference:

```SMIL
declare @release_session() -> ()

// Function-body fragment.
%cleanup = fnaddr @release_session
on_exit %cleanup
```

`on_exit` appends one callback registration and produces no value. Its operand must have the exact required callable contract with a supported ABI. Null or an invalid target causes `invalid_call`. Repeated registrations are distinct and each runs once if orderly shutdown reaches it.

The environment states which agents may register callbacks and provides a linearization order for concurrent registrations, consistent with each agent's sequencing. Successful registration publishes the registering agent's preceding ordinary writes to its eventual callback through an environment-defined happens-before edge. Callbacks execute later on the lifecycle agent, not on the registering agent. Registration is supported only during `running`; it does not capture a local environment or extend pointee lifetimes. Context-bearing closures need explicit stable storage and a wrapper function. Resource exhaustion follows the portable terminal `resource_exhausted` policy; the state/callback checks precede reservation and a failed registration appends nothing.

Orderly shutdown begins when the designated entry returns normally or the lifecycle agent executes:

```SMIL
exit [i32 0]
```

`exit` is a terminator with no intrafunction successors. Its operand has type `i32` and is the program's logical exit-status bit pattern. The environment defines how that status is reported, and separately how normal entry results map to it. Explicit exit is not a function return or catchable exceptional payload.

Before draining callbacks, the coordinator enters `shutting_down`, prevents new application entry, and quiesces every other agent that could access finalizing globals. This handoff establishes happens-before from their completed application effects to shutdown callbacks. The profile must define a conforming interrupt/thread/device ownership protocol. Disabling one local interrupt is not a general multi-agent shutdown implementation.

An explicit `exit` abandons the active SMIL invocation chain after quiescence and before shutdown callbacks run. Abandoned local storage expires. It does not run per-invocation source-language destructors; a source construct requiring those cleanups must emit cooperative returns/exceptional transfers before requesting exit.

The callback stack contains completion-registered initializer callbacks followed by application `on_exit` registrations. It is drained last-in, first-out. Each entry is removed before its callback starts and invoked at most once; the same function can appear in several entries. Dependencies therefore ensure that a dependent node's callback precedes its prerequisite's callback. Runtime `on_exit` callbacks precede earlier initialization callbacks according to their registration order.

For a dynamic global with a shutdown callback, the object remains ready while that callback executes and is marked finalized on its normal return. Content access to a finalized object causes terminal `global_finalized`. Its allocation remains reserved and its address can still be formed until program termination; finalization removes content-access permission. Other global objects remain available until their own finalization or the end of shutdown. A callback's ordinary read of an immutable object is permitted; ordinary mutation remains prohibited. Destruction of an external resource is an explicit callback effect, not a mutation privilege inferred from the name `shutdown`.

After all callbacks finish, remaining global lifetimes end, the coordinator enters `terminated`, and the environment reports the logical exit status. A bare-metal environment may halt instead of returning to a host, but it must not silently restart the same instance or rerun its constructors.

Calling `exit` outside `running`, registering a callback outside `running`, attempting nested coordinator startup/shutdown, or using either operation from an unauthorized agent causes terminal `invalid_lifecycle_transition`. A shutdown callback must return normally; a trap or terminal fault aborts further orderly shutdown. The non-raising callback type prevents a declared SMIL exceptional result from escaping it.

Terminal arithmetic/pointer/access faults, user traps, and other specified terminal events bypass the callback stack. This distinction is explicit: orderly exit runs registered global cleanup; terminal faults promise no cleanup or unwinding.

### Lifecycle Linking and Verification

The linker or equivalent whole-program binding step retains registered startup factories, hooks, shutdown functions, and their dependency metadata even when ordinary call reachability would otherwise discard them. It resolves unique initialization identifiers and validates an acyclic graph before execution. Taking a function reference also preserves any required target definition and relocation.

Verification checks factory/result types, callback callable contracts, raised effects, allowed placements, referenced dependency identifiers, supported lifecycle agents, and the coordinator's runtime interfaces. Readiness and finalized-state checks follow object association through aliases and integer reconstruction where supported.

Native platform constructors, foreign shutdown registries, and foreign exceptions require an explicit adapter and an ordering contract with this coordinator. The backend cannot assume that a platform's default constructor priority or destructor convention implements SMIL's graph and callback stack. Dynamically loading/unloading modules and restarting an instance are separate extensions, not hidden lifecycle effects of an ordinary call.

## Type Casts

Explicit conversions between integer types and between pointer types are supported. Pointer-to-integer and integer-to-pointer conversions require support from the applicable target profile.

A cast produces a new SSA value. It does not modify its operand or the contents of any storage object.

The general form is:

```SMIL
%result = <cast operation> [<destination type>] <source value>
```

The source type is determined from the source value.

### Integer Extension

The `zext` and `sext` operations extend an integer to a larger integer type. The destination width must be greater than the source width.

`zext` preserves the source bits and fills the additional high-order bits with zeros.

`sext` preserves the source bits and fills the additional high-order bits with copies of the source’s most significant bit.

```SMIL
%zero_extended = zext [i16] [i8 0xfb]
// Result: 0x00fb, representing 251.

%sign_extended = sext [i16] [i8 0xfb]
// Result: 0xfffb, representing -5 when interpreted as signed.
```

The operation determines the extension behavior. The source integer type does not carry an independent signedness attribute.

For `i1`, zero extension maps `1` to integer `1`; sign extension maps it to an all-ones result, representing signed `-1`.

Changing between signed and unsigned interpretations at the same integer width does not require a cast. Operations requiring a signedness interpretation must specify it explicitly. Such a change preserves the bit pattern but may change its mathematical interpretation.

### Integer Truncation

The `trunc` operation converts an integer to a smaller integer type. The destination width must be less than the source width.

Truncation retains the low-order destination-width bits and discards the remaining high-order bits. It performs no rounding, saturation, or adjustment to preserve the source sign.

```SMIL
%small = trunc [i4] [i8 -5]
// Source bits: 11111011
// Result bits:     1011
// The result represents -5 when interpreted as signed.

%wrapped = trunc [i4] [i8 11]
// Source bits: 00001011
// Result bits:     1011
// The result represents 11 unsigned or -5 signed.
```

Truncation preserves the source’s mathematical value when that value is representable under the intended destination interpretation. Otherwise, it still produces the precisely defined low-bit result.

Loss of mathematical value is permitted and does not cause a trap. Optional diagnostics do not change the operation’s semantics.

### Pointer Type Casts

The `ptrcast` operation changes a pointer’s pointee type without changing the addressed location:

```SMIL
// Assume %foo_ptr has type ptr [Foo].
%bar_ptr = ptrcast [ptr [Bar]] %foo_ptr
```

This operation requires compatible pointer representations within the same address space. Conversions between address spaces use `addrspacecast` and its explicit mapping contract. Unsupported representation conversions are rejected.

A pointer type cast does not:

- Read, write, copy, or convert the addressed object.
- Change the object’s lifetime or mutability.
- Establish that the object is suitably sized, aligned, or otherwise valid for access through the destination type.

Every subsequent access must independently satisfy the ordinary typed-view rules in Pointers and Memory Access. Changing the pointer’s type does not itself change the type or contents of the existing object, create record subobjects, or establish a permitted pointer-representation reinterpretation.

### Pointer and Integer Conversions

The following operations convert between pointer and integer values:

```SMIL
%bits = ptrtoint [<integer type>] <pointer value>
%address = inttoptr [ptr [<pointee type>]] <integer value>
%space_address = inttoptr [ptr <address space> [<pointee type>]] <integer value>
```

These conversions are supported only where the target profile defines their representation and behavior.

The profile must supply the pointer/integer conversion contract defined in Pointers and Memory Access: supported type/value domains, exact encoding, null mapping, association reconstruction, pointer round trips, integer round trips, and representation-state requirements. Equal pointer and integer storage sizes alone do not establish those guarantees. Supported conversions outside their runtime value domain cause `invalid_pointer_operation`.

Unsupported conversion forms must be rejected. A successful integer-to-pointer conversion establishes a usable object association only where the profile explicitly supplies that reconstruction or external-region mapping. An address-only result does not permit memory access.

Integer zero is not assumed to produce a null pointer unless the target profile explicitly defines that mapping.

## Source Text, Lexical Rules, and Grammar

This chapter defines the complete core source syntax, designated `smil.source.v1`. It replaces the earlier partial structural grammar. Semantic sections still determine types, identity, dominance, access validity, fault behavior, constant evaluation, ABI compatibility, and target support; successful parsing does not prove those properties or make a target backend available.

The source designation names this textual grammar. It is not a new target/profile/ABI or a change to the existing interface/object/library/link/image formats. No new runtime operation is introduced. A tool consuming source must select this grammar explicitly rather than infer a dialect from a CPU, filename, or host language. Selection can be fixed by a tool's documented interface or supplied by build settings; no extra source directive is introduced. Unknown source operations and clauses are diagnostics.

### Source Encoding, Whitespace, and Comments

Source is well-formed UTF-8, with Unicode scalar values as described in [RFC 3629](https://www.rfc-editor.org/rfc/rfc3629.html). An optional UTF-8 BOM is accepted only at the start and ignored. A bare surrogate, malformed byte sequence, or out-of-range code point is rejected rather than replaced. No Unicode normalization or case folding is applied.

Physical line endings are LF or CRLF; CRLF is treated as one newline. A standalone CR is invalid. Outside strings and comments, the only horizontal whitespace is ASCII space or tab. Indentation has no syntactic meaning. Other Unicode whitespace is not an alternative separator.

`//` begins a comment extending to the next physical newline or end of input. Comments may contain arbitrary Unicode scalar text; quotes and backslashes inside them have no special role. A comment does not consume its newline for statement-boundary purposes. Block comments, `#` comments, preprocessing directives, includes, macros, and conditional compilation are not part of this source grammar.

### Identifiers, Namespaces, and Token Boundaries

An ordinary name uses ASCII `[A-Za-z_][A-Za-z0-9_]*`. Names are case-sensitive. A source spelling is resolved in its existing namespace; a sigil is not part of the canonical module symbol's local-name string.

| Source token | Exact form |
| --- | --- |
| Local value/type-declaration symbol | `@` immediately followed by an ordinary name |
| Local named constant | `$` immediately followed by an ordinary name |
| Local SSA identifier | `%` immediately followed by an ordinary name or canonical nonnegative decimal digits |
| Block label | `^` immediately followed by an ordinary name |
| Qualified value/constant | `@alias::member` or `$alias::member` |
| Qualified type | Bare `alias::member` in a type position |

`%0` and `%17` are explicit SSA names, not implicit register slots or a numbering algorithm. Numeric SSA names have no leading zeroes except `%0`. Ordinary names such as `%tmp17` are unaffected. Numeric block, type, value-symbol, constant, and qualifier names are absent from this version.

A qualified name is one token: neither whitespace, comments, nor line continuation may occur between its alias, `::`, and member. Exactly one qualifier is permitted. A sigil occurs once, before the alias. Qualification is not available for SSA identifiers or block labels. A qualifier and its member both use the ordinary-name spelling; import aliases cannot be bare built-in integer-type tokens.

Keywords and operation names are contextual: the grammar recognizes their exact lowercase spelling where that construct is expected. Sigiled values and constants may have keyword spellings, for example `@add` or `$type`. A bare type name cannot replace the constructors `ptr`, `fnptr`, `varargs`, or the reserved `i[0-9]+` family. Those restrictions also apply to type declaration binders and type exports. Other ordinary names can identify types, including a spelling that is an operation in another context.

Tokens use maximal munch. Scan a whole sigiled or qualified name as one token. A remaining bare word in the `i[0-9]+` family is an integer-type token or a malformed-width diagnostic, never a fallback ordinary name; other bare words are `NAME`. `TYPE_NAME` filters `NAME` only in type-name positions. The punctuators are `(`, `)`, `[`, `]`, `{`, `}`, `=`, `,`, `:`, `->`, and `...`; `::` exists only within qualified-name tokens. Adjacent tokens need whitespace only when their characters would otherwise form a different token. A formatter should put spaces between ordinary operation operands. Strings and comments are recognized before their contents can be mistaken for punctuation or names.

There are no quoted identifiers, hyphenated/dotted bare names, implicit symbol mangling, or Unicode bare identifiers. Module, profile, ABI, access-contract, lifecycle, and fault identifiers use strings instead. Existing JSON metadata is not SMIL source: canonical key strings and runtime-private `aux` labels can use their independently defined encodings and must not be tokenized as source identifiers.

### Integer and String Tokens

A bare built-in integer type is `i` followed by canonical positive decimal digits: `i1`, `i8`, `i24`, and so on. `i0` and `i08` are invalid bare tokens. The mathematical width is not truncated to a host integer. Profile width limits are checked at binding. `iN` in explanatory templates means a chosen concrete width, not an implicit generic built-in.

An integer literal is an optional adjacent `-`, followed by either canonical decimal digits (`0` or a nonzero digit followed by digits), or `0x` followed by one or more hexadecimal digits. Hexadecimal digits may use either case; the prefix is lowercase. Decimal leading zeroes, leading `+`, digit separators, numeric suffixes, binary/octal notation, floating-point notation, and whitespace after the minus are not admitted. Negative zero is a valid spelling of zero. The existing typed-literal range rules apply after parsing; there is no untyped scalar value operand.

A field index uses the unsigned decimal form only. It has no `iN` width and admits neither a minus nor hexadecimal spelling. Value literals remain bracketed, for example `[i8 -1]` or `[word 0x00ff]`; the alias's resolved type determines whether that literal kind is permitted.

Strings use double quotes and the escape spellings of [RFC 8259 section 7](https://www.rfc-editor.org/rfc/rfc8259.html#section-7): `\"`, `\\`, `\/`, `\b`, `\f`, `\n`, `\r`, `\t`, and `\u` followed by exactly four hexadecimal digits. Unescaped characters must be Unicode scalar values other than `"`, `\`, or control characters U+0000 through U+001F. Raw physical newlines are forbidden. Unlike JSON's permissive surrogate syntax, SMIL rejects isolated surrogate escapes: a high surrogate must immediately be followed by a matching escaped low surrogate, and the pair decodes to one scalar.

Literal text and escaped text producing the same decoded scalar sequence have the same identifier meaning. Comparison, hashing of semantic metadata, duplicate detection, and lifecycle ordering use that decoded value, with the existing UTF-8 ordering rules. They do not compare the source escape spelling. A decoded identifier string must be nonempty and contain no NUL; additional existing rules still apply, such as the `user.` prefix and nonempty suffix for `trap`.

Adjacent string literals do not concatenate. Raw strings, triple quotes, `\xNN`, `\u{...}`, backslash-newline string splicing, character literals, and string-valued computation operands are absent. Use numeric integer literals for character-code values. A string selects a directive/attribute identifier; it does not allocate a string object.

### Logical Lines and Continuation

A simple statement ends at a significant newline. Blank and comment-only logical lines may occur between statements. End of input supplies the final statement boundary when delimiters are balanced; a final physical newline is optional. Semicolons do not separate statements, and two independent statements cannot share one logical line.

Newlines inside parentheses and square brackets are whitespace. Record-field, record-initializer, and switch-case brace groups also treat newlines as whitespace. Function-body braces do **not** suppress statement boundaries. Delimiter nesting must match exactly. Lists still require commas; newline is never a replacement for a comma, and trailing commas are not admitted in this version.

Function opening braces remain on the header's logical line. A newline follows that brace, every block header's colon, and every operation/terminator. A function's closing brace occupies its own logical line. A switch's braces enclose its case list as part of one terminator, so its interior newlines do not start new statements. Record declarations can likewise span their delimited field list without any marker.

Outside a string/comment, `\` followed by optional spaces/tabs, an optional `//` comment, and a physical newline continues the current logical line. It behaves as separating whitespace and joins exactly that physical newline. It never joins parts of a name, number, opcode, or string. A backslash inside a comment does not continue anything. A backslash at end of input is invalid.

```SMIL
@Pair = record {
    i16,
    i16
}

$origin = const [Pair {
    [i16 0],
    [i16 0]
}]

// An ordinary operation continued outside any open group.
%sum = add [i16] [i16 20] \
    [i16 1]
```

There is no indentation-based or “unfinished statement” continuation, and no special automatic continuation before `init`, `after`, `shutdown`, `space`, `abi`, `raises`, `normal`, or `except`. Put the clause on the current logical line, enclose its containing syntax in an already-open grouping construct, or use an explicit continuation. This makes statement termination independent of symbol resolution and the next line's keyword.

### Statement Forms and Operation Results

A publishable module consists of its header, optional target, imports, then declarations/definitions/exports. Types, constants, globals, function declarations/definitions, startup registrations, and exports are module items. Top-level computation statements are not module items. An anonymous verification fragment uses the separate fragment start rule and cannot be published without a module identity.

A function has one first/entry block and zero or more subsequent blocks. Only the entry block admits local type declarations followed by local storage declarations, before executable operations. Every block ends in exactly one terminator, with no following operation before the next block or the function's closing brace. An empty function still needs an entry block and a terminator.

One-result operations bind one SSA name; carry/borrow, overflow, and compare/exchange operations bind their two ordered results. Zero-result operations have no binding. Calls permit zero or a comma-separated result binding, with the exact count checked from the resolved callable signature. No discard placeholder or implicit discarded result is introduced.

Commas separate result bindings, signature entries, block parameters, record fields/initializers, record-construction operands, call/edge arguments, field paths, switch cases, and dependency IDs. The two commas in `br_if` are required. Other prefix operation operands are written in their defined order without commas. The complete grammar below enumerates every operation body; result-type annotations cannot be added or omitted by analogy with another instruction.

### Complete Grammar

The grammar uses quoted terminals, alternatives `|`, optional `?`, repetition `*`/`+`, and the finite list substitution `list<X> = X ("," X)*`. `value-operation<V>` has exactly two instantiations: V is `value` for runtime computations and `constant` inside constant expressions. This is a finite grammar abbreviation, not an unspecified expression language. Group interiors ignore newlines under the logical-line rules; function-body braces preserve them.

`NAME`, `TYPE_NAME`, `INTEGER_TYPE`, `INTEGER`, `INDEX`, sigiled/qualified names, `STRING`, `EOL`, and `EOF` are the lexical terminals defined above. For compactness, `EOL+` also absorbs intervening blank lines. The operation and attribute spellings are exact and case-sensitive.

```text
(* SMIL source grammar v1. Token and logical-line rules are normative in the guide.
   X? = optional; X* = repetition; X+ = one or more; | = alternatives.
   list<X> = X ("," X)*. No trailing commas. U+000A is logical EOL.
   Operation productions parameterized by V are instantiated twice:
     value-operation<value>, value-operation<constant>.
   This finite substitution is notation, not an open operand category.
   Group interiors ignore EOL; function-body braces preserve it.
   EOF implies one EOL when needed; blank EOLs may occur between statements.
*)
module = EOL* module-header EOL+ target-directive? import-directive* module-item* EOF ;
module-header = "module" STRING ;
fragment = EOL* target-directive? import-directive* module-item* EOF ;
target-directive = "target" STRING EOL+ ;
import-directive = "import" STRING "as" NAME EOL+ ;
module-item = (type-declaration | constant-definition | global-definition
             | function-declaration | export-directive | startup-definition) EOL+
             | function-definition ;
export-directive = "export" ("type" TYPE_NAME | LOCAL_CONSTANT | LOCAL_SYMBOL) ;

type-declaration = LOCAL_TYPE_SYMBOL "=" ("type" type-expression
                                   | "record" "{" list<type>? "}") ;
constant-definition = LOCAL_CONSTANT "=" "const" constant ;
global-definition = LOCAL_SYMBOL "=" "global" mutability type-expression
                    (constant | dynamic-initializer) space-clause? ;
mutability = "mutable" | "immutable" ;
space-clause = "space" "(" NAME ")" ;
dynamic-initializer = "dynamic" symbol "init" "(" STRING ")"
                      after-clause? shutdown-clause? ;
startup-definition = "startup" STRING symbol after-clause? shutdown-clause? ;
after-clause = "after" "(" list<STRING> ")" ;
shutdown-clause = "shutdown" symbol ;

type-expression = "[" type "]" ;
type = INTEGER_TYPE | TYPE_NAME | QUALIFIED_NAME
       | "ptr" NAME? type-expression
       | "fnptr" signature abi-clause? raises-clause?
       | "varargs" ;
signature = "(" fixed-parameters? ")" "->" "(" list<signature-entry>? ")" ;
fixed-parameters = "..." | list<signature-entry> ("," "...")? ;
signature-entry = type-expression extension-attribute? ;
extension-attribute = "signext" | "zeroext" ;
abi-clause = "abi" "(" STRING ")" ;
raises-clause = "raises" "(" type-expression ")" ;

symbol = LOCAL_SYMBOL | QUALIFIED_SYMBOL ;
constant-name = LOCAL_CONSTANT | QUALIFIED_CONSTANT ;
value = SSA | constant ;
constant = constant-name | symbol | typed-constant | "(" value-operation<constant> ")" ;
typed-constant = "[" type (INTEGER | "null" | "zero" | "{" list<constant>? "}") "]" ;
local-initializer = SSA | constant-name | symbol
                  | "(" value-operation<constant> ")"
                  | "[" type (INTEGER | "null" | "zero"
                             | "{" list<local-initializer>? "}") "]" ;
field-path = "field" "(" list<INDEX> ")" ;

function-declaration = "declare" LOCAL_SYMBOL signature abi-clause? raises-clause? ;
function-definition = "func" LOCAL_SYMBOL signature abi-clause? raises-clause?
                      "{" EOL+ entry-block block* "}" EOL+ ;
entry-block = block-header EOL+ (type-declaration EOL+)*
              (local-storage EOL+)* (ordinary-statement EOL+)* terminator EOL+ ;
block = block-header EOL+ (ordinary-statement EOL+)* terminator EOL+ ;
block-header = BLOCK "(" list<parameter>? ")" ":" ;
parameter = SSA ":" type-expression ;
local-storage = SSA "=" "alosf"
                ("mutable" type-expression local-initializer?
                 | "immutable" type-expression local-initializer) ;
result-binding = list<SSA> "=" ;
ordinary-statement = SSA "=" single-computation
                     | SSA "," SSA "=" pair-computation
                     | result-binding? call-operation
                     | effect-operation ;

(* Exactly these single-result forms are allowed in constant expressions.
   V = constant in parentheses; V = value in ordinary computation. *)
value-operation<V> = binary-integer type-expression V V
                    | unary-integer type-expression V
                    | "cmp" predicate V V
                    | conversion type-expression V
                    | "record_make" type-expression "(" list<V>? ")"
                    | "record_get" V field-path
                    | "record_set" V field-path V
                    | "field_addr" V field-path
                    | ("ptr_eq" | "ptr_ne" | "ptr_offset" | "fn_eq" | "fn_ne") V V
                    | "ptr_diff" type-expression V V
                    | ("sizeof" | "alignof") type-expression type-expression
                    | "offsetof" type-expression type-expression field-path
                    | "fnaddr" symbol ;
binary-integer = "add" | "sub" | "mul" | "udiv" | "urem" | "sdiv" | "srem"
                 | "xor" | "and" | "or" | "shl" | "lshr" | "ashr" ;
unary-integer = "neg" | "not" ;
conversion = "sext" | "zext" | "trunc" | "ptrcast" | "ptrtoint" | "inttoptr" | "addrspacecast" ;
predicate = "eq" | "ne" | "ult" | "ule" | "ugt" | "uge" | "slt" | "sle" | "sgt" | "sge" ;

single-computation = value-operation<value>
              | ("load" | "load_unaligned") type-expression value
              | "mmio_load" type-expression value access-clause
              | "atomic_load" type-expression value atomic-order
              | "atomic_rmw" atomic-kind type-expression value value atomic-order
              | "va_count" type-expression value
              | ("va_is" | "va_get") type-expression value value ;
pair-computation = ("uadd_carry" | "usub_borrow") type-expression value value value
              | binary-overflow type-expression value value
              | "sneg_overflow" type-expression value
              | "atomic_cmpxchg" type-expression value value value atomic-order ;
binary-overflow = "sadd_overflow" | "ssub_overflow" | "smul_overflow" | "umul_overflow" ;
effect-operation = ("store" | "store_unaligned") value value
                   | "mmio_store" value value access-clause
                   | "mmio_fence" access-clause
                   | "atomic_store" value value atomic-order
                   | "atomic_fence" atomic-order
                   | "on_exit" value ;
access-clause = "access" "(" STRING ")" ;
atomic-order = "seq_cst" ;
atomic-kind = "xchg" | "add" | "sub" | "and" | "or" | "xor" ;

call-operation = "call" symbol "(" call-arguments? ")"
                 | "call_indirect" value "(" call-arguments? ")" ;
call-arguments = "..." SSA | list<value> ("," "..." SSA)? ;
edge = BLOCK "(" list<value>? ")" ;
terminator = "br" edge
             | "br_if" value "," edge "," edge
             | "return" list<value>?
             | ("invoke" symbol | "invoke_indirect" value)
                 "(" call-arguments? ")" "normal" edge "except" edge
             | "switch" type-expression value "default" edge
                 "{" list<switch-case>? "}"
             | "raise" value
             | "trap" STRING
             | "exit" value ;
switch-case = constant ":" edge ;

(* Lexical terminals, scanned by maximal munch before the token grammar.
   NAME = ASCII [A-Za-z_][A-Za-z0-9_]* (contextual keywords).
   TYPE_NAME = NAME except ptr/fnptr/varargs and the reserved i[0-9]+ family.
   INTEGER_TYPE = i[1-9][0-9]*; i0 and leading-zero widths are invalid bare tokens.
   DECIMAL = 0 | [1-9][0-9]*; HEX = 0x[0-9A-Fa-f]+.
   INTEGER = -?(DECIMAL | HEX); INDEX = DECIMAL without a minus.
   SSA = %NAME | %DECIMAL; BLOCK = ^NAME.
   LOCAL_SYMBOL = @NAME; LOCAL_TYPE_SYMBOL = @TYPE_NAME; LOCAL_CONSTANT = $NAME.
   QUALIFIED_NAME = NAME::NAME with no internal whitespace/comments/continuations.
   QUALIFIED_SYMBOL = @QUALIFIED_NAME; QUALIFIED_CONSTANT = $QUALIFIED_NAME.
   STRING = double-quoted JSON-style escapes, decoded to Unicode scalar values;
            no raw control/newline, invalid escape, or isolated surrogate.
   EOL = significant LF after source/continuation/group processing.
   EOF = end of source. Comments are // through the next physical newline.
*)
```

### Parsing, Verification, and Compatibility

The grammar admits named types before their declarations and uses the same syntactic type position for aliases and concrete types. Consequently, forms such as `[Alias null]`, `[R zero]`, `[T { ... }]`, and `[T 7]` require resolution to check that the payload kind is valid. Parenthesized constant operations restrict every value operand to constant syntax immediately; SSA operands are allowed in local aggregate initializers only through their separate production, not by relaxing constant expressions.

Parsing also does not establish literal ranges, field counts/path validity, nominal compatibility, symbol visibility, callable result arity, pack ownership, dominance, global dependencies, profile support, or absence of execution faults. The special type `varargs` obeys its existing non-storable/borrowed rules wherever it is spelled; an alias does not make it an ordinary argument or storage type. Function/block names and result/parameter definitions still obey their existing scope and uniqueness checks.

Binding/verification diagnostics remain distinct from reached terminal faults. For example, `[i8 256]` is syntactically an integer literal but fails range verification; a correctly typed executable division by zero remains a runtime arithmetic fault if reached. A literal zero inside a required constant expression instead fails static evaluation. The grammar does not authorize a parser to reinterpret any of those cases as a host language expression.

The textual grammar fixes spellings without changing canonical identities or existing target-bound metadata. Dotted version identifiers remain decoded strings; qualified aliases resolve to canonical module keys before object emission. The interface/object/library/link/image formats and the checked v2 CPU/runtime profiles retain their existing versions and digests. Runtime-private metadata formats, resource plans, and helper descriptor tokens are not source extensions and cannot introduce arbitrary opcodes through this grammar.

### Source Grammar Conformance

The accompanying `smil_syntax_v1/grammar.ebnf` is the same grammar as this chapter and can be copied independently. `source-contract.json` pins its raw UTF-8 digest and complete opcode set. `syntax.py` is a reference lexer and syntax recognizer, with a strict complete-module entry and separate fragment/type/value entry points. Its documentation-only `examples` mode can inspect independent illustrative forms in a fence; it is not an alternative publishable-module grammar.

Conformance checks cover UTF-8/BOM/newlines, contextual and qualified names, numeric tokens, Unicode escapes, comments/continuation, grouping and list boundaries, nested pointer/callable types, constant-versus-local initialization, operation arities, mandatory access/atomic clauses, ordered callable/lifecycle clauses, forwarded packs, switch/invoke edges, declaration regions, and terminators. The document audit records every SMIL code fence, distinguishes placeholders from concrete forms, and preserves examples intentionally rejected by later semantic verification.

The reference recognizer does not resolve names, verify SSA/types/effects/lifecycle graphs, evaluate constants, or implement machine-object generation, the linker, runtime checks, or CPU backends. A source implementation must add those existing semantic checks and the target acceptance vectors. Host memory/recursion limits in a reference tool are tooling limits, not implicit changes to this unbounded grammar; an implementation must report an inability to process input rather than silently change its tokens or meaning.

## Operation Families

Operations are grouped by purpose:

- Storage, unaligned access, and field-address operations (`STOR`).
- Pointer comparison and arithmetic (`PTR`).
- Device transactions and barriers (`IO`).
- Atomic ordinary-memory operations and fences (`ATOM`).
- Record value operations (`AGG`).
- Layout queries (`LAYOUT`).
- Value conversions (`VALCO`).
- Integer arithmetic (`INTOP`).
- Integer bitwise operations (`BOP`).
- Comparisons (`CMP`).
- Function-reference and borrowed argument-pack operations (`FUNC`).
- Branches, calls, normal/exceptional transfers, and user traps (`BRTL`).
- Lifecycle registration and orderly program exit (`LIFE`).

Floating-point and vector operations require additional definitions. Naming an operation family does not establish the semantics of otherwise unspecified operations.

An operation is a primitive of the IR, not necessarily one machine instruction or one indivisible hardware action.

### Basic Integer and Bitwise Operations

The following integer operations use a declared result type `iN`:

```SMIL
%result = add [iN] <left> <right>
%result = sub [iN] <left> <right>
%result = mul [iN] <left> <right>
%result = neg [iN] <source>
```

Their operands must have that same integer type after alias resolution.

`add`, `sub`, `mul`, and `neg` return the low N bits of the mathematical result. They use wrapping arithmetic and do not trap on integer overflow.

Bitwise operations similarly require operands matching their declared result type:

```SMIL
%result = xor [iN] <left> <right>
%result = and [iN] <left> <right>
%result = or [iN] <left> <right>
%result = not [iN] <source>
```

These operations apply independently to corresponding bits. `not` complements every bit within the result width.

### Integer Operation Conventions

The following definitions apply to scalar integers of every supported positive width, including `i1` and widths smaller than a byte. Vector operations require separate definitions.

For width N, define:

```text
B = 2^N
MIN_N = -2^(N-1)
MAX_N = 2^(N-1) - 1

U(x) = the unsigned interpretation of x, in [0, B-1]
S(x) = U(x), if U(x) < B/2; otherwise U(x) - B
bits_N(k) = the N-bit pattern for k modulo B
```

These formulas use mathematical integers without intermediate overflow. They do not require a native wider machine type.

Except for shift counts and carry/borrow inputs, operands of an operation annotated `[iN]` must have type `iN` after alias resolution. Its primary result also has type `iN`.

Flag results have type `i1`: `1` means the named condition occurred and `0` means it did not. Flags are ordinary SSA values, not implicit processor state.

### Integer Division and Remainder

The following operations produce one `iN` result:

```SMIL
%quotient = udiv [iN] <dividend> <divisor>
%remainder = urem [iN] <dividend> <divisor>

%quotient = sdiv [iN] <dividend> <divisor>
%remainder = srem [iN] <dividend> <divisor>
```

Both operands must have the declared integer type.

#### Unsigned Division and Remainder

For `udiv` and `urem`, let `a = U(dividend)` and `b = U(divisor)`.

When `b` is nonzero:

```text
q = floor(a / b)
r = a - b*q
```

`udiv` returns `bits_N(q)`. `urem` returns `bits_N(r)`.

The identity `a = b*q + r` holds over mathematical integers, with `0 <= r < b`.

A zero divisor causes the `integer_divide_by_zero` arithmetic fault for either operation.

#### Signed Division and Remainder

For `sdiv` and `srem`, let `a = S(dividend)` and `b = S(divisor)`.

For a nonzero divisor, define the mathematical quotient `q` by rounding `a / b` toward zero, then define `r = a - b*q`.

`sdiv` returns `bits_N(q)` when `q` is within `[MIN_N, MAX_N]`.

`srem` returns `bits_N(r)`. A nonzero remainder has the dividend's sign, and `abs(r) < abs(b)`.

| Dividend | Divisor | Signed quotient | Signed remainder |
| --- | --- | --- | --- |
| 7 | 3 | 2 | 1 |
| -7 | 3 | -2 | -1 |
| 7 | -3 | -2 | 1 |
| -7 | -3 | 2 | -1 |

A zero divisor causes `integer_divide_by_zero` for either operation.

The pair `a = MIN_N` and `b = -1` is handled explicitly:

- `sdiv` causes `integer_divide_overflow` because its positive quotient cannot fit.
- `srem` returns zero. Its mathematical remainder is representable.

The remainder definition uses the mathematical quotient, not an executed `sdiv` operation. Therefore, `srem(MIN_N, -1)` must not acquire a quotient-overflow fault from a shared division instruction or helper.

```SMIL
%q = sdiv [i8] [i8 -7] [i8 3]
// %q represents signed -2.

%r = srem [i8] [i8 -7] [i8 3]
// %r represents signed -1.

%edge_remainder = srem [i8] [i8 -128] [i8 -1]
// Defined result: [i8 0].
```

These definitions also apply to `i1`. In particular, `sdiv [i1] [i1 -1] [i1 -1]` faults because positive one is outside the signed `i1` range; the corresponding `srem` returns zero.

Signed remainder is not a promise of a nonnegative modulo result. Floor division and other modulo conventions require explicit lowering or separately defined operations.

### Integer Shifts

The following operations produce one `iN` result:

```SMIL
%result = shl [iN] <value> <count>
%result = lshr [iN] <value> <count>
%result = ashr [iN] <value> <count>
```

The value operand must have type `iN`. The count may have any supported integer type `iM`; it need not match the value's width.

The count is interpreted as `k = U(count)` using all M bits. It is never implicitly truncated to a machine count register, masked, or reduced modulo N.

For example, an `i8` count with pattern `0xff` means 255, including when written as `[i8 -1]`. There is no negative-count interpretation in these operations.

A zero count returns the original value.

| Operation | For `0 < k < N` | For `k >= N` |
| --- | --- | --- |
| `shl` | Shift left, discard high bits, fill low bits with zeros | Zero |
| `lshr` | Shift right, discard low bits, fill high bits with zeros | Zero |
| `ashr` | Shift right, discard low bits, fill high bits with copies of the original sign bit | All zeros for a nonnegative source; all ones for a negative source |

For `k < N`, equivalent mathematical definitions are:

```text
shl(x, k)  = bits_N(U(x) * 2^k)
lshr(x, k) = bits_N(floor(U(x) / 2^k))
ashr(x, k) = bits_N(floor(S(x) / 2^k))
```

Shifts do not trap for large counts or discarded bits. Plain shifts do not produce carry or overflow flags.

```SMIL
%left = shl [i8] [i8 0x81] [i8 1]
// 0x02: the high bit is discarded.

%logical = lshr [i8] [i8 0xfb] [i8 1]
// 0x7d: unsigned 125.

%arithmetic = ashr [i8] [i8 -5] [i8 1]
// 0xfd: signed -3.

%oversized = lshr [i8] [i8 0xff] [i16 256]
// 0x00: the count is not truncated to eight bits.

%sign_fill = ashr [i8] [i8 -5] [i8 8]
// 0xff: signed -1.
```

Arithmetic right shift rounds negative values downward. Signed division rounds toward zero. Consequently, replacing division by a power of two with `ashr` requires an appropriate proof or correction:

```SMIL
%division = sdiv [i8] [i8 -5] [i8 2]
// Signed -2.

%shift = ashr [i8] [i8 -5] [i8 1]
// Signed -3.
```

These fill rules also apply to `i1` and non-power-of-two widths. A backend must normalize hardware shift behavior when it differs from these rules.

### Carry and Overflow

Core operations do not read or modify implicit processor flags.

The following operations accept an explicit incoming flag and produce a result followed by an outgoing flag:

```SMIL
%sum, %carry_out = uadd_carry [iN] <left> <right> <carry_in>
%difference, %borrow_out = usub_borrow [iN] <left> <right> <borrow_in>
```

The left and right operands have type `iN`. Incoming and outgoing flags have type `i1`. An incoming flag contributes mathematical integer zero or one, irrespective of the signed interpretation used by any other operation.

#### Addition with Carry

Let:

```text
t = U(left) + U(right) + U(carry_in)
sum = bits_N(t)
carry_out = 1 if t >= B, otherwise 0
```

A zero carry input provides ordinary unsigned addition with overflow detection. A separate unsigned-add-overflow operation is not required.

```SMIL
%sum, %carry = uadd_carry [i8] [i8 255] [i8 1] [i1 0]
// %sum = [i8 0]; %carry = [i1 1].
```

Carry chains explicitly connect successive parts of a multiword operation:

```SMIL
%low, %carry = uadd_carry [i8] [i8 0xff] [i8 1] [i1 0]
%high, %carry_out = uadd_carry [i8] [i8 0x12] [i8 0] %carry
// 0x12ff + 0x0001 = 0x1300.
// %low = 0x00; %high = 0x13; %carry_out = 0.
```

#### Subtraction with Borrow

Let:

```text
t = U(left) - U(right) - U(borrow_in)
difference = bits_N(t)
borrow_out = 1 if t < 0, otherwise 0
```

A borrow input of one subtracts one additional unit. A borrow output of one means unsigned underflow occurred.

```SMIL
%difference, %borrow = usub_borrow [i8] [i8 0] [i8 1] [i1 0]
// %difference = [i8 255]; %borrow = [i1 1].
```

SMIL borrow is not defined in terms of a processor carry flag. A backend must invert or otherwise normalize a native subtraction flag when necessary.

An unsigned-negation underflow indication can be obtained by subtracting the operand from zero with a zero borrow input.

### Explicit Overflow Results

The following operations return a wrapped `iN` value followed by an `i1` overflow indication:

```SMIL
%result, %overflow = sadd_overflow [iN] <left> <right>
%result, %overflow = ssub_overflow [iN] <left> <right>
%result, %overflow = smul_overflow [iN] <left> <right>
%result, %overflow = sneg_overflow [iN] <source>

%result, %overflow = umul_overflow [iN] <left> <right>
```

All data operands have the declared `iN` type.

For signed operations, compute the mathematical result from signed operand interpretations:

| Operation | Mathematical result `t` |
| --- | --- |
| `sadd_overflow` | `S(left) + S(right)` |
| `ssub_overflow` | `S(left) - S(right)` |
| `smul_overflow` | `S(left) * S(right)` |
| `sneg_overflow` | `-S(source)` |

The first result is `bits_N(t)`. The overflow result is one exactly when `t < MIN_N` or `t > MAX_N`.

For `umul_overflow`, compute `t = U(left) * U(right)`. The first result is `bits_N(t)`, and overflow is one exactly when `t >= B`.

These operations always return their wrapped result and flag. They do not trap when the flag is one, do not saturate, and do not create an undefined value.

```SMIL
%sum, %overflow = sadd_overflow [i8] [i8 127] [i8 1]
// %sum = 0x80, representing signed -128; %overflow = 1.

%negated, %neg_overflow = sneg_overflow [i8] [i8 -128]
// %negated = 0x80; %neg_overflow = 1.

%product, %unsigned_overflow = umul_overflow [i8] [i8 255] [i8 2]
// %product = 0xfe; %unsigned_overflow = 1.

%signed_product, %signed_overflow = smul_overflow [i8] [i8 -1] [i8 2]
// %signed_product = 0xfe, representing signed -2; %signed_overflow = 0.
```

Unsigned add and subtract overflow are obtained through `uadd_carry` and `usub_borrow` with zero incoming flags.

Carry/borrow and signed overflow are different conditions. For example, unsigned `255 + 1` produces carry, while signed `-1 + 1` does not overflow. Signed `127 + 1` overflows an `i8` interpretation while its unsigned addition produces no carry.

Flag results may be passed as block arguments, tested by `br_if`, returned from functions, or stored as ordinary `i1` values.

A backend may share machine instructions when it proves that multiple requested results have the required meanings. No such sharing may introduce hidden flag dependencies.

### Arithmetic Faults

The integer operations defined here have two arithmetic-fault conditions:

| Condition | Fault kind |
| --- | --- |
| Zero divisor in `udiv`, `urem`, `sdiv`, or `srem` | `integer_divide_by_zero` |
| `sdiv` of `MIN_N` by `-1` | `integer_divide_overflow` |

An **arithmetic fault** terminates normal execution of the program instance at the faulting operation. The operation produces no result and execution does not continue in the current function or its caller.

Arithmetic faults are defined terminal events, not undefined behavior. They do not perform SMIL exception propagation or promise stack unwinding or cleanup.

The platform environment specifies the conforming fault-reporting and termination mechanism. It may use a native trap or a runtime service, but must not silently return a substitute result or resume ordinary SMIL execution.

A target may require explicit guards when its native instruction wraps, masks operands, or otherwise differs from these semantics. Guards may be omitted when proven unnecessary.

These potential faults do not add normal successor edges to the flat CFG. Division and remainder remain ordinary operations within a block. They are not catchable by `invoke`. Explicit user faults use the separately defined `trap` terminator.

Zero divisors and signed quotient overflow are execution conditions, not operand type errors. An ordinary executable operation with constant faulting operands is not malformed SMIL merely because executing it would fault. A compiler may warn, but an unexecuted path must not cause a fault. The explicit constant-expression form instead requires successful static evaluation and rejects an arithmetic fault even when it appears within an otherwise unexecuted function.

An optimizer must preserve fault behavior and the required ordering of observable effects. In particular:

- A possibly faulting operation cannot be discarded solely because its value is unused.
- It cannot be speculatively executed on a path that would not execute it.
- A replacement must preserve the relevant fault conditions.
- Implementing `srem` through a combined quotient/remainder helper must preserve its defined `MIN_N, -1` result.

Non-faulting integer operations defined here do not affect storage or implicit machine state. Their unused results may be removed when doing so preserves all other specified behavior.

| Case | Behavior |
| --- | --- |
| Overflow in plain `add`, `sub`, `mul`, or `neg` | Wrapped result |
| Overflow in an explicit overflow operation | Wrapped result and flag |
| Carry or borrow out | Wrapped result and outgoing flag |
| Shift count at least the value width | Defined zero or sign fill |
| `srem(MIN_N, -1)` | Zero |
| Division/remainder by zero | Terminal arithmetic fault |
| `sdiv(MIN_N, -1)` | Terminal arithmetic fault |

The rules apply equally to native instructions, expanded sequences, constant folding, and runtime helpers. Target profiles cannot select different integer semantics.

Pointer-formation and address-validity/access-permission violations use the terminal fault rules in Pointers and Memory Access. The execution-violation section defines their additional fault kinds and resource policy, with arithmetic domain checks before helper/work-buffer reservation.

### Operation Summary

This table summarizes established forms. Detailed rules in the preceding sections take precedence over abbreviated descriptions.

| Operation | Family | Inputs or parameters | Results / behavior |
| --- | --- | --- | --- |
| `alosf` | `STOR` | Mutability, object type, optional initializer | Declares entry-local storage and produces its pointer |
| `load` | `STOR` | Result type, address | Reads and produces a value |
| `store` | `STOR` | Address, value | Writes storage; no result |
| `record_make` | `AGG` | Record type, ordered field values | Complete record SSA value |
| `record_get` | `AGG` | Record value, static field path | Selected field value |
| `record_set` | `AGG` | Record value, static path, replacement | New record value; source unchanged |
| `field_addr` | `STOR` | Record pointer, static field path | Pointer to the inline field in the same space |
| `ptr_eq`, `ptr_ne` | `PTR` | Matching pointer types | `i1` normalized address equality/inequality; no dereference |
| `ptr_offset` | `PTR` | Associated live pointer, signed-interpreted byte delta | Object-preserving byte offset; invalid formation faults |
| `ptr_diff` | `PTR` | Integer result type, two positions of one allocation | Signed byte difference; invalid domain or range faults |
| `addrspacecast` | `VALCO` | Destination pointer type, source in another space | Explicit object-preserving profile mapping |
| `load_unaligned`, `store_unaligned` | `STOR` | Ordinary integer view, value/result | Byte-aligned integer access; loads require initialized value bits; may split and is not atomic |
| `mmio_load`, `mmio_store` | `IO` | Integer view, value/result, named access contract | Required observable device transaction or sequence |
| `mmio_fence` | `IO` | Named access contract | Full ordering/visibility boundary in its device/shared-memory domain |
| `atomic_load`, `atomic_store` | `ATOM` | Actual integer location, value/result, `seq_cst` | Indivisible ordinary-memory access in the atomic total order |
| `atomic_rmw` | `ATOM` | RMW kind, integer type, location, operand, `seq_cst` | Old `iN` value; indivisible update |
| `atomic_cmpxchg` | `ATOM` | Integer type, location, expected/desired, `seq_cst` | Old `iN` value and `i1` success; strong compare/exchange |
| `atomic_fence` | `ATOM` | `seq_cst` | Atomic-order and ordinary-memory ordering boundary |
| `sizeof`, `alignof` | `LAYOUT` | Integer result type, object type | Allocation size/alignment in bytes after binding |
| `offsetof` | `LAYOUT` | Integer result type, record type, static path | Cumulative field offset in bytes after binding |
| `sext` | `VALCO` | Destination type, source | Sign-extended integer |
| `zext` | `VALCO` | Destination type, source | Zero-extended integer |
| `trunc` | `VALCO` | Destination type, source | Low destination-width bits |
| `ptrcast` | `VALCO` | Destination pointer type, source | Changes pointee type within the same address space and compatible representation |
| `ptrtoint` | `VALCO` | Destination integer type, pointer | Target-profile-defined integer conversion |
| `inttoptr` | `VALCO` | Destination pointer type, integer | Target-profile-defined pointer conversion |
| `add`, `sub`, `mul` | `INTOP` | Result type, two integers | Wrapping arithmetic result |
| `neg` | `INTOP` | Result type, one integer | Wrapping negation |
| `udiv`, `urem` | `INTOP` | Result type, dividend, divisor | Unsigned quotient/remainder; zero divisor faults |
| `sdiv` | `INTOP` | Result type, dividend, divisor | Signed quotient rounded toward zero; defined terminal faults |
| `srem` | `INTOP` | Result type, dividend, divisor | Signed remainder with dividend sign; MIN/-1 yields zero |
| `uadd_carry` | `INTOP` | Result type, two integers, `i1` carry input | Wrapped `iN` sum and `i1` carry |
| `usub_borrow` | `INTOP` | Result type, two integers, `i1` borrow input | Wrapped `iN` difference and `i1` borrow |
| `sadd_overflow`, `ssub_overflow`, `smul_overflow` | `INTOP` | Result type, two integers | Wrapped `iN` result and `i1` signed-overflow flag |
| `sneg_overflow` | `INTOP` | Result type, one integer | Wrapped `iN` negation and `i1` signed-overflow flag |
| `umul_overflow` | `INTOP` | Result type, two integers | Wrapped `iN` product and `i1` unsigned-overflow flag |
| `shl`, `lshr`, `ashr` | `BOP` | Result type, value, unsigned-interpreted integer count | Shifted `iN` value; defined fill for oversized counts |
| `xor`, `and`, `or` | `BOP` | Result type, two integers | Bitwise result |
| `not` | `BOP` | Result type, one integer | Bitwise complement |
| `cmp` | `CMP` | Predicate, two same-type integers | `i1` comparison result |
| `br` | `BRTL` | Destination edge | Terminates the block |
| `br_if` | `BRTL` | `i1` condition, two edges | Terminates the block |
| `call`, `call_indirect` | `BRTL` | Non-raising callable, fixed/additional arguments | Normal results; callee contract governs lowering |
| `fnaddr` | `FUNC` | Declared function symbol | Typed non-null function reference |
| `fn_eq`, `fn_ne` | `FUNC` | Matching callable types | `i1` comparison of resolved function identities/null |
| `va_count` | `FUNC` | Integer result type, live pack | Additional-argument count; range failure faults |
| `va_is`, `va_get` | `FUNC` | Requested type, live pack, unsigned index | Type/bounds test or checked argument retrieval |
| `switch` | `BRTL` | Integer selector, unique constant cases, default | Selects one explicit CFG edge |
| `invoke`, `invoke_indirect` | `BRTL` | Raising callable, arguments, normal/exception edges | Terminates block; implicit edge prefixes carry outcome |
| `raise` | `BRTL` | Declared exceptional payload | Ends invocation exceptionally; no local CFG successor |
| `trap` | `BRTL` | Constant user fault identifier | Defined terminal fault; no cleanup promise |
| `on_exit` | `LIFE` | Non-raising zero-parameter/zero-result function reference | Registers one orderly-shutdown callback |
| `exit` | `LIFE` | `i32` status | Terminates application execution and requests orderly shutdown |
| `return` | `BRTL` | Function normal results | Terminates the block and invocation |

The earlier `jump` and integer-specific `reti` forms are replaced by `br` and `return`.

The unqualified forms `div`, `mod`, and `shr` do not identify operations in this core. Use the signedness-specific division/remainder operations and explicitly logical or arithmetic right shifts defined above.
