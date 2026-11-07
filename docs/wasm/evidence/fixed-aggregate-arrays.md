# Memory 0 fixed aggregate arrays

This Stage D increment adds explicit literals and exact fresh copies of fixed
aggregate arrays. The full backend and performance acceptance remain open.
The parent is `0d64e43d32f17485526beef0d463e9c9abad9102`.

## Admitted behavior

Fixed and static-capacity limited arrays can contain positive-stride fixed
structs, enums and selected standalone variants. Headers and elements stay in
Memory 0. Shared bounded layouts define packed strides, count prefixes and
child ranges. Each literal element finishes before the next expression runs.
Limited literals store their checked final count before their elements, as the
native backend does. An owned-name element copy uses direct Memory 0
`memory.copy` without adding scratch locals for each element.

Indexed field places, ordinary references, exact fresh copies, statement
matches, length/capacity/clear and existing by-reference iteration paths work
within this subset. Nested aggregate fields can contain these arrays. Array
references remain i32, including when unrelated data arrays make ordinary
references packed i64. Data arrays can store references to inline arrays;
they cannot store the new aggregate values themselves.

Aggregate fills/defaults, push/pop, by-value iteration, whole replacement,
equality/printing, adaptations, direct nested array elements, zero-stride
variant elements and data-memory aggregate elements retain target diagnostics.
Direct field-path iteration also retains its guard; an existing named array
reference can use the admitted loop path. No aggregate value ABI is added.

## Provenance and validation

The preserved Release compiler is
`/tmp/goose-wasm-fixed-aggregate-arrays-20261107/build02/goose-tested`, SHA-256
`bd3856b6c2eedd69bd4eaf343aa9f505794f1a17ab3383194b218fbe33fa368d`.
Its source hashes were checked before each final validation unit. Production
source did not change after that build.

The full suite passed **904 checks** with wasm-tools 1.262.0, Node 24.22.2
and Wasmtime Python 49.0.0. These include executions, diagnostics and static
controls, not 904 independent programs. Fourteen new fixture families cover
packed fields, enums and copied match payloads, empty struct identities,
limited prefixes, aliases and mutable reference paths, nested fields, captured
indices, initializer effects, checked callbacks, data-owner cleanup, frame
growth and thin/packed reference ABIs. Nineteen deferred operations first pass
native validity checks, then fail for an explicit target reason at O0/O2.
Large product, prefix and combined-frame limits are compile-only checks;
they do not allocate their huge images in a native executable.

Validated damaged modules independently change a seven-byte copy to six bytes,
change an element stride from seven to eight, and extend a copy to eight bytes.
The first two fail designated field assertions under both engines. The last
fails a Node-only neighbor guard during the live owner's print completion,
before output is accepted. The owner top is checked again after execution.
Released bytes and sleeps are not used as completion evidence.

The full Linux-native baseline passed with four workers and the explicit
TinyCC library path. Existing device/platform and unsupported JIT skips remain
in the saved log. This does not establish behavior on other CPUs or operating
systems. All 52 saved C/report/diagnostic/scalar-Wasm comparisons passed.
All 168 prior-module pairs are byte-identical. These separate released units
use the same preserved compiler.

## Setup failures kept separate

The first extra-native unit stopped before a compiler build. `copy(a.pop())`
attempted to copy a fresh result; a fieldless variant array was not valid Goose;
and a global initializer attempted to read itself. The frontend rejected these
sources. The corrected pop removes the copy; the global probe reads an earlier
initialized global. The fieldless variant is excluded from native-valid target
coverage. A synthetic C++ zero-stride test is only a defensive layout check.
Successful cases from that unit were reused with their original records.

All raw attempts, command statuses and stderr remain under
`/tmp/goose-wasm-fixed-aggregate-arrays-20261107`. Each resource unit acquired
the shared lock nonblocking, waited for and reaped its children, released it,
then passed an owner/process check and fresh exclusive nonblocking probe.
No timing samples were taken.

## Costs and pending measurements

Named-source literals use 12 locals at both 32 and 256 elements. Nested literal
elements use 11 locals at both sizes. Their module sizes are 1,426/5,240 and
1,125/3,110 bytes respectively at O0/O2. Initializer code grows with the number
of expressions. Sparse global capacity checks compare 32 and 65,536 elements;
they keep scratch counts constant and avoid embedding the unused payload.

Construction performs work proportional to literal expressions and copied
bytes. Exact array copies retain the existing full-image copy cost, including
unused capacity. Frames sum planned owner images; growth retains pages.
Compile-time type checks visit the admitted element graph and reuse the
existing validated-type cache. COPY-wrapper inspection uses the existing
argument-vector helper and can allocate compiler scratch per explicit wrapper.
No new runtime heap allocator or general aggregate temporary is introduced.

Compiler CPU/RSS and allocations, guest initialization/run time, engine code
size and retained physical memory remain unmeasured. The concrete matched
measurement handoff is in `docs/wasm/measurements.md`. These static checks are
not a speed or physical-memory result. No closed scalar grant is reused.

## Independent review

The [Astra review](fixed-aggregate-arrays/astra-review.md) inspected all 42
review files and consulted all 16 context files. Source/snapshot hashes, the
staged patch, 2,593 archived evidence hashes and all 4,683 raw artifact identities
matched before and after review. It found no confirmed production defect and
ran no builds or tests. No source or test change followed the review.

The report lists limits explicitly. Direct aggregate printing and nested
default rejection have shared guards but lack dedicated new native-valid
gates. Complex source places can add scratch locals beyond the tested direct
constructors. Small damaged-copy controls do not cover every prefix/alias
combination; full-suite logs do not retain each successful command stream.
These limits do not establish a failing valid input. Costs stay pending under
the measurement handoff.
