# SMIL Integer Operations

- Define scalar arithmetic, bitwise operations, comparisons, and integer conversions for every supported positive width.
- Specify exact flags, large-count behavior, and arithmetic faults independently of hardware.

## Sources

- [Guide — Integer Comparisons](../docs/Guide_SMIL.md#integer-comparisons), [Type Casts](../docs/Guide_SMIL.md#type-casts), and [Operation Families](../docs/Guide_SMIL.md#operation-families).
- [Checked execution](0009_checked_execution.md).

## Requirements

| KEY | Requirement |
| --- | --- |
| INT-001 | Every formula below shall use mathematical integers, with `B = 2^N`, `MIN_N = -2^(N-1)`, `MAX_N = 2^(N-1)-1`, `U(x)` the unsigned pattern value, `S(x) = U(x)` below `B/2` and `U(x)-B` otherwise, and `bits_N(k) = k mod B` as an N-bit pattern. |
| INT-002 | Except for shift counts and incoming flags, data operands annotated `[iN]` shall have type `iN` after alias resolution and their primary result shall have type `iN`. Flags shall be explicit `i1` SSA values, with one indicating the named condition; operations shall not read/write implicit processor flags. |
| INT-003 | `add`, `sub`, `mul`, and `neg` shall return `bits_N` of mathematical addition, subtraction, multiplication, or negation. Overflow shall wrap without a fault, saturation, or undefined value. |
| INT-004 | `and`, `or`, and `xor` shall operate on corresponding N bits; `not` shall complement exactly N bits. |
| INT-005 | For unsigned dividend a and nonzero divisor b, `udiv` shall return `bits_N(floor(a/b))`; `urem` shall return `bits_N(a-b*floor(a/b))`, satisfying `0 <= remainder < b`. |
| INT-006 | For signed a and nonzero b, let q be a/b rounded toward zero and r = a-b*q. `sdiv` shall return q when representable; `srem` shall return r with dividend sign when nonzero and `abs(r) < abs(b)`. |
| INT-007 | All division/remainder operations shall cause terminal `integer_divide_by_zero` on zero divisor. `sdiv(MIN_N,-1)` shall cause terminal `integer_divide_overflow`; `srem(MIN_N,-1)` shall return zero without executing a quotient-overflow fault. |
| INT-008 | Shift value operands shall match `[iN]`; counts may have any supported `iM` type. The count k shall be `U(count)` using all M bits without truncation, masking, or reduction modulo N. |
| INT-009 | Zero-count shifts shall return the source. For `0 < k < N`, `shl` shall return `bits_N(U(x)*2^k)`, `lshr` shall return `bits_N(floor(U(x)/2^k))`, and `ashr` shall return `bits_N(floor(S(x)/2^k))`. |
| INT-010 | For `k >= N`, `shl` and `lshr` shall return zero; `ashr` shall return all zeros for nonnegative source and all ones for negative source. Shifts shall not fault for large counts/discarded bits or produce implicit flags. |
| INT-011 | `uadd_carry [iN] a b c` shall require c:`i1` and return `bits_N(t)` then `i1(t >= B)`, where `t = U(a)+U(b)+U(c)`. |
| INT-012 | `usub_borrow [iN] a b c` shall require c:`i1` and return `bits_N(t)` then `i1(t < 0)`, where `t = U(a)-U(b)-U(c)`. A borrow input of one shall subtract one extra unit; hardware carry polarity shall not redefine this flag. |
| INT-013 | `sadd_overflow`, `ssub_overflow`, `smul_overflow`, and `sneg_overflow` shall compute t from signed operands, return `bits_N(t)` then `i1(t < MIN_N or t > MAX_N)`, and never trap merely because overflow is one. |
| INT-014 | `umul_overflow` shall return `bits_N(U(a)*U(b))` then `i1(U(a)*U(b) >= B)`. Unsigned addition/subtraction overflow shall be available using carry/borrow with zero input. |
| INT-015 | `cmp` shall accept two matching integer types and return `i1`: `eq/ne` compare bits; `ult/ule/ugt/uge` compare U values; `slt/sle/sgt/sge` compare S values. Other value kinds shall use their dedicated comparison operations. |
| INT-016 | `zext [iM] x` and `sext [iM] x` shall require `M > N`, retain N source bits, and fill added high bits with zero or the source sign bit respectively. `trunc [iM] x` shall require `M < N` and retain exactly the low M bits without saturation/fault. |
| INT-017 | Same-width signed/unsigned interpretation shall not require a cast or change bits. Wrong-direction/equal-width extension/truncation and incorrect flag/result types or counts shall be statically rejected. |
| INT-018 | These definitions shall apply to `i1`, sub-byte, non-power-of-two, and non-native widths. Backends/helpers shall normalize hardware shifts, division, remainder, and flags when hardware semantics differ. |
| INT-019 | Arithmetic faults shall terminate at the operation with no result, catchable payload, new normal CFG edge, or cleanup promise. Zero-divisor checking shall precede quotient overflow and helper/work-buffer reservation. |
| INT-020 | Transformations shall preserve arithmetic faults and prior effects. A possibly faulting unused operation shall not be deleted or speculated onto another path without proof; replacing signed division by arithmetic shift shall correct the rounding difference when needed. |
| INT-021 | The core shall reject the obsolete/ambiguous operation spellings `div`, `mod`, and `shr`; users shall specify division/remainder signedness and right-shift kind. |

## Required conformance observations

| Operation/input | Required result |
| --- | --- |
| `add i8 255,1`; `neg i8 -128` | `0x00`; `0x80`, without faults. |
| Signed `(7,3)`, `(-7,3)`, `(7,-3)`, `(-7,-3)` division/remainder | `(2,1)`, `(-2,-1)`, `(-2,1)`, `(2,-1)`. |
| Signed i8 `(-128,-1)` | Division faults; remainder zero. |
| Signed i1 `(-1,-1)` | Division overflows; remainder zero. |
| `lshr i8 0xff` with i16 count 256 | Zero, using the full count. |
| `ashr i8 -5,1`; `sdiv i8 -5,2` | Signed -3; signed -2. |
| `ashr i8 -5,8`; i8 count spelled `-1` | All ones; count interpreted as 255. |
| `uadd_carry i8 255,1,0`; `usub_borrow i8 0,1,0` | `(0,1)`; `(255,1)`. |
| `sadd_overflow i8 127,1`; `sneg_overflow i8 -128` | `(0x80,1)`; `(0x80,1)`. |
| `umul_overflow i8 255,2`; `smul_overflow i8 -1,2` | `(0xfe,1)`; `(0xfe,0)`. |
| Zero/sign extend i1 one to i8 | `0x01` / `0xff`. |
| Truncate i8 `0xfb` to i4 | `0xb`, without a trap. |

The same cases shall be checked in constant evaluation where their operations are admitted, expanded/native execution, and helper execution. Conformance shall include widths 1, 3, 12, 24, and 64 rather than only machine-native widths.
