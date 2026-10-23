#!/usr/bin/env python3
"""Prepare, review, then explicitly run shared-native benchmarks sequentially.
Default/--plan prints the experiment and never runs a workload.
"""
import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import platform
import re
import shutil
import statistics
import subprocess
import tempfile
import time

HERE = Path(__file__).resolve().parent
CASES = ["atomics_uncontended", "atomics_contended", "claims", "scalar_read_latency",
         "scalar_write_latency", "scalar_read_throughput", "scalar_write_throughput",
         "publication", "scheduling", "mmap", "copy", "checks_disabled", "checks_enabled"]
PARALLEL = {"atomics_uncontended", "atomics_contended", "claims", "scheduling"}


def command(argv, **kwargs):
    return subprocess.run(list(map(str, argv)), check=True, capture_output=True,
                          text=True, timeout=600, **kwargs)


def plan(samples=7, warmups=2):
    return {"samples": samples, "warmups": warmups, "workers": [1, 2, 4, 8],
            "cases": CASES, "implementations": ["c_baseline", "goose_native"],
            "native_optimization": ["-O0", "-O2"], "goose_optimization": "-O2",
            "run_requires_explicit_flag": True, "sequential": True}


@contextmanager
def experiment_lock():
    # Cross-process lock; covers this harness family. Parent coordinates other work.
    with open("/tmp/goose-shared-native-benchmark.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def describe_binary(binary, generated=None):
    result = {"bytes": binary.stat().st_size}
    if shutil.which("size"):
        result["size"] = command(["size", binary]).stdout.strip()
    if shutil.which("objdump"):
        assembly = command(["objdump", "-d", binary]).stdout
        result["instruction_count_whole_binary"] = len(re.findall(r"^\s*[0-9a-f]+:\s", assembly, re.M))
        result["ownership_validation_symbol"] = "validate_register_ownership" in assembly
        functions = re.findall(r"^[0-9a-f]+ <([^>]+)>:\n(.*?)(?=^[0-9a-f]+ <|\Z)", assembly, re.M | re.S)
        result["application_instructions"] = {name: len(re.findall(r"^\s*[0-9a-f]+:\s", body, re.M))
            for name, body in functions if name in ("main", "main_g", "checked_emit", "checked_emit_g")}
    if generated:
        c = generated.read_text()
        result.update(generated_c_bytes=len(c.encode()),
                      ownership_data_present="register_owners" in c,
                      ownership_diagnostic_present="REGISTER_CLOBBER_SENTINEL" in c)
    return result


def prepare(goose, cc, directory):
    fixture = directory / "mapping.bin"
    with fixture.open("wb") as f:
        f.truncate(16777216)  # sparse input: mmap timing excludes page touching
    paths, artifacts = {}, {}
    for opt in ("-O0", "-O2"):
        for enabled in (False, True):
            suffix = opt[1:] + ("-checked" if enabled else "-unchecked")
            c_path = directory / ("goose-" + suffix + ".c")
            command([goose, "--standalone", "-O2", "--define", "CHECK_REGISTER_CLOBBERS=" + str(enabled).lower(),
                     HERE / "main.goose", "-o", c_path])
            for implementation in ("c_baseline", "goose_native"):
                binary = directory / (implementation + "-" + suffix)
                flags = [opt, "-std=c11", "-pthread", "-lm"]
                if implementation == "c_baseline":
                    command([cc, HERE / "baseline.c", "-DCHECK_REGISTER_CLOBBERS=" + str(int(enabled)),
                             *flags, "-o", binary])
                else:
                    command([cc, c_path, *flags, "-o", binary])
                key = (implementation, opt, enabled)
                paths[key] = binary
                artifacts["/".join(map(str, key))] = describe_binary(binary, c_path if implementation == "goose_native" else None)
                if not enabled and implementation == "goose_native":
                    assert not artifacts["/".join(map(str,key))]["ownership_data_present"]
    return fixture, paths, artifacts


def sample(binary, case, iterations, workers, fixture, directory):
    rss = directory / "rss.txt"
    argv = [binary, case, iterations, workers, fixture]
    if Path("/usr/bin/time").exists():
        argv = ["/usr/bin/time", "-f", "%M", "-o", rss, *argv]
    values = command(argv).stdout.split()
    assert len(values) == 3, values
    seconds, units, checksum = float(values[0]), int(values[1]), int(values[2])
    assert seconds > 0 and units > 0, values
    return {"seconds": seconds, "units": units, "checksum": checksum,
            "units_per_second": units / seconds, "ns_per_unit": seconds * 1e9 / units,
            "process_peak_rss_kib": int(rss.read_text().strip()) if rss.exists() else None}


def aggregate(values):
    seconds = [v["seconds"] for v in values]
    center = statistics.median(seconds)
    rates = [v["units_per_second"] for v in values]
    return {"median_seconds": center, "median_units_per_second": statistics.median(rates),
            "median_ns_per_unit": statistics.median(v["ns_per_unit"] for v in values),
            "seconds_mad": statistics.median(abs(v-center) for v in seconds),
            "seconds_mad_percent": statistics.median(abs(v-center) for v in seconds) * 100 / center,
            "seconds_min": min(seconds), "seconds_max": max(seconds), "samples": values}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--prepare", action="store_true", help="compile only; never run timing workloads")
    ap.add_argument("--run", action="store_true", help="parent-coordinated explicit timing authorization")
    ap.add_argument("--goose", type=Path)
    ap.add_argument("--cc", default=os.environ.get("CC", "cc"))
    ap.add_argument("--samples", type=int, default=7)
    ap.add_argument("--warmups", type=int, default=2)
    ap.add_argument("--iterations", type=int, default=200000)
    ap.add_argument("--case", action="append", choices=CASES)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--directory", type=Path, help="retain build artifacts here (default temporary)")
    ns = ap.parse_args()
    if ns.samples < 5 or ns.warmups < 1 or ns.iterations < 1:
        ap.error("use at least five samples, one warmup and one iteration")
    if ns.plan or not (ns.prepare or ns.run):
        print(json.dumps(plan(ns.samples, ns.warmups), indent=2)); return
    if not ns.goose:
        ap.error("--goose is required to compile workloads")
    if ns.run and not ns.output:
        ap.error("--run requires --output so raw measurements are retained")
    if ns.directory:
        ns.directory.mkdir(parents=True, exist_ok=True)
        directory = ns.directory.resolve()
        cleanup = None
    else:
        cleanup = tempfile.TemporaryDirectory(prefix="goose-native-benchmark-")
        directory = Path(cleanup.name)
    try:
        with experiment_lock():
            fixture, paths, artifacts = prepare(ns.goose.resolve(), ns.cc, directory)
            cpu = platform.processor()
            if Path("/proc/cpuinfo").exists():
                cpu = next((x.split(":", 1)[1].strip() for x in Path("/proc/cpuinfo").read_text().splitlines()
                            if x.startswith("model name")), cpu)
            report = {"plan": plan(ns.samples, ns.warmups), "cpu": cpu, "platform": platform.platform(),
                      "affinity": sorted(os.sched_getaffinity(0)) if hasattr(os,"sched_getaffinity") else None,
                      "compiler": command([ns.cc,"--version"]).stdout.splitlines()[0],
                      "goose": command([ns.goose.resolve(),"version"]).stdout.strip(),
                      "compiler_flags": ["-std=c11", "-pthread", "-lm"], "artifacts": artifacts, "results": []}
            if ns.run:
                for case in ns.case or CASES:
                    enabled = case == "checks_enabled"
                    for opt in ("-O0", "-O2"):
                        for workers in ([1, 2, 4, 8] if case in PARALLEL else [2] if case == "publication" else [1]):
                            # Alternate implementation order between samples to reduce drift bias.
                            collected = {"c_baseline": [], "goose_native": []}
                            for iteration in range(ns.warmups + ns.samples):
                                order = ["c_baseline", "goose_native"]
                                if iteration % 2: order.reverse()
                                pair = []
                                for implementation in order:
                                    value = sample(paths[(implementation,opt,enabled)], case, ns.iterations, workers, fixture, directory)
                                    pair.append(value)
                                    if iteration >= ns.warmups: collected[implementation].append(value)
                                assert pair[0]["checksum"] == pair[1]["checksum"], (case,pair)
                            for implementation, values in collected.items():
                                report["results"].append({"case": case, "native_optimization": opt,
                                    "workers": workers, "implementation": implementation, **aggregate(values)})
            text = json.dumps(report, indent=2) + "\n"
            if ns.output: ns.output.write_text(text)
            else: print(text, end="")
    finally:
        if cleanup: cleanup.cleanup()


if __name__ == "__main__":
    main()
