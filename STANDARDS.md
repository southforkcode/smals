# Project Standards

## Programming Languages

| Language | Standard | Allowed Uses |
| --- | --- | --- |
| Python | 3.13 | Scripts (`./scripts`) and tools (`./tools`) |
| C++ | 23 | Core software development (`./src`) |
| bash | ? | Shell scripts for BSD or Linux operating systems use bash as the scripting language |

See `CODE_STANDARDS.md` for the specified standards for each programming language used in this project.

## Compilers and interpreters

| Compiler | Version |
| --- | --- |
| clang | 21 |
| python | 3.13+ |

## Virtual Environemnts

| Venv | Description |
| --- | --- |
| `uv` | used to establish python venv environment for running python scripts and tools from this project |

## Third Party Tools

If third party binaries are required (e.g., clang), then they must come from established, reputable binary sources, **OR** be built as part of this project (see `thirdparty` folder).

For macOS:
- Apple (as part of Xcode development tools)
- Homebrew (`brew`)

(TODO: specify locations for Linux build platforms and Windows 10 and Windows 11).

## Third Party Libraries / Source

All third party libraries or source are located in `thirdparty`. If it is necessary for the third party library or tool to be built from source for this project, the source is captured as a git submodule, its version is frozen (unless explicitly required to be updated).

**If** a third party library or tool needs to be modified to meet the needs of the project, then the library is forked separately (project fork on github) and tracked in `thirdparty` as a git submodule (of the forked project). Note: this means we treat the source code of forked third-party libraries and/or tools as their own project.
