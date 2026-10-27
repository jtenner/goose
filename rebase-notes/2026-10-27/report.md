# Goose upstream rebase, 2026-10-27

The branch is ready for verification on the box. No build, test suite, or
benchmark ran on the laptop. No change was pushed. No pull request was opened.

## Branches and history

- Backup: `backup/2026-10-27-prerebase-goose` points to
  `3ef85aa33971632971c80665f4b3dca7d4131dbc`. This branch was created and
  checked before any other repository work.
- `master` still points to `3ef85aa33971632971c80665f4b3dca7d4131dbc`.
- Upstream base: `64d62fc7f148eadaed9b1c69be0c33d1da97c82f`.
- Shared old base: `a108677d300cb0e8bbb842c35a353abe67a20c6c`.
- Result branch: `rebase/goose-upstream-2026-10-27`.
- Last replayed commit: `df7d9c1f31ddd345af8d5fc625e6d20e0aafadf9`,
  `Defer benchmark artifact destinations until input discovery`.
- Final head is the commit that contains this report, named
  `Reconcile upstream test expectations and record rebase handoff`.
  Use `git rev-parse rebase/goose-upstream-2026-10-27` for its full ID.
- Replayed: **319 of 319**, including all **34 merge commits**. The final
  branch has **320 commits** after upstream: 319 replayed commits and one
  test-integration and report commit. No commit was squashed.
- NOT REPLAYED: **none**. There are no skipped-commit patches.

The rebase used `--rebase-merges --reapply-cherry-picks --empty=keep` with
`--no-update-refs`. The branch was already present in the assigned worktree
at the exact `master` commit when work started.

[commit-map.tsv](commit-map.tsv) lists all 319 original and new IDs. A graph
check confirmed each commit's author, author time, full message, parent count,
and ordered parent links. The old base maps to the new upstream base.

The UTF-8 fix `f38beb56` is retained as empty commit
`129055e564d7c3f7a0fbacc12dbbd9306046c4b8`. Upstream already supplies the
required continuation checks with a more complete decoder. Git first omitted
this commit after the conflict became empty. It was then inserted at its
original position, before the final 49 commits. The full graph check passed
after that repair.

## Conflicts

Each row is one original commit. **SEMANTIC** marks behavior or test coverage
that needs verification. The full file lists and new IDs are in
[conflicts.jsonl](conflicts.jsonl). The `conflicts/` directory contains the
unresolved combined diff for each row.

| Original commit | Files and resolution |
| --- | --- |
| `2ce51667` | `src/runtime_inline.h`: kept upstream's raw-string split before the free-slice comment and all memory API additions; text-only conflict. |
| `efc05e1b` **SEMANTIC** | `src/main.cpp`: kept build-definition propagation to `CheckRoundtrip` and upstream's `--stats` condition for its success message. |
| `244796b9` **SEMANTIC** | `src/codegen.h`, `test/run_tests.py`: kept unused-global analysis, library export-type setup, and all builder-return, worker-packet, and library-header test groups. |
| `f3bf1480` **SEMANTIC** | `test/run_tests.py`: kept both packed alignment test groups, as the original merge intended. |
| `61c195f0` **SEMANTIC** | `src/codegen.h`, `test/run_tests.py`: kept both code-generation calls and all three test groups. |
| `69b1c6e8` **SEMANTIC** | `src/codegen.h`: kept both calls in the original merge order: `FindUnusedLiteralGlobals`, then library `EmitExportTypes`. |
| `36823c6e` **SEMANTIC** | 14 files in the memory system, docs, and tests: kept the integrated memory and unsafe-pointer code, packed capability ABI, atomics, range borrows, alias invalidation, and qualified diagnostics; preserved both parents. The original merge changes only runtime string splits from its first parent. |
| `4ae3476c` **SEMANTIC** | 22 files in the compiler, memory runtime, docs, bench docs, and tests: kept integrated unsafe-pointer support, atomic checks, conditional parsing and scope, deferred state, source diagnostics, library headers, and test coverage; preserved both parents. The original merge changes only runtime string splits from its first parent. |
| `f38beb56` **SEMANTIC** | `stdlib/std.goose`: kept upstream `9a8adc29` UTF-8 decoding and its replacement rule; retained the fork fix as an empty commit and its tests as active tests. |

## Final integration changes

The final commit makes two test-only changes in addition to these notes:

1. `test/stdlib/stdlib_utf8.goose`: changed 11 expected values and one comment
   to upstream's one-replacement-per-maximal-subpart rule. All 31 check calls
   remain. For example, `E2 82 41` now expects `[65533, 65]`. The source code
   consumes the valid two-byte prefix together before reading ASCII `41`.
2. `test/run_tests.py`: removed duplicate builder-return and worker-packet
   registrations introduced while replaying merges. Each test group is still
   registered once. The resulting file matches a separate three-way merge of
   the complete old fork tree and upstream.

These are source-based rebase adaptations. They have not been executed.
The final integration commit changes no production code or hot path.

## Checks performed

- `git merge-base --is-ancestor 64d62fc7 HEAD` returned **0**.
- There are 319 mapped commits and 34 mapped merges before the final commit.
- All authors, author times, messages, and ordered parent links are preserved.
- The six embedded runtime files match `src/runtime/` byte for byte.
- Before the final integration commit, every file changed from the backup
  was also changed by the 18 upstream commits.
- A separate final-tree three-way merge found conflicts only in
  `src/main.cpp`, `src/runtime_inline.h`, and `stdlib/std.goose`. All other
  files match that reference merge, except the explicit UTF-8 fixture update.
- The reference merge returned 1 because of those three expected conflicts.
  It was a Git tree comparison, not a compiler or test failure.
- `git diff --check` passed for source and handoff files with the saved raw
  conflict diffs excluded. Those raw Git diffs keep their original whitespace.
  No conflict markers remain in the source tree.
- The protected bench worktree and its local edit were not accessed or changed.

One initial conflict edit removed too much runtime text. Its commit summary
exposed the error at once. That rebase attempt was aborted and restarted from
the original head. No part of that edit remains in this branch.

## Box verification

Run the checked-in script from the repository root on the box. Use the final
branch head and fresh build directories. Keep stdout, stderr, and exit codes.
The script stops at the first failed command. These commands were not run here.

```sh
git switch rebase/goose-upstream-2026-10-27
git status --short
git rev-parse HEAD
git merge-base --is-ancestor 64d62fc7 HEAD
bash rebase-notes/2026-10-27/verify-box.sh build
bash rebase-notes/2026-10-27/verify-box.sh bootstrap
bash rebase-notes/2026-10-27/verify-box.sh suite
bash rebase-notes/2026-10-27/verify-box.sh bench-checks
```

`build` makes fresh Debug and Release compilers. `bootstrap` runs the
Goose-in-Goose fixed-point check. `suite` runs the baseline suite with native
C and Clang coverage. `bench-checks` runs the bench tests, including lifecycle,
input identity, cache, migration, and isolation checks not all called by the
main suite.

After the box coordinator grants an exclusive measurement lease, run:

```sh
bash rebase-notes/2026-10-27/verify-box.sh bench-timings
```

This runs the sum/tree suites and the shared-native suite. It requires thermal
support. Record a failure if the box lacks that support; any ungated run needs
an explicit policy choice and must be labelled as ungated.

Give verification priority to the semantic rows above, `defer` scope exits and
`const if`, memory worker cleanup and native atomics, library-header generation,
UTF-8 replacement counts, f32 conversions and float formatting, and the bench
command's native build and cache paths. The main suite includes upstream tests
for vector arithmetic, TinyCC u64 conversions, parsing, and random integers.

Performance-sensitive changes include defer cleanup, vector arithmetic, u64
conversion, float parsing, UTF-8 decoding, random sampling, and bounds analysis.
Measurement is deferred to the box. No runtime, memory, or code-size gain is
claimed. Compare the preserved backup with this branch using matched builds
and workload inputs when the box measurement lease is active.

READY TO VERIFY: use `verify-box.sh build`, `bootstrap`, `suite`, and `bench-checks`; run `bench-timings` only under the box measurement lease.
