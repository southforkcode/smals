# Guarded runtime fixtures

Sources: [B011](../plans/01_foundation_and_contracts.md#b011), test-support standards and the separate checked-runtime implementation plan. These are deterministic test fixtures, not an implemented SMIL allocator or normative fault-ID assignment.

A fixed-capacity buffer has two canary bytes on each side, a payload extent and byte-validity shadow. A checked write validates range before mutation; out-of-range writes return bounds and leave payload/canaries unchanged. A bounded resource budget reserves with subtraction-based overflow checks; fail-next injection rejects exactly one reservation without charging it. Reads reject uninitialized bytes. Fixture faults are explicit test-only enum values (none/bounds/uninitialized/capacity/injected), independent of unresolved reference-profile wire IDs.

Construct fixtures without dynamic allocation: at most 64 payload bytes and a 68-byte backing array; an invalid requested extent yields an invalid fixture and bounds on access. No hidden allocation is used to represent an injected resource failure. Check canaries, initialization, reservation balance and preserved neighboring bytes independently. Native registry case `runtime.guards` supplies deterministic seeds and positive/negative witnesses. Debug entry and originating error reasons use the standard debug stream. The production runtime remains later work.
