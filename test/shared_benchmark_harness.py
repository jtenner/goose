#!/usr/bin/env python3
"""Phase11 structural harness contract; does NOT run timing workloads."""
import hashlib
import importlib.util
import tempfile
import json
from pathlib import Path
from native_examples_support import ROOT, run

HARNESS = ROOT / "bench/shared_native/run.py"
plan = json.loads(run(["python3", HARNESS, "--plan"]).stdout)
assert plan["samples"] >= 5 and plan["warmups"] >= 1
assert set(plan["workers"]) == {1, 2, 4, 8}
assert {"atomics_uncontended", "atomics_contended", "claims", "scalar_read_latency",
        "scalar_write_latency", "scalar_read_throughput", "scalar_write_throughput", "publication",
        "scheduling", "mmap", "copy", "checks_disabled", "checks_enabled"} <= set(plan["cases"])
assert set(plan["implementations"]) == {"c_baseline", "goose_native"}
assert plan["run_requires_explicit_flag"] is True
assert plan["units"]["copy"]["work_unit"] == "byte"
assert plan["units"]["scalar_write_latency"]["work_unit"] == "write_read_roundtrip"
assert plan["total_workload_processes"] == 900 and plan["measured_processes"] == 700
assert plan["warmup_processes"] == 200 and plan["maximum_worker_threads"] == 8
claims = json.loads(run(["python3", HARNESS, "--plan", "--case", "claims"]).stdout)
assert claims["cases"] == ["claims"] and claims["total_workload_processes"] == 144
# No toolchain required to review the experiment; invocation without --run is read-only.
assert json.loads(run(["python3", HARNESS]).stdout) == plan
print("benchmark harness plan acceptance passed (no timings run)")

# Synthetic samples verify reported variation/medians without running workloads.
spec = importlib.util.spec_from_file_location("shared_native_bench", HARNESS)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
values = [{"seconds": t, "units_per_second": 100 / t, "ns_per_unit": t * 1e7}
          for t in (1, 2, 3, 4, 100)]
summary = module.aggregate(values)
assert summary["median_seconds"] == 3 and summary["seconds_mad"] == 1
assert summary["seconds_min"] == 1 and summary["seconds_max"] == 100
assert summary["median_units_per_second"] == 100 / 3
assert summary["samples"] == values
run(["python3", HARNESS, "--prepare"], ok=False)
run(["python3", HARNESS, "--plan", "--samples", 4], ok=False)

with tempfile.TemporaryDirectory(prefix="goose-benchmark-hash-") as directory:
    source = Path(directory) / "compiler"
    source.write_bytes(b"a compiler with an unchanged version")
    fingerprint = module.fingerprint(source)
    assert fingerprint["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert fingerprint["path"] == str(source.resolve())
provenance = module.source_provenance()
assert {"main.goose", "baseline.c", "run.py"} == set(provenance["files"])
assert all(len(value) == 64 for value in provenance["files"].values())
