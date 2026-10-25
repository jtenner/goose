#!/usr/bin/env python3
"""Deterministic statistics and artifact writer checks; no timings are measured."""
import csv
import hashlib
import json
import pathlib
import subprocess
import tempfile
root = pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='goose-report-test-') as name:
    folder = pathlib.Path(name)
    subprocess.run(['c++', '-std=c++20', '-O0', str(root / 'test/bench_report.cpp'), str(root / 'src/bench_report.cpp'), '-o', str(folder / 'driver')], check=True)
    subprocess.run([str(folder / 'driver'), name], check=True)
    report = json.loads((folder / 'report.json').read_text())
    assert report['status'] == 'ok' and report['finished_at']
    row, pending = report['results']
    assert row['checksum']['components'][0]['value'] == '18446744073709551615'
    assert row['checksum']['components'][2]['value'] is True
    assert pending['summary'] is None
    assert row['summary']['median_seconds'] == 3 and row['summary']['seconds_mad'] == 1
    with (folder / 'report.csv').open(newline='') as f: rows = list(csv.DictReader(f))
    assert rows[0]['label'] == row['label'] and rows[1]['median_seconds'] == ''
    assert json.loads(rows[0]['checksum_json']) == row['checksum']
    with (folder / 'report.samples.csv').open(newline='') as f: attempts = list(csv.DictReader(f))
    assert len(attempts) == 6 and attempts[0]['phase'] == 'warmup' and attempts[0]['elapsed_ns'] == '1000000000'
    config = report['configurations'][0]
    identity = {k: config[k] for k in ('size', 'definitions', 'goose_flags', 'native_flags')}
    identity.update(goose_sha256=hashlib.sha256(b'compiler').hexdigest(), cc_sha256=None, source_files=[{'path': '/input.goose', 'sha256': report['source']['sha256']}])
    assert config['id'] == hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    assert not list(folder.glob('*.tmp-*'))
print('benchmark reports: statistics, hashes, canonical identity, JSON and CSV checks passed')
