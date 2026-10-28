#!/usr/bin/env python3
"""R1 correctness checks. No timing or benchmark work."""
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'test'))
import run_tests
from capture import HERE, run

exe = str((REPO / 'build-r2-r1/goose').resolve())
r = run_tests.Runner(Path(exe), 1)
results = []
positives = sorted((REPO / 'test/typing').glob('array_equality*.goose'))
positives += [REPO / 'test/codegen' / (n + '.goose') for n in
              ('byte_run_equality', 'scalar_struct_equality', 'bytes_value_equality', 'float_equality')]
positives += [REPO / 'test/typing' / (n + '.goose') for n in
              ('optional_call_flow', 'break_exit_flow', 'flow_scope_projection')]
negatives = [REPO / 'test/errors_tc' / (n + '.goose') for n in
             ('array_equality_double_assignment', 'array_equality_unassigned_left',
              'array_inequality_implicit_slice_shrink', 'shrink_temporary_implicit_slice',
              'shrink_temporary_binary', 'empty_array_equality')]
for f in positives:
    for mode, args in [('roundtrip', ['--roundtrip', '--check']), ('O0', ['--jit', '-O0']), ('O2', ['--jit', '-O2'])]:
        name = 'fixed-' + f.stem + '-' + mode
        status = run(name, [exe, *args, str(f)])
        out, err = [(HERE / (name + suffix)).read_text() for suffix in ('.stdout', '.stderr')]
        assert status == 0, err
        assert r.check_warnings(f, out, err)
        if mode != 'roundtrip':
            assert out == (REPO / 'test/expected' / (f.stem + '.out')).read_text(), out
        results.append({'test': str(f.relative_to(REPO)), 'mode': mode, 'status': status, 'passed': True})
for f in negatives:
    name = 'fixed-' + f.stem
    status = run(name, [exe, '--check', str(f)])
    out, err = [(HERE / (name + suffix)).read_text() for suffix in ('.stdout', '.stderr')]
    assert r.check_error(f, 'typecheck-error', status, out, err), err
    results.append({'test': str(f.relative_to(REPO)), 'mode': 'expected diagnostic', 'status': status, 'passed': True})
for n, expected in [('equality_recheck', 'false\n2\n'), ('equality_same_type', 'true\n2\n'), ('equality_bound_rhs', 'false\n2\n')]:
    for mode in ['O0', 'O2']:
        name = 'fixed-original-' + n + '-' + mode
        status = run(name, [exe, str(HERE / (n + '.goose')), '-' + mode])
        assert status == 0
        assert (HERE / (name + '.stdout')).read_text() == expected
        results.append({'test': n, 'mode': mode, 'status': status, 'passed': True})
assert r.failures == 0
(HERE / 'focused-results.json').write_text(json.dumps(results, indent=2) + '\n')
print(f'{len(results)} focused checks passed; {len(positives)} positive fixtures; {len(negatives)} negative fixtures; 3 retained cases')
