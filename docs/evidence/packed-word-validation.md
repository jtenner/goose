# Packed-word v1 scope and validation

Branch: `feat/packed-word`, based on `design/packed-word`.
Scope authority: owner decision **2026-10-31 23:51 ET**, superseding the
previous five-backing authorization. This report supersedes the earlier u128
implementation results. No merge or push was performed.

## Scope correction

V1 backings are **u8, u16, u32 and u64**. Field descriptors and read carriers
cap at 64 bits. `packed word W : u128 { ... }` produces exactly one primary
diagnostic, `128-bit packed word backings are not yet supported`, and emits
no C or aggregate fallback. u128 is deferred until a concrete two-word need
drives a separately approved round.

The general u128 type, lexer keyword, widened literal/constant storage,
constant arithmetic helper, folding and match extensions, code generation,
runtime arithmetic, formatting, serialization and ABI support are removed.
The positive u128 scalar drivers are deleted; only rejection tests remain.
Eight affected files match the design-branch baseline byte for byte:
`src/lexer.h`, `src/clone.h`, `src/bce.h`, `src/optimize.h`,
`src/codegen_stmts.h`, `src/runtime/runtime.h`, `src/runtime_inline.h` and
`src/typecheck_builtins.h`. Pre-existing internal wide-product helpers for
ordinary u64 division remain unchanged; they are not a Goose u128 scalar.

The complete diff against `design/packed-word`, including documentation and
textual evidence, remains below 3,000 added-plus-removed lines. There is no
size overrun. The reduced implementation reuses the existing scalar machinery.

## Phase status

| Phase | Current status |
|---|---|
| 1: parser, AST and tooling | Complete; four backings, dedicated u128 rejection, editor grammar updated |
| 2: checker/layouts | Complete; widths/carriers capped at 64, ordinary constants unchanged |
| 3: C generation/runtime | Complete; scalar u8–u64 lowering, no new 128-bit scalar/runtime support |
| 4: tests/evidence | Focused suites pass; full run completed with two externally blocked benchmark tests |
| 5: documentation/sample | Complete; dated scope note, sections 6–10, references and evidence agree |

The original phase checkpoints remain in branch history. Their u128
prerequisite commits are superseded by the scope-correction commit containing
this report; the final source tree contains none of that general scalar work.

## Focused results

Linux x86-64, GCC 14.2.0 and Clang 23.1.3; generated C tested at real O0/O2
with UBSan, with TinyCC execution for supported packed words.

| Driver | Passing assertions |
|---|---:|
| `test/packed_word_rejection.py`: one diagnostic, no C output, unsupported widths/type/literals | 24 |
| `test/packed_word_check.py`: layout, constructors, mutability, casts, bit-view references | 38 |
| `test/packed_word.py`: every width 1–64, preservation, values, placement, serialization, enums, traps, JIT | 3,038 |
| `test/packed_word_contracts.py`: conditional layouts, defaults/order, worker copies and contended CAS | 76 |
| `test/packed_word_residency.py`: scalar C shape, ABI and disassembly | 32 |
| `test/packed_word_editor.py`: fresh configured LSP sessions | 10 |
| **Total** | **3,218** |

All **27 tree-sitter corpus tests** also pass after removing the u128 type
and backing grammar. Tests create artifacts in temporary directories and
remove them after execution.

[Updated residency evidence](packed-word-residency.txt) records extract,
known-fit replace, construction and equality leaf kernels plus handwritten
counterparts. Both GCC and Clang at O2 show **no stack loads/stores, stack
allocation or helper calls** in these u64 leaves. Leaves are explicitly
noinline/used in test C, and a separately compiled C host exercises exported
call boundaries. This does not promise no spills under register pressure or
when a whole-word address is taken.

## Full repository suite

```sh
python3 test/run_tests.py --exe /home/dev/Projects/goose/build/goose \
  --profile baseline --cc native --require-clang -j 8
```

Result: **5,722 passing runner checks, 2 failures**, 72.2 seconds. The six
focused drivers count as six runner checks; their internal assertions are
reported separately above. [Complete log](packed-word-full-suite.txt).

| Section | Pass | Fail |
|---|---:|---:|
| lexer and shader compiler | 5 | 0 |
| parse, roundtrip and typecheck | 1511 | 0 |
| optimizer, stack report and C shapes | 22 | 0 |
| bounds-check annotations | 64 | 0 |
| generated C, built and run at -O0 and -O2 | 723 | 0 |
| dump-runtime programs | 13 | 0 |
| GS_DEBUG programs | 216 | 0 |
| compiler roots, runtime lifecycle and clang | 23 | 0 |
| unsafe raw atomics | 1 | 0 |
| worker native contract | 1 | 0 |
| builder return alignment | 1 | 0 |
| worker packet alignment | 1 | 0 |
| library headers | 1 | 0 |
| packed words | 6 | 0 |
| driver, diagnostics and language server | 55 | 2 |
| native example acceptance | 13 | 0 |
| native builds, packages and runtime I/O | 13 | 0 |
| goose_in_goose bootstrap | 23 | 0 |
| JIT (TinyCC) runs | 879 | 0 |
| parse errors (errors/) | 94 | 0 |
| typecheck errors (errors_tc/ and native modules' rejection tests) | 1980 | 0 |
| recovery (errors_tc/recovery/) | 17 | 0 |
| long call chains and guard runs | 6 | 0 |
| language reference examples (docs/reference.md) | 1 | 0 |
| samples | 53 | 0 |

Both failures (`benchmark declarations`, `benchmark compatibility`) result
from another process holding `/tmp/goose-shared-native-benchmark.lock`.
They abort before their intended benchmark assertions. The lock and its
owner were left intact; rerun these tests when that owner releases the lock.
All other executed sections pass, including compiler bootstrap, native/JIT
fixtures, memory/atomic regressions and reference examples.

Existing environment skips remain: 31 optional-module test configurations,
51 unsupported JIT fixture configurations, 5 optional-module samples,
3 unsupported JIT sample configurations, unavailable transparent huge pages
and the Windows-only commit-limit test. The earlier repository-wide
tree-sitter comparison found 141 pre-existing parse failures and no new
failures; this scope round reran the complete 27-case corpus.

## Deferrals and cleanup

u128 and all general 128-bit scalar work are deferred by the dated owner
scope decision, to be driven by a concrete two-word need. The other approved
v1 exclusions remain unchanged: signed narrow fields, pinned positions,
generic packed declarations and field reflection.

The earlier white-box validation limits also remain unchanged: source-level
layout/enum tests run, but there is no injected-corrupt-enum-metadata fixture
or direct comparison of private fingerprint strings through a testing API.
No new deferral was introduced for the supported four backings.

Full-suite generated directories were isolated, removed, and pre-existing
ones restored. Tree-sitter generation/install ran in a temporary directory.
Only source, documentation, sample and textual evidence are committed;
no generated C, binaries or test executables are retained.
