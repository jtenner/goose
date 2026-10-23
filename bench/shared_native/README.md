# Native shared memory experiment

`python3 bench/shared_native/run.py` prints the plan and does no compilation
or timing. `--prepare --goose /path/to/goose --directory /tmp/goose-bench`
compiles only and reports generated C and binary size/instruction inspection.
Run `python3 test/shared_benchmark_harness.py` for the read-only plan contract.

The parent must coordinate an idle machine before explicitly running:

```sh
python3 bench/shared_native/run.py --run --goose /path/to/goose \
  --cc /path/to/clang --samples 7 --warmups 2 --iterations 200000 \
  --output /tmp/goose-shared-results.json
```

All workloads run sequentially, with a process lock preventing another copy
of this harness. That lock cannot stop unrelated compilers or experiments;
the parent coordinates those. There are no committed timing results. Results
are performance measurements, never correctness evidence. Acceptance tests
are in `test/parallel_wasm.py` and `test/jit_clobbers.py`.

Both implementations do the same work and report seconds, work units and an
observable checksum. The standalone C11/pthreads baseline represents old
native-helper style code; only benchmarks contain application C helpers.
It has bounded pointer reads/writes and direct atomics, but does not provide
Goose's generation-safe capabilities, borrow authorization, or worker leases.
This comparison measures the cost of those guarantees too. It is not an
assertion that equivalent safety has been implemented in C. Both are built
with explicit native C `-O0` and `-O2`; Goose specialization is `-O2` in both.
A compiler fence prevents baseline loops from losing repeated memory work;
checked Goose operations have observable runtime validation calls. This
fence has no hardware instruction cost but can limit C optimization.

Cases and units:

- Uncontended atomics use one counter per worker; contended atomics use one
  counter. Units are completed fetch-adds. Independent counters are 64 bytes
  apart, with a 64-byte-aligned region, to avoid false sharing on typical
  x86-64 cache lines. Record the host before interpreting scalability.
- Claims share a Relaxed fetch-add index with a bound, as in the example.
  Units are useful jobs, excluding final out-of-range claims.
- Scalar read latency follows a dependent 8,192-element ring. Write latency
  is a dependent checked write/readback round trip, not pure store latency.
  Throughput runs four independent scalar addresses per iteration. Units
  are scalar reads/writes (write latency includes its readback).
- Publication performs an Acquire/Release ping-pong with a protected scalar
  payload, always with two workers; units are complete handshakes.
- Scheduling starts and joins 1/2/4/8 native workers per round. Units are
  workers scheduled, including startup and join. Atomic/claim timings also
  include their single pool startup and join.
- Mmap repeatedly opens, validates, maps and closes a 16 MiB sparse file;
  units are complete mapping lifecycles. Pages are not touched, so this
  measures mapping latency and process peak RSS, not resident file capacity.
- Copy repeats 512 KiB memmoves; units are bytes copied. Both begin zeroed.
- Checks run identical emission bookkeeping with/without conditional owner
  tracking. Units are emission operations. Optimizers may prove enabled
  checks redundant; report the observed result instead of assuming overhead.

Seven samples follow two warmups by default. C/Goose order alternates per
sample; no samples run simultaneously. JSON retains every sample, medians,
median absolute deviations, min/max, CPU, process affinity, platform,
compiler identity/flags, generated C metrics and whole-binary instruction
counts when objdump exists. `/usr/bin/time` supplies process peak RSS in KiB
on Linux, including runtime/thread infrastructure, not just mapped pages.
Whole-binary counts include runtime code, so use generated C marker absence
and the dedicated clobber acceptance test for compiler-elimination evidence.
Warmups exercise the OS caches in separate processes, rather than preserving
thread or allocator state across samples. Small timings can fall below timer
resolution; increase iterations and inspect variation before drawing claims.
