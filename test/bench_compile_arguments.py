#!/usr/bin/env python3
"""Compile argument regressions. Tiny checksum checks, no performance tests."""
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

exe = pathlib.Path(sys.argv.pop(1)).resolve()


class CompileArguments(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='goose-compile-arguments-')
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.source = self.root / 'entry.goose'
        self.source.write_text('extern fn value() -> i64;\nbench "input" fn entry() -> i64 { value() }\n')
        self.header = self.root / 'value.h'
        self.header.write_text('#include <stdint.h>\n#ifdef _REENTRANT\n#include "threaded.h"\n'
                               '#else\n#define VALUE 0\n#endif\n'
                               'static int64_t value(void) { return VALUE; }\n')
        self.threaded = self.root / 'threaded.h'
        self.threaded.write_text('#define VALUE 42\n')
        self.report = self.root / 'report.json'

    def invoke(self, *options):
        return subprocess.run([str(exe), 'bench', str(self.source), '--include', str(self.header),
                               '--temperature', 'off', '--samples', '5', '--warmups', '1',
                               '--json', str(self.report), *map(str, options)],
                              capture_output=True, text=True, timeout=120)

    def test_conditional_header_identity(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        first = json.loads(self.report.read_text())
        inputs = {entry['path']: entry['sha256'] for entry in first['source']['files']}
        self.assertIn(str(self.threaded), inputs)
        self.assertEqual(inputs[str(self.threaded)], hashlib.sha256(self.threaded.read_bytes()).hexdigest())
        self.assertEqual(first['results'][0]['checksum']['components'][0]['value'], '42')
        self.threaded.write_text('#define VALUE 43\n')
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        second = json.loads(self.report.read_text())
        self.assertNotEqual(first['configurations'][0]['id'], second['configurations'][0]['id'])
        self.assertEqual(second['results'][0]['checksum']['components'][0]['value'], '43')

    def test_conditional_header_output_preserved(self):
        before = self.threaded.read_bytes()
        self.report = self.threaded
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('would overwrite an input', result.stdout + result.stderr)
        self.assertEqual(self.threaded.read_bytes(), before)

    def test_conditional_header_build_change(self):
        compiler = shutil.which('cc')
        wrapper = self.root / 'cc-wrapper'
        wrapper.write_text('#!/usr/bin/env python3\nimport os, pathlib, sys\n'
                           'if "-Wl,-t" in sys.argv and "-M" not in sys.argv:\n'
                           f'    pathlib.Path({str(self.threaded)!r}).write_text("#define VALUE 99\\n")\n'
                           f'os.execv({compiler!r}, [{compiler!r}, *sys.argv[1:]])\n')
        wrapper.chmod(0o755)
        result = self.invoke('--cc', wrapper)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('changed during build', result.stdout + result.stderr)
        self.assertEqual(json.loads(self.report.read_text())['status'], 'failed')


if __name__ == '__main__':
    unittest.main()
