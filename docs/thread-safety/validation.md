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
