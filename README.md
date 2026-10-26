# Scope

This project implements a multi-platform, cross-platform set of tools for small (and other) machines.

 - 8 bit architectures like `8080`, `6502`, `65c02`
 - 16 bit architectures like `8086`, `65816`, `6800`
 - 32 bit architectures like `68000`, `i286`
 - 64 bit architectures like `arm64`, modern *Intel* processors

The focus is on the small architectures not well supported by modern tools like *LLVM*.

This project supports both big-endian and little-endian platforms.

## Architecture

In general, this tool provides tools for compiling high-level languages like C++ and low-level languages like assembly.

The basic design requires conversion of high-level languages into Intermediate Language (IL), then into implementation (binary code).

Note that optimization for code size or code speed are done through typical graph analysis and compaction. However, it is done where useful. For example, loop unrolling may not be useful for 6502 due to limits on code size, but may be useful for 68000.

```
+----------------------+
| High Level Languages |
| E.g., C++, C, Pascal |
+----------------------+
           |
           V
+----------------------+
|   SMAls IL (SMIL)    | 
+----------------------+
          |
          V
+----------------------+
|  SMIL Assembler and  | This is a SMIL-to-Object Code backend per architecture.
|  Optimizer (SMASh)   | "Smashes" an IL file into object file.
+----------------------+
          |
          V
+----------------------+   +----------------------+
| Machine Code Objects |<--|      Assemblers      |
+----------------------+   +----------------------+
          |
          V
+----------------------+
|       Linker         |
+----------------------+
          |
          V
+----------------------+
| Executables / Libs   |
+----------------------+
```

## SMIL

Pronounced like the English word noun and verb, "smile". SMIL is an intermediate language used to compile high-level languages into machine code by providing an abstract machine language that can be assembled into supported architectures.

Compiling into SMIL provides an opportunity for non-architecture specific optimizations. Compiling from SMIL to real machine code (RMC) is also a place where architecture/processor specific optimizations can be applied.

It is **the goal** of this project to allow any SMIL to be convertible to RMC for any platform. This means, while not practical, an 8-bit machine could support a 64-bit divide operation. This fixes the design of the IL. It's not over-fitted to modern or archaic architectures. It is designed to generalize machine operations and be translatable to specific machines.

Why not *LLVM*?
- It doesn't support small machines.
- It is very complex, but very powerful.
- It is the right thing to use for modern architectures.
- This project is focused on the forgotten platforms, with an eye towards experimentation, imagination, and learning.
- We probably *could* extend LLVM for small machines. But the goal is for me to learn about bulding a LLVM-like system of compilers, and I think it will be better for smaller machines outside the LLVM environment (hypothesis).
