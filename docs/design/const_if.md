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

An unused plain helper may need an enclosing caller for a selected
`return ... from`. Its standalone check then defers without reporting an error.
The whole speculative specialization transaction is quarantined, including
completed recursive members, so later real callers check fresh bodies in their
own context. An exported entry must supply a valid context itself; its error
is reported independently of errors in other functions.

The [deferred-state audit](const_if_deferred_state.md) records variable proof
marks, shared type caches and the corresponding rollback rules.

Unused immutable scalar/string literal globals that no live checked body or
global initializer names introduce no generated storage. Other global
initializers still run in source order, including side effects and their
dependencies.

Run `python test/const_if.py path/to/goose --core-only` for this layer.
