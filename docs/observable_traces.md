# Observable trace records

Sources: [B007](../plans/01_foundation_and_contracts.md#b007) and [evidence policy](../plans/00_delivery_and_evidence.md). This is an evidence representation, not an interpreter or a native-profile contract.

An Event owns logical sequence, closed kind (value/memory/device/fault/lifecycle/resource), subject, numeric value, byte payload and private debug text. Trace comparison validates each input's strictly increasing sequence and known kinds, then compares count and every semantic field in vector order. Debug text is excluded. Both empty traces are a valid zero-effect comparison. Equal but invalid order cannot pass. Sequence values are explicit ordinals; gaps are allowed but the expected sequence must match exactly.

Use Result<void>/Diagnostic rather than exceptions. Originating comparison/validation errors include actionable codes TRACE_ORDER, TRACE_KIND, TRACE_LENGTH or TRACE_MISMATCH, phase execution, and an event-index span. A caller propagates without duplicate logging. Hand-authored expected and actual records exercise all six kinds, semantic mutations, reordered/invalid traces and debug-only differences. No runtime semantics or native conformance is inferred from this representation.
