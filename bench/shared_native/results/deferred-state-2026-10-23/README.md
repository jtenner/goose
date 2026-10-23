# Deferred-state transaction correction

The first-write journal in `41dc6eb30e9363f1f97a51aeb047aad18d96746c`
removes the measured full-snapshot regression while retaining rollback and
unused-function checking. These are compiler `check` measurements, including
process startup and parsing, with no C generation or runtime execution.
Historical results in the parent directory remain unchanged.

## Measured results

O2 wall medians below use seven samples after two warmups. RSS is the median
of process peak RSS, in KiB. Speedup is **before / corrected**. The complete
[CSV](summary.csv) contains both O0/O2, median, MAD, min/max for wall and RSS,
and all 38 comparison ratios; the four JSON files retain every accepted sample.

| Source | Functions | Before ms | Corrected ms | Speedup | Before / corrected RSS KiB |
|---|---:|---:|---:|---:|---:|
| Ordinary, 500 globals | 250 | 71.256 | 23.535 | 3.03x | 9,380 / 8,660 |
| Ordinary, 500 globals | 500 | 130.846 | 26.041 | 5.02x | 11,148 / 10,204 |
| Ordinary, 500 globals | 1,000 | 346.469 | 32.559 | 10.64x | 15,084 / 13,268 |
| Ordinary, 500 globals | 2,000 | 806.918 | 44.771 | 18.02x | 23,800 / 19,848 |
| Ordinary, 500 globals | 4,000 | 1,695.320 | 69.615 | 24.35x | 39,304 / 33,076 |
| Actual `samples/parallel_wasm/main.goose` | — | 11.468 | 9.603 | 1.19x | 11,492 / 11,012 |

The std-import cases also include an unrelated named-return helper. All sizes
250/500/1,000 retain real computations; `calls` specializes a generic callee,
`stores` retains slices in arrays, and `deferred-stores` reaches a foreign
return after reference and store analysis. This exercises both successful and
deferred roots even when the program contains named returns.

| With std import, 1,000 functions, O2 | Before ms | Corrected ms | Speedup | Before / corrected RSS KiB |
|---|---:|---:|---:|---:|
| Ordinary | 273.357 | 38.971 | 7.01x | 18,044 / 16,272 |
| Calls | 333.809 | 48.755 | 6.85x | 25,400 / 21,852 |
| Stores | 384.553 | 50.207 | 7.66x | 32,636 / 26,072 |
| Deferred stores | 157.246 | 70.078 | 2.24x | 28,472 / 28,164 |

Across these std-import cases and all sizes/levels, speedup ranges from
1.42x to 8.03x. All 36 before/corrected comparisons improved their median
wall time and RSS. The smallest RSS improvement was 228 KiB (0.80%) for
1,000 deferred-store functions at O0; retained speculative objects still cost
memory. For ordinary 1,000/O2, wall MAD was 3.073 / 0.477 ms and ranges were
343.212–367.945 / 31.274–33.725 ms. At 4,000/O2 they were 2.845 / 0.216 ms
and 1,680.680–1,704.250 / 68.541–70.373 ms.

A separately measured upstream control uses exactly the ordinary 1,000-function
input. Here the baseline is upstream `94cc64d`, rather than the merged fork.

| Check | Upstream median / MAD ms | Corrected median / MAD ms | Corrected wall change | Upstream / corrected RSS KiB |
|---|---:|---:|---:|---:|
| O0 | 31.720 / 0.462 | 31.986 / 0.090 | +0.84% | 13,124 / 13,224 |
| O2 | 32.670 / 1.324 | 31.580 / 0.251 | −3.34% | 13,336 / 13,212 |

The small upstream differences overlap observed ranges: O0 wall
31.141–34.975 / 31.148–32.194 ms and RSS 12,956–13,436 / 12,968–13,368 KiB;
O2 wall 31.283–34.772 / 31.309–32.117 ms and RSS
13,148–13,372 / 12,968–13,516 KiB. The O0 median regressions are 0.266 ms
and 100 KiB (+0.76% RSS); these measurements do not establish a remaining
systematic overhead or an advantage over upstream.

## Protocol and provenance

Executed sequentially on Linux x86-64, AMD Ryzen 7 8845HS, CPU0, on
2026-10-23 from 18:34:07 to 18:35:52 UTC. Both compilers used GCC 14.2.0
Release `-O3 -DNDEBUG`. All 19 source cells ran at Goose O0/O2: 684 fresh
check processes, comprising 532 measured samples and 152 warmups. Baseline
and corrected order alternated per iteration. Every process succeeded; no
sample was retried or removed. No build, test or other benchmark ran alongside
the collection. Frequency was not fixed, and these local seven-sample results
are not a representative-project average or a statistical confidence interval.

The exact effective environment is in [commands.json](commands.json), including
`GOOSE_STDLIB=/home/dev/Projects/goose/stdlib` for every compiler. Only its six
listed environment variables were passed; all work/oracle/sanitizer variables
were absent. The harness pinned itself and inherited compiler affinity to
CPU0. GNU `/usr/bin/time` supplies peak RSS; Python's monotonic process-wall
interval surrounds the subprocess invocation, including its wrapper overhead.

| Role | Source commit | `src` tree |
|---|---|---|
| Before, merged fork | `8464cc68c3478fcdaf1884c64f13a704264e993c` | `2049b52b10eaf0192e66514fbac40bf5e2d0d3ec` |
| Corrected | `41dc6eb30e9363f1f97a51aeb047aad18d96746c` | `741cbecbd8b0f95e4ab9148161a5af870cb3ca12` |
| Upstream control | `94cc64daeabcae6f072dc1fe2b864acda5a001bc` | `3475e40623430a375683dce0f9bad35ebd7300e4` |

Compiler SHA256 values, unchanged before/after:

- Before: `c35d93ece5653cfd4d984295d91ac63db63c9b8873a3b6d10ea30503407ab327`
- Corrected: `169c9d41d2506b1c4e302be64cba35941d473d441b5e7debfb4e8c3322ecbcf1`
- Upstream: `f56ac3c31d3bbc1c200efc65d908063b9de9d4ae4127032c22f5432e9e8a5280`

Collection used harness commit `6c79197f17065396c95f84963e82c48cfb7eccd2`,
SHA256 `45ea33bbad28330174f4f03859a7e5587086e3daad1851d59566d0eea6fc7431`.
Its later tests/tooling commits do not change the corrected compiler source.
The earlier read-only plans were prepared at `d02a517d`; their recorded harness
hash therefore differs. Their exact commands and inputs were preserved.

[commands.json](commands.json) records the executed argv, dates, status,
binary checks and output hashes. [collect.py](collect.py) is the exact
sequential coordinator; [collection.log](collection.log) records transitions.
Each `*.processes.jsonl` retains all warmups, accepted samples, argv, output,
return codes, wall seconds and RSS. The per-plan logs and JSON checkpoints are
also retained. `inputs/` contains all 19 exact input texts;
[input-dependencies.json](input-dependencies.json) fingerprints the shared stdlib
and real sample directory, rechecked unchanged after collection.
[SHA256SUMS](SHA256SUMS) covers all artifacts, including this document and the
summary. Check it from this directory with `sha256sum -c SHA256SUMS`.

## Scope and remaining costs

These results measure removal of exhaustive deferred-state copying/scanning,
not linearity of the whole compiler. The inherited per-root global-flow
checkpoint remains O(U×G), global setup retains O(G²) work, and lookup,
provenance and large touched-record payloads have their own costs. The
4,000-function result holds globals fixed at 500. It does not establish
scaling when globals grow with functions. Quarantine retains discarded
allocations until AST destruction; no GC or runtime behavior changed.
The [design audit](../../../../docs/design/const_if_deferred_state.md)
describes the rollback barriers and deterministic work bounds.
