#!/usr/bin/env python3
"""Record initial scalar Wasm samples. Run only in a coordinator-approved quiet window."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]


def run(args):
    result = subprocess.run(list(map(str, args)), cwd=ROOT, capture_output=True, timeout=90)
    if result.returncode:
        raise RuntimeError(f'{args}: exit {result.returncode}\n{result.stderr.decode(errors="replace")}')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--lease', type=Path, required=True, help='active coordinator lease JSON')
    a = p.parse_args()
    lease = json.loads(a.lease.read_text())
    if not lease.get('active') or lease.get('owner') != '/root':
        p.error('an active lease for this coordinator is required')
    exe = a.exe.resolve()
    directory = a.output.resolve().parent
    directory.mkdir(parents=True, exist_ok=True)
    report = {'schema': 1, 'lease': lease, 'environment': {'platform': platform.platform(),
        'cpu_count': os.cpu_count()}, 'compiler': str(exe),
        'compiler_sha256': hashlib.sha256(exe.read_bytes()).hexdigest(),
        'commit': run(['git', 'rev-parse', 'HEAD']).stdout.decode().strip(), 'workloads': {}}
    for name in ('scalar', 'conversion'):
        source = ROOT / 'bench' / 'wasm' / (name + '.goose')
        wasm, c, native = directory / (name + '.wasm'), directory / (name + '.c'), directory / (name + '.native')
        before = time.perf_counter_ns()
        run([exe, '-O2', '--target', 'wasm', '-o', wasm, source])
        compile_ms = (time.perf_counter_ns() - before) / 1e6
        run(['wasm-tools', 'validate', wasm])
        run([exe, '-O2', '--standalone', '-o', c, source])
        run(['cc', '-O2', c, '-pthread', '-lm', '-ldl', '-o', native])
        native_rows, expected = [], None
        for sample in range(-2, 7):
            before = time.perf_counter_ns()
            result = run([native])
            elapsed = (time.perf_counter_ns() - before) / 1e6
            expected = result.stdout.decode()
            native_rows.append({'sample': sample, 'warmup': sample < 0, 'process_ms': elapsed})
        node = json.loads(run(['node', ROOT / 'bench' / 'wasm' / 'measure.mjs', wasm]).stdout)
        assert node['answer'] == expected, f'{name}: native/Wasm result mismatch'
        report['workloads'][name] = {'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'module_sha256': hashlib.sha256(wasm.read_bytes()).hexdigest(), 'wasm_bytes': wasm.stat().st_size,
            'goose_invocation_ms': compile_ms, 'native_process_rows': native_rows, 'node': node,
            'node_run_median_ms': statistics.median(row['run_ms'] for row in node['rows'] if not row['warmup']),
            'native_process_median_ms': statistics.median(row['process_ms'] for row in native_rows if not row['warmup'])}
    a.output.write_text(json.dumps(report, indent=2) + '\n')
    print(a.output)


if __name__ == '__main__':
    main()
