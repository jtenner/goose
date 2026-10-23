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
