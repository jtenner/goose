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
    assert len(attempts) == 6 and attempts[0]['phase'] == 'warmup' and attempts[0]['elapsed_ns'] == '9000000000'
    config = report['configurations'][0]
    identity = {k: config[k] for k in ('size', 'definitions', 'goose_flags', 'native_flags')}
    identity.update(goose_sha256=hashlib.sha256(b'compiler').hexdigest(), cc_sha256=hashlib.sha256(b'cc').hexdigest(), source_files=[{'path': report['source']['path'], 'sha256': report['source']['sha256']}])
    assert config['id'] == hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    assert not list(folder.glob('*.tmp-*'))
    partial = json.loads((folder / 'partial.json').read_text())
    bad = partial['results'][1]['attempts']
    assert [a['elapsed_ns'] for a in bad] == ['0', '-1', None]
    with (folder / 'partial.samples.csv').open(newline='') as f: bad_csv = list(csv.DictReader(f))[-3:]
    assert [a['elapsed_ns'] for a in bad_csv] == ['0', '-1', '']
    assert [a['seconds'] for a in bad] == [0, -1e-9, None]
    assert partial['results'][0]['status'] == 'ok' and partial['status'] == 'failed'
    assert not (folder / 'unused.csv').exists()
    import sys
    sys.path.insert(0, str(root / 'bench'))
    from native_results import InvalidResult, read_results
    def rejects(data, message):
        path = folder / 'adapter.json'
        path.write_text(json.dumps(data))
        try:
            read_results(path, allow_ungated=True)
        except InvalidResult:
            return
        raise AssertionError(message)
    import copy
    rejects(report, 'pending row was accepted')
    report['results'] = report['results'][:1]
    path = folder / 'adapter.json'
    path.write_text(json.dumps(report))
    assert read_results(path, allow_ungated=True)['results'][0]['summary']['median_seconds'] == 3
    for change in ('zero', 'negative', 'incomplete', 'checksum', 'bits', 'summary', 'fingerprint', 'failed'):
        bad = copy.deepcopy(report)
        target = bad['results'][0]
        if change == 'zero': target['attempts'][1]['elapsed_ns'] = '0'
        elif change == 'negative': target['attempts'][1]['elapsed_ns'] = '-1'
        elif change == 'incomplete': target['attempts'].pop()
        elif change == 'checksum': target['attempts'][0]['checksum']['components'][0]['value'] = '1'
        elif change == 'bits': target['checksum']['components'][1]['value'] = '0x7ff0000000000000'
        elif change == 'summary': target['summary']['median_seconds'] = 99
        elif change == 'fingerprint': bad['configurations'][0]['goose_flags'].append('-O0')
        else: bad['status'] = 'failed'
        rejects(bad, change)

print('benchmark reports: statistics, hashes, canonical identity, JSON and CSV checks passed')
