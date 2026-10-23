#!/usr/bin/env python3
"""Narrow shader LSan suppression contract; optional leak-enabled compiler probe.

python3 test/sanitizer_suppressions.py [path/to/asan-goose]
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SUPPRESSIONS = ROOT / 'test/lsan.supp'
EXPECTED = {'cute_spirv.h', 'cspv_parse_unary', 'cspv_parse_block',
            'cspv_gen_top_level', 'ck_map_ensure_capacity'}
checks = 0
if len(sys.argv) > 1:
    # Exercise the line-table-only stacks even on hosts without llvm-symbolizer.
    symbolizer = shutil.which('addr2line')
    assert symbolizer, 'addr2line is required for this Linux sanitizer probe'
    env = dict(os.environ)
    options = (f'allow_addr2line=true:external_symbolizer_path={symbolizer}:detect_leaks=1')
    env['ASAN_OPTIONS'] = ':'.join(filter(None, [env.get('ASAN_OPTIONS'), options]))
    env['LSAN_OPTIONS'] = ':'.join(filter(None, [env.get('LSAN_OPTIONS'), f'suppressions={SUPPRESSIONS}']))
    result = subprocess.run([str(Path(sys.argv[1]).resolve()), '--compile-shader',
                             str(ROOT / 'test/gfx/probe.frag')],
                            capture_output=True, text=True, env=env, timeout=90)
    output = result.stdout + result.stderr
    assert result.returncode == 0, (result.returncode, output)
    assert 'fragment shader' in output, output
    assert not any(marker in output for marker in ('AddressSanitizer', 'LeakSanitizer',
                                                   'UndefinedBehaviorSanitizer', 'runtime error:')), output
    checks += 1
# No broad ckit/allocator/compiler suppression, or suppression of new journal code.
actual = {line.strip().removeprefix('leak:') for line in SUPPRESSIONS.read_text().splitlines()
          if line.strip().startswith('leak:')}
assert actual == EXPECTED, (actual, EXPECTED)
checks += 1
print(f'shader sanitizer suppressions: {checks} checks passed (leak detection enabled for probe)')
