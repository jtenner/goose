#!/usr/bin/env python3
"""Prepare, review, then explicitly run shared-native benchmarks sequentially.
Default/--plan prints the experiment and never runs a workload.
"""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
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
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import native_results as native

HERE = Path(__file__).resolve().parent
CASES = ["atomics_uncontended", "atomics_contended", "claims", "scalar_read_latency",
         "scalar_write_latency", "scalar_read_throughput", "scalar_write_throughput",
         "publication", "scheduling", "mmap", "copy", "checks_disabled", "checks_enabled"]
PARALLEL = {"atomics_uncontended", "atomics_contended", "claims", "scheduling"}
WORK_UNITS = {"atomics_uncontended": "fetch_add", "atomics_contended": "fetch_add",
              "claims": "useful_job", "scalar_read_latency": "scalar_read",
              "scalar_write_latency": "write_read_roundtrip", "scalar_read_throughput": "scalar_read",
              "scalar_write_throughput": "scalar_write", "publication": "handshake",
              "scheduling": "worker_start_and_join", "mmap": "mapping_lifecycle", "copy": "byte",
              "checks_disabled": "emission_operation", "checks_enabled": "emission_operation"}


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def fingerprint(executable):
    path = Path(shutil.which(str(executable)) or executable).resolve()
    return {"path": str(path), "sha256": sha256_file(path)}


def source_provenance():
    result = {"files": {name: sha256_file(HERE / name) for name in ("main.goose", "mmap.goose", "baseline.c", "run.py")}}
    result['adapter_sha256'] = sha256_file(HERE.parent / 'native_results.py')
    try:
        repo = HERE.parent.parent
        result["git_commit"] = command(["git", "-C", repo, "rev-parse", "HEAD"]).stdout.strip()
        status = subprocess.run(["git", "-C", str(repo), "diff", "--quiet", "HEAD", "--",
                                 *[str(HERE / name) for name in result["files"]]], capture_output=True)
        result["git_dirty"] = status.returncode != 0
    except (OSError, subprocess.CalledProcessError):
        result.update(git_commit=None, git_dirty=None)
    return result


def command(argv, **kwargs):
    return subprocess.run(list(map(str, argv)), check=True, capture_output=True,
                          text=True, timeout=600, **kwargs)


def plan(samples=7, warmups=2, cases=None, *, legacy_goose=False, experiments=1):
    cases = cases or CASES
    pairs = 2 * sum(4 if case in PARALLEL else 1 for case in cases)
    return {"samples": samples, "warmups": warmups, "workers": [1, 2, 4, 8],
            "cases": cases, "paired_scenarios": pairs,
            "units": {case: {"work_unit": WORK_UNITS[case], "rate_unit": WORK_UNITS[case] + "/second",
                              "latency_unit": "ns/" + WORK_UNITS[case]} for case in cases},
            "warmup_processes": pairs * 2 * warmups * experiments, "measured_processes": pairs * 2 * samples * experiments,
            "total_workload_processes": pairs * 2 * (samples + warmups) * experiments,
            "maximum_worker_threads": 8 if any(c in PARALLEL for c in cases) else 2 if "publication" in cases else 0,
            "simultaneous_workload_processes": 1, "implementations": ["c_baseline", "goose_native"],
            "native_optimization": ["-O0", "-O2"], "goose_optimization": "-O2",
            "run_requires_explicit_flag": True, "sequential": True,
            "experiments": experiments,
            "native_rows": [] if legacy_goose or 'mmap' not in cases else ['mmap/-O2'],
            "ordering_policy": "alternate whole-row blocks across experiments for native rows; alternate samples for legacy rows"}


def collect_legacy(binary, case, iterations, workers, fixture, directory, samples, warmups):
    values, expected = [], None
    for index in range(samples + warmups):
        value = sample(binary, case, iterations, workers, fixture, directory)
        identity = value['units'], value['checksum']
        if expected is not None and identity != expected:
            raise ValueError('legacy row changed its units or checksum')
        expected = identity
        if index >= warmups:
            values.append(value)
    return values


def collect_native_mmap(goose, cc, fixture, output, samples, warmups, temperature):
    value = native.run_native(goose, HERE / 'mmap.goose', output, key='mmap_lifecycle',
                              size='medium', types=('u64',), cc=cc, samples=samples, warmups=warmups,
                              definitions=['BENCH_FIXTURE=' + json.dumps(str(fixture))], temperature=temperature)
    _, values = native.shared_samples(value['native_report'], key='mmap_lifecycle', size='medium', units=64)
    if any(v['checksum'] != 64 * 16777216 for v in values):
        raise ValueError('unexpected mmap checksum')
    return value, values


@contextmanager
def experiment_lock(path="/tmp/goose-shared-native-benchmark.lock"):
    # Cross-process lock; covers this harness family. Parent coordinates other work.
    with open(path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield lock


@contextmanager
def native_lock_turn(lock):
    # No C work is active here. The native supervisor takes the same lock.
    # A competing process in either handoff gap causes failure, not overlap.
    fcntl.flock(lock, fcntl.LOCK_UN)
    try:
        yield
    finally:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)


def describe_binary(binary, generated=None):
    result = {"bytes": binary.stat().st_size, **fingerprint(binary)}
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
        result.update(generated_c_bytes=len(c.encode()), generated_c_sha256=sha256_file(generated),
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
    ap.add_argument('--legacy-goose', action='store_true', help='keep exact per-sample pairing for every case')
    ap.add_argument('--experiments', type=int, default=1, help='alternate native block order across experiments')
    ap.add_argument('--temperature', choices=('required', 'off'), default='required')
    ap.add_argument("--directory", type=Path, help="retain build artifacts here (default temporary)")
    ns = ap.parse_args()
    if ns.samples < 5 or ns.warmups < 1 or ns.iterations < 1 or ns.experiments < 1:
        ap.error("use at least five samples, one warmup and one iteration")
    if ns.plan or not (ns.prepare or ns.run):
        print(json.dumps(plan(ns.samples, ns.warmups, ns.case, legacy_goose=ns.legacy_goose, experiments=ns.experiments), indent=2)); return
    if not ns.goose:
        ap.error("--goose is required to compile workloads")
    if ns.run and not ns.output:
        ap.error("--run requires --output so raw measurements are retained")
    if ns.directory:
        ns.directory.mkdir(parents=True, exist_ok=True)
        directory = ns.directory.resolve()
        cleanup = None
    elif ns.run:
        ns.output = ns.output.resolve()
        ns.output.parent.mkdir(parents=True, exist_ok=True)
        directory = Path(tempfile.mkdtemp(prefix=ns.output.stem + '.artifacts-', dir=ns.output.parent))
        cleanup = None  # Native attempt logs and artifacts must survive report writing.
    else:
        cleanup = tempfile.TemporaryDirectory(prefix="goose-native-benchmark-")
        directory = Path(cleanup.name)
    try:
        with experiment_lock() as lock:
            goose_executable = fingerprint(ns.goose.resolve())
            compiler_executable = fingerprint(ns.cc)
            source = source_provenance()
            fixture, paths, artifacts = prepare(ns.goose.resolve(), ns.cc, directory)
            if not ns.legacy_goose and 'mmap' in (ns.case or CASES):
                command([ns.goose.resolve(), 'bench', HERE / 'mmap.goose', '--list',
                         '--define', 'BENCH_FIXTURE=' + json.dumps(str(fixture))])
            if goose_executable != fingerprint(ns.goose.resolve()) or compiler_executable != fingerprint(ns.cc):
                raise RuntimeError("compiler executable changed during preparation")
            after = source_provenance()
            if source["files"] != after["files"] or source['adapter_sha256'] != after['adapter_sha256']:
                raise RuntimeError("benchmark source changed during preparation")
            cpu = platform.processor()
            if Path("/proc/cpuinfo").exists():
                cpu = next((x.split(":", 1)[1].strip() for x in Path("/proc/cpuinfo").read_text().splitlines()
                            if x.startswith("model name")), cpu)
            report = {"schema_version": 2,
                      "plan": plan(ns.samples, ns.warmups, ns.case, legacy_goose=ns.legacy_goose, experiments=ns.experiments), "cpu": cpu, "platform": platform.platform(),
                      "affinity": sorted(os.sched_getaffinity(0)) if hasattr(os,"sched_getaffinity") else None,
                      "compiler": command([ns.cc,"--version"]).stdout.splitlines()[0],
                      "goose": command([ns.goose.resolve(),"version"]).stdout.strip(),
                      "compiler_flags": ["-std=c11", "-pthread", "-lm"], "artifacts": artifacts,
                      "goose_executable": goose_executable, "compiler_executable": compiler_executable,
                      "source": source, "results": []}
            if ns.run:
                for experiment in range(ns.experiments):
                    for case in ns.case or CASES:
                        enabled = case == "checks_enabled"
                        for opt in ("-O0", "-O2"):
                            for workers in ([1, 2, 4, 8] if case in PARALLEL else [2] if case == "publication" else [1]):
                                # Alternate implementation order between samples to reduce drift bias.
                                collected = {"c_baseline": [], "goose_native": []}
                                native_row = None
                                migrated = case == 'mmap' and opt == '-O2' and not ns.legacy_goose
                                if migrated:
                                    order = ['c_baseline', 'goose_native']
                                    if experiment % 2: order.reverse()
                                    for implementation in order:
                                        if implementation == 'goose_native':
                                            with native_lock_turn(lock):
                                                native_row, collected[implementation] = collect_native_mmap(
                                                    ns.goose.resolve(), Path(compiler_executable['path']), fixture,
                                                    directory / ('mmap-' + str(experiment) + '.native.json'),
                                                    ns.samples, ns.warmups, ns.temperature)
                                        else:
                                            collected[implementation] = collect_legacy(paths[(implementation,opt,enabled)],
                                                case, ns.iterations, workers, fixture, directory, ns.samples, ns.warmups)
                                    if any(v['units'] != 64 or v['checksum'] != 64 * 16777216
                                           for v in collected['c_baseline']):
                                        raise ValueError('C/native mmap units or checksum mismatch')
                                for iteration in ([] if migrated else range(ns.warmups + ns.samples)):
                                    order = ["c_baseline", "goose_native"]
                                    if iteration % 2: order.reverse()
                                    pair = []
                                    for implementation in order:
                                        value = sample(paths[(implementation,opt,enabled)], case, ns.iterations, workers, fixture, directory)
                                        pair.append(value)
                                        if iteration >= ns.warmups: collected[implementation].append(value)
                                    assert pair[0]["checksum"] == pair[1]["checksum"], (case,pair)
                                for implementation, values in collected.items():
                                    metadata = dict(statistic='median', timing_scope='internal function region',
                                                    ordering_policy='alternate samples', experiment=experiment)
                                    if migrated:
                                        metadata['ordering_policy'] = 'whole-row blocks: ' + ','.join(order)
                                        if implementation == 'goose_native':
                                            metadata.update(timing_scope='function', isolation=native_row['isolation'],
                                                            thermal_policy=native_row['thermal_policy'],
                                                            native_report=native_row['native_report'], artifact=native_row['artifact'])
                                    report["results"].append({"case": case, "native_optimization": opt, **metadata,
                                        "workers": workers, "implementation": implementation,
                                        **report["plan"]["units"][case], **aggregate(values)})
            text = json.dumps(report, indent=2) + "\n"
            if ns.output: ns.output.write_text(text)
            else: print(text, end="")
    finally:
        if cleanup: cleanup.cleanup()


if __name__ == "__main__":
    main()
