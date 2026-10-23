#!/usr/bin/env python3
"""Native definition strings/aliases in memory orders and page advice.
Compile generated C and execute at both Goose and C O0/O2. No TinyCC.
"""
import argparse
from pathlib import Path
import re
import shutil
import tempfile
from native_examples_support import ROOT, run

SOURCE = ROOT / 'test/memory/native_config_definitions/main.goose'
PROFILES = [dict(LOAD_ORDER='Acquire', STORE_ORDER='Release', CAS_SUCCESS='AcqRel',
                 CAS_FAILURE='Acquire', ADVICE='Sequential'),
            dict(LOAD_ORDER='SeqCst', STORE_ORDER='SeqCst', CAS_SUCCESS='SeqCst',
                 CAS_FAILURE='Relaxed', ADVICE='Random')]
BASE = dict(ALLOC_BYTES=128, MEM_BYTES=32, OFFSET=1, VALUE=4660, BIG_ENDIAN=False,
            USE_ALIAS=False, **PROFILES[0])
ORDERS = {'Relaxed':'__ATOMIC_RELAXED', 'Acquire':'__ATOMIC_ACQUIRE',
          'Release':'__ATOMIC_RELEASE', 'AcqRel':'__ATOMIC_ACQ_REL', 'SeqCst':'__ATOMIC_SEQ_CST'}


def has_advice_code(c, advice):
    # Three operands precede the selected integer policy; two location operands
    # follow it. Accept both LocArgs filename symbols and literal filenames.
    return re.search(r'\bgs_shared_page_advice\([^,;\n]+,[^,;\n]+,[^,;\n]+,\s*'
                     + str(advice) + r'\s*,\s*(?:gs_file\d+|"[^"\n]*")\s*,\s*\d+\s*\)', c) is not None


def check_advice_codegen():
    # Location arguments use a generated filename symbol. Keep the policy in
    # the fourth argument distinct from digits in the filename or source line.
    for filename in ('gs_file0', 'gs_file12', '"fixture.goose"'):
        for advice in (1, 2):
            call = f'gs_shared_page_advice(t1, t2, t3, {advice}, {filename}, 12);'
            assert has_advice_code(call, advice)
            assert not has_advice_code(call, 3 - advice)
    for call in ('gs_shared_page_advice(t1, t2, t3, advice, gs_file1, 1);',
                 'gs_shared_page_advice(t1, t2, t3, 12, gs_file1, 1);',
                 'gs_shared_page_advice(t1, t2, t3, 2, "1", 1);',
                 'gs_shared_page_advice(t1, t2, 1, gs_file1, 1);'):
        assert not has_advice_code(call, 1)


def flags(values):
    import json
    args = []
    for name, value in values.items():
        if value is not None:
            literal = json.dumps(value) if isinstance(value, (str, bool)) else str(value)
            args += ['--define', name + '=' + literal]
    return args


def reject_checks(goose):
    cases = [('LOAD_ORDER', 'Release', 'memory order'), ('STORE_ORDER','Acquire','memory order'),
             ('CAS_FAILURE','Release','failure'), ('CAS_SUCCESS','Relaxed','failure'),
             ('ADVICE','UnknownAdvice','page advice'), ('LOAD_ORDER',7,'compile-time string'),
             ('LOAD_ORDER',True,'compile-time string'), ('ADVICE',7,'compile-time string'),
             ('LOAD_ORDER',None,'LOAD_ORDER'), ('ADVICE',None,'ADVICE'),
             ('BIG_ENDIAN','false','bool'), ('OFFSET','1','integer'), ('VALUE','4660','u16')]
    checks = 0
    for level in ('-O0','-O2'):
        for alias in (False, True):
            for key, value, message in cases:
                values = dict(BASE, USE_ALIAS=alias)
                values[key] = value
                result = run([goose, 'check', level, *flags(values), SOURCE], ok=False)
                assert message in result.stderr, (key, value, message, result.stderr)
                checks += 1
    return checks


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('goose', type=Path)
    ap.add_argument('--cc', default=shutil.which('clang') or shutil.which('gcc') or 'cc')
    ns = ap.parse_args()
    check_advice_codegen()
    goose = ns.goose.resolve()
    assert SOURCE.exists(), SOURCE
    configurations = 0
    with tempfile.TemporaryDirectory(prefix='goose-native-config-') as directory:
        root = Path(directory)
        for level in ('-O0','-O2'):
            for profile in PROFILES:
                for alias in (False, True):
                    for endian in (False, True):
                        values = dict(BASE, **profile)
                        values.update(USE_ALIAS=alias, BIG_ENDIAN=endian)
                        generated = root / 'native.c'
                        run([goose,'--standalone',level,*flags(values),SOURCE,'-o',generated])
                        c = generated.read_text()
                        assert 'build::' not in c
                        assert re.search(r'__atomic_load_n\([A-Za-z_]\w*,\s*' + ORDERS[profile['LOAD_ORDER']] + r'\)', c)
                        assert re.search(r'__atomic_store_n\([^;\n]*,\s*' + ORDERS[profile['STORE_ORDER']] + r'\)', c)
                        assert re.search(r'__atomic_compare_exchange_n\([^;\n]*,\s*' + ORDERS[profile['CAS_SUCCESS']] + r',\s*' + ORDERS[profile['CAS_FAILURE']] + r'\)', c)
                        advice = 1 if profile['ADVICE'] == 'Sequential' else 2
                        assert has_advice_code(c, advice), (profile['ADVICE'], advice)
                        for native in ('-O0','-O2'):
                            app = root / 'native'
                            run([ns.cc,native,'-std=c11','-pthread',generated,'-lm','-o',app],timeout=600)
                            result = run([app,root/'mapping.bin'])
                            assert result.stdout == f'native config ok {str(alias).lower()} {str(endian).lower()}\n'
                            configurations += 1
        negative = reject_checks(goose)
        # Native const-if ignores inactive invalid/non-string/undefined order
        # operands, while selecting that arm diagnoses the actual load order.
        selected = root / 'selected.goose'
        selected.write_text('fn main() { let o, ok = shared_alloc(64); assert(ok); '
                            'let t = shared_atomic_u32(o, 0, 0); '
                            'const if build::SELECT_INVALID { atomic_load(t, build::ORDER); } '
                            'else { atomic_load(t, "Acquire"); } assert(shared_close(o)); }\n')
        for level in ('-O0','-O2'):
            for invalid in ('Release', 7, None):
                args = flags(dict(SELECT_INVALID=False, ORDER=invalid))
                generated = root / 'selected.c'
                run([goose,'--standalone',level,*args,selected,'-o',generated])
                for native in ('-O0','-O2'):
                    app = root / 'selected'
                    run([ns.cc,native,'-std=c11','-pthread',generated,'-lm','-o',app],timeout=600)
                    run([app])
                    configurations += 1
            result = run([goose,'check',level,*flags(dict(SELECT_INVALID=True,ORDER='Release')),selected],ok=False)
            assert 'memory order' in result.stderr
            negative += 1
    print(f'native config definitions: {configurations} native configurations passed; {negative} rejection checks')


if __name__ == '__main__':
    main()
