# Safer threading validation

## Piece B

Baseline: fork `dd8c82c55`, existing isolated values and shared atomics retained.
No compiler or runtime behavior change. Tests cover gated spawn snapshots,
helper/format transitivity, variable-size flat queue copies, repeated contained
joins, and ordinary C payload visibility after completion.

- Full baseline suite, GCC 14 plus Clang 23, O0/O2/debug/TinyCC: serial run
  recorded 5,090 passing section checks and three failures. Two were caused by
  putting the conda Clang installation's linker on GCC's PATH; the formatter
  saw a staged Piece C fixture before its syntax was implemented. All three
  checks passed on targeted rerun with only Clang/Clang++ wrappers on PATH and
  the future fixture moved out of the source tree.
- Full corrected-toolchain parallel run: all compiler/runtime, error, example,
  bootstrap and sample checks passed. Its only two failures were benchmark
  declaration/compatibility lock contention; both passed in the serial run.
  The benchmark lock was never removed or bypassed. Together these runs and
  the targeted rerun verify every section check (5,093), with no remaining
  functional failure.
- Focused C lifecycle/visibility fixture: GCC O2 and Clang 23 ASan/UBSan O1
  passed (`runtime thread cleanup ok`).
- The four reported upstream O2/debug dispatch/regex failures were not changed;
  they did not occur in these fork runs.

Commands: `python3 test/run_tests.py --exe build/goose --profile baseline
--cc native --require-clang -j1` (also `-j8`). Corrected PATH uses wrappers for
Clang 23.1.3 without placing its conda linker ahead of `/usr/bin/ld`.
Full outputs and the successful targeted rerun are in `evidence/piece-b-*.log`.

The Piece B follow-up separates the format-only global from the ordinary
helper-only global so neither graph edge can mask the other. It passed the
GCC/Clang Goose/C O0/O2/debug matrix and Clang ASan/UBSan; see
`evidence/piece-b-snapshot-final.log`. TSan also passed the controlled C
completion/lifecycle fixture (`evidence/piece-b-tsan.log`).

## Piece C

The opt-in `--strict-worker-native` setting reaches check/build/run and LSP.
Declaration suffixes are `worker_callable` and `main_thread_only`; an omitted
suffix is unclassified. Existing package main-thread restrictions take
precedence. The checked specialization graph is walked before optimization,
retaining helper/dispatch/format edges and rejecting all five unsafe pointer
builtins in strict workers. Diagnostics include the worker path and extern
source location. Default unclassified behavior is preserved.

Before implementation, the Piece B compiler accepted every graph/unsafe escape
source that the new contract requires rejecting. For this red run only, a
wrapper removed the not-yet-recognized strict flag to exercise the old checker;
new annotation syntax also lacked parser support. The retained failing output
is `evidence/piece-c-before-checks.log`. The final harness invokes the real
strict option directly, and also verifies default-mode compatibility.

Focused tests cover direct, recursive, generic, bound-function, dispatch and
format paths; per-declaration overload classification; package restrictions;
selected constant arms; imported dynamic-library declarations; conflicting
annotations; unsafe pointer operations including integer spawn arguments;
CLI verbs and actual LSP diagnostics. Acceptance includes copied mutable
globals, static literal views, local/resizable arrays, existing shared atomics,
and the native scheduler fixture. Native stdlib declarations receive no
implicit exemption: e.g. json float formatting reaches unclassified `ldexp`
until that native declaration is audited and annotated.

- Full baseline suite: **5,094 passing section checks, zero failures**; GCC 14,
  Clang 23 second frontend, native O0/O2/debug, TinyCC, bootstrap and samples.
  Audio/gfx/physics/ui layers are not built in and retain the suite's usual skips.
- Full Clang ASan/UBSan suite: 4,305 passing section checks and four toolchain
  failures (the installation has no `clang++` executable). All four passed
  targeted reruns using `clang --driver-mode=g++ --gcc-toolchain=/usr --sysroot=/`:
  compiler_roots, compiler_containers, compiler_process and library headers.
  Thus all 4,309 section checks are verified, with no unresolved failure. The
  final expanded strict harness also passed in that sanitizer rerun. The full
  failed run and successful reruns are both retained, not presented as a single
  zero-failure sanitizer invocation.
- Focused scheduler/strict tests passed GCC O0/O2/debug, Clang ASan/UBSan
  O0/O2/debug, and Clang TSan O0/O2/debug. All native fixture and separate-runtime
  compilation units receive the instrumentation flags.
- Worktree compiler SHA256 at validation:
  `b22468dd29f2d7f0d0f695707c498924f57651c8bbaf6867f66d76d28c8ae66a`.

Final full-suite and focused output is retained under `evidence/piece-c-*`.
No upstream dispatch/regex baseline fix was attempted; the four reported
upstream O2/debug failures are absent on this fork's baseline run.

## Slipstream acceptance and adoption

No Slipstream source was changed. Its pre-existing `experiment.md` and
`experiment-results.md` changes were left alone. Using the new compiler,
`make -B scheduler-test parallel-test parallel-jit-test` passed scheduler C
atomics/fallback/allocation checks, byte oracles and 100,000-job integration,
immutable metadata/planning, and 202 semantic/boundary regressions per validator
(release/debug/TinyCC), including contained failure and all-worker joins.

The parallel JIT script passed the serial/parallel output comparisons,
concurrent contexts, repeated pools, large streaming input and cleanup cases,
then failed its final `cached` input case with `byte 0: cannot read module`.
Rebuilding the same driver with the Piece B/pre-contract compiler reproduced
the identical failure at the same assertion. This is an external baseline
failure, not a successful full JIT acceptance claim. See
`evidence/slipstream-acceptance.log` and `slipstream-baseline-jit.log`.

The scheduler can use the existing fork `SharedAtomicU64` plus Relaxed
`atomic_fetch_add` for claims, keeping initialization before spawn and result
reads/destruction after every join. That requires threading the capability
through Goose workers and moving the claim into Goose; safe capabilities cannot
be converted to a pointer for its current C counter adapter. Strict adoption
also requires auditing/annotating the transitive native calls. Neither
migration was made here, and no new mutex, TLS API or ownership system was added.
