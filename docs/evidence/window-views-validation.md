# Trimmed window views v1: implementation evidence

Branch: `feat/window-views-v1`, in `/home/dev/Projects/goose-window-views-v1`.
Base: fork master `953e020657a8dd09422709bacb5ec995e05c4771`.
Validated implementation head: `81431872` (the following evidence commit only
adds this report and logs). Nothing was pushed and no PR was opened.
Design authority: `design/window-views`, trim commits `2334022e` and `aeb9be82`;
the entire trim and the packed-word design and implementation history were read.

## Delivered behavior

One builtin, `read_record_le<T>(at: i64, data: const u8[:]) -> T, bool`,
returns an eager independent struct snapshot. T must be a nonempty,
nongeneric, non-root ordinary struct of direct writable unqualified integer
fields (u/i8/16/32/64, including aliases). The checker rejects pads, defaults,
conditional declarations in either configuration, result qualifiers, packed
words, nested records, arrays, slices, references, floats, bools, enums,
index types, varints and native pointer fields. Existing argument checking
rejects handles and UnsafePtr buffers.

Codegen evaluates position then slice exactly once, zeros fresh result
storage, and emits `start <= length && N <= length - start`. Byte-pointer
arithmetic and all constant-offset loads occur inside the successful guard.
There are no per-field checks, user calls while decoding, new runtime ABI,
parser/AST changes or new type/lifetime categories. Signed decoding uses
representable signed arithmetic to avoid out-of-range C conversions; suffixed
integer literals also work with embedded TinyCC's minimal headers.

## Validation and comparison

Linux x86-64; GCC 14.2.0, Clang 23.1.3 and embedded TinyCC.
No execution claim is made for other architectures or big-endian hosts.
Exact-byte fixtures establish little-endian interpretation independently of
native struct images. No performance claim or Slipstream integration is made.

| Gate | Unmodified master | Feature branch |
|---|---:|---:|
| Full runner | 5,722 pass, 2 fail | 5,727 pass, 2 fail |
| Tree-sitter complete corpus | 27 pass, 0 fail | 27 pass, 0 fail |
| Focused record acceptance | unavailable | 4,407 checks pass |
| Registered CTest | unavailable | 1 pass, 0 fail |

Full runner command, executed before edits and again on the branch:

```sh
MISE_CLANG_VERSION=23.1.3 python3 test/run_tests.py --exe build/goose \
  --profile baseline --cc native --require-clang -j 8
MISE_CLANG_VERSION=23.1.3 ctest --test-dir build --output-on-failure
```

Both runner failures are exactly `benchmark declarations` and `benchmark
compatibility`: the shared-native benchmark lock is occupied by the running
external measurement. They occur in both baseline and branch. The lock and
measurement were left intact. Baseline took 74s; branch took 73s. Existing
optional-module/platform/JIT skips remain in the logs. The five additional
runner passes come from the new codegen and rejection fixtures. The focused
driver is registered separately with CTest; the fixture runner is unchanged.
The sample also ran explicitly under TinyCC and printed `1`, `8`, `3`.

[Baseline runner](window-views-baseline.txt), [branch runner](window-views-suite.txt),
[baseline corpus](window-views-corpus-baseline.txt), [branch corpus](window-views-corpus.txt),
[CTest](window-views-ctest.txt). Corpus generation/install/tests ran in temporary
directories; no generated tree-sitter source was changed.

Focused tests run accepted and rejected programs under --check, --parse,
-O0 and -O2; native C is executed with GCC/Clang at both optimization levels
with UBSan and nonrecovering diagnostics. The same positive oracle executes
under TinyCC. Tests cover all eight scalar types, zero/one/high-bit/all-one
patterns, both signed extremes, mixed fields and integer aliases; exact-end,
one-byte-short, empty data, starts at/beyond length, negatives and both i64
extremes; every failure field is checked for zero. They prove argument order
with a resizing position expression, source/snapshot independence, unchanged
neighbor bytes, aggregate storage, returned multiple values and decoding from
the destination's old bytes. Emitted-C checks at O0/O2 find exactly one
logical extent guard, loads after the guard, no source-pointer arithmetic
before it and no GS_IDX/abort in the decoder. An exported unrelated dynamic
index retains its normal GS_IDX check even under optimized inference.

## Three worked layouts

| Record | Fields and offsets | Proven extent |
|---|---|---:|
| Flat signature | ten u32 at 0,4,...,36; two u8 at 40,41 | 42 bytes |
| Flat metadata | thirteen u32 at 0,4,...,48; seven i64 at 52,60,...,100; three u32 at 108,112,116 (23 fields) | 120 bytes |
| Memory limits | minimum u64 at 0; maximum u64 at 8; flags u32 at 16 | 20 bytes |

The focused driver independently sums widths and decodes a deterministic
byte fixture with Python int.from_bytes, checking every field on success
and failure. Each layout is exercised at unaligned start 1 ending exactly
at the buffer end, and through the boundary matrix.

## Scope and footprint

No semantic deviation from the trimmed v1. There is one testing distinction:
`--parse` accepts valid existing struct/call syntax and stops before semantic
eligibility checks. It therefore succeeds for the unsupported layouts;
--check/-O0/-O2 reject them with one plain diagnostic and no C output. Moving
these checks into parsing would contradict the trim's existing-builtin and
no-parser-edit requirements. The packed-word u128 test rejects at parse time
because that sibling feature has a grammar-level rejection.

The eight compiler files add **167 lines**: six shared integration sites add
7 lines; two isolated headers add 160. This is smaller than the estimated
214–338 lines, with no footprint overrun or blocked functionality. Tests,
CMake registration, documentation and sample add 287 lines, making **454
implementation lines** before this evidence bundle. All changes are additions
relative to master; the literal correction checkpoint does not add net lines.
The complete changed-file counts follow (physical added lines against master).

| File | Added lines |
|---|---:|
| `CMakeLists.txt` | 8 |
| `docs/evidence/window-views-baseline.txt` | 61 |
| `docs/evidence/window-views-corpus-baseline.txt` | 40 |
| `docs/evidence/window-views-corpus.txt` | 40 |
| `docs/evidence/window-views-ctest.txt` | 7 |
| `docs/evidence/window-views-suite.txt` | 61 |
| `docs/evidence/window-views-validation.md` | 190 |
| `docs/reference.md` | 37 |
| `docs/stdlib.md` | 17 |
| `samples/record_read/main.goose` | 11 |
| `src/builtins.h` | 1 |
| `src/codegen.h` | 1 |
| `src/codegen_builtins.h` | 1 |
| `src/codegen_record_read.h` | 82 |
| `src/main.cpp` | 2 |
| `src/typecheck.h` | 1 |
| `src/typecheck_builtins.h` | 1 |
| `src/typecheck_record_read.h` | 78 |
| `test/codegen/record_read.goose` | 25 |
| `test/errors_tc/record_read_bool.goose` | 3 |
| `test/expected/record_read.out` | 12 |
| `test/record_read.py` | 174 |
| **Total including textual evidence** | **853** |

## Resolved validation failures and cleanup

The first master run selected an unconfigured mise Clang shim (5,699 pass,
25 fail). Explicitly selecting the installed Clang 23.1.3 fixed every Clang
failure on untouched master; only the two benchmark failures remained.
Every initial failure name is retained here for traceability:

- `native memory backend`
- `cgen-clang-release codegen_exec.goose`
- `cgen-clang-debug codegen_exec.goose`
- `simd2-clang simd_versions.goose`
- `simd1-clang simd_versions.goose`
- `simd0-clang simd_versions.goose`
- `simd2-clang stdlib_base64.goose`
- `simd1-clang stdlib_base64.goose`
- `simd0-clang stdlib_base64.goose`
- `mul_add-simd2-clang-O2 simd_mul_add.goose`
- `mul_add-simd1-clang-O2 simd_mul_add.goose`
- `mul_add-simd0-clang-O2 simd_mul_add.goose`
- `mul_add-simd2-clang-O0 simd_mul_add.goose`
- `mul_add-simd1-clang-O0 simd_mul_add.goose`
- `mul_add-simd0-clang-O0 simd_mul_add.goose`
- `vec1-clang vec_elemwise.goose`
- `vec0-clang vec_elemwise.goose`
- `packed_word.py`
- `packed_word_contracts.py`
- `packed_word_residency.py`
- `benchmark declarations`
- `benchmark compatibility`
- `jit_clobbers.py`
- `conditional_shared_layout.py`
- `native_config_definitions.py`

During implementation, the first build caught use of a codegen-only IntSize
helper in the checker; it now uses the existing integer bit width. Focused
testing caught an invalid array cast and missing explicit multiple-result
return in test sources, then TinyCC's missing UINT64_C/INT64_C macros in
emission. Those were corrected. Generated-code test development also exposed
ordinary inference eliminating a constant caller's unrelated index check,
and the existing restriction against exporting a multiple-result function;
the final test exports only the unrelated single-result index function.
The final focused test, full suite and corpus results above include all fixes.

All implementation, tests, docs and evidence are committed in checkpoint
commits. The worktree build directory and generated C/binaries are removed
after validation; focused tests and corpus runs clean their temporary
artifacts on success and failure. No upstream or fork publication occurred.

## Draft change description

Read flat little-endian wire records with one recoverable extent check and
ordinary named struct fields. The new read_record_le builtin returns a fresh
snapshot and success flag, or a zero record on short input. Integer-only
layouts keep the compiler change small; boundary, signed-value, aliasing and
generated-code tests cover the contract across GCC, Clang and TinyCC.
