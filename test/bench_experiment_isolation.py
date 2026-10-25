#!/usr/bin/env python3
"""Saved suite state checks with mock measurements. No timing runs."""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bench'))
import run_bench as suite


class ExperimentIsolationChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.statefile = self.folder / 'results-native-v2.json'
        self.output = self.folder / 'report.md'
        self.legacy = dict(ok=True, ms=1, peak=4096, statistic='best',
                           timing_scope='process', out='1\n2\n')
        self.saved = dict(schema_version=2, cache_identity={'same': 'inputs'},
            results={'tree': {'old row': {'old-cc': {'large': self.legacy}}},
                     'sum': {'goose grow-only array': {'clang': {'medium': self.legacy}}}},
            baseline={k: self.legacy for k in ('goose', 'cpp')},
            mismatch={'tree/large': {'old row': 'wrong'}}, reps=3,
            sizes=['medium', 'large'], toolchains=['old-cc', 'clang'],
            tcdefs={'old-cc': {'desc': 'old compiler', 'opt': '-O2'},
                    'clang': {'desc': 'saved compiler', 'opt': '-O2'}},
            environment=dict(host='saved host', cpu='saved CPU', ram_bytes=8 << 30,
                             os='saved OS', affinity=[2, 4], rust_version='saved rustc'))

    def run_suite(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), \
             patch.object(suite, 'GENDIR', self.folder), \
             patch.object(sys, 'argv', ['bench', '--out', str(self.output), *args]):
            self.assertEqual(suite.main(), 0)
        return self.output.read_text()

    def test_partial_run_replaces_state_even_with_matching_cache_identity(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                self.check_partial_run(legacy)

    def check_partial_run(self, legacy):
        self.statefile = self.folder / ('results-legacy-v2.json' if legacy else 'results-native-v2.json')
        self.statefile.write_text(json.dumps(self.saved))
        cc = SimpleNamespace(cc='mock-cc', desc='current compiler', style='gcc')
        native = dict(self.legacy, statistic='median', timing_scope='function',
                      isolation='process', thermal_policy={'mode': 'disabled'},
                      checksum={'components': [{'type': 'i64', 'value': str(n)} for n in (1, 2)]})
        with patch.object(suite.tc, 'find_ccs', return_value={'clang': cc}), \
             patch.object(suite.tc, 'find_goose', return_value='mock-goose'), \
             patch.object(suite.tc, 'find_rustc', return_value=None), \
             patch.object(suite, 'cache_identity', return_value=self.saved['cache_identity']), \
             patch.object(suite, 'Harness') as harness, \
             patch.object(suite, 'measure_exe', return_value=self.legacy), \
             patch.object(suite, 'measure_baseline', return_value=None), \
             patch.object(suite.tc, 'cpu_name', return_value='current CPU'), \
             patch.object(suite.tc, 'ram_bytes', return_value=16 << 30), \
             patch.object(suite.tc, 'os_name', return_value='current OS'), \
             patch('platform.node', return_value='current host'), \
             patch('os.sched_getaffinity', return_value={7, 3}, create=True):
            harness.return_value.native_row.return_value = native
            harness.return_value.build_cpp.return_value = (Path('mock-exe'), None)
            harness.return_value.build_goose.return_value = (Path('mock-exe'), None)
            text = self.run_suite('--only', 'sum', '--sizes', 'small', '--no-jit',
                                  *(['--legacy-goose'] if legacy else []))
        saved = json.loads(self.statefile.read_text())
        self.assertEqual(set(saved['results']), {'sum'})
        for toolchains in saved['results']['sum'].values():
            self.assertEqual(set(toolchains), {'clang'})
            self.assertEqual(set(toolchains['clang']), {'small'})
        self.assertIsNone(saved['baseline'])
        self.assertEqual(saved['mismatch'], {})
        self.assertEqual(saved['sizes'], ['small'])
        self.assertEqual(saved['toolchains'], ['clang'])
        self.assertEqual(saved['tcdefs'], {'clang': {'desc': 'current compiler', 'opt': '-O2'}})
        self.assertEqual(saved['environment'], dict(host='current host', cpu='current CPU',
            ram_bytes=16 << 30, os='current OS', affinity=[3, 7], rust_version=None))
        self.assertIn('| CPU affinity | 3, 7 |', text)
        self.assertNotIn('saved CPU', text)
        self.assertNotIn('Startup floor', text)

    def test_report_only_uses_saved_environment_without_host_or_compiler_probes(self):
        saved = copy.deepcopy(self.saved)
        saved.update(results={'sum': {'cpp vector': {'clang': {'small': self.legacy}}}},
                     baseline=None, mismatch={}, sizes=['small'], toolchains=['clang'])
        self.statefile.write_text(json.dumps(saved))
        with patch.object(suite.tc, 'cpu_name', side_effect=AssertionError('CPU probe')), \
             patch.object(suite.tc, 'ram_bytes', side_effect=AssertionError('RAM probe')), \
             patch.object(suite.tc, 'os_name', side_effect=AssertionError('OS probe')), \
             patch.object(suite.tc, 'find_ccs', side_effect=AssertionError('C compiler probe')), \
             patch.object(suite.tc, 'find_rustc', side_effect=AssertionError('Rust compiler probe')), \
             patch('platform.node', side_effect=AssertionError('host probe')), \
             patch('os.sched_getaffinity', side_effect=AssertionError('affinity probe'), create=True):
            text = self.run_suite('--report-only')
        for row in ('| Host | saved host |', '| CPU | saved CPU |', '| RAM | 8 GB |',
                    '| OS | saved OS |', '| CPU affinity | 2, 4 |',
                    '| Rust | saved rustc, `-O -C codegen-units=1` |'):
            self.assertIn(row, text)
        self.assertEqual(json.loads(self.statefile.read_text()), saved)

    def test_old_state_without_environment_does_not_describe_current_host(self):
        saved = copy.deepcopy(self.saved)
        del saved['environment']
        saved.update(results={'sum': {'cpp vector': {'clang': {'small': self.legacy}}}},
                     baseline=None, mismatch={}, sizes=['small'], toolchains=['clang'])
        self.statefile.write_text(json.dumps(saved))
        with patch.object(suite.tc, 'find_ccs', return_value={}), \
             patch.object(suite.tc, 'find_rustc', return_value=None), \
             patch.object(suite.tc, 'cpu_name', side_effect=AssertionError('CPU probe')), \
             patch.object(suite.tc, 'ram_bytes', side_effect=AssertionError('RAM probe')), \
             patch.object(suite.tc, 'os_name', side_effect=AssertionError('OS probe')):
            text = self.run_suite('--report-only')
        for name in ('Host', 'CPU', 'RAM', 'OS', 'CPU affinity', 'Rust'):
            self.assertIn(f'| {name} | not recorded |', text)

    def test_unavailable_affinity_is_recorded_as_unknown(self):
        for error in (AttributeError, OSError):
            with self.subTest(error=error), \
                 patch('os.sched_getaffinity', side_effect=error, create=True), \
                 patch('platform.node', return_value='host'), \
                 patch.object(suite.tc, 'cpu_name', return_value='CPU'), \
                 patch.object(suite.tc, 'ram_bytes', return_value=8 << 30), \
                 patch.object(suite.tc, 'os_name', return_value='OS'):
                self.assertIsNone(suite.measurement_environment(None)['affinity'])


if __name__ == '__main__':
    unittest.main()
