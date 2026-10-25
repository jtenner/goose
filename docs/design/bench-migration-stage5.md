# Native benchmark migration: stage 5

This change implements the Python integration and first migration groups from
`docs/design/bench_command.md` on `design/goose-bench-command`
(`b4c3ae23bf1c654ba88c7ba9b6aaa51aaf63968a`). Stages 1–4 are the base commit
`59e63282`. The migration map is the unchanged
[file inventory](bench-file-inventory.md), copied from `docs/bench-file-inventory`
at `a9ca81f07220f0a1a5b40900394326087885bcfc`. Its outputs describe the old
files at their old sizes; they are not measurements of the new entries.

Stage 5 expansion remains blocked until BLOCK design review findings 1–9 are
resolved. The artifact contract remains incomplete until finding 10 is
resolved. The input identity fixes alone do not remove either block.

## Completed groups

1. `bench/native_results.py` validates JSON v1, launches one file/key/size,
   checks the source and compiler hashes, flags, definitions, counts, isolation,
   thermal policy, ordered typed checksums, and successful completion.
   It retains the full native artifact and command log. Integer and boolean
   legacy lines have an exact conversion rule. Float lines require a separate
   audited rule; they are not rounded or joined into a hash.
2. `bench/run_bench.py` uses native rows for sum and tree by default. It stores
   median milliseconds and nullable RSS bytes. Native rows carry the complete
   report, function key, configuration ID, isolation and thermal policy. The
   report marks their timing scope and excludes them from legacy timing and
   memory ratios and geomeans. Foreign timers are unchanged.
3. `bench/shared_native/run.py` uses native `mmap` at O2. It maps accepted calls
   to samples, converts RSS bytes to KiB, derives rates from 64 mapping
   lifecycles, and checks the C checksum separately. Native/C order alternates
   by whole row across `--experiments`; legacy rows still alternate per sample.
   The parent releases the shared lock for the native supervisor and must
   acquire it again before C work. Raw native files survive beside the report.

The native command acquires the shared lock before benchmark compilation and
holds it until all workload process groups have been cleaned up. An occupied
lock prevents compiler launch. Listing entries does not acquire this lock.
On Linux, the supervisor adopts orphaned helpers, checks group signals, and
reaps the group before starting another row or releasing the lock. A cleanup
error fails the row. If termination cannot be confirmed, cleanup keeps the
lock and retries, even after its deadline; stderr reports this retained lock.
The caller's previous child-subreaper setting is restored after cleanup.

`--legacy-goose` keeps the old timing boundary and ordering for either harness.
The suite uses `results-native-v2.json` or `results-legacy-v2.json` under
`bench/gen`; the old `results.json` remains separate. Version 2 states are
replaced on each collection, including partial runs. Cross-run merging is
disabled until an experiment identity includes the measurement environment and
each retained row's dependency and configuration record. The current input and
policy fingerprint is evidence only; it is not sufficient for result reuse.
Environment descriptions use the host, CPU, RAM, OS, CPU affinity (where
available), and Rust version saved with the measurements. Older states without
that evidence report it as not recorded. There is no silent conversion of
historical timings. `--report-only` reads the selected version 2 state without
collecting data or probing the current host and compilers. `--skip-build` is
available for legacy rows; native rows build through the native command.

## Source and state audit

| Entry | Size map: small / medium / large | State and boundary |
|---|---|---|
| `sum_generated` | 1000000 / 16000000 / 128000000 | Local RNG reset to 12345, local array; construction, eight algorithmic passes, and local cleanup remain inside the entry. Returns length and total as two i64 values. |
| `tree_build_sum` | 16 / 20 / 24 | Global node pool grows during construction. The harness requires process isolation. Construction and eight passes remain inside the entry; global pool teardown stays outside function time and is a difference from the legacy process metric. Returns count and total as two i64 values. |
| `mmap_lifecycle` | Same 64 operations for every size | Uses a stable 16 MiB fixture passed as `BENCH_FIXTURE`. Each call opens, maps and closes it without touching pages. No mutable fixture, open mapping or worker survives. Process isolation is the initial harness mode. Returns mapped-byte checksum as u64. |

The suite's size values are checked against the two source maps in
`test/bench_migration.py`. Ordinary sum/tree `main` wrappers remain for legacy
runs and print both values in the original order. They require an explicit
quoted definition, for example `--define 'BENCH_SIZE="small"'`. The native
command supplies that definition itself. Goose files are no longer rewritten
for these entries; legacy and JIT suite paths use the same source with a size
definition. Other Goose files retain their old rewrite path.

## Remaining inventory and planned order

Stage 5 expansion remains blocked until findings 1–9 of BLOCK design review
`mcp:c782c063` are resolved. The artifact contract remains incomplete until
finding 10 is resolved.

These groups are deliberately left on the legacy path. Annotation support does
not by itself establish repeatability or equivalent work across languages.

| File in `bench/goose/` | Group / reason still unmigrated |
|---|---|
| `sum.goose` | Migrated in group 1. |
| `tree.goose` | Migrated in group 1; reuse remains unsupported by the suite. |
| `rng.goose` | Helper module with no workload or main; no benchmark entry needed. |
| `blur.goose` | Next local-state group; audit size-dependent layout and checksum. |
| `blur_assert.goose` | Same group; retain assertion work and compare variants. |
| `blur_rows.goose` | Same group; audit row layout and size mapping. |
| `particles.goose` | Next local-state group; preserve the explicit quantized float checksum rule. |
| `particles_scalar.goose` | Same group; pair with elementwise implementation. |
| `push.goose` | Next local-state group; preserve all four result components. |
| `push_ref.goose` | Same group; audit spare storage and reference lifetime. |
| `records_fixed.goose` | Next local-state group; preserve layout and construction work. |
| `records_var.goose` | Same group; compare the variable-size representation. |
| `respond.goose` | Next local-state group; preserve bytes and unsigned hash components. |
| `respond_stream.goose` | Same group; preserve the stream construction boundary. |
| `strlist.goose` | Next local-state group; audit input and owned-string cleanup. |
| `words.goose` | Next local-state group; preserve all three results and table work. |
| `words_dictionary.goose` | Same group; compare dictionary work and size map. |
| `graph.goose` | Global-state group; mutable global distance array needs an audit or process mode. |
| `graph_csr.goose` | Same group; global distance/output arrays. |
| `interp.goose` | Same group; global expression pool. |
| `scene.goose` | Same group; global node pool. |
| `lru.goose` | Same group; global slots and mask, six ordered results. |
| `lru_indices.goose` | Same group; pair slot reset and result audit. |
| `lru_nonopt.goose` | Same group; pair slot reset and result audit. |
| `calc.goose` | Parser group; global text, position, node count, eight results. |
| `calc_noerr.goose` | Same group; retain error-counter results even when zero. |
| `calc_noparen.goose` | Same group; preserve parser-specific work. |
| `calc_slices.goose` | Same group; mutable parser position and node count. |
| `sexp.goose` | Same group; global text, pools, roots and parser position. |
| `bintrees.goose` | Needs a stable scalar-return design for size-dependent, variable-length printed results. |

For shared-native, O0 mmap and all atomics, claims, scalar reads/writes,
publication, scheduling, copy and check variants remain legacy. Their timed
setup, capability lifetimes, workers and result rules need separate audits.
The native CLI currently couples O0 to debug checks; that is not the existing
release-runtime O0 experiment, so this change does not label it equivalent.
The C baseline remains unchanged. Vendored `bddicken` and `kostya` suites are
not migrated: they require an explicit maintenance decision. Goose-in-Goose
native execution and further platform/sensor support remain separate work.

## Verification and limits

No live benchmark timing runs were performed. Checks use synthetic JSON,
recorded inventory stdout, command mocks, source-size audits, report generation,
lock handoff, discovery and compiler dry runs. The inventory fixture tests
prove exact conversion of historical values, not execution equivalence of the
migrated code. In particular, the old sum inventory used N=4000000, which is
not one of the new named sizes.

Useful non-timing checks:

```sh
python3 test/bench_migration.py
python3 test/bench_experiment_isolation.py
python3 test/shared_benchmark_harness.py
python3 test/bench_report.py
python3 bench/run_bench.py --plan --only sum,tree --sizes small
python3 bench/shared_native/run.py --plan --case mmap --experiments 2
goose++ bench bench/goose/sum.goose --list --sizes small,medium,large
goose++ bench bench/goose/tree.goose --list --sizes small,medium,large
```

Deferred until an exclusive measurement window: live native/C checksum
equivalence at matched sizes; repeated-call validation in both isolation
modes where state permits; Linux Tctl smoke tests; timing distributions and
ordering effects; native/foreign RSS and allocation comparisons; runtime
overhead and code-size comparisons. No speed or memory improvement is claimed.
