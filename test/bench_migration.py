#!/usr/bin/env python3
"""Native adapter and harness checks with synthetic records. No timing runs."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import re
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bench'))
import native_results as native
import run_bench as suite


def synthetic_report(source, compiler, cc):
    """Synthetic seconds [1,2,3,4,100]; these are not host measurements."""
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    flags = ['-O2', '--bounds-check=on', '--recursive-frame-check=on', '--backend=native', '--runtime=linked']
    config = dict(size='medium', definitions=[dict(name='BENCH_SIZE', type='string', value='medium')],
                  goose_flags=flags, native_flags=['-O2', '-fno-lto', '-lm', '-pthread', '-ldl', '--cc=' + str(cc)])
    files = [dict(path=str(source), sha256=digest(source))]
    identity = dict(config, goose_sha256=digest(compiler), cc_sha256=digest(cc), source_files=files)
    config['id'] = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    checksum = dict(components=[dict(type='u64', value='18446744073709551615')])
    attempts = [dict(index=i, phase='warmup' if i == 1 else 'measure', slot=1 if i == 1 else i-1,
                     retry=0, status='accepted', error=None, child_id=1, checksum=checksum,
                     elapsed_ns=str(t * 1000000000), seconds=t, process_peak_rss_bytes=None)
                for i, t in enumerate([9, 1, 2, 3, 4, 100], 1)]
    row = dict(key='entry', size='medium', configuration_id=config['id'], status='ok', error=None,
               isolation='process', checksum=checksum, accepted_warmups=1, accepted_samples=5,
               thermal_rejections=0, attempts=attempts, process_peak_rss_bytes=None,
               children=[dict(id=1, exit_code=0, signal=None)],
               summary=dict(median_seconds=3, seconds_mad=1, seconds_mad_percent=100/3,
                            seconds_min=1, seconds_max=100))
    return dict(schema_version=1, status='ok', finished_at='synthetic', error=None,
                source=dict(path=str(source), sha256=digest(source), files=files),
                toolchain=dict(goose=dict(path=str(compiler), sha256=digest(compiler)),
                               cc=dict(path=str(cc), sha256=digest(cc))), configurations=[config],
                policy=dict(samples=5, warmups=1, isolation='process', max_retries=10,
                            thermal=dict(mode='disabled', sensors=[], gate_c=60, ceiling_c=65, poll_interval_ms=50)),
                results=[row])


class MigrationChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.source, self.compiler, self.cc = [self.folder / name for name in ('work.goose', 'goose', 'cc')]
        for p in (self.source, self.compiler, self.cc):
            p.write_text(p.name)
        self.report = synthetic_report(self.source, self.compiler, self.cc)
        self.output = self.folder / 'result.json'

    def read(self, report=None):
        self.output.write_text(json.dumps(self.report if report is None else report))
        return native.read_results(self.output, allow_ungated=True)

    def invoke(self, **kwargs):
        def record(argv, **unused):
            self.output.write_text(json.dumps(self.report))
            return subprocess.CompletedProcess(argv, 0, '', '')
        with patch.object(native.subprocess, 'run', side_effect=record):
            return native.run_native(self.compiler, self.source, self.output, key='entry', size='medium',
                                     types=('u64',), cc=self.cc, samples=5, warmups=1,
                                     temperature='off', **kwargs)

    def test_projection_and_units(self):
        report = self.read()
        m = native.measurement(report, key='entry', size='medium', types=('u64',))
        self.assertEqual((m['ms'], m['peak']), (3000, None))
        self.assertEqual(native.decoded_checksum(m['checksum']), (2**64 - 1,))
        self.assertFalse(suite.comparable(m))
        self.assertEqual(suite.fmt_mb(m), '--')
        _, samples = native.shared_samples(report, key='entry', size='medium', units=100)
        self.assertEqual([s['seconds'] for s in samples], [1, 2, 3, 4, 100])
        self.assertEqual(samples[2]['units_per_second'], 100/3)
        self.assertIsNone(samples[2]['process_peak_rss_kib'])

    def test_legacy_exact_components(self):
        self.assertEqual(native.legacy_checksum('42\n18446744073709551615\ntrue\n', ('i64', 'u64', 'bool')),
                         (42, 2**64 - 1, True))
        for text, types in [('42\n', ('i64', 'i64')), ('1.0\n', ('f64',)), ('-1\n', ('u64',))]:
            with self.assertRaises(native.InvalidResult):
                native.legacy_checksum(text, types)

    def test_dry_run_no_process_or_output(self):
        with patch.object(native.subprocess, 'run', side_effect=AssertionError('launched process')):
            argv = self.invoke(dry_run=True)
        self.assertIn('--json', argv)
        self.assertIn('--filter', argv)
        self.assertFalse(self.output.exists())

    def test_command_and_provenance(self):
        value = self.invoke()
        self.assertEqual(value['statistic'], 'median')
        self.assertEqual(value['artifact'], str(self.output))
        for change in ('source', 'key', 'samples', 'isolation', 'thermal', 'flags', 'types'):
            with self.subTest(change=change):
                original = copy.deepcopy(self.report)
                if change == 'source': self.report['source']['path'] = '/wrong'
                if change == 'key': self.report['results'][0]['key'] = 'wrong'
                if change == 'samples': self.report['policy']['samples'] = 6
                if change == 'isolation': self.report['policy']['isolation'] = 'reuse'
                if change == 'thermal': self.report['policy']['thermal']['ceiling_c'] = 90
                if change == 'flags': self.report['configurations'][0]['native_flags'].append('-O0')
                if change == 'types': self.report['results'][0]['checksum']['components'][0]['type'] = 'i64'
                with self.assertRaises(native.InvalidResult): self.invoke()
                self.report = original

    def test_bad_records(self):
        for change in ('zero', 'negative', 'incomplete', 'warmup', 'summary', 'rss', 'missing', 'failed', 'ungated'):
            data = copy.deepcopy(self.report)
            row = data['results'][0]
            if change == 'zero': row['attempts'][1]['elapsed_ns'] = '0'
            if change == 'negative': row['attempts'][1]['elapsed_ns'] = '-1'
            if change == 'incomplete': row['attempts'].pop()
            if change == 'warmup': row['attempts'][0]['checksum'] = dict(components=[dict(type='u64', value='0')])
            if change == 'summary': row['summary']['median_seconds'] = 4
            if change == 'rss': row['process_peak_rss_bytes'] = -1
            if change == 'missing': del data['policy']
            if change == 'failed': data['status'] = 'failed'
            with self.subTest(change=change), self.assertRaises(native.InvalidResult):
                if change == 'ungated':
                    self.output.write_text(json.dumps(data))
                    native.read_results(self.output)
                else: self.read(data)

    def test_plans_only(self):
        p = subprocess.run([sys.executable, ROOT / 'bench/run_bench.py', '--plan', '--only', 'sum,tree', '--sizes', 'small'],
                           check=True, capture_output=True, text=True)
        plan = json.loads(p.stdout)
        self.assertEqual(len(plan['rows']), 2)
        self.assertTrue(all(row['engine'] == 'native' for row in plan['rows']))

    def test_size_maps_and_legacy_sources(self):
        args = type('Args', (), {})()
        harness = suite.Harness(args, {}, [], None)
        for b in suite.BENCHMARKS:
            for g in b['goose']:
                if g['file'] not in suite.NATIVE_CASES:
                    continue
                source = suite.GOOSEDIR / g['file']
                text = source.read_text()
                values = [int(n) for n in re.findall(r'\{ (\d+) \}', text.split('let PASSES')[0])]
                self.assertEqual(values, b['sizes'])
                self.assertEqual(harness.goose_source(g['file'], b['sizes'][0], 'unused'), source)
                self.assertEqual(harness.size_flags(g['file'], b['sizes'][0]),
                                 ['--define', 'BENCH_SIZE="small"'])
                self.assertNotIn('BENCH_N', text)

    def test_report_only_with_native_row(self):
        m = native.measurement(self.read(), key='entry', size='medium', types=('u64',))
        legacy = dict(ok=True, ms=6000, peak=4096, statistic='best', timing_scope='process', out='1\n')
        state = dict(schema_version=2, results={'sum': {
            'goose grow-only array': {'test': {'large': m}},
            'cpp vector': {'test': {'large': legacy}}}}, baseline=None, mismatch={}, reps=3,
            sizes=['large'], toolchains=['test'], tcdefs={'test': {'desc': 'synthetic', 'opt': '-O2'}})
        (self.folder / 'results-native-v2.json').write_text(json.dumps(state))
        output = self.folder / 'report.md'
        with patch.object(suite, 'GENDIR', self.folder), patch.object(suite.tc, 'find_ccs', return_value={}), \
             patch.object(suite.tc, 'find_rustc', return_value=None), \
             patch.object(sys, 'argv', ['bench', '--report-only', '--out', str(output)]):
            self.assertEqual(suite.main(), 0)
        text = output.read_text()
        self.assertIn('[native: median, function, process, thermal=disabled]', text)
        self.assertNotIn('2.00x', text)
        self.assertIn('3,000.0', text)


if __name__ == '__main__':
    unittest.main()
