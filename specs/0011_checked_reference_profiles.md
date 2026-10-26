# SMIL Checked Reference Profiles

- Define the shared checked v2 representation, packet ABI, runtime, and reference-monitor contracts.
- Identify the 38 CPU/mode profiles and the evidence required to advertise backend availability.

## Sources

- [Guide — Concrete Reference Profiles](../docs/Guide_SMIL.md#concrete-reference-profiles).
- [Target/layout/ABI](0010_targets_layout_and_abi.md), [execution](0009_checked_execution.md), [linking](0013_objects_and_static_linking.md), and [lifecycle](0014_program_lifecycle.md).
- [Unavailable companion inputs](0000_smil.md#unavailable-normative-inputs). Manifest-specific values absent from the guide shall remain unresolved, not inferred from an existing machine ABI.

## Requirements

| KEY | Requirement |
| --- | --- |
| REF-001 | The reference set shall use target IDs `smil.ref.<model>.checked.v2` for the catalog below, manifest format `smil.target-profile.v1`, shared format `smil.reference-contracts.v2`, shared ID `smil.ref.checked.contracts.v2`, and runtime component `smil.rt.checked.packet.v2`. These shall describe project reference boards/monitors rather than platform C/OS ABIs. |
| REF-002 | Every indexed profile shall be fully resolved without binding-time inheritance/host defaults. Binding shall validate the exact index entry, manifest/shared-contract digests and closed schema, reject unknown IDs/fields/contracts, and record exact resolved identities. Linking shall require equality of all resolved components, including CPU/environment, until an explicit compatibility revision exists. |
| REF-003 | Canonical JSON digests shall be SHA-256 of UTF-8 JSON with sorted object keys, no insignificant whitespace, unescaped non-ASCII, no normalization, and significant array order. Duplicate keys/floating numbers shall be rejected. Index shall pin profile digests; profiles shall pin shared-contract digest; no digest shall include itself. |
| REF-004 | A tool shall advertise a profile as implemented only when its encoder, complete lowering/runtime closure, linker/loader contract, and relevant conformance vectors pass. An unavailable backend shall produce a diagnostic rather than emit code for a nearby CPU. Proposed profile status shall not satisfy this gate. |
| REF-005 | Reference integers shall support every width 1 through 65535. For representation bytes B=`ceil(N/8)` and catalog cap C, alignment shall be the largest power of two at most `min(B,C)` and allocation `round_up(B,alignment)`. Wider bound types shall be unsupported, not truncated. |
| REF-006 | Empty records shall have representation zero, allocation one, alignment one, and distinct live allocation positions. An empty normal-result tuple shall instead have zero payload bytes; no-results shall remain distinct from one empty-record result. |
| REF-007 | Data/ROM/I/O pointers shall be 16 bytes aligned to `min(C,4)`; function references eight bytes with that alignment. Pointer fields shall be target-endian u32 allocation identity, allocation-relative byte offset, cached normalized coordinate, and effective read/write rights at offsets 0,4,8,12. Rights shall use bits 0/1 with other bits zero. |
| REF-008 | Null shall have all pointer fields zero. Address-only data/ROM values shall have identity/offset/rights zero and nonzero cached coordinate. Equality shall distinguish null then compare cached coordinates, including expired values. Access/arithmetic shall require live matching registry identity, consistent coordinate/offset, rights, valid view, and readiness. |
| REF-009 | Runtime storage shall begin with a 128-byte context, followed by `object_slots*48` registry bytes, `callback_slots*8` callback bytes, then private scratch, within manifest capacities. Registry fields shall use the ordered target-endian u32 contract; zero identity shall mark an unused slot. |
| REF-010 | Monitor allocation ID shall be 1; global IDs shall begin at 16 in canonical qualified-key order. Each executed local declaration shall receive a fresh monotonic identity and logical slot charge under RES-008; freed slots shall not permit identity reuse. Return/raise/abandonment shall expire all owning local identities before reuse. |
| REF-011 | Registry/catalog/packet/native-return/runtime-private storage shall not be ordinary registered objects. Numeric guessing shall not make it accessible. Proofs may remove physical checks/fields privately but shall preserve semantic charges and observable stored/public representations. Alternate thin encodings shall require a different layout/runtime contract. |
| REF-012 | Minimum pointer-inspection integer width M shall be 16 for the catalog's 8-bit families and 32 for the others; supported conversion widths shall be M through 65535 without truncation. Numeric values outside each domain shall cause `invalid_pointer_operation`. |
| REF-013 | Data/ROM `ptrtoint` shall zero-extend cached coordinate (null to zero), including expired-value inspection, within manifest `data_rom_encoding_max`. `inttoptr` zero shall be null; a uniquely containing live strict-interior position shall reconstruct canonical association/rights in that space; an unregistered coordinate shall become address-only. |
| REF-014 | Data/ROM integer round trips shall preserve every accepted numeric value exactly. Pointer round trips shall cover null and uniquely mapped live strict-interior positions with canonical object/space rights, excluding expired, one-past, and attenuated-rights values. Adjacent boundaries may reconstruct a different allocation; no hidden integer provenance shall be retained. |
| REF-015 | I/O conversions shall map null to zero and monitor coordinate a in 0..7 to a+1; inverse values 1..8 shall reconstruct those live canonical monitor positions and zero shall be null. Other integers shall fault. Both round-trip guarantees shall cover exactly this domain. |
| REF-016 | ROM shall contain constant-initialized immutable objects also accessible by read-only data views. Data/ROM mappings shall preserve identity/position/rights; data-to-ROM shall fault for RAM. Mappings between I/O and any other space shall be unsupported; the reference monitor shall have no data-space device aliases. |
| REF-017 | Native translation shall preserve normalized coordinates: real 8086 shall use `segment=physical>>4`, `offset=physical&15` with recomputation before wrapping; 286 protected shall use code selector 0x08 and data selectors `0x10+8*k` for sixteen 64-KiB windows; MIPS shall use uncached KSEG1 for low reference physical memory. Other exact translations shall come from manifests. |
| PKT-001 | The default ABI shall pass a runtime-private native packet address in the catalog's incoming registers. No fixed/additional logical value or normal/raised result shall travel as a native value-register argument/result. |
| PKT-002 | The caller shall reserve a cap-aligned packet beginning with the contract's 64-byte, sixteen-target-endian-u32 header, magic `0x534d494c`. It shall include signature, fixed/additional counts/table, outcome payload locations/tag, callee identity, caller frame, saved software top, and optional software continuation; reserved fields shall be zero. Exact field offsets shall require the shared contract. |
| PKT-003 | Argument entries shall be 16 bytes each, containing type ID, payload offset, allocation size, reserved zero, in source order. Zero count shall use table offset zero. Payloads shall follow the table with per-type alignment, ordinary encoding, zero ABI padding, and by-value copies inaccessible as source packet storage. Offset arithmetic shall not wrap. |
| PKT-004 | After arguments, the caller shall reserve one region aligned for and sized to the greater of normal-result tuple and raised payload. Result tuple layout shall follow ordinary field layout without nominal identity. Both present outcomes shall use that region; absent carriers shall have offset zero. Only the selected carrier shall be read. |
| PKT-005 | Outcome zero shall mean pending, one normal, two raised. The callee shall write selected payload before the tag; non-raising signatures shall not return tag two. Termination shall manufacture no outcome. The callee shall validate target/signature/header/descriptors before consuming arguments. |
| PKT-006 | The caller shall copy selected results into surviving backing before packet release/restoring saved software top. Hardware flags/native return registers shall not carry logical results. Extension attributes shall retain effective identity but cause no physical widening without a wider carrier; unused bits shall remain canonical zero. |
| PKT-007 | All calls shall obey manifest clobber/preservation and restore native SP/processor modes on normal/raised return. 6502 zero-page bytes 0x20..0x3f shall be call-clobbered scratch; other families shall use only their explicitly reserved runtime scratch. |
| FRM-001 | Software frames shall grow upward in the dedicated region, with a 32-byte private contract header, locals in declaration order/alignment, then shadow/private temporary/spill/packet areas as applicable. Total extents shall be computed/bounded and checked before reservation. |
| FRM-002 | Native return storage shall be separate from ordinary locals, preflight every implicit/explicit push or link-save frame, and reserve the manifest emergency portion exclusively for terminal reporting. Predecrement SP shall begin at aligned region end; postdecrement SP at last usable byte/index, respecting actual return writes. |
| FRM-003 | Native call/return mechanisms shall obey the family table below. Link-register saves shall be reserved before a nested call overwrites the incoming link. Dispatchers shall validate IDs and cover every retained function/continuation without writable trampolines or assumed computed-jump support. |
| FRM-004 | The 8008 shall use software continuation IDs and static jump dispatch for generated and compiler-introduced helper calls/returns. Generated `CALL`, `RST`, and `RET` shall be absent; hardware return-stack depth shall not cap logical recursion. |
| RFN-001 | A function reference shall contain target-endian u32 function ID followed by exact callable signature ID; null shall be the zero pair. Function catalog records shall contain function ID, signature ID, normalized entry, and reserved zero. IDs shall resolve to fixed targets for the instance lifetime. |
| RFN-002 | Function-address constants/storage shall use FNREF relocation. Indirect entry shall validate both IDs against catalogs and apply native translation/dispatch. Native C pointers, C calling conventions, and dynamic loading shall not be implicit interfaces. |
| RFN-003 | All reference profiles shall support explicit typed variadic calls, receipt, and runtime forwarding. Packs shall reference a live invocation's additional descriptors; forwarding shall copy descriptors/complete values into a new packet. Type/index/count checks shall follow [0005](0005_functions_and_calls.md). Native C varargs shall require an adapter. |
| RFN-004 | Raised outcomes shall use packet tags/payloads without native unwinding. Both normal/raised completion shall expire callee locals before the caller edge; frontend cleanups shall remain explicit CFG operations. |
| MON-001 | `smil.ref.monitor.v1` shall be the sole predefined device contract and expose the eight logical registers below, with only i8 transactions, exactly once per access, no widening/posting/DMA/shared RAM. Other widths/directions shall be rejected when known or fault at access. |
| MON-002 | Status/fault reporting shall write offsets 2,3,4,5 in that order, low significance first independent of target endian, then command offset 6. Command one shall permanently stop with exact i32 exit bits; command two with the fault ID. No restart/resume shall follow. |
| MON-003 | 6502/6800 monitor registers shall map from memory 0x7ff0. 8008 reads at logical 0/7 shall use input ports 0/1; writes 1..6 output ports 8..13. 8080/8085/x86 shall use isolated ports from 0xf0. Immediate-only dynamic port selection shall use checked dispatch without probing reads. |
| MON-004 | 68k/PowerPC/ARM/MIPS/SPARC shall use manifest-defined synchronous monitor traps/registers with service 0 read, 1 write, 2 fence. Services shall perform the exact nonspeculative transaction, return read bytes in the specified register, restore SP/mode, and obey clobbers. Trap instruction availability alone shall not prove service availability. |
| MON-005 | Monitor `mmio_fence` shall complete prior synchronous monitor transactions and establish the compiler boundary. It shall imply no DMA access to RAM. Real devices/shared-memory protocols shall require different explicit contracts. |
| RAT-001 | Each reference environment shall have exactly one application agent `main`, with application interrupts, NMI entry, async reentry, other threads/CPUs, concurrent foreign writers/callbacks, and DMA mutation excluded by explicit environment gating. Enabling another agent shall violate these profile versions. |
| RAT-002 | Core atomics shall support widths 1..65535 at actual live ordinary integer locations with ordinary alignment. Finite byte-vector sequences may implement indivisibility solely for the advertised single-agent domain. They shall not imply interrupt/multiprocessor safety. |
| RAT-003 | Helpers shall use no locks and complete in finitely many steps for finite operands and sufficient reserved resources. Sequentially consistent fences shall preserve compiler ordering without emitting unsupported modern opcodes. |
| RRT-001 | Catalogs shall distinguish integers, pointers, callable value representations, nominal records, internal result tuples, and signatures. Aliases shall share identities. Canonical finite structural keys shall stop at nominal identities, include resolved ABI/attributes/effects, exclude provisional numeric IDs, and be UTF-8 canonical-JSON sorted before numbering. |
| RRT-002 | Image metadata shall describe type sizes/alignment/fields/references, callable parameters/results/effects, globals/rights/readiness, and native function/continuation entries. Generated ROM tables/specialized checkers shall agree with the descriptor. Runtime-private Raw/FrameRaw/count/mode carriers shall not be source pointers or forge association. |
| RRT-003 | Every accepted operation shall have a legal native expansion or generated/linked helper from the contract catalog below. A helper name without its implementation shall not close lowering. Helper packets/clobbers and logical operand/result order shall follow the core plus only contracted private annotations. |
| RRT-004 | The source entry shall be designated `smil_main`, fixed `() -> ([i32])`, default packet ABI, non-raising/non-variadic. Lifecycle shall install constants, execute the resolved dependency order, publish readiness, enter it, drain callbacks, and report i32 bits. Other language entry forms shall use wrappers. |
| RRT-005 | Only `main` shall register callbacks or execute `exit`. Callbacks shall be valid non-null default-ABI zero-parameter/zero-result fixed non-raising references. Capacity shall be reserved before completion-registered actions and committed only on success. |
| RRT-006 | Explicit exit shall expire abandoned locals and reset software/native call state to the reserved coordinator root before callback execution. Terminal reporting shall require no new packet/ordinary native call and shall use pre-reserved emergency/architectural exception state. |
| RRT-007 | Built-in faults shall use the fixed shared-contract IDs, including 14/15 from MET-005. Deduplicated user identifiers shall be sorted by UTF-8 and assigned from 65536. Dynamic capacity/counter/tracking failures shall be terminal and static impossible placements diagnostic. |
| RIMG-001 | Reference executable format shall be `smil.ref.image.v1` with UTF-8 JSON descriptor and fixed-placement raw segments, recording target/contracts/digests, entry, segment bounds/kinds/digests, catalogs, initialization order, and user IDs. Segments shall lie wholly in permitted regions; unmapped holes shall not be ordinary RAM. |
| RIMG-002 | All relocations shall be applied before bootstrap; constant ROM shall contain final values and dynamic globals reside only in writable ordinary RAM. Dynamic linking/rebasing/native OS executable assumptions and relocation-time factory execution shall be absent. Relocation details shall follow [0013](0013_objects_and_static_linking.md). |
| RCPU-001 | Every emitted instruction shall be legal for the exact selected mode/subset. Intel 32-bit variants shall use the 80386 integer baseline without implicit x87/MMX/SSE/CMOV/CMPXCHG8B. PowerPC shall use the contracted common 32-bit integer subset without implicit POWER/floating/vector operations. |
| RCPU-002 | Reference 68k emission shall exclude MOVEP, CAS/CAS2, long multiply/divide, bitfield, floating-point, and MMU instructions. Required logical behavior shall use conforming helpers/expansions. Processor model succession shall not imply an unrestricted instruction superset. |
| RCPU-003 | `ppc970-32` shall use 32-bit execution, not a 64-bit pointer or ELF ABI. 286 real/protected shall be separate contracts. RISC encoders shall enforce execution-state and delay-slot restrictions from the family table/manifest. |

## Reference model catalog

REF-001, REF-005, and PKT-001 incorporate this catalog. The coordinate width limits normalized locations, not logical integer widths. “Cap” specifies maximum ordinary integer alignment in bytes.

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

## Native transfer rules

FRM-003 incorporates these family-specific rules.

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

## Monitor registers

MON-001 incorporates these transaction restrictions.

| Offset | Permitted transaction |
| --- | --- |
| 0 | Read one `i8`, always returns 1: transmitter ready |
| 1 | Write one `i8`, emits that byte once |
| 2, 3, 4, 5 | Write result bits 7:0, 15:8, 23:16, 31:24 respectively |
| 6 | Write command 1 to report orderly exit or 2 to report a terminal fault, then stop the instance permanently |
| 7 | Read one `i8`, always returns zero |

## Helper contract catalog

RRT-003 incorporates these names and semantic obligations; exact private signatures require the unavailable shared contract.

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

## Required backend conformance observations

A profile advertisement shall demonstrate exact non-native arithmetic at widths 1, 3, 12, 24, and 64; both byte orders and empty/nested record layouts; canonical pointer/function copies and relocations; recursive frame/identity lifetimes; one-past and dangling-pointer behavior; preflight before stack/table/counter overflow; packet/result/exception/variadic behavior; preservation/clobbers; indirect-target validation; exact monitor transactions; fault/status reporting; deterministic initialization/failure/LIFO shutdown; and the selected CPU mode/instruction subset. Segmented profiles shall demonstrate boundary translation, 8008 software-continuation depth, and RISC profiles their required delay slots. Manifest validation alone shall not establish CPU execution or backend conformance.
