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
    subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-c', str(folder / 'runner.c'), '-o', str(folder / 'runner.o')], check=True)
    report = json.loads((folder / 'report.json').read_text())
    assert report['status'] == 'ok' and report['finished_at']
    assert set(report) == {'schema_version','run_id','status','started_at','finished_at','source','host','toolchain','configurations','policy','results','error'}
    assert set(report['source']) == {'path','sha256','files','git_commit','git_dirty'}
    assert set(report['host']) == {'os','kernel','architecture','cpu_model','logical_cpus','affinity','clock','clock_resolution_ns','memory_metric'}
    assert set(report['policy']) == {'samples','warmups','isolation','setup_timeout_seconds','sample_timeout_seconds','gate_timeout_seconds','max_retries','thermal'}
    assert set(report['policy']['thermal']) == {'mode','reason','gate_c','ceiling_c','poll_interval_ms','sensors'}
    assert set(report['configurations'][0]) == {'id','size','definitions','goose_flags','native_flags','executable_sha256','generated_c_sha256'}
    row, pending = report['results']
    assert set(row) == {'key','label','source_line','size','configuration_id','status','isolation','checksum','accepted_warmups','accepted_samples','thermal_rejections','attempts','summary','temperature_max_observed_c','process_peak_rss_bytes','memory_unavailable_reason','children','error'}
    assert set(row['attempts'][0]) == {'index','phase','slot','retry','child_id','status','elapsed_ns','seconds','checksum','gate_wait_seconds','temperature_before_c','temperature_after_c','temperature_max_observed_c','temperature_reads','temperature_max_poll_gap_ms','process_peak_rss_bytes','error'}
    assert set(row['children'][0]) == {'id','exit_code','signal','process_peak_rss_bytes','stdout_path','stderr_path','logs_truncated'}
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
    contract = (root / 'docs/bench_artifacts.md').read_text().splitlines()
    for file, prefix in [('report.csv', 'schema_version,run_id,key,label,'), ('report.samples.csv', 'schema_version,run_id,key,size,')]:
        assert (folder / file).read_text().splitlines()[0] == next(line for line in contract if line.startswith(prefix))
    assert (folder / 'binary.sha256').read_text() == hashlib.sha256((folder / 'binary').read_bytes()).hexdigest()
    interrupted = json.loads((folder / 'interrupted.json').read_text())
    assert interrupted['status'] == 'interrupted' and interrupted['finished_at'] and interrupted['results'][0]['status'] == 'ok'
    assert (folder / 'preserved.json').read_text() == 'previous checkpoint'
    assert not list(folder.glob('*.tmp-*'))
    partial = json.loads((folder / 'partial.json').read_text())
    bad = partial['results'][1]['attempts']
    assert [a['elapsed_ns'] for a in bad] == ['0', '-1', None]
    with (folder / 'partial.samples.csv').open(newline='') as f: bad_csv = list(csv.DictReader(f))[-3:]
    assert [a['elapsed_ns'] for a in bad_csv] == ['0', '-1', '']
    assert [a['seconds'] for a in bad] == [0, -1e-9, None]
    assert partial['results'][0]['status'] == 'ok' and partial['status'] == 'failed'
    with (folder / 'partial.csv').open(newline='') as f: partial_csv = list(csv.DictReader(f))
    assert partial_csv[-1]['status'] == 'pending' and partial_csv[-1]['error_code'] == 'clock'
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
    gated = copy.deepcopy(report)
    gated['policy']['thermal']['mode'] = 'required'
    gated['policy']['thermal']['sensors'] = [{'id': 'cpu', 'chip': 'fake', 'device_path': '/fake', 'label': 'Tctl', 'input_path': '/fake/temp_input'}]
    for attempt in gated['results'][0]['attempts']:
        attempt.update(temperature_before_c=60, temperature_after_c=60, temperature_max_observed_c=60,
                       temperature_max_poll_gap_ms=int(attempt['elapsed_ns']) / 1e6 + 0.000002,
                       temperature_reads=[{'sensor_id': 'cpu', 'offset_ns': '-1', 'c': 60},
                                          {'sensor_id': 'cpu', 'offset_ns': str(int(attempt['elapsed_ns']) + 1), 'c': 60}])
    gated['results'][0]['temperature_max_observed_c'] = 60
    path.write_text(json.dumps(gated))
    assert read_results(path)['policy']['thermal']['mode'] == 'required'
    gated['results'][0]['attempts'][0]['temperature_reads'].pop()
    rejects(gated, 'missing thermal bracket')
    for change in ('zero', 'negative', 'incomplete', 'checksum', 'bits', 'summary', 'fingerprint', 'failed', 'slot', 'child', 'exit'):
        bad = copy.deepcopy(report)
        target = bad['results'][0]
        if change == 'zero': target['attempts'][1]['elapsed_ns'] = '0'
        elif change == 'negative': target['attempts'][1]['elapsed_ns'] = '-1'
        elif change == 'incomplete': target['attempts'].pop()
        elif change == 'checksum': target['attempts'][0]['checksum']['components'][0]['value'] = '1'
        elif change == 'bits': target['checksum']['components'][1]['value'] = '0x7ff0000000000000'
        elif change == 'summary': target['summary']['median_seconds'] = 99
        elif change == 'fingerprint': bad['configurations'][0]['goose_flags'].append('-O0')
        elif change == 'slot': target['attempts'][1]['slot'] = 9
        elif change == 'child': target['attempts'][0]['child_id'] = 99
        elif change == 'exit': target['children'][0]['exit_code'] = 1
        else: bad['status'] = 'failed'
        rejects(bad, change)

print('benchmark reports: statistics, hashes, canonical identity, JSON and CSV checks passed')
