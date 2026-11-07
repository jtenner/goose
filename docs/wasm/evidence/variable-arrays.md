# Initial variable-array lowering

This stage adds explicit scalar/reference array literals for
`T[]`, `T[u8]`, `T[u16]`, `T[u32]` and `T[u64]`. It does not add varints,
variable elements, strings, slices, serialization, general constructors,
whole-array assignment or by-value array arguments/results. Variable-array
mutation builtins other than length remain target diagnostics. Indexed element
writes and reference rebinding are supported.

The packed value lives in an assigned data memory: the declared unsigned length
prefix followed immediately by elements. Prefix widths come from `ValueLayout`.
The checked payload byte count is reserved once before any element initializer
runs. Data-memory offsets remain stable. Local owners retain a saved top in the
existing ordered cleanup list; global owners use persistent dedicated memories.

A local variable-array value is a packed i64 object pointer in a Wasm local.
A global uses a private Memory0 pointer word. That word is not the array's
stored value image. The actual bytes remain on the data stack. Ordinary stored
references remain 8 bytes. Memory0 inline/growable header references stay thin;
references into variable arrays use the packed memory/offset form. The storage
pass detects data-address interfaces through nested array/reference types,
even when no actual owner is present. Known owners use fixed-index loads and
stores; reference parameters and paths use checked dispatch.

Returning a reference keeps the existing owner alive under frontend lifetime
rules. The emitter accepts only matching reference-return layouts when an
expression is used as an array address. Owned temporary values still require
the pending destination lowering. Whole-array assignment must not become a
pointer alias and is rejected before output.

The first Release compiler SHA256
`78a2f4a3db727c55869aefe1eb4e08e6f7f7f80b55095594571280555ef28476`
passed targeted O0/O2 native/Node/Wasmtime/owner checks, 281 Wasm checks, the full
native suite, 52 exact native/scalar comparisons and 62 unchanged prior Wasm
modules. The cases cover all fixed prefix widths, globals, aliases, reference
parameters/results, dynamic call bases, nested paths, argument effects,
rebinding, scope reuse and a nested interface with no actual data owner.

A further native-valid 14,000-element literal exposed input-sized scratch:
56,015 locals and a 2,209,599-byte module. Both wasm-tools and Node reject the
local count. A 9,000-element i64 payload passed but used 36,021 locals and a
1,414,542-byte module. These are file/validation observations, not timing or RSS
measurements. Raw failing records remain at
`/tmp/goose-wasm-variable-arrays-20261107/large-before`.

The constructor now reuses one value local. The reservation already checks
`saved + total_bytes <= UINT32_MAX`; each constant element offset is inside
that reserved range. Thus the direct i32 addition cannot wrap, and adding the
offset to a packed pointer cannot carry into its memory id. Values are
computed before their store. This removes repeated address-check temporaries
and duplicate trap strings while keeping initialization order. Compiler output
still grows with the explicit literal's element count.

The rebuilt Release compiler SHA256 is
`ccb45b63e07c3dc3a80ef392e12db035453b6fd65cd7e7b4387efb5222ad464f`.
The same original large sources now pass validation, Node, Wasmtime and
completed-owner checks at O0/O2. The 14,000-element module uses 16 locals and
230,800 bytes; the 9,000-element module uses 22 locals and 162,931 bytes.
Both optimization settings emit identical bytes for each source. The growth
case checks an actual data memory of at least 131,072 bytes after completion
and restored scoped tops. These are logical capacity observations.

The first repaired-module attempt exposed a test-only JavaScript argument
limit while spreading its code bytes. Production validation and execution had
already passed. The owner checker now copies those bytes with a loop. The
original failure is preserved in `constructor-repair`; successful same-source
checks are in `constructor-repair02`. No production code changed for this
checker repair. The full Wasm suite passed 289 checks. The full native suite passed all
groups except the relocated compiler's TinyCC bundle lookup. That helper
failed before guest subprocesses. The exact failed check then passed with
`GOOSE_TCCLIB` set to the existing build-tree bundle. The remaining 52 exact
C/stack-report/diagnostic/scalar-Wasm comparisons and 62 old Wasm module pairs
also passed. Source hashes match the saved compiler. Failures and separate
lease releases are preserved in [validation.json](variable-arrays/validation.json).

An independent Astra source and evidence review found no confirmed production
defect. Its [unchanged report](variable-arrays/astra-review.md) has a cutoff
before the final packaging/compatibility continuation. The later checks above
were verified by the parent; they are not attributed to that review. The review
lists remaining combination coverage limits, near-4-GiB limits and unmeasured
costs. In particular, large dynamic-base constructors and variable owners with
every cleanup exit are not direct execution coverage of this checkpoint. No compiler CPU/RSS,
allocation count, runtime throughput or physical-memory gain is claimed.
