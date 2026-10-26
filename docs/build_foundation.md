# Build foundation

Sources: [standards](../STANDARDS.md), [build/evidence plan](../plans/01_foundation_and_contracts.md#b002), and [host policy](../AGENTS.md#build-hosts-and-portability).

Use portable CMake targets: one static library `smil_core`, exporting its include directory and C++23 requirement; one dependency-free test executable `smil_tests`, linked to that library. The initial library exports the tool version; this is compiler build identity and does not imply source or target support. CTest has a positive version check and an expected process-failure witness; direct execution must also demonstrate nonzero status. Select clang 21 externally via the host-local toolchain pins; reject other compiler major versions during configuration. No hard-coded host paths enter shared configuration.

Build in fresh `build/smil`, preserving preexisting `build/` artifacts. Later increments extend the test executable and acceptance gates. Test failures are return values and diagnostics; no external test dependency is introduced. Build acceptance includes formatting/linting; B003 will make these explicit build targets. Before then run the qualified tools directly on changed units.

macOS is primary. For each Linux architecture, configure and execute separately in an identified container with clang 21. Record unavailable environments as missing evidence and bounded follow-up work. Windows is untested here; recipe: `cmake -S . -B build/smil -G Ninja -DCMAKE_CXX_COMPILER=clang++`, `cmake --build build/smil`, `ctest --test-dir build/smil --output-on-failure`, and `build/smil/smil_tests.exe --fail` (last command must exit 1). Choose qualified local executables; do not infer Windows results from another host.
