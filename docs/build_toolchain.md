# Build toolchain

The [project standards](../STANDARDS.md) require clang 21 and C++23. Tool qualification follows the [bootstrap plan](../plans/01_foundation_and_contracts.md#bt01); it does not qualify generated SMIL programs or their target CPUs.

## macOS compiler pin

Use the Apple Command Line Tools executables below for subsequent local acceptance commands. Resolve neither an arbitrary `clang++` on PATH nor a newly selected Xcode installation without requalification. The [BT01 receipt](../plans/evidence/BT01.md) records executable hashes, provenance and positive/negative observations.

| Setting | Pinned value |
| --- | --- |
| C compiler | `/Library/Developer/CommandLineTools/usr/bin/clang` |
| C++ compiler | `/Library/Developer/CommandLineTools/usr/bin/clang++` |
| Version | Apple clang version 21.0.0 (`clang-2100.3.34.2`) |
| Host target | `arm64-apple-darwin27.0.0` |
| Source | Apple Command Line Tools; Apple code-signing chain |
| Language | `-std=c++23` |
| SDK | `/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk`, version 27.0; pass `-isysroot` for direct compiler invocations |

When the CMake build is implemented in B002, select these explicitly on a fresh build directory:

```sh
/opt/homebrew/Cellar/cmake/4.4.4/bin/cmake -S . -B build/smil \
  -DCMAKE_C_COMPILER=/Library/Developer/CommandLineTools/usr/bin/clang \
  -DCMAKE_CXX_COMPILER=/Library/Developer/CommandLineTools/usr/bin/clang++ \
  -DCMAKE_OSX_SYSROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk
```

This is a host-local selection, not a hard-coded shared CMake setting. Other hosts supply their own qualified clang 21 paths. A compiler, SDK or developer-directory change requires rerunning the small qualification before relying on the receipt. The smoke cases exercise C++23 language selection, compile/link/run, standard-library error values, and rejection of an invalid compile-time condition. Direct invocation initially failed to find `cstdio` without an SDK; the explicit SDK makes both cases discriminating. No compiler installation, shared build configuration or product design changes are needed for this existing tool.

## macOS CMake pin

[BT02](../plans/01_foundation_and_contracts.md#bt02) qualifies the existing Homebrew CMake installation. Use `/opt/homebrew/Cellar/cmake/4.4.4/bin/cmake`, version **4.4.4**, for subsequent local acceptance commands, including the future B002 command above. `/opt/homebrew/bin/cmake` and `/opt/homebrew/opt/cmake` currently resolve to that keg; use the versioned executable so a Homebrew relink does not silently select another version.

The [BT02 receipt](../plans/evidence/BT02.md) records Homebrew package provenance, executable/receipt hashes, and known-good/known-bad script invocations. Requalify after replacing the executable or its installed CMake modules. This pin is host-local; no shared build configuration or compiler design changes are needed. B002 will supply and validate the actual project configuration and build.

For later Windows qualification, select an approved CMake installation and run the receipt's two scripts with its full executable path:

```powershell
& $CMake --version
& $CMake -P good.cmake
if ($LASTEXITCODE -ne 0) { throw 'CMake smoke failed' }
if ((Get-Content -Raw good-result.txt) -ne "42`n") { throw 'Incorrect result' }
& $CMake -P bad.cmake
if ($LASTEXITCODE -eq 0) { throw 'Unknown command was accepted' }
if (Test-Path bad-result.txt) { throw 'Execution continued after invalid input' }
```

Use a fresh directory and retain the unknown-command diagnostic. This recipe is unexecuted; it provides no Windows evidence.

## Other build hosts

Linux x64 and ARM64 and Windows x64 are untested by this macOS tool qualification. No shared build or platform adapter changes are included. Later build work follows the [host matrix](../AGENTS.md#build-hosts-and-portability).

For later Windows execution, select an approved clang 21 installation, record `clang++ --version`, then run the smoke fixture from the BT01 receipt:

```powershell
& $Clangxx -std=c++23 -Wall -Wextra -Werror good.cpp -o good.exe
if ($LASTEXITCODE -ne 0) { throw 'Compilation failed' }
.\good.exe
if ($LASTEXITCODE -ne 0) { throw 'Smoke execution failed' }
& $Clangxx -std=c++23 -Wall -Wextra -Werror bad.cpp -o bad.exe
if ($LASTEXITCODE -eq 0) { throw 'Invalid source was accepted' }
if (Test-Path bad.exe) { throw 'Invalid source produced an executable' }
```

Use a fresh output directory, verify the expected `clang smoke: 42` output, and retain the static-assert diagnostic. This is an unexecuted recipe, not Windows evidence; the future B002 build receipt must record actual host coverage and any bounded follow-up obligations.

## macOS Python pin

BT03 provisions Homebrew `python@3.13` 3.13.18. Use `/opt/homebrew/Cellar/python@3.13/3.13.18/Frameworks/Python.framework/Versions/3.13/bin/python3.13` for project scripts; uv environments must use Python 3.13. Source: Homebrew core bottle, installed with `HOMEBREW_NO_AUTO_UPDATE=1 brew install python@3.13`. Requalification is required after changing the installation. [Qualification receipt](../plans/evidence/BT03.md). No shared build or design change.

## macOS clang-format pin

Use `/Library/Developer/CommandLineTools/usr/bin/clang-format` (Apple 21.0.0 (clang-2100.3.34.2)). Source: Apple Command Line Tools, verified Apple signature chain. Requalify on replacement. [Receipt](../plans/evidence/BT04.md). This is a host-local tool selection.

## macOS clang-tidy pin

Use `/opt/homebrew/Cellar/llvm@21/21.1.8_1/bin/clang-tidy` (21.1.8 (Homebrew llvm@21 21.1.8_1)). Source: existing Homebrew core llvm@21 bottle; no installation. Requalify on replacement. [Receipt](../plans/evidence/BT05.md). This is a host-local tool selection.
