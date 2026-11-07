# Byte strings and print snapshots

String literals now construct admitted fixed, static-capacity limited,
fixed-prefix variable and growable byte arrays. Their exact bytes, including
zero bytes, are copied into independent owner storage. Prefix/header fields
use the existing shared layout rules. One bulk copy reads static Memory0 bytes
and writes the assigned memory. A cached dispatch helper handles dynamic
memory identities. No per-byte AST or guest heap allocation is introduced.

Byte-array printing captures each argument before later effects. The optional
host imports capture bytes from the named memory, transfer a snapshot to a
completed print line, or release it on an exited scope. Snapshot actions share
the ordered cleanup path with defers and data owners. Null byte references
render as `null`. Maps are lazy and per instance. Old scalar modules retain
their import set and bytes. Ordinary string literals printed directly retain
the existing fast path. General slices, varints, compound printing, custom
formatting and value-result destinations remain pending.

The optional ABI group consists of:

- `snapshot_memory_bytes_v1(memory: i32, offset: i32, length: i32) -> i32`:
  copy the bounded byte range and return an owning handle.
- `print_snapshot_v1(line: i32, snapshot: i32)`: consume the handle and transfer
  its bytes to the pending line.
- `drop_snapshot_v1(snapshot: i32)`: release an unconsumed handle on a scope exit.

Addresses and lengths use unsigned Memory32 bits. Memory0 is identity 0;
other identities name exported `data_memory_N` memories. Invalid identities,
ranges or handles fail; handles are not guest pointers. They are private to
one adapter instance and cannot be consumed twice. Node terminal cleanup clears
remaining I/O state after failure; the Wasmtime command-line adapter terminates.

The Release compiler SHA256 is
`09491aaf99a5da41f0ca9df7b9a10fb2e5989832faf40c01d656b0805b9a46e5`.
Both fixtures first ran through the prior native C backend at O0/O2. Their
native output matches the new output in Node 24.22.2 and Wasmtime Python
49.0.0. wasm-tools 1.262.0 validates the modules. The prior Wasm compiler rejects
the inputs at the specific unsupported constructor or print diagnostic and
writes no module. Cases cover every admitted layout family, empty/embedded-zero
strings, globals, independent mutation, stable references across growth,
dynamic copy bases, large payloads, nullable references, nested output, later
argument mutation/growth, return/inlined return, defer, break and continue.

The final frozen-adapter run passed 323 harness checks. The owner check reads
actual scoped tops after `_start`. Snapshot checks observe live map state at
print completion, before terminal cleanup. Two deliberately broken adapters
are rejected for their specific missing-drop and retained-live-view behavior.
The bulk-copy helper is checked in both engines for invalid memory identities,
zero length at the boundary, source/destination bounds and unchanged destination
bytes on failure. A later argument's divide-by-zero emits no partial line.

The first full run also passed, but an adapter edit overlapped its startup.
That result is not presented as a run frozen at the final adapter version.
The overlap, correction and separate final run are preserved. Compiler sources
did not change during the build. Both wrapper owners exited, all children were
reaped, leases were released, and the final nonblocking exclusive probe passed
and was immediately released. The [release record](byte-strings/release-verification.json)
identifies the exact sources and compiler. Raw files remain at
`/tmp/goose-wasm-byte-strings-20261107`.

All 72 prior modules match the immediate prior compiler byte for byte. The 52
older-checkpoint C/scalar-Wasm/stack-report/diagnostic comparisons also match;
they are artifact comparisons, not 52 new program executions. This stage ran
new native oracles but did not rerun the full native project baseline. Earlier
native-suite and targeted TinyCC packaging-path results remain separate.

The independent [Astra review](byte-strings/astra-review.md) found no confirmed
defect and checked hashes, comparisons and final-run provenance. It lists gaps
for deeper nullable chains, inner exits preserving outer captures, byte-array
reference paths/rebinding, all prefix widths, invalid host-ABI handles/ranges,
and exceptional Python-host reuse. Individual intentional-control stderr and
statuses are asserted by the frozen harness but were not separately archived.

The 70,000-byte construction fixture emits a 77,648-byte module at both levels.
Its large-copy function has 13 declared locals and 177 instruction bytes. The
printing modules are 7,202/7,575 bytes at O0/O2. These are saved-file observations.
Host snapshot storage and copying grow with captured byte length; final line
assembly copies bytes again. Literal occurrences are not globally deduplicated.
The compiler erases snapshot actions by scanning the current cleanup list, so
P byte prints with A retained actions can require O(P*A) compiler scan work.
There is no such list scan at guest runtime. No controlled CPU/RSS, allocation,
runtime, process-residency or platform measurements establish a speed gain or
minimum physical-memory footprint. Scope restoration does not shrink a memory.

Queued performance work: measure common scalar compile/start paths against the
prior checkpoint; measure static/dynamic byte copies, many print arguments and
prior defers, repeated/large captures, and compiler CPU/RSS. Use exact native
C and Wasm identities and the project's shared lease/host controls. This stage
does not reuse an old timing grant or add samples to a closed campaign. The
full coordinated performance matrix remains required before project completion.
