# Native compiler extension validation

Baseline: upstream `94cc64daeabcae6f072dc1fe2b864acda5a001bc`, fork
`jtenner/goose`, Linux x86_64, AMD Ryzen 7 8845HS (16 logical CPUs), GCC
14.2.0, Clang 23.1.3, CMake 4.4.4, Python 3.13. Upstream runtime version:
`a5dbd11b6309`. Optional audio/gfx/physics/ui packages were not built in.

Commands:

```sh
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j 6
PATH=/home/dev/.local/share/mise/installs/clang/23.1.3/bin:$PATH \
  python3 test/run_tests.py --profile baseline --cc native --require-clang -j 6
```

The clean upstream build succeeded: configuration 0.409 seconds, build 77.907
seconds, peak compiler-build child RSS 2,202,504 KiB. The full baseline suite
passed in 142 seconds, including 51 sample checks, native C at O0/O2, TinyCC
runs, compiler/runtime unit tests, diagnostics, documentation examples,
language-server checks, and the Goose-in-Goose bootstrap. Threaded TinyCC
programs and optional multimedia execution were skipped as documented upstream.
The compiler emitted existing GCC warnings; no compiler errors occurred.

The initial run had eight environment failures: the installed `clang` shim
had no selected version. Prepending the actual installed compiler directory
resolved them without repository changes. The passing run used a separate
clean upstream worktree to keep source-inspection checks independent of edits.

Native definitions acceptance tests were committed before implementation;
the unmodified compiler rejected the first invocation with `unknown option:
--define`. Run the focused tests with
`python3 test/cli_definitions.py build/goose`.

## Initial integrated extension validation (historical)

Claude and DeepSeek reviewed `102c0df53d8369325f7c33c3ae6ca308615a4b89`.
The independent parent reviewed the diagnostic-only follow-up `61587de3`:
synthetic definition errors now use the real condition location without
mutating immutable values. Compiler source subtree after that correction:
`2049b52b10eaf0192e66514fbac40bf5e2d0d3ec`. After that correction, the initial
stack's Release and assertions-enabled Debug each pass **5,125 reported section checks**, in
separate sequential runs (118 s and 123 s). Both include the native example group and expanded
library-header regression. The final 3,000-job Wasm acceptance also passes
normally and with ThreadSanitizer (Clang 23); these are correctness runs.
`build/goose` is a refreshed Release build and runs the checked clobber sample.
Full-suite counters include grouped drivers; their internal checks are not
summed again as unique test cases.

The extension preserves ordinary worker isolation. Shared allocation/view/access
and atomic handles have distinct compiler types; the checked runtime pins
worker memory through lease cleanup. UnsafePtr operations have separate caller
obligations and do not confer safe shared-memory authority.

Full-suite commands (use a build beside the checkout so standard-library and
sample resources resolve):

```sh
python3 test/run_tests.py --exe build/goose --profile baseline --cc native --require-clang -j4
python3 test/run_tests.py --exe build-final-debug/goose --profile baseline --cc native --require-clang -j4
python3 test/cli_definitions.py build-final-debug/goose
python3 test/const_if.py build-final-debug/goose
python3 test/parallel_wasm.py build/goose
python3 test/conditional_shared_layout.py build/goose
python3 test/native_config_definitions.py build/goose
python3 test/jit_clobbers.py build/goose
```

Runtime version: `3a21ace949ed`. Compiler executable hashes, source revisions and
native flags accompany the benchmark records. Claude Opus 5.5 and
Concentrate/OpenCode DeepSeek 1017 each completed one review thread and
approved frozen source `102c0df5`. Claude also independently reproduced all
published statistics from the raw measurements. Its documentation findings
are addressed in the results: size-dependent compiler regression, multi-worker
scheduling costs, and the optimized-away C write/readback comparison. The
diagnostic-only follow-up has separate independent parent approval; the two
model approvals do not extend to that later source revision. The CLI version identifies the
runtime and is insufficient to distinguish compiler source snapshots.

Independent review covered CLI parsing/configuration isolation/source locations;
const-if specialization transactions, field layouts and constructors; shared
lifetime and native atomic generation; mappings and zero-length copying; unsafe
pointer storage, alias effects and C ABI; builder result-count alignment; worker
packet byte copying; and their combined behavior. Confirmed issues were retained
as regression tests before fixes. These included abandoned recursive
specializations and speculative proof/cache state, unaligned native wrappers
and packed result/packet counts, missing u64 generation lock-free checks on u32
paths, stale bounds facts after synchronized raw writes, and string-definition
source locations. Library headers test only public signature dependencies, including flat enum
payloads with private native siblings, C/C++ hosts and retained ABI refusals.
The focused full-sanitizer header matrix passes 352 subprocess checks per
GCC/Clang frontend, with source unchanged after freezing.

Conditional layout tests execute both 8-byte/16-byte layouts, active reflection
and constructors, and actual cross-configuration files with explicit layout
fingerprints. A mismatched fingerprint is rejected before reading payloads.
Packed capability wrappers have byte alignment; registered atomic cells retain
4/8-byte alignment checks. Tests explicitly re-enable alignment sanitization
for these paths. The ordinary sanitizer profile retains inherited exclusions
for unrelated general packed scalar accesses; it is not evidence of universal
alignment safety.

The parallel sample emits real x86-64 bytes for the documented `()->i32` Wasm
subset. It does not allocate executable pages or invoke the emitted code and
is not a complete WebAssembly implementation. Its stress checks compare every
emitted byte and claim/publication state across serial and 1/2/4/8 workers,
including 3,000 jobs, malformed inputs, cancellation and cleanup. Native builds
are used for threads; embedded TinyCC execution is not used for native memory.

## Deferred-state journal validation (current)

The performance correction is frozen at compiler source
`41dc6eb30e9363f1f97a51aeb047aad18d96746c`, `src` tree
`741cbecbd8b0f95e4ab9148161a5af870cb3ca12`. It replaces exhaustive deferred-state
snapshots with first-write journals while retaining unused-function checks,
rollback of earlier live proofs and quarantine of speculative cache products.
Structural work regressions were committed first in `755dc3d2`. The
[design audit](design/const_if_deferred_state.md) describes the mutation barriers,
ownership rules and exhaustive testing oracle. The independent parent reviewed
this correction separately from the historical model reviews above.

Author Release (`GCC 14.2.0 -O3 -DNDEBUG`) and assertions-enabled Debug each
pass **5,127 reported section checks**, with `GOOSE_DEFERRED_VERIFY=1` throughout
the full baseline suite. The focused const-if driver passes 825 checks and the
new deterministic work driver passes 52, without timing thresholds.

The Clang 23 ASan/UBSan compiler passes the full sanitizer profile's **4,354
reported section checks**, with the exhaustive oracle, compiler alignment
sanitization and `detect_leaks=1` enabled. The raw initial run's shader leaks
were reproduced on the pre-fix compiler. The passing rerun uses addr2line
symbols and the repository's narrow exclusions for four unchanged CuteSpirv
allocation functions; it does not disable leak detection globally. Sanitized
compiler work/marks/transaction drivers also pass 52/245/357 checks. The native
profile's inherited packed-scalar alignment limits and TinyCC leak limits
remain as documented below and in [testing](testing.md).

The [measured correction](../bench/shared_native/results/deferred-state-2026-10-23/README.md)
retains all 684 successful check processes, exact source/compiler/harness hashes,
wall/RSS samples and median/MAD/min/max. Ordinary 1,000-function O2 checking
improves from **346.469 to 32.559 ms** against the merged pre-fix fork. The
separate upstream control is 32.670 versus 31.580 ms at O2; upstream/corrected
differences at both O0/O2 overlap the observed time and RSS ranges. Larger
sizes, std imports, generic calls, deferred stores and the real parallel Wasm
source are included; the results do not claim whole-compiler linearity.

## Platform and validation limits

| Target | Status |
| --- | --- |
| Linux x86-64, GCC 14.2 / Clang 23.1.3 | Built and exercised: compiler, native memory, atomics, mappings/advice, UnsafePtr and examples. ASan/UBSan with focused alignment checks and TSan tested. |
| Linux i486/i686 cross-target probes | Compile-only lock-free validation, including u64 generations on u32 paths; no 32-bit runtime claim. |
| Windows / macOS | OS allocation/mapping branches exist; no execution validation here. |
| MSVC | Native shared atomic backend is explicitly unsupported; no silent locking fallback. |
| Embedded TinyCC | Existing ordinary supported programs remain tested. Native shared memory needs TLS and UnsafePtr needs packed typedef alignment; explicitly unsupported. |
| Other pointer widths / big-endian hosts | UnsafePtr rejects non-64-bit pointers; no host execution coverage. Both requested byte endians are tested on this little-endian host. |

Struct field conditions may use build definitions/global constants; generic
structs support such layouts, while conditions depending on type parameters
are explicitly rejected. Configuration-dependent types are ABI incompatible
unless the application validates a matching layout/version. Readonly mappings
are not snapshots; applications must prevent external truncation. Unsafe raw
access still requires valid provenance, extent, lifetime, permissions, effective
type and synchronization; numerical checks cannot establish these properties.

Inherited limits outside these corrections remain documented: ordinary
variable-mode enum streams can emit unaligned typed scalar stores; a
variable-prefix owning alias `.items.push` can emit malformed C, and ordinary
embedded TinyCC execution has an existing LeakSanitizer allocation report.
Compiler-only sanitized const-if checks and the tested native programs pass;
these results do not establish a compiler-wide or TinyCC-wide leak-free claim.
Optional multimedia/device tests retain upstream environment skips.

Measured native costs and the historical synthetic compiler regression, with
raw samples, flags, hashes, variation and limits, remain in the
[benchmark record](../bench/shared_native/results/README.md). The roughly 10.5x
slowdown at 500 globals and 1,000 unreached functions describes the initial
feature stack's exhaustive snapshots, before the journal correction above.
The current compiler still scans global flow per root (O(U×G)), retains O(G²)
global setup work, and has separate name lookup, provenance, large touched-record
and quarantine-memory costs. Removing full snapshots does not bound those
costs or establish linear compilation. The native runtime measurements are
unchanged: four/eight-worker start/join costs are 1.20x/1.21x the weaker C
baseline; the 40.32x source write/readback ratio uses a largely optimized-away
C loop and is not a physical-operation latency ratio.
