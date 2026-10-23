#!/usr/bin/env python3
"""Phase11 structural harness contract; does NOT run timing workloads."""
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
# No toolchain required to review the experiment; invocation without --run is read-only.
assert json.loads(run(["python3", HARNESS]).stdout) == plan
print("benchmark harness plan acceptance passed (no timings run)")
