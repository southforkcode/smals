# SMIL Source Syntax

- Define the exact `smil.source.v1` textual language.
- Make tokenization, statement boundaries, and result bindings independent of target selection.

## Sources

- [Guide_SMIL.md — Source Text, Lexical Rules, and Grammar](../docs/Guide_SMIL.md#source-text-lexical-rules-and-grammar).
- [Scope and conformance](0000_smil.md).

## Requirements

| KEY | Requirement |
| --- | --- |
| SYN-001 | A source consumer shall select `smil.source.v1` through its documented interface or build settings; it shall not infer a dialect from a CPU, filename, or host language. |
| SYN-002 | Source shall be valid UTF-8 containing Unicode scalar values. A BOM shall be accepted and ignored only at the start. Malformed encoding, surrogate scalars, and out-of-range code points shall be rejected without replacement. |
| SYN-003 | Physical newlines shall be LF or CRLF, with CRLF counted once. A standalone CR shall be rejected. Outside strings/comments, horizontal whitespace shall consist only of ASCII space and tab. Indentation shall have no syntactic effect. |
| SYN-004 | `//` shall introduce a comment through the physical newline or EOF without consuming its statement boundary. Quotes/backslashes in comments shall have no special effect. Block comments, `#` comments, preprocessing, includes, and macros shall be rejected. |
| SYN-005 | Ordinary names shall match ASCII `[A-Za-z_][A-Za-z0-9_]*` and be case-sensitive. Sigils shall immediately precede their names: `@`, `$`, `%`, and `^` for value/type binders, constants, SSA values, and blocks respectively. |
| SYN-006 | Numeric SSA names shall use `%0` or `%` followed by a nonzero decimal digit and further decimal digits. Numeric names shall not imply register slots or automatic numbering. Other sigiled namespaces and qualifiers shall not admit numeric names. |
| SYN-007 | A qualified name shall contain exactly one `alias::member`, with one optional value/constant sigil before the alias and no internal whitespace, comment, or continuation. SSA and block names shall not be qualified. |
| SYN-008 | Tokens shall use maximal munch. Bare `i[0-9]+` shall be an integer-type token or malformed-width diagnostic, never an ordinary-name fallback. Import aliases shall not be built-in integer-type tokens. |
| SYN-009 | Type-name positions shall exclude `ptr`, `fnptr`, `varargs`, and the `i[0-9]+` family, including declaration binders and type exports. Other keywords/opcodes shall be contextual lowercase spellings; sigiled names such as `@add` shall be permitted. |
| SYN-010 | Integer types shall use canonical positive decimal widths, `i[1-9][0-9]*`. Widths shall be parsed mathematically without host-width truncation; `i0` and `i08` shall be rejected. |
| SYN-011 | Integer tokens shall be optional adjacent `-` followed by canonical decimal digits or lowercase `0x` and one or more hexadecimal digits. Negative zero and either case of hex digits shall be accepted. Leading `+`, decimal leading zeros, separated minus, suffixes, digit separators, binary/octal/floating notation shall be rejected. |
| SYN-012 | Field indices shall use canonical unsigned decimal tokens without a minus or hexadecimal prefix. Computation scalar literals shall be typed and bracketed; bare integer value operands shall be rejected. |
| SYN-013 | Strings shall be double-quoted and admit JSON escapes for quote, backslash, slash, backspace, form feed, newline, carriage return, tab, and four-hex-digit Unicode escapes. Raw controls/newlines, invalid escapes, and isolated surrogate escapes shall be rejected; adjacent escaped surrogate pairs shall decode to one scalar. |
| SYN-014 | Decoded identifier strings shall be nonempty and contain no NUL. Equality, duplicate detection, hashing, and lifecycle ordering shall use decoded scalar sequences without normalization or case folding, rather than escape spelling. A trap identifier shall additionally begin with `user.` and have a nonempty suffix. |
| SYN-015 | Adjacent strings shall not concatenate. Raw/triple-quoted strings, character literals, `\\xNN`, brace Unicode escapes, string splicing, and string-valued computation operands shall be rejected. Strings shall not allocate storage. |
| SYN-016 | Significant newline shall end a simple statement. EOF shall supply a final boundary when delimiters are balanced. Blank/comment-only logical lines shall be allowed; semicolons and multiple independent statements on one logical line shall be rejected. |
| SYN-017 | Newlines in parentheses, brackets, record field/initializer braces, and switch-case braces shall be whitespace. Function-body braces shall preserve statement boundaries. Delimiters shall match; lists shall require commas and prohibit trailing commas. |
| SYN-018 | A function opening brace shall occur on its header's logical line. Its opening brace, each block-header colon, and every operation/terminator shall be followed by a logical newline. A function closing brace shall occupy its own logical line. |
| SYN-019 | Outside strings/comments, a backslash followed by optional spaces/tabs, optional `//` comment, and a physical newline shall join exactly that newline as separating whitespace. A final backslash at EOF shall be rejected. Continuation shall not join token fragments. |
| SYN-020 | Clauses such as `init`, `after`, `shutdown`, `space`, `abi`, `raises`, `normal`, and `except` shall not imply continuation. Indentation or an unfinished statement shall not imply continuation. |
| SYN-021 | The complete grammar below shall define the accepted module, fragment, declaration, operation, and terminator forms. Unknown operations/clauses and unlisted operand annotations shall be rejected. |
| SYN-022 | Publishable source shall use the module start rule with an explicit header. Anonymous verification units shall use the separate fragment start rule and shall not be published as interfaces/objects. Top-level computation statements shall not be module items. |
| SYN-023 | One-result operations shall bind one SSA name; pair-result operations shall bind two in specified order; zero-result operations shall have no binding. Calls shall bind exactly their resolved result count. There shall be no implicit result discard or discard placeholder. |
| SYN-024 | Parenthesized constant expressions shall exclude SSA operands syntactically. Local aggregate initializers shall permit SSA operands only through the local-initializer production. Parsing shall not weaken this distinction based on optimization proofs. |
| SYN-025 | The parser shall preserve unresolved named types for later resolution. Semantic verification shall reject invalid literal payload kinds, result counts, types, names, dominance, and target requirements even when their syntax parses. |

## Required conformance observations

| Input distinction | Required outcome |
| --- | --- |
| LF versus CRLF, initial BOM, absent final newline | Same parsed meaning. |
| `%0` versus `%00`; `i8` versus `i08`; `[i8 -1]` versus `[i8 - 1]` | First form accepted; second form rejected. |
| Equivalent literal/escaped identifier strings | Same semantic identifier and duplicate detection. |
| Comment containing a backslash | Physical newline still ends the statement. |
| Multiline record/switch list versus multiline function body | Group newlines ignored; function operation boundaries retained. |
| `[i8 256]`; runtime `udiv` by zero; constant-expression `udiv` by zero | Parse then range rejection; runtime fault if reached; static evaluation rejection, respectively. |
| Missing `access(...)`, missing `seq_cst`, reordered callable clauses, missing terminator | Rejected by the specified grammar. |

## Complete grammar

The following finite grammar is normative under SYN-021. Its `list<X>` and `value-operation<V>` abbreviations have only the substitutions described in the block. Token and logical-line rules above govern its terminals.

```text
(* SMIL source grammar v1. Token and logical-line rules are normative in this specification.
   X? = optional; X* = repetition; X+ = one or more; | = alternatives.
   list<X> = X ("," X)*. No trailing commas. U+000A is logical EOL.
   Operation productions parameterized by V are instantiated twice:
     value-operation<value>, value-operation<constant>.
   This finite substitution is notation, not an open operand category.
   Group interiors ignore EOL; function-body braces preserve it.
   EOF implies one EOL when needed; blank EOLs may occur between statements.
*)
module = EOL* module-header EOL+ target-directive? import-directive* module-item* EOF ;
module-header = "module" STRING ;
fragment = EOL* target-directive? import-directive* module-item* EOF ;
target-directive = "target" STRING EOL+ ;
import-directive = "import" STRING "as" NAME EOL+ ;
module-item = (type-declaration | constant-definition | global-definition
             | function-declaration | export-directive | startup-definition) EOL+
             | function-definition ;
export-directive = "export" ("type" TYPE_NAME | LOCAL_CONSTANT | LOCAL_SYMBOL) ;

type-declaration = LOCAL_TYPE_SYMBOL "=" ("type" type-expression
                                   | "record" "{" list<type>? "}") ;
constant-definition = LOCAL_CONSTANT "=" "const" constant ;
global-definition = LOCAL_SYMBOL "=" "global" mutability type-expression
                    (constant | dynamic-initializer) space-clause? ;
mutability = "mutable" | "immutable" ;
space-clause = "space" "(" NAME ")" ;
dynamic-initializer = "dynamic" symbol "init" "(" STRING ")"
                      after-clause? shutdown-clause? ;
startup-definition = "startup" STRING symbol after-clause? shutdown-clause? ;
after-clause = "after" "(" list<STRING> ")" ;
shutdown-clause = "shutdown" symbol ;

type-expression = "[" type "]" ;
type = INTEGER_TYPE | TYPE_NAME | QUALIFIED_NAME
       | "ptr" NAME? type-expression
       | "fnptr" signature abi-clause? raises-clause?
       | "varargs" ;
signature = "(" fixed-parameters? ")" "->" "(" list<signature-entry>? ")" ;
fixed-parameters = "..." | list<signature-entry> ("," "...")? ;
signature-entry = type-expression extension-attribute? ;
extension-attribute = "signext" | "zeroext" ;
abi-clause = "abi" "(" STRING ")" ;
raises-clause = "raises" "(" type-expression ")" ;

symbol = LOCAL_SYMBOL | QUALIFIED_SYMBOL ;
constant-name = LOCAL_CONSTANT | QUALIFIED_CONSTANT ;
value = SSA | constant ;
constant = constant-name | symbol | typed-constant | "(" value-operation<constant> ")" ;
typed-constant = "[" type (INTEGER | "null" | "zero" | "{" list<constant>? "}") "]" ;
local-initializer = SSA | constant-name | symbol
                  | "(" value-operation<constant> ")"
                  | "[" type (INTEGER | "null" | "zero"
                             | "{" list<local-initializer>? "}") "]" ;
field-path = "field" "(" list<INDEX> ")" ;

function-declaration = "declare" LOCAL_SYMBOL signature abi-clause? raises-clause? ;
function-definition = "func" LOCAL_SYMBOL signature abi-clause? raises-clause?
                      "{" EOL+ entry-block block* "}" EOL+ ;
entry-block = block-header EOL+ (type-declaration EOL+)*
              (local-storage EOL+)* (ordinary-statement EOL+)* terminator EOL+ ;
block = block-header EOL+ (ordinary-statement EOL+)* terminator EOL+ ;
block-header = BLOCK "(" list<parameter>? ")" ":" ;
parameter = SSA ":" type-expression ;
local-storage = SSA "=" "alosf"
                ("mutable" type-expression local-initializer?
                 | "immutable" type-expression local-initializer) ;
result-binding = list<SSA> "=" ;
ordinary-statement = SSA "=" single-computation
                     | SSA "," SSA "=" pair-computation
                     | result-binding? call-operation
                     | effect-operation ;

(* Exactly these single-result forms are allowed in constant expressions.
   V = constant in parentheses; V = value in ordinary computation. *)
value-operation<V> = binary-integer type-expression V V
                    | unary-integer type-expression V
                    | "cmp" predicate V V
                    | conversion type-expression V
                    | "record_make" type-expression "(" list<V>? ")"
                    | "record_get" V field-path
                    | "record_set" V field-path V
                    | "field_addr" V field-path
                    | ("ptr_eq" | "ptr_ne" | "ptr_offset" | "fn_eq" | "fn_ne") V V
                    | "ptr_diff" type-expression V V
                    | ("sizeof" | "alignof") type-expression type-expression
                    | "offsetof" type-expression type-expression field-path
                    | "fnaddr" symbol ;
binary-integer = "add" | "sub" | "mul" | "udiv" | "urem" | "sdiv" | "srem"
                 | "xor" | "and" | "or" | "shl" | "lshr" | "ashr" ;
unary-integer = "neg" | "not" ;
conversion = "sext" | "zext" | "trunc" | "ptrcast" | "ptrtoint" | "inttoptr" | "addrspacecast" ;
predicate = "eq" | "ne" | "ult" | "ule" | "ugt" | "uge" | "slt" | "sle" | "sgt" | "sge" ;

single-computation = value-operation<value>
              | ("load" | "load_unaligned") type-expression value
              | "mmio_load" type-expression value access-clause
              | "atomic_load" type-expression value atomic-order
              | "atomic_rmw" atomic-kind type-expression value value atomic-order
              | "va_count" type-expression value
              | ("va_is" | "va_get") type-expression value value ;
pair-computation = ("uadd_carry" | "usub_borrow") type-expression value value value
              | binary-overflow type-expression value value
              | "sneg_overflow" type-expression value
              | "atomic_cmpxchg" type-expression value value value atomic-order ;
binary-overflow = "sadd_overflow" | "ssub_overflow" | "smul_overflow" | "umul_overflow" ;
effect-operation = ("store" | "store_unaligned") value value
                   | "mmio_store" value value access-clause
                   | "mmio_fence" access-clause
                   | "atomic_store" value value atomic-order
                   | "atomic_fence" atomic-order
                   | "on_exit" value ;
access-clause = "access" "(" STRING ")" ;
atomic-order = "seq_cst" ;
atomic-kind = "xchg" | "add" | "sub" | "and" | "or" | "xor" ;

call-operation = "call" symbol "(" call-arguments? ")"
                 | "call_indirect" value "(" call-arguments? ")" ;
call-arguments = "..." SSA | list<value> ("," "..." SSA)? ;
edge = BLOCK "(" list<value>? ")" ;
terminator = "br" edge
             | "br_if" value "," edge "," edge
             | "return" list<value>?
             | ("invoke" symbol | "invoke_indirect" value)
                 "(" call-arguments? ")" "normal" edge "except" edge
             | "switch" type-expression value "default" edge
                 "{" list<switch-case>? "}"
             | "raise" value
             | "trap" STRING
             | "exit" value ;
switch-case = constant ":" edge ;

(* Lexical terminals, scanned by maximal munch before the token grammar.
   NAME = ASCII [A-Za-z_][A-Za-z0-9_]* (contextual keywords).
   TYPE_NAME = NAME except ptr/fnptr/varargs and the reserved i[0-9]+ family.
   INTEGER_TYPE = i[1-9][0-9]*; i0 and leading-zero widths are invalid bare tokens.
   DECIMAL = 0 | [1-9][0-9]*; HEX = 0x[0-9A-Fa-f]+.
   INTEGER = -?(DECIMAL | HEX); INDEX = DECIMAL without a minus.
   SSA = %NAME | %DECIMAL; BLOCK = ^NAME.
   LOCAL_SYMBOL = @NAME; LOCAL_TYPE_SYMBOL = @TYPE_NAME; LOCAL_CONSTANT = $NAME.
   QUALIFIED_NAME = NAME::NAME with no internal whitespace/comments/continuations.
   QUALIFIED_SYMBOL = @QUALIFIED_NAME; QUALIFIED_CONSTANT = $QUALIFIED_NAME.
   STRING = double-quoted JSON-style escapes, decoded to Unicode scalar values;
            no raw control/newline, invalid escape, or isolated surrogate.
   EOL = significant LF after source/continuation/group processing.
   EOF = end of source. Comments are // through the next physical newline.
*)
```
