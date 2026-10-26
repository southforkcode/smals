# SMAls Specifications

These specs are effective for this project.

| File | Description |
| ---- | ----------- |
| [0000_smil.md](0000_smil.md) | Scope, normative interpretation, guide coverage, and unresolved companion contracts (`SMIL`). |
| [0001_source_syntax.md](0001_source_syntax.md) | Exact `smil.source.v1` token rules, statement boundaries, and complete grammar (`SYN`). |
| [0002_types_and_storage.md](0002_types_and_storage.md) | Names, type identity, literals, SSA values, local/global objects, and mutability (`TYP`). |
| [0003_constants_and_aggregates.md](0003_constants_and_aggregates.md) | Constant evaluation, symbolic addresses, record values, field paths, and layout queries (`AGG`, `CST`). |
| [0004_integer_operations.md](0004_integer_operations.md) | Arithmetic, shifts, flags, comparisons, conversions, and arithmetic faults (`INT`). |
| [0005_functions_and_calls.md](0005_functions_and_calls.md) | Calls, function references, borrowed variadics, typed exceptions, and cooperative exits (`FUN`, `VAR`, `EXC`). |
| [0006_control_flow_and_ssa.md](0006_control_flow_and_ssa.md) | Explicit edges, block parameters, switch/trap, reachability, and dominance (`CFG`, `SSA`). |
| [0007_pointers_and_memory.md](0007_pointers_and_memory.md) | Object association, pointer conversions/arithmetic, typed/unaligned memory, and access faults (`PTR`, `MEM`). |
| [0008_devices_and_atomics.md](0008_devices_and_atomics.md) | Device transaction contracts, integer atomics, agents, and synchronization (`DEV`, `ATM`). |
| [0009_checked_execution.md](0009_checked_execution.md) | Initialized reads, data races, staged faults, resource accounting, optimizer obligations, and execution metadata (`EXE`, `RES`, `OPT`, `MET`). |
| [0010_targets_layout_and_abi.md](0010_targets_layout_and_abi.md) | Target binding, ordinary data layout, address spaces, ABI, compatibility, and environment obligations (`TGT`, `LAY`, `SPC`, `ABI`, `CMP`, `ENV`). |
| [0011_checked_reference_profiles.md](0011_checked_reference_profiles.md) | 38 checked v2 reference profiles, packet/frame contracts, monitor, runtime catalogs, and CPU conformance (`REF`, `PKT`, `FRM`, `RFN`, `MON`, `RAT`, `RRT`, `RIMG`, `RCPU`). |
| [0012_modules_and_interfaces.md](0012_modules_and_interfaces.md) | Module ownership/visibility, nominal identities, public type closure, fingerprints, and serialized constants (`MOD`, `IDN`, `IFC`). |
| [0013_objects_and_static_linking.md](0013_objects_and_static_linking.md) | Objects/libraries, complete selection, relocations/catalogs, lifecycle metadata, images, and loader validation (`OBJ`, `REL`, `CAT`, `LNK`, `LIFM`, `IMG`). |
| [0014_program_lifecycle.md](0014_program_lifecycle.md) | Bootstrap, dynamic factories, startup graph, readiness, failure, exit callbacks, and finalization (`LIFE`). |

These documents convert [the SMIL guide](../docs/Guide_SMIL.md) into behavioral contracts. Requirement keys and required conformance observations support verification and subsequent planning; the documents do not prescribe a development sequence. Start with [scope and source coverage](0000_smil.md) and the [glossary](GLOSSARY.md).

The referenced profile/linking/execution companion bundles are absent from this checkout. [Unavailable normative inputs](0000_smil.md#unavailable-normative-inputs) identifies the resulting contract gaps; the specifications do not claim implemented backends or fully resolved binary interchange.

## Specification Standards

1. Specification documents are named:

   `dddd_synopsis.md`

   - Where `dddd` is a unique decimal number.
   - Where `synopsis` is a short English description in *snake case*.

2. Inactive, retired, replaced specifications are moved to the `retired` folder and added to the index in `retired/README.md`.

3. Specification documents follow the `SPEC_TEMPLATE.md` format defined in this folder.

4. Specification documents must be:

   - **Clear**. Unambiguous, English language statements which either refer to the generally acceptable, commonly understood, meanings of words or defines unique concepts as proper nouns and includes those terms in `GLOSSARY.md`.
   - Consistent
   - Concise
   - Correct
   - Actionable. Requirements state concrete behavior and constraints from which an implementation plan can be derived.
   - Measurable
   - Behavioral
   - Characterized by non-functional aspects
   - Unique. A specification must define one or more requirements that stand by themselves. I.e., each statement is measurable on its own.
