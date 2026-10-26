#!/usr/bin/env python3
"""Missing root inputs must never permit report writes over sidecars."""
import pathlib
import subprocess
import sys
import tempfile
import unittest

exe = pathlib.Path(sys.argv.pop(1)).resolve()


class MissingSource(unittest.TestCase):
    def check_sidecar(self, option, derived=False):
        with tempfile.TemporaryDirectory(prefix='goose-missing-source-') as directory:
            root = pathlib.Path(directory)
            source = root / ('entry.samples.goose' if derived else 'entry.goose')
            sidecar = source.with_suffix('.build')
            before = b'c_defines = ["KEEP=42"];\n'
            sidecar.write_bytes(before)
            output = root / 'entry.build'
            result = subprocess.run([str(exe), 'bench', str(source), '--temperature', 'off',
                                     option, str(output)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn('cannot hash provenance input', result.stderr)
            self.assertEqual(sidecar.read_bytes(), before, result.stdout + result.stderr)
            if derived:
                self.assertFalse(output.exists())

    def test_missing_source_json_preserves_sidecar(self):
        self.check_sidecar('--json')

    def test_missing_source_summary_csv_preserves_sidecar(self):
        self.check_sidecar('--csv')

    def test_missing_source_sample_csv_preserves_sidecar(self):
        self.check_sidecar('--csv', derived=True)


if __name__ == '__main__':
    unittest.main()
