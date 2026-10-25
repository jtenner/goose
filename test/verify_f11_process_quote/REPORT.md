# Goose F11 fix

Branch: `fix/goose-f11-process-quote`.
Baseline: `ad75c5af7afdd589a9ba215e9e04ac9b01f24505`.
Test checkpoint: `c785d0f7`.
Fix checkpoint and tested source: `63d62f302203decf92655567a20774e7bf9152aa`.
The final report commit is given in the final handoff.

The fix adds `*`, `?`, and `[` to the quote check in
`src/process.cpp:240`. The formatter now puts literal wildcard arguments
in double quotes. A POSIX shell then keeps each pattern as one literal
argument. The product change is one line.

The checker and driver came from verification branch
`verify/goose-f11-process-quote-r2` at `3dc444b1`. The only checker change
sets the default source reference to `HEAD`. It builds committed production
source, not the working tree. Use `--ref` to select another commit.

Focused checks run:

```sh
python3 test/verify_f11_process_quote/check.py --ref ad75c5af7afdd589a9ba215e9e04ac9b01f24505
python3 test/verify_f11_process_quote/check.py --ref 63d62f302203decf92655567a20774e7bf9152aa
```

Both native builds passed with Debian C++ 14.2.0 on Linux. The shell was
`/usr/bin/dash`. The fixture directory contained `a.c` and `b.c`.

- Before the fix: exit 1. All three controls passed. Each wildcard case
  (`*.c`, `?.c`, `[ab].c`) became two arguments, `a.c` and `b.c`.
- After the fix: exit 0. All six cases passed. Each wildcard stayed one
  unchanged argument. The controls were `plain.c`, `two words.c`, and one
  empty argument. The checker tests the count and exact argument values.
- Raw build commands, source hashes, binary hashes, outputs, and exit
  codes are in `evidence/before.*.txt` and `evidence/after.*.txt`.

The test was committed before the source fix. No full suite, full Goose
build, benchmark, or timing test was run. No merge was made. Windows and
macOS shell behavior was not tested. This fix covers literal wildcard
characters; it does not establish correctness for all shell syntax.

One independent GPT-6.1-Sol reviewer used high reasoning and read all
requested source and test files. It found no remaining defect in this scope.
It confirmed the count check for the empty argument and the one-line fix.
It did not run tests or inspect the saved run evidence. The parent checked
its findings against the source and raw results. The full review is in
`evidence/gpt-review.txt`.

Claude Code was run from this repository root with normal authentication,
model `opus`, effort `high`, read-only tools `Read,Glob,Grep`, MCP tools
disabled, and permission mode `dontAsk`. The exact commits, diffs, source
paths, required behavior, and raw results were supplied without prior
review findings. Claude exited 1 with a session-limit message. It did not
return a review, so its review scope is incomplete. The launch arguments,
brief, diffs, stdout, stderr, and exit code are in
`evidence/claude-review/`. The original packet is outside the source tree at
`/tmp/goose-f11-fix-slivfzho`. No credentials were accessed or changed.

Performance remains unmeasured. `CommandLineText` runs for verbose output,
dry-run output, and build-failure diagnostics in `src/build.h`. The larger
character set can affect its scan cost. Arguments with wildcards now use
the quote loop and add two quote bytes. This can affect string growth and
allocations. Process execution still receives the original argument vector.

Proposed later workloads compare the baseline and fix with the same native
optimized build and environment: plain argument lists; lists with many
wildcards; long arguments with a wildcard near the start or end; and large
argument vectors near string-capacity boundaries. Measure formatter CPU
cost, allocation count, allocated bytes, peak memory, and code size. Use
dry-run and verbose build commands to check the end-to-end effect. Keep
output handling identical between builds. No performance gain or minimal
memory footprint is claimed from the correctness checks.

READY TO MEASURE
