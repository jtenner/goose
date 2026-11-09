# Borrowed selections from fixed temporary owners

Parent: d4b6ee4e7be81c0de5e5741539cbf185deec85d8.
Scope: Stage C correctness only. Branch: `feat/wasm-multimemory-backend`.

Ordinary direct calls with a scalar or void result can now borrow a field or
element of a fixed temporary. Explicit and implicit address forms use the same
stored read place. Each owner stays live through later arguments and the call.
The result is saved before ordered cleanup. Existing storage-plan, range and
memory-identity checks remain active. Stored reference fields retain their
existing value-read behavior.

The parent fails Wasm compilation for 48 native-valid O0/O2 variants. Two more
variants already work and remain regression checks. The 25 families cover
numeric pointees, packed fields, aggregate subobjects, fixed-array subobjects,
two live owners, mixed value arguments, data-memory references, memory growth,
early return/continue/break and void calls. Invalid whole-temporary address and
write-through sketches remain separate and are not counted as backend defects.

The candidate passes 50 fresh native/Node/Wasmtime pairs and 16 complete Memory 0
image and fault-control checks. Controls detect early owner release, missing
cleanup, wrong values and writes outside the owner. The growth case checks the
complete image before and after Memory 0 grows. The full suite passes 8,108
checks. Core and all suffix behavior/image helpers run fresh. Its 2,094 fixture
pairs comprise 2,044 executed parent records with exact source/module identity
and the 50 fresh pairs. All 52 exact output and diagnostic comparisons pass.

Tested compiler SHA256:
`e25673ebfaf696b9165e5e0b5f15a467fd520f3698af7fb21e983325fc5fda74`.
All 85 compiler source hashes and 6,179 test/script input hashes match the frozen
validation inputs. The quiet hold began after the full suite had completed;
the stop check found no owned processes. No test was interrupted or repeated to
replace a failed result. The owner released the hold at 2026-11-09T12:24:51 UTC.

Previously supported fixture modules are byte-identical. Newly supported calls
use the existing fixed reservation/copy and ordered restore needed to hold the
borrowed owner. The compiler adds argument recognition and uses existing plan
records; it adds no runtime field or new heap service. These are source-level
cost limits. No measurements, timing, profiling, allocation or physical-memory
claims are part of this checkpoint.

Escaping reference results and reference-carrying aggregate results remain
guarded. Inline/callback paths, nonfixed temporary owners, remaining compound
lifetime events and general thin-reference propagation still need Stage C work.
Stages D, E and F follow in order. Stage F is in scope. The backend is not
complete.

Commands, failures, raw outputs, hashes and complete-image controls are in the
[archive manifest](temporary-borrows/archive-manifest.json). A read-only source
bug search found no confirmed defect; it did not execute code.
