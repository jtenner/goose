# Parallel Wasm function compiler

Build with a Goose compiler containing native shared-memory builtins:

```sh
goose build -O2 samples/parallel_wasm/main.goose -o /tmp/wasm-compiler
python3 test/parallel_wasm.py /path/to/goose
```

The acceptance script builds real binary Wasm modules without dependencies.
Run the executable as `wasm-compiler file.wasm file_size workers mode`.
Workers `0` selects the identical serial compiler; `1`, `2`, `4`, `8` select
native worker pools. Modes are `normal`, `abort`, `cancel`, and `faults`.
Each `job index status visits hex` line reports native output. Statuses are
2 success, 3 rejected body, 4 contained worker abort, 5 cancelled/unclaimed.
The summary gives job count, claimed job count and failed worker count.

The deliberately small subset accepts the Wasm v1 header, one function type
`() -> i32`, a function section whose type indices are zero, and a code
section with matching count and bounded body lengths. Sections must be in
order, unique, and consume exactly their declared bytes. Other sections,
including custom sections, imports, exports and memories, are rejected.
An empty module is allowed. Limits are 256 MiB input, 100,000 functions,
4,096 bytes per body, and operand depth 128. This is a subset compiler,
not a general Wasm validator. The framing follows the
[Wasm binary module specification](https://webassembly.github.io/spec/core/binary/modules.html);
LEBs are bounded and sign bits checked as in the
[binary value specification](https://webassembly.github.io/spec/core/binary/values.html).

Each body must declare zero locals and contain `i32.const` (signed LEB32),
`i32.add`, and a final `end`, optionally preceded by `return`. Stack underflow,
wrong final depth, trailing instructions and unsupported operations fail the
job. Constants emit `mov eax, imm32; push rax`. Adds emit
`pop rcx; pop rax; add eax, ecx; push rax`. Return emits `pop rax; ret`.
The 32-bit add gives Wasm's wrapping arithmetic. No folding, checksum, or
interpretation substitutes for code emission. The output is x86-64 machine
code regardless of host; this example neither maps executable pages nor
calls output. Byte-for-byte oracle comparison validates emission, not
execution, executable-memory protection, or full ABI integration.

The parent maps the input readonly and validates framing before spawning.
It owns a work table with function index, body offset/length, output slot
and capacity; the status column is a separate typed atomic region indexed
by the same function index. Offsets are validated before adding lengths.
Workers claim unique indices with `atomic_fetch_add(next, 1, "Relaxed")`.
Every result slot is disjoint; a worker releases its borrow and publishes
success/error with Release, and the parent observes status with Acquire.
There is no central mutex in claims and no application C helper. Checked
ordinary memory operations may use runtime registry synchronization; this
example makes no assertion that all memory access is lock-free.

The parent holds all owners and joins every worker before reading output or
closing. Start gating makes live-lease close checks deterministic, and the
cancel mode requests shutdown before releasing that gate. A contained abort
intentionally abandons an active result borrow; join cleans it up. Jobs left
RUNNING become aborted, and unclaimed jobs become cancelled. Failure is
reported rather than silently retried. The `faults` mode checks impossible
allocation size, stale capabilities, out-of-range accesses, use after
release, readonly writes, and close while borrowed. Allocation failures
unwind owners allocated so far. The file must remain unchanged while mapped;
this sample does not snapshot a concurrently rewritten/truncated file.

Acceptance covers thousands of varied functions, serial/pool equality,
zero jobs, excess workers, repeated starts, malformed framing, malformed and
unsupported instructions, aborted workers and shutdown. It compares the
exact machine bytes to an independent Python emitter and checks visits.
