# Native compile-time definitions

`--define NAME=VALUE` supplies an immutable Goose literal in the compiler-owned
`build` namespace. Repeat it for multiple names:

```sh
goose check --define DEBUG=true --define WORKERS=8 main.goose
goose run --define DEBUG=false --define 'LABEL="release"' main.goose
goose build --define DEBUG=false --define WORKERS=8 main.goose
```

Use `build::DEBUG`, `build::WORKERS`, and `build::LABEL` as Goose values. This
also works for compile-time integer sizes and `const for` sources. Definitions
never become C macros or global variables. Unused values emit no data.
`-DNAME=VALUE` retains its existing, separate generated-C macro behavior.

String definitions also supply compile-time string arguments, directly or
through immutable global aliases. For example, `embed_file(build::DATA_FILE)`
accepts `--define 'DATA_FILE="module.wasm"'`; the file remains relative to the
Goose source containing the call. `embed_shader` accepts string definitions for
its stage and source text too. Local variables and mutable globals retain their
existing restrictions in these compile-time APIs.

Names are ASCII identifiers other than language keywords. Values are `true`,
`false`, decimal integers from -9223372036854775808 through
18446744073709551615, or double-quoted string literals with Goose escapes.
Integers have type `i64`, or `u64` above `i64.max`; explicit Goose conversions
follow ordinary language rules. An optional leading sign is accepted. Other
expressions, floating-point values, overflow, missing values, duplicate names,
and source declarations in namespace `build` are errors.

Definitions belong to one compilation, including its imports and every worker
specialization. Every multi-test compilation and language-server analysis gets
a fresh symbol table. The compiler has no persisted type-layout or specialization
cache. Generated programs are regenerated on every build; the native runtime
and package caches contain C services, not Goose specializations.
Native intermediates have a configuration-specific subdirectory; definition
order does not change its identity. Builds sharing one directory serialize
the generated-C write and native link, preventing concurrent configurations
from compiling each other's source. Output executable paths remain the
caller's responsibility: use distinct `-o` paths for concurrent deliverables.

Start an editor server with the same configuration, for example
`goose lsp --define DEBUG=true --define WORKERS=8`. Restart it to change that
configuration. Definitions are compilation inputs: build systems must include
them in artifact cache keys. A type whose fields depend on configuration is
not automatically ABI-compatible with that type from another configuration.

Benchmark execution and discovery (`goose++ bench file.goose [--list]`) supply the string
`build::BENCH_SIZE` independently for each selected size (`medium` by default;
`--sizes` accepts a duplicate-free subset of small,medium,large in canonical
order). An explicit `--define BENCH_SIZE=...` on bench is a duplicate definition.
Ordinary build/check/run/dump acquire no implicit value and may define it
explicitly. Source owns the size mapping through ordinary expressions or
existing `const if`; discovery adds no constant evaluator or source rewriting.


## Conditional packed-word layouts

`const if` also selects fields inside `packed word` declarations. Selected
fields determine bit offsets, constructor arguments and defaults. Excluded
fields consume no bits; reserve their width in an `else` when later positions
must stay fixed. The checker records a compilation-local layout fingerprint
including enum ordinal mappings. It is not an automatically enforced wire
protocol identifier: applications must version persisted formats and agree
on definitions across FFI boundaries. The width of the backing alone does not
prove compatible field meanings. Editor servers need the same `--define`
arguments as builds. Command-line integer definitions remain limited to
[-2^63, 2^64-1]. Packed words introduce no new scalar integer type or literal
range; u128 backings are deferred.

## Compile-time scalar functions

Declare a compile-time-only helper with `const fn`. Its explicit parameters and
one result must use literal `bool` or `u64` types. Its body contains exactly one
`return expression;`:

```goose
const fn needs_edges(edges: bool, paths: bool) -> bool {
    return edges || paths;
}
const NEED_EDGES: bool =
    needs_edges(build::FACT_BUILD_EDGES, build::FACT_BUILD_PATHS);
```

Run this example with both independent inputs, for example
`goose++ check --define FACT_BUILD_EDGES=false --define FACT_BUILD_PATHS=true main.goose`.
Use `NEED_EDGES` in an ordinary `const if`; do not pass a derived NEED definition
on the CLI. Only the selected branch is checked and emitted, including at O0.

Bodies accept scalar literals, their own parameters, scalar operators, direct
calls to other marked helpers, and expression `if` with two expression arms.
Both arms must have the same scalar kind and are checked even when unselected;
only the selected arm incurs value faults. `&&` and `||` evaluate both operands,
as the existing constant boolean evaluator does. Integers inside helpers are
u64; arithmetic wraps and shift counts are masked according to existing u64
constant rules. Negative literals and casts inside helpers are rejected.

Helpers cannot read globals or `build::` names: pass inputs explicitly. They
cannot use statements, locals, loops, strings, aggregates, layout operations,
generics, overloads, aliases in signatures, defaults, or declaration modifiers.
Calls accept constant scalar expressions, including eligible immutable globals
and build inputs; integer arguments must fit u64. Runtime locals remain invalid.

Calls work in existing scalar constant contexts: conditional bodies, fields and
constructors, array sizes/capacities/fill counts, integer pattern bounds, and
integer entries of `const for <N> in [expressions]`. A typed scalar global
`const` initializer can materialize a computed bool/u64 for ordinary runtime
reads. Array tables use ordinary array syntax with those named scalar results;
see [the fixed width-table sample](../samples/compile_time_functions/main.goose).
Local initializers, array elements, and field defaults must refer to named
results instead of calling a helper directly. Helpers have no runtime function
value, prototype, body, or startup call at any optimization level.

Each declaration permits at most 16 parameters. A request permits 32 active
calls and 10,000 scalar evaluator visits, shared across nested calls and global
arguments. Taking an active call cycle is an error; an unselected well-typed
self-call is allowed. No results are cached across configurations or LSP source
snapshots. Source initializers remain available after scalar normalization.
