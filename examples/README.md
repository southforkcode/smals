# First complete module

answer.smil follows the complete module/function/entry/return productions in specs/0001_source_syntax.md and exports a function returning the typed i32 literal 42. It has no placeholders or target binding. The scaffold CLI can be invoked with `smil verify examples/answer.smil` (likewise parse/bind/link/run), but currently reports CAP001 / unavailable, exit 2. commands.json records these actual expectations; successful SMIL parsing or execution is not claimed. Use `smil --version` for the available tool-identity command.
