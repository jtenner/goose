#!/usr/bin/env python3
"""Deterministic deferred-transaction scaling contract; no timing thresholds.

python3 test/deferred_state_work.py /path/to/goose
The opt-in work report counts copied records and visited AST types, not time.
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('compiler_check', ROOT / 'bench/shared_native/compiler_check.py')
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


def main():
    exe = Path(sys.argv[1]).resolve()
    checks = 0
    failures = []
    with tempfile.TemporaryDirectory(prefix='goose-deferred-work-') as directory:
        source = Path(directory) / 'work.goose'

        def check(text, ok=True, verify=False):
            nonlocal checks
            source.write_text(text)
            env = dict(os.environ, GOOSE_DEFERRED_WORK='1')
            env.pop('GOOSE_DEFERRED_VERIFY', None)
            if verify:
                env['GOOSE_DEFERRED_VERIFY'] = '1'
            p = subprocess.run([exe, 'check', source], capture_output=True, text=True, env=env, timeout=90)
            assert p.returncode in (0, 1), (p.returncode, p.stderr[-4000:])
            assert (p.returncode == 0) == ok, (p.returncode, p.stdout, p.stderr[-4000:])
            reports = [json.loads(line.split(' ', 1)[1]) for line in p.stderr.splitlines()
                       if line.startswith('GOOSE_DEFERRED_WORK ')]
            assert len(reports) == 1, p.stderr[-4000:]
            checks += 1
            return reports[0]

        # Ordinary semantic checking stays enabled, including bad unused bodies.
        check('fn bad()->i64{missing()}fn main(){}', ok=False)
        for case, stdlib, named in [('ordinary', False, False), ('ordinary', False, True),
                                    ('ordinary', True, False), ('calls', True, True),
                                    ('arrays', False, True), ('stores', True, True),
                                    ('deferred', False, False), ('deferred-stores', True, True)]:
            results = [check(bench.source_for(40, size, case, stdlib, named)) for size in (0, 24, 48, 96)]
            assert results[-1]['roots'] >= 96, results  # no skip-all-unused shortcut
            assert (results[-1]['deferrals'] >= 96) == case.startswith('deferred'), results
            for key in ('variables', 'arrays', 'typevisits', 'auxiliary'):
                # Fixed import/declaration setup is subtracted. The contract is
                # proportional to this root's work, independent of old locals
                # and types. Fourfold input allows fourfold work plus slack.
                small = results[1][key] - results[0][key]
                large = results[3][key] - results[0][key]
                if large > 4 * small + 96:
                    failures.append((case, stdlib, named, key, results))
            if results[-1]['variables'] - results[0]['variables'] > 12 * 96:
                failures.append((case, 'unrelated globals copied', results))
            # The exhaustive oracle runs separately from the cost contract.
            check(bench.source_for(40, 12, case, stdlib, named), verify=True)
        # Growing unrelated globals must not cause full-record copies per root.
        small = check(bench.source_for(40, 48, 'calls', True, True))
        large = check(bench.source_for(160, 48, 'calls', True, True))
        if large['variables'] > small['variables'] + 120:
            failures.append(('unrelated global growth', small, large))
        # Earlier live obligations must survive a discarded root; an unused
        # deferred writable binding must disappear. Actual calls still conflict.
        helper = 'fn stop(){let r=&FLAG;const if true{return 7 from outer;}}'
        live = 'let FLAG=true;' + helper + 'fn outer()->i64{0}'
        api = 'export fn api()->i64{const if FLAG{1}else{2}}'
        assert check(live + api + 'fn main(){}')['deferrals'] >= 1
        check(live + api + 'fn main(){const if FLAG{}let r=&FLAG;}', ok=False)
        check((live + api + 'fn main(){outer();}').replace('fn outer()->i64{0}',
                                                               'fn outer()->i64{stop();0}'), ok=False)
        for value in ('0.0/0.0', '(1e308*1e308)-(1e308*1e308)', '-0.0', '0.0',
                      '1e308*1e308', '-1e308*1e308'):
            check(f'let X={value};fn unused()->i64{{1}}fn main(){{}}', verify=True)
    assert not failures, json.dumps(failures, indent=2)
    print(f'deferred-state deterministic work: {checks} checks passed (no timings)')


if __name__ == '__main__':
    main()
