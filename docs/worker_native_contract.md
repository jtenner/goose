# Strict worker-native contracts

`goose++ check --strict-worker-native main.goose` opts into a hard check of
native calls reachable from every `thread_fn`. The same option works with
`build`, `run`, and `lsp`. Default mode preserves existing unclassified FFI.
Native declarations in imported standard-library code are not implicitly trusted.

Classify each extern declaration after its result types, before its optional
C symbol and semicolon:

```goose
extern fn snapshot(handle: u64) -> i64 worker_callable;
extern fn destroy(handle: u64) main_thread_only = "native_destroy";
extern fn legacy(handle: u64); // unclassified
```

The classification applies to this declaration, including its specializations,
not its package or other declarations sharing a C symbol. Use one canonical
Goose declaration for each native operation; contradictory aliases cannot be
validated against the native implementation. A package's existing
`main_thread_only = true` restriction still forbids all its worker calls;
`worker_callable` cannot override it. Explicit `main_thread_only` is enforced
in default mode too. Members of `extern "library" { ... }` use the same suffix.

Strict mode rejects unclassified and main-thread-only externs in the checked
worker graph, including recursive/generic helpers, dispatch cases, bound
function arguments and format hooks. The diagnostic gives a worker-to-callee
path and the offending declaration's file, line and column. Only selected
constant branches participate. Coordinator-only calls are unaffected.

Strict mode also rejects `unsafe_ptr_from_handle`, `unsafe_handle_from_ptr`,
`unsafe_ptr_add`, `unsafe_load` and `unsafe_store` anywhere in that graph.
There is no Goose function exemption. Put necessary raw-memory work behind a
narrow, audited native declaration instead. Safe shared capabilities and their
existing atomic operations remain allowed; no new atomics are introduced.

`worker_callable` is an assertion by the adapter author, not a native race
proof. Document and audit at least these obligations alongside each adapter:

- Which native objects the handles name and which operations may overlap.
- Bounds, alignment, read/write permissions and any disjoint output slots.
- Synchronization and publication, including any atomic memory orders.
- Resource lifetime through every worker join, including contained failure.
- Whether pointers to worker-local arguments may be retained (normally not).

Ordinary values remain isolated: spawn copies arguments and the globals a
worker uses, and each worker has its own stacks and globals. Integer handles
remain flat values even if two copies name the same native object. The checker
cannot establish native ownership, pointer provenance, correct annotations,
disjoint writes, native synchronization or coordinator destruction timing.
It does not add a mutex, a user TLS API or an ownership system.

The regression fixture `test/threads/native_contract/scheduler.goose` models a
sealed snapshot, atomic claim, worker-local scratch, one writer per result,
all-worker joins and coordinator-only destruction. Its C adapter's contract is
intentional test code, not a general handle API. The fixture passes duplicated
integer handles to demonstrate that structural checking does not prove native
resource isolation. Existing fork atomics can supply the claim counter when
the scheduler accepts a `SharedAtomicU64` capability directly; safe capabilities
cannot be converted into raw addresses for an existing C adapter.

See [native memory](native_memory.md) for capability, worker lease, atomic order
and platform limits. Verified native execution remains Linux x86-64 GCC/Clang;
this check does not extend backend support.
