# Native `const if`

`const if condition { ... } else { ... }` selects a branch at specialization
time. Both branches must parse. Only the selected branch is name-resolved,
typechecked, expanded and emitted, including at `-O0`. A missing `else` is an
empty block. Nested conditions and `else if` chains are supported in function
bodies. Each selected body is an ordinary lexical block: its variables do not
escape it, and returns, breaks and continues retain their enclosing targets.
A value-producing selected branch may be used as an expression.

Conditions must be bool constants. Supported forms are bool literals, immutable
global named constants, native `build::NAME` definitions, `!`, `&&`, `||`, bool/string
equality, and comparisons of supported integer constant expressions. Integer
arithmetic uses the same evaluator, widths, overflow checks and diagnostics as
array extents. This is not a general compile-time interpreter: calls, runtime
values and local variables (including `let` variables and parameters) cannot
be conditions. Lexical shadowing of a global is respected. Both operands of
`&&` and `||` must be valid constant expressions, even if the result is already
known. An undefined build definition is an error; use an explicit value such as
`--define DEBUG=false`.

```
fn trace<T>(value: T) {
    const if build::DEBUG { print(value); }
    else { const if false { unavailable(value); } }
}
```

A condition inside a `const for` is evaluated separately after that entry's
bindings are substituted. Generic function specializations keep independent
selected bodies. Types in the excluded arm, including qualified names, alias
uses and enum variants, produce no semantic diagnostics. Syntax errors in
those arms still fail compilation. Parse-level dumps preserve both arms.

## Conditional fields

A struct field list may contain conditional blocks, nested to any supported
parser depth. Commas separate ordinary fields and conditional blocks. Each
block may be empty and its `else` may be omitted. Ordinary field qualifiers,
defaults and explicit `pad` entries work within a selected block.

```
struct Record<T> {
    a: u32,
    const if build::DEBUG { let diagnostics: u64 = 0, } else {},
    z: T,
}
```

The compiler selects and flattens fields before declaration checking and
layout. Conditions may depend on build definitions or global constants, but
must not depend on the struct's type parameters. Generic structs with
configuration-dependent fields are supported. Duplicate names are rejected
among the selected fields. An excluded field has no type, offset, bytes,
default, accessor or reflection entry in the effective type. `fields<T>`
enumerates effective non-pad fields in declaration order.

Layouts remain packed: the compiler inserts no automatic alignment padding.
For `u32 a`, optional `u64 b`, `u32 z`, the layout is 8 bytes without `b` and
16 bytes with it; `z` is at offset 4 or 12. Use explicit `pad` declarations
where alignment is required. A struct with no effective fields still occupies
one byte, as other empty Goose structs do. Atomic/shared subsystems must check
alignment against the selected effective layout; const-if selection does not
make a packed atomic field aligned.

These configurations are ABI incompatible. Every module, native consumer,
serialized-data producer and reader that exchanges such a type must use the
same definitions. There is no automatic cross-configuration compatibility or
layout padding. Applications that exchange persisted or external data should
version their format or validate a layout fingerprint, including total size,
field order and field offsets, before reading it. The acceptance tests exercise
such fingerprints using `bytes_of` and alternate configurations repeatedly.

Run `python test/const_if.py path/to/goose` for both optimization levels,
configuration switching, excluded-code checks in emitted C, layouts,
constructors and rejection cases. `--core-only` isolates function branches;
`--fields-only` additionally tests conditional layouts.
