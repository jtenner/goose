# Unsigned LEB array-length prefixes

The admitted fixed-size scalar and ordinary-reference array elements now work
with `T[varint]` length storage. Counts use the native canonical unsigned LEB128
format. The shared layout query keeps its dynamic element-offset marker.
This extension does not implement signed zigzag varint elements or fields.

Construction reserves the complete prefix and payload before it evaluates
elements. Literal, fill and string constructors write canonical count bytes.
The same-layout copy path captures count and width before reservation and
checks the combined byte total before narrowing to Memory32. Copies include
the source prefix. Mutable aliases, globals and ordered cleanup retain their
existing ownership rules.

One cached reader per module returns count bits and prefix width. It selects
one concrete memory before decoding. Its one-byte fast path avoids the loop;
the continuation path reads at most ten bytes. It rejects nonshortest,
overlong and above-64-bit encodings. Low-offset addition is checked before
conversion to i32, so it cannot carry into a packed memory identity. Real
constructed Memory32 arrays need at most five prefix bytes. This is an encoding
reader, not a complete untrusted-array or serialization validator.

Indexing and byte snapshots reuse the decoded width within the operation.
Equality reads it before the element loop. Iteration reloads it with the
current referenced owner on each test, including a rebind across prefix widths.
Nested reference-array walks can still decode a parent twice. General
mixed-layout equality uses the checker's slice path and remains a target
diagnostic. Layout adaptation, assignments, by-value arguments/results,
compound and relative values, slices and serialization remain pending.

The frozen Release compiler SHA256 is
`6f110d8e62ab7e5bae82eee65d42aa82bc979058ac2abb6203a1adea01360b66`.
Four native-valid inputs passed at Goose O0/O2 with the prior compiler. Its
Wasm backend rejected all eight attempts for the missing-prefix feature.
The golden C sources use `cc -O0` at both Goose levels. All eight new target
modules validate with wasm-tools 1.262.0 and match native output in Node
24.22.2 and Wasmtime Python 49.0.0. Completed-owner checks observe actual frame
and data tops after synchronous `_start` return. They also pin bytes `[128, 1]`
plus 128 payload bytes for the persistent owner, with top 131.

The first full suite stopped at a new test's expected native wording. Native
reported index 128 and length 128; Wasm used its generic array-bounds text.
Both correctly rejected the intended access. Only that expectation changed.
The preserved-compiler continuation passed all 455 Wasm checks, 52 exact
artifact/diagnostic comparisons and 92 prior-module pairs. The 52 comparisons
contain 34 native C/report pairs and 18 older Wasm pairs; they are not 52 new
native executions. No fresh full native baseline was run for this Wasm-only
extension. The earlier complete native record, new native oracles and exact
C/report comparisons remain available.

The independent [Astra review](varint-prefix/astra-review.md) found no confirmed
defect. It checked all 21 changed files, all 4,144 final source/harness hashes,
compiler identities, all saved comparison pairs and static module metadata.
The [continuation provenance](varint-prefix/continuation/provenance.json) shows
that production and adapters match the build, with only the stated test
expectation changed. All children were reaped, owner 3921947 exited, the lease
was released, and the exact-stage process check and fresh nonblocking exclusive
probe passed. The probe was immediately released. The
[release record](varint-prefix/release-verification.json) pins those facts.

Raw evidence is `/tmp/goose-wasm-varint-prefix-20261107`. The failed first
attempt and continuation remain separate. Archived subprocess records retain
stdout, stderr and exits under their exact file names in JSON; the raw files
remain unchanged. No aggregate `continuation/unit.exit` was written at run
completion. The recorded command exits, lease/release data and later saved
tool-completion receipt provide the wrapper evidence. The full-suite success
log is an aggregate summary, not separate successful subprocess logs.

Saved module sizes range from 4,723 to 10,932 bytes. The reader body is 513 bytes
in the three-memory helper module and 10,371 in the 65-memory module, including
local declarations and end. Emission work and code size grow linearly with
memory count, bounded at 65. These are static byte counts, not speed results.
All 92 old modules are byte-identical. The reader uses four scalar locals and
no guest scratch buffer or growth. Compiler strings/vectors can still allocate.
Filling, copying and host byte snapshots remain proportional to payload size.
Reservations grow in 64 KiB pages; restoring a top does not shrink a buffer or
prove physical release.

No controlled compiler CPU/RSS/allocation, guest timing, physical-memory or
cross-platform runtime measurements were taken. No speed or minimal-footprint
claim is made. Queued measurement work covers one-byte and longer prefixes,
known and dynamic memories, owner count, repeated nested paths, initialization,
copy size and retained pages, with exact references and a fresh shared lease.
The full project's performance matrix remains pending.

The review records direct coverage gaps for effectful indices across prefix
widths, optional-null byte printing, zero-fill effects, additional malformed
widths, unsupported-type combinations and copy-overflow guards. The small
memory test at `0xffffffff` traps on its first load; it does not execute the
final-address continuation overflow branch. That branch's no-carry argument
comes from source inspection. No multi-gigabyte test or allocation was made.
