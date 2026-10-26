# SMIL Device Transactions and Atomic Memory

- Specify observable device accesses separately from ordinary storage.
- Define sequentially consistent integer atomics, participating agents, and synchronization.

## Sources

- [Guide — Device Regions and MMIO Transactions](../docs/Guide_SMIL.md#device-regions-and-mmio-transactions) and [Atomic Access to Shared Ordinary Storage](../docs/Guide_SMIL.md#atomic-access-to-shared-ordinary-storage).
- [Memory](0007_pointers_and_memory.md), [execution validation](0009_checked_execution.md), and [reference monitor](0011_checked_reference_profiles.md).

## Requirements

| KEY | Requirement |
| --- | --- |
| DEV-001 | Every device access contract shall be versioned and specify region identity/extent/lifetime/mappings/agents; legal directions, widths, alignment and byte order; exact transaction sequence/byte enables/splitting; side effects/reserved bits; ordering/completion/posting/barriers; shared memory/coherence/DMA rules; and bus/device failure behavior including partial completion. |
| DEV-002 | An `access("id")` shall resolve at binding, be recorded in compatibility metadata, and authorize only its specified region/transactions. A pointer space name alone shall not define device behavior. MMIO may represent memory mapping, isolated port I/O, or synchronous monitor services under the contract. |
| DEV-003 | `mmio_load [iN] p` and `mmio_store p v` shall accept integer types matching the pointer pointee and explicitly supported contract widths. Non-byte widths shall have an explicit value/transaction-bit mapping, including ignored/required bits. Ordinary iN storage rules shall not imply that mapping. |
| DEV-004 | Each successful dynamic access shall perform its contract's exact transaction/sequence once. Unused reads shall still occur. Optimization shall not remove, duplicate, speculate, merge, widen, or split transactions when doing so changes their observable sequence. |
| DEV-005 | An agent's MMIO transactions shall retain textual execution order, including across contracts. The selected contracts shall implement that order compatibly; individual access shall not imply a completion barrier for ordinary memory/device work. |
| DEV-006 | `mmio_fence access(id)` shall enforce full earlier/later MMIO and ordinary-memory ordering/visibility in the contract's device/shared-memory domain, including required posting drains, hardware barriers, and cache maintenance. Unsupported guarantees shall cause rejection. |
| DEV-007 | A device fence shall not itself wait for independent DMA/device completion or create CPU-thread synchronization. Completion shall use the device protocol; atomic fences shall not substitute for device fences. External ordinary-memory mutation shall require explicit coherence and ownership rules. |
| DEV-008 | MMIO-only regions shall reject ordinary/unaligned/atomic access even through ordinary-space aliases. Core device operations shall not accept record/pointer values or imply generic volatile RAM behavior. Environment devices shall not be constructed by global initializer stores. |
| DEV-009 | Invalid accesses shall fail the pre-transaction checks in [0009](0009_checked_execution.md). Bus/device faults after an authorized transaction begins shall follow the contract and may retain already committed external effects. |
| ATM-001 | Core atomics shall accept only `seq_cst` and the exact forms in [0001](0001_source_syntax.md). Other orderings/scopes and weak compare/exchange shall require extensions. |
| ATM-002 | Each atomic location shall be one actual ordinary integer object/leaf with access width equal to its declared resolved type. Partial/integer-reinterpreted, record, pointer, unaligned, and device views shall be rejected. Aliases shall not create different atomic locations. |
| ATM-003 | A profile shall specify supported widths, atomic alignment, regions, participating agents, progress, and interrupt/reentrancy guarantees. Extra alignment shall be proven/checked or handled by a conforming helper; existing declarations shall not imply extra alignment. |
| ATM-004 | Each atomic access shall be indivisible for its logical value/representation with respect to every participating agent, including interoperability between native/helper paths. Ordinary encoding, i1 canonical stores, and unused-high-bit clearing shall be preserved. |
| ATM-005 | `atomic_load` shall return the current iN; `atomic_store` shall replace it. `atomic_rmw` shall return the old value and install `xchg`, modular `add/sub`, or bitwise `and/or/xor` with its operand in one indivisible action. Other RMW kinds shall be rejected. |
| ATM-006 | `atomic_cmpxchg` shall return old iN then i1 success. Matching N value bits shall install desired with success one; mismatch shall perform no write with success zero. It shall be strong with no spurious failure. |
| ATM-007 | All participating `seq_cst` accesses/fences shall have one total order consistent with agent sequencing and happens-before. Extending it with initialization and ordinary writes consistently with happens-before, each read shall observe the latest preceding location write. RMW read/update shall occupy one position. |
| ATM-008 | Atomic writes shall have release semantics; reads shall have acquire semantics. A read observing an atomic write shall synchronize with that actual write. Successful compare/exchange and RMW shall be read/write; failed compare/exchange shall be an acquiring read. Equal numeric values shall not substitute for observed-write identity. |
| ATM-009 | Happens-before shall be the transitive closure of agent sequencing, observed-write synchronization, and explicit environment ordering edges. Thread/interrupt entry, exit, handoff, and creation shall add edges only under their environment contract. |
| ATM-010 | `atomic_fence seq_cst` shall participate in the total order and order preceding/following ordinary accesses in its agent. It shall not read a value or independently create cross-agent synchronization; publication shall require atomic communication or an environment event. |
| ATM-011 | Conflicting accesses shall overlap storage footprints with at least one actual write. Across agents, unordered conflicting accesses with at least one non-atomic access shall constitute a data race, including mixed atomic/ordinary use. Ordinary writes between atomic phases shall remain ordered relative to conflicts. |
| ATM-012 | Values shall be initialized before reading/publication. Plain and atomic stores may initialize; atomic loads, all RMW including `xchg`, and both compare/exchange outcomes shall require a complete old value. Failed compare/exchange shall initialize nothing; fences shall read no value. |
| ATM-013 | A helper/critical section shall exclude every advertised competitor and preserve synchronization/progress. Masking one local interrupt shall not establish exclusion of another CPU, NMI, or device. A helper that can deadlock under advertised reentry shall not be conforming. |
| ATM-014 | No implicit lock-free/wait-free guarantee shall be inferred. Unsupported atomic requirements shall be diagnosed rather than lowered to tearing access. Optimizations shall preserve observations, actual write footprints, synchronization, race checks, total order, and advertised progress. |

## Required conformance observations

| Case | Required outcome |
| --- | --- |
| Two reads of a device register with unchanged address | Two prescribed observable transactions, including unused results. |
| Contract i8 register accessed as i1 or wider type | Rejection when statically unsupported; appropriate runtime access fault otherwise. |
| Ordinary-space alias of an MMIO-only register | Ordinary access remains prohibited. |
| One-time payload write followed by release atomic ready=1, acquiring read observes that write | Payload read ordered after its write and observes the published value absent later writes. |
| Uninitialized `atomic_rmw xchg` or compare/exchange | `uninitialized_read` before result/write/synchronization. |
| Compare/exchange mismatch concurrent only with another read | No conflicting write attributed to the failed operation. |
| Unsupported interrupt competitor in single-agent reference profile | Profile violation; byte sequences shall not be advertised as interrupt-safe atomics. |
