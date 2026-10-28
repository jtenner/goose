#!/usr/bin/env python3
"""Record source, configuration, and tested executable identity."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[4]
here = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

files = subprocess.check_output(['git', 'ls-files', '-z', 'src', 'third_party', 'cmake', 'CMakeLists.txt'], cwd=root).decode().split('\0')
inputs = {f: sha(root / f) for f in files if f and (root / f).is_file()}
record = {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
          'product_diff': subprocess.check_output(['git', 'diff', 'HEAD', '--', 'src', 'third_party', 'cmake', 'CMakeLists.txt'], cwd=root, text=True),
          'binary_path': str(root / 'build-r2-r1/goose'),
          'binary_sha256': sha(root / 'build-r2-r1/goose'),
          'build_inputs_sha256': inputs,
          'build_input_map_sha256': hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest(),
          'cache_sha256': sha(root / 'build-r2-r1/CMakeCache.txt'),
          'generated_version': (root / 'build-r2-r1/version/goose_version.h').read_text(),
          'version_output': subprocess.check_output([str(root / 'build-r2-r1/goose'), '--version'], cwd=root, text=True).strip()}
assert record['product_diff'] == ''
(here / (sys.argv[1] + '.json')).write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({k: v for k, v in record.items() if k not in ['build_inputs_sha256', 'product_diff']}, indent=2))
