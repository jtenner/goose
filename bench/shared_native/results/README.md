# Measured native-memory and compiler costs

Linux x86-64, AMD Ryzen 7 8845HS, Clang 23.1.3 generated C, GCC 14.2
Release (`-O3 -DNDEBUG`) Goose compiler, runtime `3a21ace949ed`. Source
`c66e6200fa20327f56dfe1569c26aa147e061123`, compiler SHA256
`5c9a0df6f5b1090acd02113aa1137c73b83d23aa2212398110a4c890b6cac60c`.

Seven samples after two warmups; 200,000 requested iterations, with the
per-case caps/work units described in [the harness](../README.md). Fifty
paired scenarios at native O0/O2 produced 700 samples in 900 sequential
workload processes. Affinity was pinned to CPUs 0,2,4,6,8,10,12,14 (one
logical CPU per physical core); frequency was not fixed. No competing build,
test or benchmark workload was observed at admission. The compiler-only
experiment followed sequentially on CPU0.

The C helper baseline lacks Goose generation checks, borrow authorization
and worker leases. Ratios therefore include the cost of those guarantees
and differing optimizer opportunities; they are not a safety-equivalent
language comparison. Wall time per completed unit includes worker pool
start/join where applicable. Parallel ns/unit is inverse aggregate
throughput, not an isolated atomic-instruction latency distribution.

## Native O2 medians

MAD is median absolute deviation of elapsed time, shown as a percentage
for C/Goose. All O0/O2 samples, min/max, checksums, units, flags, executable
and workload hashes are in the [raw record](linux-x86_64-2026-10-23.json).

| Workload (unit) | C ns/unit | Goose ns/unit | Goose/C cost | MAD % C/Goose | Goose units/s |
| --- | ---: | ---: | ---: | ---: | ---: |
| atomics_uncontended (fetch_add) | 2.347 | 2.175 | 0.93x | 4.0/6.3 | 459,868,432 |
| atomics_contended (fetch_add) | 2.454 | 2.362 | 0.96x | 2.9/1.9 | 423,372,714 |
| claims (useful_job) | 2.444 | 2.743 | 1.12x | 0.7/2.0 | 364,517,834 |
| scalar_read_latency (scalar_read) | 1.355 | 6.880 | 5.08x | 0.4/5.5 | 145,340,915 |
| scalar_write_latency (write_read_roundtrip) | 0.341 | 13.732 | 40.32x | 1.1/3.6 | 72,821,570 |
| scalar_read_throughput (scalar_read) | 0.300 | 6.806 | 22.71x | 9.2/2.7 | 146,918,441 |
| scalar_write_throughput (scalar_write) | 0.271 | 6.562 | 24.24x | 2.1/2.8 | 152,388,470 |
| publication (handshake) | 148.058 | 269.063 | 1.82x | 5.1/4.7 | 3,716,596 |
| scheduling (worker_start_and_join) | 17814.760 | 17814.765 | 1.00x | 1.2/2.7 | 56,133 |
| mmap (mapping_lifecycle) | 8961.062 | 8739.391 | 0.98x | 8.0/14.9 | 114,424 |
| copy (byte) | 0.019 | 0.018 | 0.95x | 4.2/5.0 | 55,070,281,346 |
| checks_disabled (emission_operation) | 0.144 | 0.158 | 1.09x | 10.7/3.4 | 6,347,392,808 |
| checks_enabled (emission_operation) | 0.159 | 0.133 | 0.84x | 14.9/17.3 | 7,493,443,237 |

Checked scalar operations cost substantially more than the weaker baseline:
read latency is 5.08x, write/readback 40.32x, scalar read throughput cost
22.71x and write throughput cost 24.24x in this workload. The source-level
write/readback can be forwarded by the C optimizer. Its C baseline takes
only 68 microseconds (0.341 ns per source round trip), so the 40.32x ratio
compares against a largely optimized-away loop, not physical store latency.
Thirty-six of the 100 measured group medians are below 1 ms. Exact ratios
are specific to this host and optimizer, especially in these short windows.
No broad performance improvement is
claimed. Smaller differences in atomics, copying and mapping overlap the
observed variation.

## Worker counts at native O2

| Workers | Uncontended atomic Mops/s | Contended atomic Mops/s | Claims Mjobs/s | Start/join workers/s | Start/join Goose/C cost | Start/join MAD % C/Goose |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 459.87 | 423.37 | 364.52 | 56,133 | 1.00x | 1.2/2.7 |
| 2 | 887.97 | 140.85 | 150.35 | 68,068 | 1.04x | 3.4/4.6 |
| 4 | 1515.52 | 155.12 | 131.89 | 73,358 | 1.20x | 3.4/4.9 |
| 8 | 3111.17 | 172.94 | 156.37 | 56,546 | 1.21x | 0.6/1.7 |

The 1.00x scheduling entry above describes one worker. At four and eight
workers, start/join costs 20% and 21% more than the C baseline, with the low
variation shown here.

Claim MAD reaches 20.5%/22.6% for two/four Goose workers; eight workers
reach 11.3%. Mapping Goose MAD is 14.9% at O2. Twelve of the fifty pairs
have at least one implementation at or above 10% MAD. These short local
measurements do not establish small speedups or universal scaling. The
whole-process mmap peak RSS medians are C 1,976 KiB / Goose 2,168 KiB at
O2 (O0: 1,984 / 2,164 KiB); pages in the 16 MiB input were not touched.
Copying measures about 55.1 GB/s (51.3 GiB/s) for Goose at O2. Its zero
checksum is weak correctness evidence; independent copy tests establish
correctness. Disassembly retains repeated 524,288-byte memcpy calls in the
C O2 loop, so the measured baseline copy loop was not eliminated.

## Compile-time-disabled checks

Unchecked generated C contains neither ownership fields nor the diagnostic
sentinel, at native O0/O2. The dedicated clobber regression separately
checks calls, data, parameters and object symbols at Goose/native O0/O2.

| Goose artifact | Whole-binary instructions | Application instructions |
| --- | ---: | ---: |
| goose_native/-O0/False | 10286 | {"main": 23, "main_g": 2905} |
| goose_native/-O0/True | 10349 | {"main": 23, "main_g": 2968} |
| goose_native/-O2/False | 6613 | {"main": 3389} |
| goose_native/-O2/True | 6613 | {"main": 3389} |

The checked/unchecked O2 binaries each have 6,613 instructions because the
native optimizer also proves this benchmark's enabled checks redundant.
Timing differences in that pair cannot isolate check-removal overhead.
At O0 the checked application has 63 additional instructions. Whole-binary
counts include runtime code, so they are not counts of validation alone.

## Compiler regression: ordinary unused functions

A synthetic ordinary source contains 500 i64 globals and 1,000 unused
zero-argument functions plus empty main. It has no new syntax or imports.
Both Release compilers run `check`, with the same generated source and no C
generation. Each of the four groups has seven process-wall samples after
two warmups; implementation order alternates. GNU time supplies peak RSS.
The exact source generator, input hash, binaries and samples are in the
[compiler record](compiler-check-linux-x86_64-2026-10-23.json).

| Check | Baseline median / MAD ms | Extended median / MAD ms | Time ratio | Baseline / extended RSS KiB |
| --- | ---: | ---: | ---: | ---: |
| -O0 | 33.292 / 1.085 | 349.156 / 1.446 | 10.49x | 13,192 / 14,916 |
| -O2 | 32.871 / 0.608 | 349.121 / 1.292 | 10.62x | 13,116 / 14,960 |

This is a measured regression of about 10.5x at this synthetic workload's
size, not a fixed multiplier, runtime JIT cost or representative-project
average. Each unreached function takes a deferred-state snapshot that copies
the live variable definitions and scans the type collection. Its bookkeeping
therefore grows with unreached functions times live variable definitions;
it can grow quadratically as those functions introduce more definitions.
Larger codebases can regress more than 10.5x. The independent reviewer used
counting-only instrumentation (no timing): 250/500/1,000 unreached functions
with the same 500 globals produced 156,375/375,250/1,000,500 variable-definition
copies. That identifies scaling in the bookkeeping, without measuring how
much of elapsed time it causes. No time profile was collected. The
correctness transaction is retained and this compiler cost is disclosed.

Reproduce the experiments with `run.py --run --samples 7 --warmups 2
--iterations 200000` and `compiler_check.py --run --baseline /path/to/upstream
--extended /path/to/final --output /tmp/check.json`, under the affinities
above. Native results use the exact compiler in the record; rebuild hashes
may differ. The [environment record](environment-linux-x86_64-2026-10-23.json)
retains admission, commands, successful native run and corrected frontend
retry. The first frontend generator accidentally used reserved function
names f32/f64 and stopped during its first warmup; it yielded no accepted
samples. Only the corrected check_fn_* source is summarized here. No failed
or noisy sample has been selectively removed from the accepted datasets.
Benchmarks are not correctness evidence.
