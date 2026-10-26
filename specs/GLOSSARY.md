# Specification Glossary

This document specifies proper nouns or otherwise the meanings of specialized terms (nouns, adjectives, verbs, adverbs, etc.) needed to understand the exact meaning of the specification.

| Term / Expression | Definition |
| ----------------- | ---------- |
| SMIL | Small Machine Intermediate Language: the typed SSA representation and explicit storage/control-flow contracts defined by [0000](0000_smil.md). |
| SMIL Source v1 (`smil.source.v1`) | The textual grammar and lexical/statement-boundary rules in [0001](0001_source_syntax.md), independent of target/transport versions. |
| Target Profile | A versioned CPU, layout, ABI, environment, and runtime selection that fixes physical implementation contracts without changing logical operation meanings. |
| Unbound SMIL | SMIL whose target contracts have not been resolved; only target-independent verification/transformation decisions are complete. |
| Target-Bound SMIL | SMIL with a resolved target and required component contracts, permitting layout-dependent decisions and physical lowering. |
| Checked Reference Profile | One of the 38 project-owned single-agent `.checked.v2` CPU/mode environments in [0011](0011_checked_reference_profiles.md); its definition is distinct from backend availability. |
| Representation Size | Number of bytes containing a stored value's encoding, excluding trailing allocation padding. |
| Allocation Size | Space reserved for an object, including trailing padding, at least its representation size and a multiple of required alignment. |
| Required Alignment | Positive power-of-two byte alignment required for an ordinary typed access under the resolved layout. |
| Callable Contract | Ordered logical parameter/result types, effective ABI attributes, variadic status, raised type, and resolved ABI of a function/reference. |
| SSA Value | Complete immutable typed value with one static function-local definition and potentially multiple dynamic bindings when its defining operation/block executes repeatedly. |
| Entry Declaration Region | Initial entry-block region containing local types, then `alosf` declarations, before any ordinary operation or terminator. |
| Local Storage Object | Allocation created by a processed `alosf` and owned by one invocation, with separately declared mutable or immutable contents. |
| Global Storage Object | One module-owned addressable allocation reserved during bootstrap and shared by referencing invocations, with lifecycle-controlled content readiness. |
| Named Constant | Immutable non-addressable module value whose constant initializer is evaluated without executing SMIL functions. |
| Constant Expression | Parenthesized permitted single-result operation whose recursively constant operands must evaluate successfully at compilation or binding. |
| Record-Zero Initializer | `[R zero]`: recursively supplies integer zeroes and typed data/callable nulls without allocating targets or promising zero representation bytes. |
| Field Path | Nonempty static decimal index sequence selecting only inline record fields, never dereferencing pointer fields. |
| Object Association | Allocation/region identity, byte position, and restrictions carried semantically by a pointer; also called provenance. |
| One-Past Position | Offset L of a positive-size L allocation, legal for comparison/checked arithmetic but not dereference. |
| Address-Only Pointer | Profile-supported non-null pointer with a numeric coordinate but no usable object association; it cannot authorize object arithmetic, field selection, or storage access. |
| Normalized Address Coordinate | Profile-defined location used for pointer equality/inspection, independent of alternate native segment/bank/address encodings. |
| Integer View | A typed ordinary integer access fitting within one actual integer leaf's representation bytes, with no padding/field/reference reinterpretation. |
| Function Reference | Typed `fnptr` value identifying a fixed callable contract/target or typed null; distinct from a data pointer and constructed from a function by `fnaddr`. |
| Borrowed Argument Pack | Non-storable `[varargs]` SSA value describing additional typed arguments, usable only within its owning live invocation except for explicit forwarding into another pack. |
| Raised Payload | One complete ordinary value transferred by `raise` to an invoking caller's explicit exceptional edge; distinct from terminal faults. |
| Terminal Fault | Defined event that prevents further normal execution, returns no result, preserves earlier completed effects, and promises neither unwinding nor orderly shutdown. |
| Device Access Contract | Versioned definition of an associated device region's exact allowed observable transactions, mappings, ordering/completion, and failure protocol. |
| Agent | Thread, interrupt context, or other participant explicitly included in the environment's ordinary-memory/atomic synchronization domain. |
| Memory Footprint | Union of representation-byte ranges of the leaves actually accessed, excluding padding and distinguishing read from actual write effects. |
| Happens-Before | Transitive closure of within-agent sequencing, observed atomic release/acquire communication, and explicit environment ordering edges. |
| Data Race | Cross-agent overlapping conflicting memory events with at least one non-atomic access and no happens-before order, detected before the later event commits. |
| Checked Execution Prefix | Completed memory/synchronization/effect history against which the next operation is validated before it may commit or terminate the instance. |
| Semantic Resource Accounting | Profile-mandated identity increments, live-object charges, registrations, and other events that remain required despite physical optimization. |
| Execution Plan (`smil.execution-plan.v1`) | Required private object metadata describing actual function frame/shadow/native usage and checked reservation sites; this is a runtime resource contract artifact. |
| Module | Explicitly identified source ownership, separate-compilation, and lifecycle-registration unit with private-by-default definitions and explicit exports. |
| Canonical Symbol Key | JSON triple `[module_identity, namespace, local_name]` resolving a source entity independently of import alias/path/input order. |
| Interface Fingerprint | Canonical SHA-256 digest of a module's logical exported interface payload; used to pin exact import compatibility. |
| Import Lock | Object metadata binding a required module identity to the exact bound interface digest used for compilation. |
| Program Instance | One statically linked selected module set and its runtime state, initialized and terminated once. |
| Lifecycle Node | One dynamic-global factory or startup hook with a unique program-wide initialization ID, prerequisites, and optional completion callback. |
| Ready Global | Global whose complete constant/factory value has been installed and whose contents may be accessed subject to ordinary validity rules. |
| Finalized Global | Dynamic global whose registered shutdown callback has returned normally; its allocation/address remains reserved but content access is prohibited. |
| Orderly Shutdown | Coordinator transition that quiesces application agents and drains registered callbacks LIFO before reporting exit status. |
| Completion Callback | Shutdown registration committed only after its initializer action succeeds and, for a factory, the complete value is installed. |

## Standards

A term, expression, word that is defined here must:

- Define the meaning of something that is not commonly understood. For example, we do not define the word "Dog" if its meaning is exactly that understood by a fluent, English speaker: i.e., an animal from the canine family. If dog is referenced in a spec, it is written in lowercase if it's not the first word of a sentence to indicate "dog" refers to the common meaning.
- Consistent and unique. The way we refer to a special concept or meaning is consistently used and its denotation and meaning are different from other terms defined and used. For example, if we define the term "Red Yeti", then its definition is only applicabler to "Red Yeti" and no other specialized term in this glossary; and, "Red Yeti" ONLY refers to the definition here and nothing else in these documents.
- Concise. Specialized terms and expressions use the smallest number of words required to be understandable and definable. For example, "Amber/Yellow Indicator" maybe be refined to either "Amber Signal" or "Yellow Signal" (but not both).
- Jargon is avoided, but if used, it MUST be commonly understood from the field of Computer Science, Mathematics, Philosophy, Computer Engineering, or related field. If it is an uncommon term, then it is defined here and its definition references via web url link ane external source, using the best source possible. For example, if the term is defined on Joe's Blog or Yale's Department of Computer Science page, the external referencel inks to Yale's Computer Science page.
