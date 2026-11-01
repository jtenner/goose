# Packed-word implementation validation

Branch: `feat/packed-word`, created from `design/packed-word`.
Compiler tested: `5a48b687` (the final documentation checkpoint adds no compiler changes).
Date: 2026-11-01. Native target: Linux x86-64, GCC 14.2.0 and Clang 23.1.3.
No merge or push was performed.

## Phase checkpoints

| Phase | Status | Checkpoint |
|---|---|---|
| 1: parser, AST, tooling | Implemented | `54b45276` |
| u128 prerequisite | Independently tested before packed layout/lowering | `129f71cc`, `5b9e1b6d` |
| 2: checker and layouts | Implemented | `a3e2ec97` |
| 3: scalar C generation/runtime | Implemented | `7649f078` |
| 4: acceptance and residency evidence | Implemented; final regression run below | `b67207f0` |
| Regression corrections | TinyCC masks, u128 shifts, signed comparisons, narrowing guards | `5a48b687` |
| 5: documentation and sample | Implemented in the documentation checkpoint containing this report | — |

All five backings ship. u128 was not reduced to a two-field aggregate or
removed from scope. Its portable constant and independent native scalar
checkpoints preceded packed-word checking and lowering. The implementation
stayed within the original rough size estimates; it did not require a scope
reduction. Nominal declaration infrastructure is reused with an explicit
packed-word discriminator; the emitted representation is still the scalar.

## Focused checks

| Driver | Passing checks |
|---|---:|
| `test/compiler_uint128.py`: Python oracle, portable two-limb arithmetic, UBSan | 12,017 |
| `test/u128.py`: independent native scalar oracle, C O0/O2, GCC/Clang, UBSan | 850 |
| `test/packed_word_check.py`: diagnostics and selected-branch checking | 38 |
| `test/packed_word.py`: every width, raw preservation, values, placement, serialization, enums, traps, u8–u64 JIT | 6,111 |
| `test/packed_word_contracts.py`: configurations, defaults/evaluation order, worker values, contended CAS | 76 |
| `test/packed_word_residency.py`: C shape, native ABI, disassembly, unsupported backend | 35 |
| `test/packed_word_editor.py`: fresh true/false-configured LSP sessions | 10 |
| **Total driver assertions** | **19,137** |

Additionally, all 27 tree-sitter corpus cases pass, and the sample produces
all 3 expected output lines. The repository-wide tree-sitter sweep parsed
3,112 files and reported 141 existing failures. A clean temporary parser built
from the design-branch grammar reported 142 failures on that same file set:
no new failures, and the new packed-word syntax fixture now parses. The
remaining failures concern pre-existing grammar gaps such as root structs
and ordinary conditional fields; they were not changed by this feature.

The native drivers compile actual generated C at both O0 and O2 under UBSan,
not only different Goose inlining levels. Runtime out-of-range writes and
invalid enum reads are checked in release builds. Raw invalid enum bits can
be copied and preserved while unrelated fields are updated. Existing native
memory/atomic misuse and order regressions pass in the full suite.

## Residency evidence

[Recorded C and disassembly](packed-word-residency.txt) contain all four u64
leaf kernels (extract, replace known-fit field, construct, equality), their
handwritten counterparts, exact compiler versions, target and flags.
Both GCC and Clang at O2 produce register arguments/results with **no stack
loads/stores, stack allocation, or helper calls** in those leaf symbols.
The test marks the leaf definitions noinline/used and calls through exports
from a separately compiled C host, so inlining cannot hide an aggregate ABI.
The host also roundtrips a high-half u128 value using the generated header.
Address-taking and register-pressure cases remain outside this no-spill claim.

## Full repository run

Command:

```sh
python3 test/run_tests.py --exe /home/dev/Projects/goose/build/goose \
  --profile baseline --cc native --require-clang -j 8
```

Final result: **5,723 passing runner checks, 2 failures**, 79.5 seconds.
The seven focused drivers count as seven checks in this runner total; their
19,137 internal assertions above are not added again. The complete
[runner log](packed-word-full-suite.txt) records the section counts and failures.

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
| packed words and portable u128 | 7 | 0 |
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

The two failures are `benchmark declarations` and `benchmark compatibility`.
Both abort because another process already holds
`/tmp/goose-shared-native-benchmark.lock`; they fail before the intended
benchmark assertions. That process and its lock were left intact. Rerunning
those two tests after the benchmark owner releases the lock remains deferred.

Environment-supported skips remain visible: 31 optional native-module tests,
51 unsupported JIT fixture configurations, 5 optional native-module samples,
3 unsupported JIT sample configurations, transparent huge pages unavailable,
and the Windows-only commit-limit check. These are separate configurations,
not necessarily distinct source files. Audio/gfx/physics/ui are not built
into this compiler.

The first full run exposed and led to a TinyCC mask fix. A separate scalar
audit found high-literal shift folding and led to dedicated regressions.
That run also exposed GCC accidentally finding the Clang distribution's
linker through PATH. The final run exposed only the Clang driver executables,
leaving GCC's assembler/linker discovery intact. No failure expectations or
benchmark locks were bypassed to obtain the final counts.

## Limits and cleanup

Approved v1 exclusions remain: signed narrow fields, pinned positions,
generic packed declarations, and field reflection. Native u128 requires
unsigned __int128 support; TinyCC rejects it explicitly. u128 atomics and
128-bit native memory scalar APIs are not added. Existing 64-bit index/count
APIs require explicit conversion; scalar shifts accept u128 counts.

The tests cover source-reachable enum layouts and configured raw encodings.
They do not inject corrupt enum metadata into a live checker or directly
compare the private fingerprint strings through a testing API. The checker
stores the fingerprint and checks inferred enum widths; these two proposed
white-box test cases remain validation limitations. No public fingerprint
builtin was part of v1.

Focused tests remove their temporary files on success and failure. Full-suite
generated directories were isolated, removed, and pre-existing directories
restored. Generated tree-sitter parser files and its temporary installation
were removed. Only source, sample, documentation, and textual evidence are
committed; no C binaries, assembly objects, generated runtime cache, or test
executables are included.
