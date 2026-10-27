#!/usr/bin/env bash
# Run only on the box. Select one phase explicitly.
set -euo pipefail

cd "$(dirname "$0")/../.."
goose_debug="$PWD/build-rebase-20261027-debug/goose"
goose_release="$PWD/build-rebase-20261027-release/goose"

case "${1:-}" in
  build)
    cmake -S . -B build-rebase-20261027-debug -DCMAKE_BUILD_TYPE=Debug -DGOOSE_BUILTIN_LIBS=all
    cmake --build build-rebase-20261027-debug --config Debug --parallel 2
    cmake -S . -B build-rebase-20261027-release -DCMAKE_BUILD_TYPE=Release -DGOOSE_BUILTIN_LIBS=all
    cmake --build build-rebase-20261027-release --config Release --parallel 2
    ;;
  bootstrap)
    python3 test/run_tests.py --goose-in-goose-only --exe "$goose_debug" --profile baseline --cc native
    ;;
  suite)
    python3 test/run_tests.py --exe "$goose_debug" --profile baseline --cc native --require-clang
    ;;
  bench-checks)
    # Run in sequence. Several checks use the shared benchmark lock.
    for script in bench_declarations bench_runtime bench_checksums bench_compatibility \
        bench_lifecycle bench_input_identity bench_cmake_inputs bench_compile_arguments \
        bench_missing_source bench_runtime_cache; do
      python3 "test/$script.py" "$goose_release"
    done
    for script in bench_thermal bench_report bench_migration bench_experiment_isolation \
        shared_benchmark_harness; do
      python3 "test/$script.py"
    done
    ;;
  bench-timings)
    # Start only after the box coordinator grants an exclusive measurement lease.
    evidence_dir="$(mktemp -d /tmp/goose-rebase-20261027-box.XXXXXX)"
    printf 'Box measurement files: %s\n' "$evidence_dir"
    python3 bench/run_bench.py --exe "$goose_release" --only sum,tree \
      --sizes small,medium,large --samples 7 --warmups 2 --temperature required \
      --out "$evidence_dir/sum-tree.md"
    python3 bench/shared_native/run.py --run --goose "$goose_release" \
      --samples 7 --warmups 2 --experiments 2 --temperature required \
      --directory "$evidence_dir/shared-build" --output "$evidence_dir/shared.json"
    ;;
  *)
    printf 'Usage: bash %s {build|bootstrap|suite|bench-checks|bench-timings}\n' "$0" >&2
    exit 2
    ;;
esac
