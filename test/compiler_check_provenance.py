#!/usr/bin/env python3
"""Measurement provenance/cleanup/plan contract. No timing processes."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / 'bench/shared_native/compiler_check.py'
spec = importlib.util.spec_from_file_location('compiler_check', HARNESS)
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)
contaminated = {'PATH': '/usr/bin', 'GOOSE_STDLIB': '/fixed/stdlib', 'KEEP': 'value',
                'GOOSE_DEFERRED_WORK': '1', 'GOOSE_DEFERRED_VERIFY': '1', 'ASAN_OPTIONS': 'x',
                'ASAN_SYMBOLIZER_PATH': 'x', 'LSAN_OPTIONS': 'x', 'UBSAN_OPTIONS': 'x',
                'TSAN_OPTIONS': 'x', 'MSAN_OPTIONS': 'x', 'HWASAN_OPTIONS': 'x', 'DFSAN_OPTIONS': 'x',
                'LLVM_SYMBOLIZER_PATH': 'x'}
clean, removed = bench.timing_environment(contaminated)
assert clean == {'PATH': '/usr/bin', 'GOOSE_STDLIB': '/fixed/stdlib', 'KEEP': 'value'}
assert set(removed) == set(contaminated) - set(clean)
assert len(contaminated) > len(clean), 'input environment must remain intact'
base = bench.source_identity('8464cc68')
fixed = bench.source_identity('41dc6eb3')
assert base['commit'] == '8464cc68c3478fcdaf1884c64f13a704264e993c'
assert base['src_tree'] == '2049b52b10eaf0192e66514fbac40bf5e2d0d3ec'
assert fixed['src_tree'] == '741cbecbd8b0f95e4ab9148161a5af870cb3ca12'
summary = bench.aggregate([dict(seconds=n, process_peak_rss_kib=n*100) for n in (1, 2, 3, 4, 100)])
assert summary['peak_rss_mad_kib'] == 100
assert summary['peak_rss_min_kib'] == 100 and summary['peak_rss_max_kib'] == 10000
p = subprocess.run(['python3', HARNESS, '--sizes', '250', '500', '1000', '2000', '4000',
                    '--cpu', '0', '--baseline-source-ref', '8464cc68', '--extended-source-ref', '41dc6eb3',
                    '--build-compiler', 'GCC 14.2.0', '--build-cxxflags=-O3 -DNDEBUG'],
                   capture_output=True, text=True)
assert p.returncode == 0, p.stderr
plan = json.loads(p.stdout)
assert plan['requested_cpu'] == 0 and plan['affinity'] == sorted(os.sched_getaffinity(0))
assert plan['compiler_build'] == dict(compiler='GCC 14.2.0', configuration='Release', cxxflags='-O3 -DNDEBUG')
assert plan['requested_source_refs'] == dict(baseline='8464cc68', extended='41dc6eb3')
assert len(plan['harness_sha256']) == 64 and 'baseline' not in plan
assert [s['unused_functions'] for s in plan['sources']] == [250, 500, 1000, 2000, 4000]
print('compiler-check provenance/environment/plan acceptance passed (no timings)')
