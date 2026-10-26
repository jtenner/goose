#!/usr/bin/env python3
"""Runtime cache content checks use isolated inputs, never timing assertions."""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

exe = pathlib.Path(sys.argv.pop(1)).resolve()


class RuntimeCache(unittest.TestCase):
    def test_timestamp_preserving_runtime_header_change(self):
        with tempfile.TemporaryDirectory(prefix='goose-runtime-cache-') as directory:
            root = pathlib.Path(directory)
            source = root / 'entry.goose'
            source.write_text('extern fn runtime_value() -> i64;\n'
                              'bench "input" fn entry() -> i64 { runtime_value() }\n')
            header = root / 'runtime-value.h'
            header.write_text('#include <stdint.h>\nint64_t runtime_value(void) { return 42; }\n')
            wrapper = root / 'cc-wrapper'
            compiler = shutil.which('cc')
            count = root / 'compiles'
            wrapper.write_text('#!/usr/bin/env python3\nimport os, pathlib, sys\n'
                               'args = sys.argv[1:]\n'
                               'if any(x.endswith("/goose_runtime.c") for x in args):\n'
                               f'    args += ["-include", {str(header)!r}]\n'
                               '    if "-c" in args:\n'
                               f'        with open({str(count)!r}, "a") as out: out.write("compile\\n")\n'
                               f'os.execv({compiler!r}, [{compiler!r}, *args])\n')
            wrapper.chmod(0o755)
            env = dict(os.environ, GOOSE_HOME=str(root / 'cache'))
            report = root / 'report.json'

            def run():
                result = subprocess.run([str(exe), 'bench', str(source), '--cc', str(wrapper),
                                         '--temperature', 'off', '--samples', '5', '--warmups', '1',
                                         '--json', str(report)], capture_output=True, text=True,
                                        timeout=120, env=env)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                data = json.loads(report.read_text())
                self.assertEqual(data['status'], 'ok')
                inputs = {entry['path']: entry['sha256'] for entry in data['source']['files']}
                self.assertEqual(inputs[str(header)], hashlib.sha256(header.read_bytes()).hexdigest())
                return data

            first = run()
            self.assertEqual(first['results'][0]['checksum']['components'][0]['value'], '42')
            self.assertEqual(count.read_text().splitlines(), ['compile'])
            repeat = run()
            self.assertEqual(first['configurations'][0]['id'], repeat['configurations'][0]['id'])
            self.assertEqual(count.read_text().splitlines(), ['compile'])
            before = header.stat()
            header.write_text(header.read_text().replace('42', '43'))
            os.utime(header, ns=(before.st_atime_ns, before.st_mtime_ns))
            self.assertEqual(header.stat().st_mtime_ns, before.st_mtime_ns)
            second = run()
            self.assertNotEqual(first['configurations'][0]['id'], second['configurations'][0]['id'])
            self.assertEqual(second['results'][0]['checksum']['components'][0]['value'], '43')
            self.assertEqual(count.read_text().splitlines(), ['compile', 'compile'])
            # An object from an older Goose has no content stamp.
            stamp = next((root / 'cache' / 'build' / 'runtime').rglob('goose-bench-inputs.txt'))
            stamp.unlink()
            rebuilt = run()
            self.assertEqual(rebuilt['results'][0]['checksum']['components'][0]['value'], '43')
            self.assertEqual(count.read_text().splitlines(), ['compile', 'compile', 'compile'])


if __name__ == '__main__':
    unittest.main()
