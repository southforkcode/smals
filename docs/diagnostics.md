# Diagnostics and command boundaries

Sources: project contributors, SMIL-004/005 in specs/0000_smil.md; source grammar in specs/0001_source_syntax.md; B005/B014 in plans/01_foundation_and_contracts.md. Prior complete design: retired/diagnostics_v1.md.

Result<T> is std::expected<T, Diagnostic>; diagnostics own phase/code/source span/reason. Spans use a source identifier, half-open byte offsets and one-based line/column. Phase names distinguish command-line, parsing, verification, binding, linking and execution; an explicit unknown sentinel is defensive metadata, never successful execution.

parse_command accepts exactly --version or one of parse/verify/bind/link/run followed by one nonempty input path. Other arguments produce CLI001 at <command-line> [0,first-argument-size), line/column 1, reason `expected --version or <parse|verify|bind|link|run> <input>`. Tool identity succeeds independently. Valid stage commands currently return CAP001, phase matching the requested boundary, span covering the input path, and reason `<stage> stage is unavailable`. Exit 2 means unavailable; malformed CLI exits 1. No source file is opened, artifact published or source/runtime success implied. Calling the unavailable-stage helper with version returns CLI002.

One diagnostic emission path logs the originating reason once; main propagates status without repeating it. Unit cases cover exact fields and all command boundaries. examples/answer.smil is a complete target-independent module by inspection against the normative grammar; examples/commands.json records current unavailable observations. Its literal return value is not executed by this scaffold. Later increments replace each unavailable boundary with real demonstrated behavior.
