#!/usr/bin/env python3
"""Compiler benchmark generation/plan contract. Never runs timings."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / 'bench/shared_native/compiler_check.py'
spec = importlib.util.spec_from_file_location('compiler_check', HARNESS)
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)
p = subprocess.run(['python3', HARNESS, '--globals', '17', '--sizes', '10', '20', '40',
                    '--case', 'ordinary', '--case', 'calls', '--case', 'deferred', '--stdlib',
                    '--named-return', '--baseline', '/does/not/exist'], capture_output=True, text=True)
assert p.returncode == 0, p.stderr
plan = json.loads(p.stdout)
assert plan['run_requires_explicit_flag'] and plan['results'] == [] and 'baseline' not in plan
assert len(plan['sources']) == 9
for item in plan['sources']:
    assert item['globals'] == 17 and item['unused_functions'] in (10, 20, 40)
    assert len(item['source_sha256']) == 64 and item['stdlib'] and item['named_return']
    text = bench.source_for(17, item['unused_functions'], item['case'], True, True)
    assert 'import std;' in text and 'return 7 from destination' in text
    assert text.count('fn check_fn_') == item['unused_functions']
assert 'g0' not in bench.source_for(0, 2)
assert 'i64[2]' in bench.source_for(0, 2, 'arrays')
with tempfile.TemporaryDirectory() as directory:
    source = Path(directory) / 'real.goose'
    source.write_text('fn main(){}\n')
    p = subprocess.run(['python3', HARNESS, '--source', source], capture_output=True, text=True)
    assert json.loads(p.stdout)['sources'][0]['source'] == str(source)
summary = bench.aggregate([dict(seconds=x, process_peak_rss_kib=x*100) for x in (1, 2, 3, 4, 100)])
assert summary['median_seconds'] == 3 and summary['seconds_mad'] == 1
p = subprocess.run(['python3', HARNESS, '--run'], capture_output=True, text=True)
assert p.returncode != 0 and '--run requires' in p.stderr
print('compiler-check generator/plan acceptance passed (no timings)')
